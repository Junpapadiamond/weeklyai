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
import requests
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
TIMEOUT = 5
MAX_WORKERS = 10
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

LOW_CONFIDENCE_SOURCES = {
    "bing",
    "google_favicon",
    "google",
    "duckduckgo",
    "iconhorse",
    "icon_horse",
    "faviconkit",
    "yandex",
    "clearbit",
}
LOW_CONFIDENCE_HOST_MARKERS = (
    "favicon.bing.com",
    "google.com/s2/favicons",
    "icons.duckduckgo.com",
    "icon.horse",
    "favicon.yandex.net",
    "api.faviconkit.com",
    "logo.clearbit.com",
    "/logos/custom/default-ai.svg",
    "logo-default.png",
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
    """检查 URL 是否可访问且是图片类型。"""
    headers = {"User-Agent": USER_AGENT}

    def _is_image_response(resp: requests.Response) -> bool:
        if not (200 <= resp.status_code < 400):
            return False
        content_type = str(resp.headers.get("content-type") or "").lower()
        if not content_type:
            return False
        return (
            content_type.startswith("image/")
            or "image/svg+xml" in content_type
            or "x-icon" in content_type
            or "vnd.microsoft.icon" in content_type
        )

    try:
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=headers,
        )
        if _is_image_response(response):
            return True
    except Exception:
        pass

    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=headers,
            stream=True,
        )
        return _is_image_response(response)
    except Exception:
        return False


def _extract_icon_size(tag: str) -> int:
    match = re.search(r'sizes=["\']([^"\']+)["\']', tag, re.IGNORECASE)
    if not match:
        return 0
    size_text = match.group(1).lower()
    if "any" in size_text:
        return 1024
    values = re.findall(r"(\d+)\s*x\s*(\d+)", size_text)
    if not values:
        return 0
    return max(int(w) * int(h) for w, h in values)


def _extract_icon_candidates_from_html(base_url: str, html: str) -> list[tuple[int, str]]:
    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    for tag in re.findall(r"<link\b[^>]*>", html, re.IGNORECASE):
        rel_match = re.search(r'rel=["\']([^"\']+)["\']', tag, re.IGNORECASE)
        href_match = re.search(r'href=["\']([^"\']+)["\']', tag, re.IGNORECASE)
        if not rel_match or not href_match:
            continue
        rel = rel_match.group(1).lower()
        if "icon" not in rel:
            continue
        href = href_match.group(1).strip()
        if not href or href.startswith("data:"):
            continue

        absolute = urljoin(base_url, href)
        if _has_low_confidence_marker(absolute):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)

        score = _extract_icon_size(tag)
        if "apple-touch-icon" in rel:
            score += 10000
        elif "shortcut icon" in rel:
            score += 9000
        else:
            score += 8000

        if absolute.lower().endswith(".svg"):
            score += 500
        if "favicon" in absolute.lower():
            score += 200
        if "logo" in absolute.lower():
            score += 100

        candidates.append((score, absolute))

    for meta_pattern in (
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    ):
        for match in re.finditer(meta_pattern, html, re.IGNORECASE):
            href = match.group(1).strip()
            if not href:
                continue
            absolute = urljoin(base_url, href)
            if _has_low_confidence_marker(absolute):
                continue
            if absolute in seen:
                continue
            lower = absolute.lower()
            if "logo" not in lower and "icon" not in lower and "favicon" not in lower:
                continue
            seen.add(absolute)
            candidates.append((1500, absolute))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates


def _extract_icon_from_html(domain: str) -> list[str]:
    """从主页 HTML 提取 icon 链接候选（按优先级排序）。"""
    roots = [f"https://{domain}"]
    if not str(domain).startswith("www."):
        roots.append(f"https://www.{domain}")

    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()
    for root in roots:
        try:
            resp = requests.get(
                root,
                timeout=TIMEOUT,
                allow_redirects=True,
                headers={"User-Agent": USER_AGENT},
            )
            if not (200 <= resp.status_code < 400):
                continue
            html_candidates = _extract_icon_candidates_from_html(resp.url, resp.text)
            for score, url in html_candidates:
                if url in seen:
                    continue
                seen.add(url)
                candidates.append((score, url))
        except Exception:
            continue

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [url for _, url in candidates]


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

