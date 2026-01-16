#!/usr/bin/env python3
"""
Rating Calculator Tool for WeeklyAI

Auto-calculates ratings for blogs/news items based on engagement metrics.

Rating formula:
- GitHub stars contribute 40%
- Forks/engagement contribute 20%
- Points/votes contribute 30%
- Recency contributes 10%

Usage:
    python calculate_ratings.py                # Update blogs_news.json
    python calculate_ratings.py --dry-run      # Preview changes without saving
    python calculate_ratings.py --verbose      # Show detailed calculations
"""

import json
import os
import sys
import argparse
import math
from datetime import datetime
from typing import Dict, Any, List, Optional

# Data file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
BLOGS_FILE = os.path.join(DATA_DIR, 'blogs_news.json')
PRODUCTS_FILE = os.path.join(DATA_DIR, 'products_featured.json')

# Rating calculation weights
WEIGHTS = {
    'stars': 0.40,      # GitHub stars
    'forks': 0.20,      # GitHub forks / engagement
    'points': 0.30,     # HN points, Reddit votes, etc.
    'recency': 0.10,    # How recent the item is
}

# Normalization ranges (log scale for better distribution)
# These are calibrated based on typical values in the dataset
STAR_MAX = 100000      # 100K stars = max contribution
FORK_MAX = 20000       # 20K forks = max contribution
POINTS_MAX = 5000      # 5K points = max contribution
RECENCY_DAYS_MAX = 365 # 1 year old = 0 recency score


def log_normalize(value: float, max_val: float) -> float:
    """Normalize value using log scale (0-1 range)."""
    if value <= 0:
        return 0.0
    if value >= max_val:
        return 1.0
    # Log scale normalization
    return math.log1p(value) / math.log1p(max_val)


def linear_normalize(value: float, max_val: float) -> float:
    """Normalize value using linear scale (0-1 range)."""
    if value <= 0:
        return 0.0
    if value >= max_val:
        return 1.0
    return value / max_val


def calculate_recency_score(date_str: Optional[str]) -> float:
    """Calculate recency score (1.0 = today, 0.0 = 1 year+ old)."""
    if not date_str:
        return 0.5  # Default for unknown dates

    try:
        # Handle different date formats
        if isinstance(date_str, str):
            if 'T' in date_str:
                item_date = datetime.fromisoformat(date_str.replace('Z', '+00:00').split('+')[0])
            else:
                item_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
        else:
            return 0.5

        days_old = (datetime.now() - item_date).days
        if days_old < 0:
            days_old = 0

        # Linear decay: 0 days = 1.0, 365 days = 0.0
        return max(0.0, 1.0 - (days_old / RECENCY_DAYS_MAX))

    except (ValueError, TypeError):
        return 0.5


def extract_metrics(item: Dict[str, Any]) -> Dict[str, float]:
    """Extract engagement metrics from an item."""
    extra = item.get('extra', {})
    if isinstance(extra, str):
        try:
            extra = json.loads(extra)
        except:
            extra = {}

    metrics = {
        'stars': 0,
        'forks': 0,
        'points': 0,
        'recency': 0.5,
    }

    # GitHub metrics
    metrics['stars'] = extra.get('stars', 0) or 0
    metrics['forks'] = extra.get('forks', 0) or 0

    # HN/Reddit points
    metrics['points'] = extra.get('points', 0) or extra.get('votes', 0) or 0

    # Comments can also indicate engagement
    comments = extra.get('comments', 0) or 0
    if comments > 0 and metrics['points'] == 0:
        metrics['points'] = comments * 2  # Comments are worth ~2 points

    # Weekly users (for products)
    weekly_users = item.get('weekly_users', 0) or 0
    if weekly_users > 0:
        # Convert weekly users to equivalent "points"
        metrics['points'] = max(metrics['points'], weekly_users / 100)

    # Recency
    date_str = item.get('published_at') or item.get('first_seen')
    metrics['recency'] = calculate_recency_score(date_str)

    return metrics


def calculate_rating(item: Dict[str, Any], verbose: bool = False) -> float:
    """Calculate rating for an item (1.0 - 5.0 scale)."""
    metrics = extract_metrics(item)

    # Normalize each metric
    normalized = {
        'stars': log_normalize(metrics['stars'], STAR_MAX),
        'forks': log_normalize(metrics['forks'], FORK_MAX),
        'points': log_normalize(metrics['points'], POINTS_MAX),
        'recency': metrics['recency'],  # Already 0-1
    }

    # Calculate weighted score (0-1)
    weighted_score = (
        normalized['stars'] * WEIGHTS['stars'] +
        normalized['forks'] * WEIGHTS['forks'] +
        normalized['points'] * WEIGHTS['points'] +
        normalized['recency'] * WEIGHTS['recency']
    )

    # Convert to 1-5 scale with some minimum floor
    # We want most items to be 3.0-4.5, with outliers at 2.5 or 5.0
    rating = 2.5 + (weighted_score * 2.5)

    # Clamp to valid range
    rating = max(1.0, min(5.0, rating))

    # Round to 1 decimal place
    rating = round(rating, 1)

    if verbose:
        name = item.get('name', 'Unknown')[:30]
        print(f"  {name}: stars={metrics['stars']}, forks={metrics['forks']}, "
              f"points={metrics['points']}, recency={metrics['recency']:.2f} -> {rating}")

    return rating


