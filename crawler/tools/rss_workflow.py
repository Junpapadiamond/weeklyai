#!/usr/bin/env python3
"""
RSS 完整工作流: 抓取 → 转换 → 审批 → 入库

使用:
    python tools/rss_workflow.py                   # 完整流程
    python tools/rss_workflow.py --fetch           # 只抓取 RSS
    python tools/rss_workflow.py --convert         # 只转换产品
    python tools/rss_workflow.py --approve         # 审批候选产品
    python tools/rss_workflow.py --auto            # 全自动 (4分以上自动入库)
"""

import json
import os
import sys
import argparse
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
CANDIDATES_DIR = os.path.join(DATA_DIR, 'candidates')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products_featured.json')

# ============================================
# 工具函数
# ============================================

def load_json(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(filepath: str, data: list):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_name(name: str) -> str:
    return ''.join(c.lower() for c in name if c.isalnum())


# ============================================
# Step 1: 抓取 RSS
# ============================================

def step_fetch_rss():
    """抓取 RSS 新闻"""
    print("\n" + "=" * 50)
    print("📡 Step 1: 抓取 RSS 新闻")
    print("=" * 50)
    
    from tools.rss_feeds import fetch_all_feeds, identify_product_mentions
    
    # 抓取各类 RSS
    categories = ['tech_media', 'chinese_media', 'community']
    print(f"\n🔄 抓取 {categories}...")
    articles = fetch_all_feeds(categories)
    
    # 标记产品提及
    articles = identify_product_mentions(articles)
    
    print(f"  ✅ 获取 {len(articles)} 篇")
    
    # 保存
    output_file = os.path.join(DATA_DIR, 'blogs_news.json')
    save_json(output_file, articles)
    
    print(f"\n📰 总计抓取 {len(articles)} 篇新闻")
    return articles


# ============================================
# Step 2: 转换为产品
# ============================================

def step_convert_to_products(limit: int = 30):
    """将 RSS 新闻转换为产品数据"""
    print("\n" + "=" * 50)
    print("🔄 Step 2: 转换为产品数据")
    print("=" * 50)
    
    # 调用 rss_to_products
    import subprocess
    result = subprocess.run(
        ['python3', 'tools/rss_to_products.py', '--limit', str(limit)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ 转换失败: {result.stderr}")
        return []
    
    # 读取今天的候选文件
    today = datetime.now().strftime('%Y%m%d')
    candidates_file = os.path.join(CANDIDATES_DIR, f'rss_candidates_{today}.json')
    
    if os.path.exists(candidates_file):
        return load_json(candidates_file)
    return []


# ============================================
# Step 3: 审批产品
# ============================================

def step_approve_products(auto_approve: bool = False, min_score: int = 4):
    """审批候选产品"""
    print("\n" + "=" * 50)
    print("✅ Step 3: 审批候选产品")
    print("=" * 50)
    
    # 收集所有候选文件
    all_candidates = []
    for filename in os.listdir(CANDIDATES_DIR):
        if filename.endswith('.json') and filename.startswith('rss_candidates'):
            filepath = os.path.join(CANDIDATES_DIR, filename)
            candidates = load_json(filepath)
            all_candidates.extend(candidates)
    
    if not all_candidates:
        print("📭 没有待审批的产品")
        return []
    
    # 加载已有产品 (用于去重)
    products = load_json(PRODUCTS_FILE)
    existing_names = {normalize_name(p.get('name', '')) for p in products}
    
    # 筛选新产品
    new_products = []
    for candidate in all_candidates:
        name = candidate.get('name', '')
        if normalize_name(name) in existing_names:
            continue
        
        score = candidate.get('dark_horse_index', 0)
        
        if auto_approve:
            # 自动模式: 4分以上直接入库
            if score >= min_score:
                print(f"  ✅ 自动入库: {name} ({score}分)")
                new_products.append(candidate)
            else:
                print(f"  ⏭️ 跳过 (评分 {score}): {name}")
        else:
            # 手动模式: 显示并询问
            print(f"\n[{score}分] {name}")
            print(f"    💰 {candidate.get('funding_total', 'N/A')}")
            print(f"    💡 {candidate.get('why_matters', '')[:80]}...")
            
            choice = input("    入库? [Y/n/q]: ").strip().lower()
            if choice == 'q':
                break
            if choice != 'n':
                new_products.append(candidate)
    
    return new_products


# ============================================
# Step 4: 入库
# ============================================

def step_save_to_featured(new_products: list):
    """保存新产品到 featured"""
    print("\n" + "=" * 50)
    print("💾 Step 4: 保存到数据库")
    print("=" * 50)
    
    if not new_products:
        print("📭 没有新产品需要保存")
        return
    
    products = load_json(PRODUCTS_FILE)
    
    # 准备新产品数据
    for product in new_products:
        # 添加必要字段
        product.setdefault('slug', product.get('name', '').lower().replace(' ', '-'))
        product.setdefault('trending_score', product.get('dark_horse_index', 3) * 20)
        product.setdefault('final_score', product.get('dark_horse_index', 3) * 20)
        product.setdefault('first_seen', datetime.now().isoformat())
        product.setdefault('last_seen', datetime.now().isoformat())
        
        products.append(product)
    
    # 按评分排序
    products.sort(key=lambda x: (
        x.get('dark_horse_index', 0),
        x.get('final_score', 0)
    ), reverse=True)
    
    save_json(PRODUCTS_FILE, products)
    
    print(f"✅ 添加 {len(new_products)} 个新产品")
    print(f"📦 总产品数: {len(products)}")


# ============================================
# 清理候选文件
# ============================================

def cleanup_candidates():
    """清理已处理的候选文件"""
    for filename in os.listdir(CANDIDATES_DIR):
        if filename.startswith('rss_candidates') and filename.endswith('.json'):
            filepath = os.path.join(CANDIDATES_DIR, filename)
            # 移动到归档
            archive_dir = os.path.join(CANDIDATES_DIR, 'archive')
            os.makedirs(archive_dir, exist_ok=True)
            archive_path = os.path.join(archive_dir, filename)
            os.rename(filepath, archive_path)
            print(f"  📁 归档: {filename}")


# ============================================
# 主函数
# ============================================

def main():
    parser = argparse.ArgumentParser(description="RSS 完整工作流")
    parser.add_argument("--fetch", action="store_true", help="只抓取 RSS")
    parser.add_argument("--convert", action="store_true", help="只转换产品")
    parser.add_argument("--approve", action="store_true", help="审批候选产品")
    parser.add_argument("--auto", action="store_true", help="全自动模式 (4分以上自动入库)")
    parser.add_argument("--min-score", type=int, default=4, help="自动入库最低分数")
    parser.add_argument("--limit", type=int, default=30, help="处理文章数量上限")
    parser.add_argument("--skip-fetch", action="store_true", help="跳过 RSS 抓取")
    
    args = parser.parse_args()
    
    print("\n🚀 WeeklyAI RSS 工作流")
    print("=" * 50)
    
    # 确定执行哪些步骤
    run_all = not (args.fetch or args.convert or args.approve)
    
    # Step 1: 抓取 RSS
    if args.fetch or (run_all and not args.skip_fetch):
        step_fetch_rss()
    
    # Step 2: 转换产品
    if args.convert or run_all:
        step_convert_to_products(args.limit)
    
    # Step 3: 审批
    if args.approve or run_all:
        new_products = step_approve_products(
            auto_approve=args.auto,
            min_score=args.min_score
        )
        
        # Step 4: 入库
        if new_products:
            step_save_to_featured(new_products)
            cleanup_candidates()
    
    print("\n✅ 工作流完成")


if __name__ == "__main__":
    main()