def get_logo_url(domain: str, allow_clearbit: bool = False) -> tuple:
    """
    获取产品 logo URL
    
    返回: (logo_url, source)
    """
    if not domain:
        return None, None
    
    # 先用 HTML 提取出的 icon 候选，优先级最高
    extracted_candidates = _extract_icon_from_html(domain)
    # 上限控制：只探测前几项高优先级 icon，避免个别站点返回超长列表导致超时。
    for extracted in extracted_candidates[:8]:
        if _has_low_confidence_marker(extracted):
            continue
        if check_url_exists(extracted):
            return extracted, "html"

    # 再走常见站点图标路径
    hosts = [domain]
    if not str(domain).startswith("www."):
        hosts.append(f"www.{domain}")

    direct_candidates = []
    for host in hosts:
        direct_candidates.extend([
            (f"https://{host}/apple-touch-icon.png", "apple_touch_icon"),
            (f"https://{host}/apple-touch-icon-precomposed.png", "apple_touch_icon"),
            (f"https://{host}/favicon-196x196.png", "favicon"),
            (f"https://{host}/favicon-96x96.png", "favicon"),
            (f"https://{host}/favicon-32x32.png", "favicon"),
            (f"https://{host}/favicon.svg", "favicon"),
            (f"https://{host}/favicon.ico", "favicon"),
        ])
    for url, source in direct_candidates:
        if _has_low_confidence_marker(url):
            continue
        if check_url_exists(url):
            return url, source

    # 可选 Clearbit 兜底（默认关闭，避免继续引入低质量来源）
    if allow_clearbit:
        clearbit = f"https://logo.clearbit.com/{domain}"
        if _has_low_confidence_marker(clearbit):
            return None, None
        if check_url_exists(clearbit):
            return clearbit, "clearbit"
    
    return None, None


def _should_fix_product(product: dict, only_missing: bool = False) -> bool:
    current_logo = product.get("logo_url") or product.get("logo", "")

    if only_missing:
        return not current_logo

    if not current_logo:
        return True
    if not current_logo.startswith("http"):
        return True
    if _is_low_confidence_logo(product):
        return True
    return False


def process_product(product: dict, only_missing: bool = False, allow_clearbit: bool = False) -> dict:
    """处理单个产品，尝试获取 logo"""
    name = product.get("name", "Unknown")
    website = product.get("website", "")
    _sanitize_logo_fields(product)

    if not _should_fix_product(product, only_missing=only_missing):
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
    logo_url, source = get_logo_url(domain, allow_clearbit=allow_clearbit)
    
    if logo_url:
        product['logo_url'] = logo_url
        product['logo_source'] = source
        print(f"  ✅ {name}: {source} ({domain})")
    else:
        print(f"  ❌ {name}: 无法获取 logo ({domain})")
    
    return product


def fix_logos(
    input_path: str,
    output_path: str = None,
    dry_run: bool = False,
    only_missing: bool = False,
    allow_clearbit: bool = False,
):
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
        if not only_missing and logo and not logo.startswith('http'):
            stats["invalid_logo"] += 1
        if _should_fix_product(p, only_missing=only_missing):
            to_fix.append(p)
    
    print(f"\n📊 统计:")
    print(f"   无 logo: {stats['no_logo']}")
    print(f"   无效 logo: {stats['invalid_logo']}")
    print(f"   需要修复: {len(to_fix)}")
    
    if dry_run:
        print("\n🔍 预览模式，不会修改文件")
        if only_missing:
            print("   模式: 仅补缺失 logo")
        print("\n需要修复的产品:")
        for p in to_fix[:20]:
            print(f"  - {p.get('name')}: {p.get('website', 'no url')}")
        if len(to_fix) > 20:
            print(f"  ... 还有 {len(to_fix) - 20} 个")
        return
    
    print(f"\n🔧 开始修复 {len(to_fix)} 个产品的 logo...")
    if only_missing:
        print("   模式: 仅补缺失 logo")
    if allow_clearbit:
        print("   模式: 允许 Clearbit 兜底")
    
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                process_product,
                p,
                only_missing,
                allow_clearbit,
            ): p
            for p in to_fix
        }
        
        for future in as_completed(futures):
            try:
                result = future.result()
                logo_val = result.get('logo_url') or result.get('logo', '')
                if logo_val and logo_val.startswith("http") and not _has_low_confidence_marker(logo_val):
                    stats["fixed"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                print(f"  ❌ Error: {e}")
                stats["failed"] += 1
    
    # process_product 是原地更新，保持原始顺序
    updated_products = products
    
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
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="只补缺失 logo，不修改已有 logo"
    )
    parser.add_argument(
        "--allow-clearbit",
        action="store_true",
        help="允许 clearbit 作为最后兜底（默认关闭）",
    )
    
    args = parser.parse_args()
    
    # 确定文件路径
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(script_dir, args.input)
    output_path = os.path.join(script_dir, args.output) if args.output else input_path
    
    fix_logos(
        input_path,
        output_path,
        args.dry_run,
        args.only_missing,
        args.allow_clearbit,
    )


if __name__ == "__main__":
    main()
