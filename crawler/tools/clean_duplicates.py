#!/usr/bin/env python3
"""
产品数据清理工具

功能：
1. 检测并移除重复产品
2. 修复缺失的 slug
3. 标记缺失 website 的产品
4. 生成清理报告
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.dedup import (
    DuplicateChecker,
    deduplicate_products,
    fix_missing_fields,
    generate_slug,
    normalize_domain,
    normalize_name,
    name_similarity,
    get_domain_key,
)


def load_products(filepath: str) -> List[Dict]:
    """加载产品数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_products(products: List[Dict], filepath: str):
    """保存产品数据"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


def analyze_duplicates(products: List[Dict], similarity_threshold: float = 0.90):
    """分析重复情况"""
    print("\n" + "=" * 60)
    print("重复分析报告")
    print("=" * 60)
    
    # 1. 域名重复（使用 domain_key，区分同一公司的不同产品）
    domain_map: Dict[str, List[Dict]] = {}
    for p in products:
        domain_key = get_domain_key(p.get('website', ''))
        if domain_key:
            if domain_key not in domain_map:
                domain_map[domain_key] = []
            domain_map[domain_key].append(p)
    
    domain_dups = {k: v for k, v in domain_map.items() if len(v) > 1}
    
    print(f"\n📍 域名重复 (同一 URL 路径): {len(domain_dups)} 个")
    for domain_key, items in domain_dups.items():
        print(f"\n  {domain_key}:")
        for item in items:
            print(f"    - {item.get('name')} (score: {item.get('dark_horse_index', '?')})")
    
    # 2. 名称重复
    name_map: Dict[str, List[Dict]] = {}
    for p in products:
        name = normalize_name(p.get('name', ''))
        if name:
            if name not in name_map:
                name_map[name] = []
            name_map[name].append(p)
    
    name_dups = {k: v for k, v in name_map.items() if len(v) > 1}
    
    print(f"\n📛 规范化名称重复: {len(name_dups)} 个")
    for name, items in name_dups.items():
        print(f"\n  [{name}]:")
        for item in items:
            print(f"    - {item.get('name')} ({item.get('website', 'no url')})")
    
    # 3. 相似名称
    print(f"\n🔍 相似名称检测 (阈值: {similarity_threshold:.0%}):")
    seen_pairs = set()
    similar_count = 0
    
    for i, p1 in enumerate(products):
        name1 = p1.get('name', '')
        if not name1:
            continue
        
        for p2 in products[i+1:]:
            name2 = p2.get('name', '')
            if not name2:
                continue
            
            sim = name_similarity(name1, name2)
            if sim >= similarity_threshold and sim < 1.0:
                pair = tuple(sorted([name1, name2]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    similar_count += 1
                    print(f"\n  [{sim:.0%}] {name1}")
                    print(f"       ↔ {name2}")
                    print(f"       URLs: {p1.get('website', 'N/A')} vs {p2.get('website', 'N/A')}")
    
    if similar_count == 0:
        print("  (无相似名称)")
    
    # 4. 缺失字段
    missing_website = [p for p in products if not p.get('website')]
    missing_slug = [p for p in products if not p.get('slug')]
    
    print(f"\n⚠️  缺失字段:")
    print(f"  - 无 website: {len(missing_website)} 个")
    print(f"  - 无 slug: {len(missing_slug)} 个")
    
    if missing_website:
        print("\n  无 website 的产品:")
        for p in missing_website[:10]:
            print(f"    - {p.get('name', 'N/A')}")
        if len(missing_website) > 10:
            print(f"    ... 还有 {len(missing_website) - 10} 个")
    
    return {
        "domain_duplicates": len(domain_dups),
        "name_duplicates": len(name_dups),
        "similar_names": similar_count,
        "missing_website": len(missing_website),
        "missing_slug": len(missing_slug),
    }


def clean_products(
    products: List[Dict],
    similarity_threshold: float = 0.85,
    fix_slugs: bool = True,
    remove_duplicates: bool = True,
    keep: str = "best"
) -> tuple:
    """
    清理产品数据
    
    Returns:
        (cleaned_products, removed_products, stats)
    """
    stats = {
        "original_count": len(products),
        "duplicates_removed": 0,
        "slugs_fixed": 0,
        "missing_website": 0,
    }
    
    # 1. 修复缺失的 slug
    if fix_slugs:
        for p in products:
            if not p.get('slug'):
                name = p.get('name', '')
                if name:
                    p['slug'] = generate_slug(name)
                    stats["slugs_fixed"] += 1
    
    # 2. 去重
    removed = []
    if remove_duplicates:
        products, removed = deduplicate_products(
            products,
            similarity_threshold=similarity_threshold,
            keep=keep
        )
        stats["duplicates_removed"] = len(removed)
    
    # 3. 统计缺失 website
    stats["missing_website"] = len([p for p in products if not p.get('website')])
    stats["final_count"] = len(products)
    
    return products, removed, stats


def main():
    parser = argparse.ArgumentParser(description="产品数据清理工具")
    parser.add_argument(
        "--input", "-i",
        default="data/products_featured.json",
        help="输入文件路径"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径（默认覆盖输入文件）"
    )
    parser.add_argument(
        "--backup", "-b",
        action="store_true",
        help="清理前备份原文件"
    )
    parser.add_argument(
        "--analyze-only", "-a",
        action="store_true",
        help="仅分析，不修改文件"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.85,
        help="名称相似度阈值 (默认: 0.85)"
    )
    parser.add_argument(
        "--keep",
        choices=["first", "best"],
        default="best",
        help="保留策略: first=保留第一个, best=保留评分最高的 (默认: best)"
    )
    parser.add_argument(
        "--no-fix-slugs",
        action="store_true",
        help="不修复缺失的 slug"
    )
    
    args = parser.parse_args()
    
    # 确定文件路径
    script_dir = Path(__file__).parent.parent
    input_path = script_dir / args.input
    output_path = Path(args.output) if args.output else input_path
    
    # 加载数据
    print(f"📂 加载数据: {input_path}")
    products = load_products(input_path)
    print(f"   共 {len(products)} 个产品")
    
    # 分析
    analysis = analyze_duplicates(products, args.threshold)
    
    if args.analyze_only:
        print("\n✅ 仅分析模式，未修改文件")
        return
    
    # 清理
    print("\n" + "=" * 60)
    print("开始清理...")
    print("=" * 60)
    
    cleaned, removed, stats = clean_products(
        products,
        similarity_threshold=args.threshold,
        fix_slugs=not args.no_fix_slugs,
        keep=args.keep
    )
    
    # 备份
    if args.backup:
        backup_path = input_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        save_products(products, backup_path)
        print(f"\n💾 已备份到: {backup_path}")
    
    # 保存
    save_products(cleaned, output_path)
    print(f"\n💾 已保存到: {output_path}")
    
    # 保存被移除的重复项
    if removed:
        removed_path = script_dir / "data" / "duplicates_removed.json"
        save_products(removed, removed_path)
        print(f"🗑️  重复项已保存到: {removed_path}")
    
    # 输出统计
    print("\n" + "=" * 60)
    print("清理统计")
    print("=" * 60)
    print(f"  原始数量: {stats['original_count']}")
    print(f"  移除重复: {stats['duplicates_removed']}")
    print(f"  修复 slug: {stats['slugs_fixed']}")
    print(f"  最终数量: {stats['final_count']}")
    print(f"  仍缺 website: {stats['missing_website']}")
    
    if removed:
        print(f"\n🗑️  被移除的重复项:")
        for p in removed[:10]:
            reason = p.get('_duplicate_reason', 'unknown')
            print(f"    - {p.get('name')}: {reason}")
        if len(removed) > 10:
            print(f"    ... 还有 {len(removed) - 10} 个")


if __name__ == "__main__":
    main()