def calculate_reading_time(item: Dict[str, Any]) -> Optional[int]:
    """Estimate reading time in minutes based on description length."""
    description = item.get('description', '')
    if not description:
        return None

    # Average reading speed: ~200 words per minute
    # Average word length: ~5 characters
    chars = len(description)
    words = chars / 5
    minutes = max(1, round(words / 200))

    # Cap at reasonable maximum for blog summaries
    return min(minutes, 15)


def get_content_type(item: Dict[str, Any]) -> str:
    """Determine content type based on item attributes."""
    source = item.get('source', '').lower()
    website = item.get('website', '').lower()
    description = item.get('description', '').lower()

    # Tutorial indicators
    tutorial_keywords = ['tutorial', 'guide', 'how to', 'step by step', 'learn', 'getting started']
    if any(kw in description for kw in tutorial_keywords):
        return 'tutorial'

    # News indicators
    news_keywords = ['announces', 'launches', 'releases', 'funding', 'raises', 'acquires']
    if any(kw in description for kw in news_keywords):
        return 'news'

    # Repository indicators
    if 'github.com' in website or source == 'github':
        return 'repo'

    # Discussion indicators (HN, Reddit)
    if source in ['hackernews', 'reddit']:
        return 'discussion'

    return 'article'


def get_difficulty_level(item: Dict[str, Any]) -> str:
    """Estimate difficulty level based on content."""
    description = item.get('description', '').lower()
    name = item.get('name', '').lower()
    text = f"{name} {description}"

    # Beginner indicators
    beginner_keywords = ['beginner', 'introduction', 'basics', 'getting started', 'simple', 'easy']
    if any(kw in text for kw in beginner_keywords):
        return 'beginner'

    # Advanced indicators
    advanced_keywords = ['advanced', 'deep dive', 'architecture', 'optimization', 'performance',
                        'distributed', 'scaling', 'internals', 'under the hood']
    if any(kw in text for kw in advanced_keywords):
        return 'advanced'

    return 'intermediate'


def process_items(items: List[Dict[str, Any]], verbose: bool = False,
                  add_metadata: bool = True) -> tuple:
    """Process items and calculate ratings."""
    updated = 0
    skipped = 0
    already_rated = 0

    for item in items:
        name = item.get('name', 'Unknown')
        current_rating = item.get('rating')

        # Calculate new rating
        new_rating = calculate_rating(item, verbose=verbose)

        # Only update if:
        # 1. No rating exists, OR
        # 2. Rating is exactly 0 or null, OR
        # 3. Rating appears to be a placeholder (exactly 5.0 for GitHub repos)
        source = item.get('source', '')
        is_placeholder = (
            current_rating is None or
            current_rating == 0 or
            (current_rating == 5.0 and source == 'github')
        )

        if is_placeholder:
            item['rating'] = new_rating
            updated += 1
            if verbose:
                print(f"  ✓ {name}: {current_rating} -> {new_rating}")
        else:
            already_rated += 1

        # Add additional metadata if requested
        if add_metadata:
            # Reading time
            if 'reading_time_minutes' not in item:
                reading_time = calculate_reading_time(item)
                if reading_time:
                    item['reading_time_minutes'] = reading_time

            # Content type
            if 'content_type' not in item or item.get('content_type') == 'blog':
                item['content_type'] = get_content_type(item)

            # Difficulty level
            if 'difficulty_level' not in item:
                item['difficulty_level'] = get_difficulty_level(item)

    return updated, already_rated, skipped


def main():
    parser = argparse.ArgumentParser(description='Calculate ratings for WeeklyAI items')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed calculations')
    parser.add_argument('--blogs-only', action='store_true', help='Only process blogs')
    parser.add_argument('--products-only', action='store_true', help='Only process products')
    parser.add_argument('--no-metadata', action='store_true', help='Skip adding reading time/content type')
    args = parser.parse_args()

    total_updated = 0
    total_already_rated = 0

    # Process blogs
    if not args.products_only:
        if os.path.exists(BLOGS_FILE):
            print(f"\n📰 Processing blogs_news.json...")
            with open(BLOGS_FILE, 'r', encoding='utf-8') as f:
                blogs = json.load(f)

            updated, already_rated, _ = process_items(
                blogs,
                verbose=args.verbose,
                add_metadata=not args.no_metadata
            )
            total_updated += updated
            total_already_rated += already_rated

            print(f"  Blogs: {updated} ratings calculated, {already_rated} already had ratings")

            if not args.dry_run and updated > 0:
                with open(BLOGS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(blogs, f, indent=2, ensure_ascii=False)
                print(f"  ✓ Saved {BLOGS_FILE}")
        else:
            print(f"Warning: {BLOGS_FILE} not found")

    # Process products (usually already have ratings, but fill gaps)
    if not args.blogs_only:
        if os.path.exists(PRODUCTS_FILE):
            print(f"\n📦 Processing products_featured.json...")
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                products = json.load(f)

            updated, already_rated, _ = process_items(
                products,
                verbose=args.verbose,
                add_metadata=False  # Products don't need reading time
            )
            total_updated += updated
            total_already_rated += already_rated

            print(f"  Products: {updated} ratings calculated, {already_rated} already had ratings")

            if not args.dry_run and updated > 0:
                with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(products, f, indent=2, ensure_ascii=False)
                print(f"  ✓ Saved {PRODUCTS_FILE}")
        else:
            print(f"Warning: {PRODUCTS_FILE} not found")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: "
          f"{total_updated} ratings calculated, {total_already_rated} unchanged")


if __name__ == '__main__':
    main()
