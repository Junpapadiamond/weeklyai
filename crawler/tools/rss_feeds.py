#!/usr/bin/env python3
"""
RSS 新闻聚合模块

功能:
- 聚合多个 RSS 源的 AI/科技新闻
- 支持 YouTube 频道订阅
- 自动识别包含新产品信息的文章
- 输出到 blogs_news.json

使用:
    python tools/rss_feeds.py              # 抓取所有源
    python tools/rss_feeds.py --youtube    # 只抓取 YouTube
    python tools/rss_feeds.py --tech       # 只抓取科技媒体
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

# 添加项目路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    print("⚠️ feedparser 未安装，运行: pip install feedparser")

# ============================================
# RSS 源配置
# ============================================

RSS_FEEDS = {
    # 主流科技媒体
    "tech_media": [
        {
            "name": "TechCrunch AI",
            "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
            "category": "funding",
            "language": "en",
        },
        {
            "name": "VentureBeat AI",
            "url": "https://venturebeat.com/category/ai/feed/",
            "category": "industry",
            "language": "en",
        },
        {
            "name": "The Verge AI",
            "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
            "category": "product",
            "language": "en",
        },
        {
            "name": "Ars Technica",
            "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
            "category": "tech",
            "language": "en",
        },
        {
            "name": "Wired AI",
            "url": "https://www.wired.com/feed/tag/ai/latest/rss",
            "category": "industry",
            "language": "en",
        },
    ],
    
    # 社区/论坛
    "community": [
        {
            "name": "Hacker News AI",
            "url": "https://hnrss.org/newest?q=AI+startup",
            "category": "community",
            "language": "en",
        },
        {
            "name": "Reddit r/artificial",
            "url": "https://www.reddit.com/r/artificial/.rss",
            "category": "community",
            "language": "en",
        },
        {
            "name": "Reddit r/MachineLearning",
            "url": "https://www.reddit.com/r/MachineLearning/.rss",
            "category": "research",
            "language": "en",
        },
        {
            "name": "Product Hunt AI",
            "url": "https://www.producthunt.com/topics/artificial-intelligence/feed",
            "category": "product",
            "language": "en",
        },
    ],
    
    # 中文媒体
    "chinese": [
        {
            "name": "36氪",
            "url": "https://36kr.com/feed",
            "category": "funding",
            "language": "zh",
        },
        {
            "name": "机器之心",
            "url": "https://www.jiqizhixin.com/rss",
            "category": "research",
            "language": "zh",
        },
        {
            "name": "少数派",
            "url": "https://sspai.com/feed",
            "category": "product",
            "language": "zh",
        },
    ],
    
    # Newsletter
    "newsletter": [
        {
            "name": "The Rundown AI",
            "url": "https://www.therundown.ai/feed",
            "category": "news",
            "language": "en",
        },
        {
            "name": "Ben's Bites",
            "url": "https://bensbites.beehiiv.com/feed",
            "category": "tools",
            "language": "en",
        },
    ],
}

# YouTube 频道
YOUTUBE_CHANNELS = [
    {
        "name": "Two Minute Papers",
        "channel_id": "UCbfYPyITQ-7l4upoX8nvctg",
        "category": "research",
    },
    {
        "name": "AI Explained",
        "channel_id": "UCNJ1Ymd5yFuUPtn21xtRbbw",
        "category": "explainer",
    },
    {
        "name": "Matt Wolfe",
        "channel_id": "UCJIfeSCssxSC_Dhc5s7woww",
        "category": "tools",
    },
    {
        "name": "Fireship",
        "channel_id": "UCsBjURrPoezykLs9EqgamOA",
        "category": "dev",
    },
    {
        "name": "Yannic Kilcher",
        "channel_id": "UCZHmQk67mN2CWjyrAqjhmCQ",
        "category": "research",
    },
    {
        "name": "The AI Advantage",
        "channel_id": "UCjq5DjGAP57dv_zdi1HVtXg",
        "category": "tools",
    },
    {
        "name": "All About AI",
        "channel_id": "UCUyeluBRhGPCW4rPe_UvBZQ",
        "category": "tools",
    },
    {
        "name": "跟李沐学AI",
        "channel_id": "UCfeLGcQHpqVFBG1hCqVV6bg",
        "category": "research",
    },
]

# ============================================
# RSS 解析
# ============================================

def get_youtube_rss(channel_id: str) -> str:
    """生成 YouTube 频道 RSS URL"""
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def parse_date(date_str: str) -> Optional[datetime]:
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        # feedparser 通常返回 struct_time
        if hasattr(date_str, 'tm_year'):
            return datetime(*date_str[:6])
        # 尝试常见格式
        for fmt in [
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
        ]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    except Exception:
        pass
    return None


def fetch_feed(feed_config: Dict) -> List[Dict]:
    """抓取单个 RSS 源"""
    if not HAS_FEEDPARSER:
        return []
    
    url = feed_config.get("url")
    name = feed_config.get("name", url)
    
    try:
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:20]:  # 每个源最多 20 条
            published = parse_date(entry.get("published_parsed") or entry.get("updated_parsed"))
            
            # 只保留最近 7 天的文章
            if published and published < datetime.now() - timedelta(days=7):
                continue
            
            article = {
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:500] if entry.get("summary") else "",
                "published": published.isoformat() if published else None,
                "source": name,
                "category": feed_config.get("category", "other"),
                "language": feed_config.get("language", "en"),
            }
            
            # 清理 HTML
            article["summary"] = re.sub(r'<[^>]+>', '', article["summary"]).strip()
            
            if article["title"] and article["link"]:
                articles.append(article)
        
        print(f"  ✅ {name}: {len(articles)} 篇文章")
        return articles
    
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return []


def fetch_youtube_feeds() -> List[Dict]:
    """抓取所有 YouTube 频道"""
    articles = []
    print("\n📺 抓取 YouTube 频道...")
    
    for channel in YOUTUBE_CHANNELS:
        feed_config = {
            "url": get_youtube_rss(channel["channel_id"]),
            "name": f"YouTube: {channel['name']}",
            "category": channel.get("category", "video"),
            "language": "en",
        }
        articles.extend(fetch_feed(feed_config))
    
    return articles


def fetch_all_feeds(categories: List[str] = None) -> List[Dict]:
    """抓取所有 RSS 源"""
    all_articles = []
    
    if categories is None:
        categories = list(RSS_FEEDS.keys())
    
    for category in categories:
        if category not in RSS_FEEDS:
            continue
        
        print(f"\n📰 抓取 {category}...")
        for feed_config in RSS_FEEDS[category]:
            all_articles.extend(fetch_feed(feed_config))
    
    return all_articles


def identify_product_mentions(articles: List[Dict]) -> List[Dict]:
    """识别文章中的产品提及 (简单关键词匹配)"""
    product_keywords = [
        "launch", "raises", "funding", "Series A", "Series B", "seed",
        "startup", "announces", "releases", "introduces", "unveils",
        "融资", "发布", "推出", "上线", "获投", "估值",
    ]
    
    for article in articles:
        text = f"{article['title']} {article['summary']}".lower()
        article["has_product_mention"] = any(kw.lower() in text for kw in product_keywords)
    
    return articles


def save_articles(articles: List[Dict], output_file: str = None):
    """保存文章到 JSON"""
    if output_file is None:
        output_file = os.path.join(PROJECT_ROOT, "data", "blogs_news.json")
    
    # 按发布时间排序
    articles.sort(key=lambda x: x.get("published") or "", reverse=True)
    
    # 去重
    seen = set()
    unique_articles = []
    for article in articles:
        key = article["link"]
        if key not in seen:
            seen.add(key)
            unique_articles.append(article)
    
    # 保存
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_articles, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 保存 {len(unique_articles)} 篇文章到 {output_file}")
    return unique_articles


# ============================================
# CLI
# ============================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="RSS 新闻聚合")
    parser.add_argument("--youtube", action="store_true", help="只抓取 YouTube")
    parser.add_argument("--tech", action="store_true", help="只抓取科技媒体")
    parser.add_argument("--chinese", action="store_true", help="只抓取中文媒体")
    parser.add_argument("--community", action="store_true", help="只抓取社区")
    parser.add_argument("--all", action="store_true", help="抓取所有源")
    parser.add_argument("--output", "-o", help="输出文件路径")
    
    args = parser.parse_args()
    
    if not HAS_FEEDPARSER:
        print("❌ 请先安装 feedparser: pip install feedparser")
        return
    
    print("🔄 RSS 新闻聚合")
    print("=" * 50)
    
    all_articles = []
    
    if args.youtube:
        all_articles = fetch_youtube_feeds()
    elif args.tech:
        all_articles = fetch_all_feeds(["tech_media"])
    elif args.chinese:
        all_articles = fetch_all_feeds(["chinese"])
    elif args.community:
        all_articles = fetch_all_feeds(["community"])
    else:
        # 默认抓取所有
        all_articles = fetch_all_feeds()
        all_articles.extend(fetch_youtube_feeds())
    
    # 识别产品提及
    all_articles = identify_product_mentions(all_articles)
    
    # 保存
    save_articles(all_articles, args.output)
    
    # 统计
    product_articles = [a for a in all_articles if a.get("has_product_mention")]
    print(f"\n📊 统计:")
    print(f"  - 总文章数: {len(all_articles)}")
    print(f"  - 包含产品提及: {len(product_articles)}")


if __name__ == "__main__":
    main()
