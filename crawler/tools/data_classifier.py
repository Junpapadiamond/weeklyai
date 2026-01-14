"""
Data Classifier for WeeklyAI

Separates products into:
- products: Real AI products (apps, tools, models with real usage)
- blogs: Blog posts, news articles, discussions, Reddit posts
- filtered: Low-quality or irrelevant items

Classification Rules:
1. GitHub/Hugging Face sources or domains → filtered
2. HackerNews: "Ask HN:", opinion pieces, blog URLs → blogs
3. Tech News: All news articles → blogs
4. Reddit: All Reddit posts → blogs
5. Exhibition: Items without real AI features → filtered
"""

import re
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any


# Blog/news URL patterns
BLOG_URL_PATTERNS = [
    r'/blog/',
    r'/archive/',
    r'/article/',
    r'/post/',
    r'/news/',
    r'medium\.com',
    r'substack\.com',
    r'dev\.to/',
    r'hashnode\.dev',
    r'wordpress\.com',
    r'blogspot\.com',
    r'mirror\.xyz',
    r'newsletter',
]

# Discussion title patterns (not products)
DISCUSSION_PATTERNS = [
    r'^ask\s+hn[:\s]',
    r'^tell\s+hn[:\s]',
    r'^poll[:\s]',
    r'what\s+(?:are|is)\s+(?:your|the)',
    r'how\s+do\s+(?:you|i)',
    r'anyone\s+(?:using|tried|know)',
    r'looking\s+for\s+recommendations',
    r'thoughts\s+on',
    r'opinion\s+on',
    r'discussion[:\s]',
    r'weekly\s+thread',
    r'monthly\s+thread',
]

BLOCKED_SOURCES = {'github', 'huggingface', 'huggingface_spaces'}
BLOCKED_DOMAINS = ('github.com', 'huggingface.co')

# Real product indicators (keep these as products)
REAL_PRODUCT_INDICATORS = [
    'launched',
    'introducing',
    'announcing',
    'we built',
    'i built',
    'my startup',
    'our product',
    'try it',
    'check it out',
    'now available',
    'just released',
    'open source',
    'free tier',
    'sign up',
    'get started',
]


def classify_product(product: Dict[str, Any]) -> str:
    """
    Classify a single product.

    Returns:
        'product' - Real AI product for main display
        'blog' - Blog/news/discussion for blog section
        'filtered' - Low quality, remove from display
    """
    name = (product.get('name') or '').lower().strip()
    description = (product.get('description') or '').lower()
    website = (product.get('website') or '').lower()
    source = product.get('source', '')
    extra = product.get('extra', {}) or {}

    text = f"{name} {description}"

    # Hard block GitHub/HuggingFace sources/domains (non-end-user products)
    if source in BLOCKED_SOURCES:
        return 'filtered'
    if any(domain in website for domain in BLOCKED_DOMAINS):
        return 'filtered'

    # === Source-specific rules ===

    # 1. HackerNews classification
    if source == 'hackernews':
        # Discussion threads → blog
        for pattern in DISCUSSION_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return 'blog'

        # Blog URLs → blog
        for pattern in BLOG_URL_PATTERNS:
            if re.search(pattern, website, re.IGNORECASE):
                return 'blog'

        # HN item links (not external products) → blog
        if 'news.ycombinator.com/item' in website:
            # Unless it's a Show HN with good engagement
            if extra.get('is_show_hn') and extra.get('points', 0) > 50:
                return 'product'
            return 'blog'

        # Low engagement HN posts → blog
        points = extra.get('points', 0) or 0
        if points < 30:
            return 'blog'

        # Show HN with external link → product
        if extra.get('is_show_hn') and not 'news.ycombinator.com' in website:
            return 'product'

        # Default HN → blog (most are discussions)
        return 'blog'

    # 2. Reddit posts → always blog
    if source == 'reddit' or 'reddit.com' in website:
        return 'blog'

    # 3. Tech News → always blog
    if source == 'tech_news':
        return 'blog'

    # 4. Exhibition items
    if source == 'exhibition':
        # Check for actual AI keywords
        ai_keywords = ['ai', 'machine learning', 'neural', 'smart', 'intelligent', 'automation']
        has_ai = any(kw in text for kw in ai_keywords)

        if not has_ai:
            return 'filtered'

        return 'product'

    # 7. AI Hardware → product
    if source == 'ai_hardware':
        return 'product'

    # 8. Company products → product
    if source == 'company':
        return 'product'

    # 9. AI Tools directories → product
    if source in ['aitools', 'aitoptools', 'toolify']:
        return 'product'

    # === Quality checks for remaining ===

    # Blog URL patterns → blog
    for pattern in BLOG_URL_PATTERNS:
        if re.search(pattern, website, re.IGNORECASE):
            return 'blog'

    # Very short/empty descriptions → filtered
    if len(description) < 15:
        return 'filtered'

    # Check for product indicators → product
    for indicator in REAL_PRODUCT_INDICATORS:
        if indicator in text:
            return 'product'

    # Default → product
    return 'product'


