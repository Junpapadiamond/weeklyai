#!/usr/bin/env python3
"""
批量修复和补充产品 Logo

策略：
1. 官网 HTML 中声明的 apple-touch-icon / icon
2. 官网常见高质量图标路径
3. Clearbit Logo API (最后兜底)
3. 官网 favicon 提取
"""

import json
import os
import re
import sys
import time
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
TIMEOUT = 5
MAX_WORKERS = 10

LOGO_SOURCES = {
    "clearbit": "https://logo.clearbit.com/{domain}",
}
LOW_CONFIDENCE_SOURCES = {"bing", "google_favicon", "google", "duckduckgo", "iconhorse", "icon_horse", "faviconkit", "yandex"}
LOW_CONFIDENCE_HOST_MARKERS = (
    "favicon.bing.com",
    "google.com/s2/favicons",
    "icons.duckduckgo.com",
    "icon.horse",
    "favicon.yandex.net",
    "api.faviconkit.com",
)


def _has_low_confidence_marker(value: str) -> bool:
    text = str(value or "").strip().lower()
    return bool(text) and any(marker in text for marker in LOW_CONFIDENCE_HOST_MARKERS)


def extract_domain(url: str) -> str:
    """从 URL 提取域名"""
    if not url:
        return ""
    
    try:
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        domain = re.sub(r'^www\.', '', domain)
        return domain
    except Exception:
        return ""


def check_url_exists(url: str, timeout: int = TIMEOUT) -> bool:
    """检查 URL 是否可访问（部分站点不支持 HEAD）"""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=headers
        )
        if 200 <= response.status_code < 400:
            return True
    except Exception:
        pass
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=headers,
            stream=True
        )
        return 200 <= response.status_code < 400
    except Exception:
        return False


def _absolute_url(base: str, href: str) -> str:
    if href.startswith("//"):
        return f"https:{href}"
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("/"):
        return f"https://{base}{href}"
    return f"https://{base}/{href}"


