#!/usr/bin/env python3
"""
批量修复和补充产品 Logo

策略：
1. Clearbit Logo API (最佳质量)
2. Google Favicon API (备选)
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

# Logo 来源优先级
LOGO_SOURCES = {
    "clearbit": "https://logo.clearbit.com/{domain}",
    "google_favicon": "https://www.google.com/s2/favicons?domain={domain}&sz=128",
    "duckduckgo": "https://icons.duckduckgo.com/ip3/{domain}.ico",
}


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
    """检查 URL 是否可访问"""
    try:
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        return response.status_code == 200
    except Exception:
        return False


def get_logo_url(domain: str) -> tuple:
    """
    获取产品 logo URL
    
    返回: (logo_url, source)
    """
    if not domain:
        return None, None
    
    # 1. 尝试 Clearbit (最佳质量)
    clearbit_url = f"https://logo.clearbit.com/{domain}"
    if check_url_exists(clearbit_url):
        return clearbit_url, "clearbit"
    
    # 2. 尝试 Google Favicon
    google_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    # Google favicon 通常都存在，但可能是默认图标
    # 我们先尝试，后面可以人工筛选
    if check_url_exists(google_url):
        return google_url, "google"
    
    # 3. 尝试 DuckDuckGo
    ddg_url = f"https://icons.duckduckgo.com/ip3/{domain}.ico"
    if check_url_exists(ddg_url):
        return ddg_url, "duckduckgo"
    
    return None, None


def process_product(product: dict) -> dict:
    """处理单个产品，尝试获取 logo"""
    name = product.get('name', 'Unknown')
    website = product.get('website', '')
    current_logo = product.get('logo', '')
    
    # 检查是否需要修复
    needs_fix = False
    
    if not current_logo:
        needs_fix = True
    elif not current_logo.startswith('http'):
        needs_fix = True
    elif 'google.com/s2/favicons' in current_logo and 'sz=128' not in current_logo:
        # 升级低分辨率 favicon
        needs_fix = True
    
    if not needs_fix:
        return product
    
    # 提取域名
    domain = extract_domain(website)
    if not domain:
        print(f"  ⚠️  {name}: 无法提取域名")
        return product
    
    # 获取 logo
    logo_url, source = get_logo_url(domain)
    
    if logo_url:
        product['logo'] = logo_url
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
        logo = p.get('logo', '')
        if not logo:
            stats["no_logo"] += 1
            to_fix.append(p)
        elif not logo.startswith('http'):
            stats["invalid_logo"] += 1
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
                if result.get('logo') and result['logo'].startswith('http'):
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
