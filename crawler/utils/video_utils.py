"""
Video utilities for fetching YouTube video previews for AI products.
Uses YouTube search (no API key needed for basic search).
"""

import re
import requests
from typing import Optional, Dict, Any
from urllib.parse import quote_plus


def search_youtube_video(product_name: str, keywords: list = None) -> Optional[Dict[str, Any]]:
    """
    Search YouTube for a video about the product.
    Returns video info including thumbnail and embed URL.

    Note: This uses YouTube's public search page, not the API.
    For production, consider using YouTube Data API with an API key.
    """
    if not product_name:
        return None

    # Build search query
    search_terms = [product_name]
    if keywords:
        search_terms.extend(keywords[:2])
    search_terms.append('AI')  # Add AI context

    query = ' '.join(search_terms)
    encoded_query = quote_plus(query)

    try:
        # Use YouTube search page (works without API key)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None

        # Extract video ID from response (simplified extraction)
        # Look for video IDs in the page content
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', response.text)

        if not video_ids:
            return None

        # Get first unique video ID
        video_id = video_ids[0]

        return {
            'video_id': video_id,
            'url': f'https://www.youtube.com/watch?v={video_id}',
            'embed_url': f'https://www.youtube.com/embed/{video_id}',
            'thumbnail': f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg',
            'thumbnail_hq': f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg',
        }

    except Exception as e:
        print(f"  ⚠ YouTube search failed for {product_name}: {e}")
        return None


def get_video_thumbnail(video_url: str) -> Optional[str]:
    """Extract thumbnail URL from a YouTube video URL."""
    if not video_url:
        return None

    # Extract video ID
    patterns = [
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, video_url)
        if match:
            video_id = match.group(1)
            return f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg'

    return None


def enrich_product_with_video(product: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
    """
    Add video preview info to a product if available.
    Only enriches products that don't already have video info unless force=True.
    """
    extra = product.get('extra', {}) or {}

    # Skip if already has video info
    if not force and extra.get('video_url'):
        return product

    # Only search for certain product types (trending, new)
    score = product.get('hot_score', 0) or product.get('trending_score', 0)
    if score < 70 and not force:
        return product

    # Search for video
    name = product.get('name', '')
    categories = product.get('categories', [])

    video_info = search_youtube_video(name, categories)

    if video_info:
        extra['video_url'] = video_info['url']
        extra['video_thumbnail'] = video_info['thumbnail']
        extra['video_embed'] = video_info['embed_url']
        product['extra'] = extra

    return product