def _extract_icon_from_html(domain: str) -> str:
    """从主页 HTML 提取 favicon/icon 链接"""
    try:
        resp = requests.get(
            f"https://{domain}",
            timeout=TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if not (200 <= resp.status_code < 400):
            return ""
        html = resp.text
        # 优先 apple-touch-icon，其次 icon/shortcut icon
        patterns = [
            r'rel=["\']apple-touch-icon["\'][^>]*href=["\']([^"\']+)["\']',
            r'rel=["\']icon["\'][^>]*href=["\']([^"\']+)["\']',
            r'rel=["\']shortcut icon["\'][^>]*href=["\']([^"\']+)["\']',
        ]
        for pat in patterns:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                return _absolute_url(domain, m.group(1))
    except Exception:
        return ""
    return ""


def _extract_logo_domain(logo_url: str) -> str:
    if not logo_url:
        return ""
    try:
        if "domain=" in logo_url:
            m = re.search(r"domain=([^&]+)", logo_url)
            return (m.group(1) if m else "").lower()
        if "url=" in logo_url:
            m = re.search(r"url=([^&]+)", logo_url)
            return (m.group(1) if m else "").lower()
        parsed = urlparse(logo_url)
        host = (parsed.netloc or "").lower()
        path = (parsed.path or "").lower()
        if "logo.clearbit.com" in host:
            return path.strip("/").split("/")[0]
        return host
    except Exception:
        return ""


def _is_low_confidence_logo(product: dict) -> bool:
    source = str(product.get("logo_source") or "").strip().lower()
    if source in LOW_CONFIDENCE_SOURCES:
        return True

    return _has_low_confidence_marker(product.get("logo_url")) or _has_low_confidence_marker(product.get("logo"))


def _sanitize_logo_fields(product: dict) -> bool:
    """删除低质量 provider 残留，但保留已经存在的正规 logo。"""
    changed = False
    for field in ("logo", "logo_url"):
        if _has_low_confidence_marker(product.get(field)):
            product[field] = ""
            changed = True

    source = str(product.get("logo_source") or "").strip().lower()
    if source in LOW_CONFIDENCE_SOURCES:
        product["logo_source"] = ""
        changed = True

    return changed

def get_logo_url(domain: str) -> tuple:
    """
    获取产品 logo URL
    
    返回: (logo_url, source)
    """
    if not domain:
        return None, None
    
    # 尝试从主页 HTML 提取
    extracted = _extract_icon_from_html(domain)
    if extracted and check_url_exists(extracted):
        return extracted, "html"

    # 常见的站点自带图标路径优先于第三方 favicon provider
    direct_candidates = [
        (f"https://{domain}/apple-touch-icon.png", "apple_touch_icon"),
        (f"https://{domain}/apple-touch-icon-precomposed.png", "apple_touch_icon"),
        (f"https://{domain}/favicon-32x32.png", "favicon"),
        (f"https://{domain}/favicon.ico", "favicon"),
    ]
    for url, source in direct_candidates:
        if check_url_exists(url):
            return url, source

    # 最后才兜底 Clearbit
    for source, pattern in LOGO_SOURCES.items():
        url = pattern.format(domain=domain)
        if check_url_exists(url):
            return url, source
    
    return None, None


def process_product(product: dict) -> dict:
    """处理单个产品，尝试获取 logo"""
    name = product.get('name', 'Unknown')
    website = product.get('website', '')
    _sanitize_logo_fields(product)
    current_logo = product.get('logo_url') or product.get('logo', '')
    
    # 检查是否需要修复
    needs_fix = False

    if not current_logo:
        needs_fix = True
    elif not current_logo.startswith('http'):
        needs_fix = True
    elif _is_low_confidence_logo(product):
        needs_fix = True
    else:
        # 如果 logo 域名与网站不匹配，强制更新
        website_domain = extract_domain(website)
        logo_domain = _extract_logo_domain(current_logo)
        if website_domain and logo_domain and website_domain not in logo_domain:
            needs_fix = True
    
    if not needs_fix:
        return product
    
    # 提取域名
    if website and website.lower() == "unknown":
        print(f"  ⚠️  {name}: website unknown")
        return product

    domain = extract_domain(website)
    if not domain:
        print(f"  ⚠️  {name}: 无法提取域名")
        return product
    
    # 获取 logo
    logo_url, source = get_logo_url(domain)
    
    if logo_url:
        product['logo_url'] = logo_url
        product['logo_source'] = source
        print(f"  ✅ {name}: {source} ({domain})")
    else:
        print(f"  ❌ {name}: 无法获取 logo ({domain})")
    
    return product


def fix_logos(input_path: str, output_path: str = None, dry_run: bool = False):
    """
    批量修复产品 logo
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径 (默认覆盖输入)
        dry_run: 预览模式
    """
    if not output_path:
        output_path = input_path
    
    # 加载数据
    print(f"📂 加载数据: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"   共 {len(products)} 个产品")
    
    # 统计
    stats = {
        "total": len(products),
        "no_logo": 0,
        "invalid_logo": 0,
        "fixed": 0,
        "failed": 0,
    }
    
    # 找出需要修复的产品
    to_fix = []
    for p in products:
        logo = p.get('logo_url') or p.get('logo', '')
        if not logo:
            stats["no_logo"] += 1
            to_fix.append(p)
        elif not logo.startswith('http'):
            stats["invalid_logo"] += 1
            to_fix.append(p)
        elif _is_low_confidence_logo(p):
            to_fix.append(p)
        else:
            website = p.get('website', '')
            website_domain = extract_domain(website)
            logo_domain = _extract_logo_domain(logo)
            if website_domain and logo_domain and website_domain not in logo_domain:
                to_fix.append(p)
    
    print(f"\n📊 统计:")
    print(f"   无 logo: {stats['no_logo']}")
    print(f"   无效 logo: {stats['invalid_logo']}")
    print(f"   需要修复: {len(to_fix)}")
    
    if dry_run:
        print("\n🔍 预览模式，不会修改文件")
        print("\n需要修复的产品:")
        for p in to_fix[:20]:
            print(f"  - {p.get('name')}: {p.get('website', 'no url')}")
        if len(to_fix) > 20:
            print(f"  ... 还有 {len(to_fix) - 20} 个")
        return
    
    print(f"\n🔧 开始修复 {len(to_fix)} 个产品的 logo...")
    
    # 使用线程池并行处理
    fixed_products = {p.get('name'): p for p in products}
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_product, p): p for p in to_fix}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                name = result.get('name')
                logo_val = result.get('logo_url') or result.get('logo', '')
                if logo_val and logo_val.startswith('http'):
                    fixed_products[name] = result
                    stats["fixed"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                print(f"  ❌ Error: {e}")
                stats["failed"] += 1
    
    # 更新产品列表
    updated_products = list(fixed_products.values())
    
    # 保存
    print(f"\n💾 保存到: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(updated_products, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 修复统计:")
    print(f"   成功修复: {stats['fixed']}")
    print(f"   修复失败: {stats['failed']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="批量修复产品 Logo")
    parser.add_argument(
        "--input", "-i",
        default="data/products_featured.json",
        help="输入文件路径"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径 (默认覆盖输入)"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="预览模式，不修改文件"
    )
    
    args = parser.parse_args()
    
    # 确定文件路径
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(script_dir, args.input)
    output_path = os.path.join(script_dir, args.output) if args.output else input_path
    
    fix_logos(input_path, output_path, args.dry_run)


if __name__ == "__main__":
    main()