def classify_all(products: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Classify all products into three categories.

    Returns:
        (products_list, blogs_list, filtered_list)
    """
    products_list = []
    blogs_list = []
    filtered_list = []

    for product in products:
        classification = classify_product(product)
        product['content_type'] = classification

        if classification == 'product':
            products_list.append(product)
        elif classification == 'blog':
            blogs_list.append(product)
        else:
            filtered_list.append(product)

    return products_list, blogs_list, filtered_list


def process_data_file(input_path: str, output_dir: str = None) -> Dict[str, int]:
    """
    Process a products JSON file and generate separated outputs.

    Args:
        input_path: Path to products_latest.json
        output_dir: Directory for output files (defaults to same as input)

    Returns:
        Statistics dictionary
    """
    if output_dir is None:
        output_dir = os.path.dirname(input_path)

    # Load data
    with open(input_path, 'r', encoding='utf-8') as f:
        all_products = json.load(f)

    # Classify
    products, blogs, filtered = classify_all(all_products)

    # Sort by score
    products.sort(key=lambda x: x.get('final_score', x.get('top_score', 0)), reverse=True)
    blogs.sort(key=lambda x: x.get('final_score', x.get('top_score', 0)), reverse=True)

    # Save outputs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    products_file = os.path.join(output_dir, 'products_featured.json')
    blogs_file = os.path.join(output_dir, 'blogs_news.json')
    filtered_file = os.path.join(output_dir, 'filtered_items.json')

    with open(products_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    with open(blogs_file, 'w', encoding='utf-8') as f:
        json.dump(blogs, f, ensure_ascii=False, indent=2)

    with open(filtered_file, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    stats = {
        'total': len(all_products),
        'products': len(products),
        'blogs': len(blogs),
        'filtered': len(filtered),
    }

    print(f"\n{'='*50}")
    print("Data Classification Complete")
    print(f"{'='*50}")
    print(f"  Total items:     {stats['total']}")
    print(f"  Products:        {stats['products']} (main display)")
    print(f"  Blogs/News:      {stats['blogs']} (blog section)")
    print(f"  Filtered out:    {stats['filtered']} (hidden)")
    print(f"{'='*50}")
    print(f"\nOutput files:")
    print(f"  {products_file}")
    print(f"  {blogs_file}")
    print(f"  {filtered_file}")

    return stats


def print_classification_report(products: List[Dict]) -> None:
    """Print detailed classification breakdown."""
    by_source = {}
    by_type = {'product': 0, 'blog': 0, 'filtered': 0}

    for p in products:
        source = p.get('source', 'unknown')
        content_type = p.get('content_type', 'unknown')

        if source not in by_source:
            by_source[source] = {'product': 0, 'blog': 0, 'filtered': 0}
        by_source[source][content_type] += 1
        by_type[content_type] += 1

    print("\n" + "="*60)
    print("Classification Breakdown by Source")
    print("="*60)
    print(f"{'Source':<20} {'Products':>10} {'Blogs':>10} {'Filtered':>10}")
    print("-"*60)

    for source, counts in sorted(by_source.items()):
        print(f"{source:<20} {counts['product']:>10} {counts['blog']:>10} {counts['filtered']:>10}")

    print("-"*60)
    print(f"{'TOTAL':<20} {by_type['product']:>10} {by_type['blog']:>10} {by_type['filtered']:>10}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Classify WeeklyAI products')
    parser.add_argument('--input', '-i', default='../data/products_latest.json',
                       help='Input JSON file')
    parser.add_argument('--output-dir', '-o', default=None,
                       help='Output directory')
    parser.add_argument('--report', '-r', action='store_true',
                       help='Print detailed report')

    args = parser.parse_args()

    # Resolve paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, args.input) if not os.path.isabs(args.input) else args.input

    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        exit(1)

    output_dir = args.output_dir or os.path.dirname(input_path)

    # Process
    stats = process_data_file(input_path, output_dir)

    if args.report:
        with open(input_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        # Classify for report
        for p in products:
            p['content_type'] = classify_product(p)
        print_classification_report(products)
