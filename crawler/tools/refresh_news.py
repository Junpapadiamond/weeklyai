"""Independent, bounded news ingestion. No model generation or product crawling.

Each feed checkpoints into the snapshot as soon as it completes. An unavailable
platform retains its dated last-known items; the report distinguishes that from
a successful refresh. Search excerpts are labelled, never passed off as posts.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import html
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlparse, urlunparse, parse_qs, parse_qsl, urlencode

import feedparser
import requests

CRAWLER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CRAWLER))
from utils.social_sources import load_reddit_subreddits, load_youtube_channel_ids
from utils.tavily_client import parse_date
from spiders.cn_news_spider import CN_RSS_FEEDS, is_ai_relevant
from spiders.tech_news_spider import TechNewsSpider

SOURCES = ('x', 'reddit', 'youtube', 'hackernews', 'producthunt', 'tech_news', 'cn_news')
SEARCH_DOMAINS = {
    'x': ['x.com', 'twitter.com'], 'reddit': ['reddit.com'],
    'youtube': ['youtube.com'], 'hackernews': ['news.ycombinator.com'],
    'producthunt': ['producthunt.com'],
    'tech_news': ['techcrunch.com', 'theverge.com', 'venturebeat.com'],
    'cn_news': ['36kr.com', 'qbitai.com', 'jiqizhixin.com'],
}
USER_AGENT = 'DarkHorseRadar/1.0 (+https://darkhorseradar.com)'


def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', str(value or '')))).strip()


def canonical_url(value):
    try:
        url = urlparse(str(value or '').strip())
        if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password:
            return ''
        host = url.hostname.lower().removeprefix('www.')
        host = {'twitter.com': 'x.com', 'mobile.twitter.com': 'x.com', 'old.reddit.com': 'reddit.com'}.get(host, host)
        # Preserve article identity parameters; only discard known trackers.
        kept = urlencode(sorted((key, value) for key, value in parse_qsl(url.query)
            if not key.lower().startswith('utm_') and key.lower() not in ('fbclid', 'gclid')))
        return urlunparse(('https', host, url.path.rstrip('/'), '', kept, ''))
    except ValueError:
        return ''


def normalize(item, now):
    if not isinstance(item, dict):
        return None
    out = dict(item)
    extra = dict(out.get('extra') or {})
    date = parse_date(out.get('published_at') or extra.get('published_at'))
    url = canonical_url(out.get('website'))
    name = clean(out.get('name'))
    # Never turn a crawl date, missing date or future timestamp into news.
    if not url or not name or not date or date > now or date < now - timedelta(days=90):
        return None
    source = str(out.get('source', '')).lower()
    source = {'twitter': 'x', 'youtube_rss': 'youtube'}.get(source, source)
    out.update(name=name[:300], description=clean(out.get('description'))[:1200],
               website=url, source=source, published_at=date.isoformat(), content_type='blog')
    # Platforms are global; platform identity does not establish a US location.
    out['market'] = 'cn' if source in ('cn_news', 'cn_news_glm') else 'global'
    extra['news_market'] = out['market']
    out['extra'] = extra
    return out


def merge_news(existing, fresh, now, per_source=60):
    by_url = {}
    for item in fresh + existing:
        item = normalize(item, now)
        if item:
            # Same article on distinct platforms keeps each discussion entry.
            by_url.setdefault((item['source'], item['website']), item)
    counts = Counter()
    merged = []
    for item in sorted(by_url.values(), key=lambda x: x['published_at'], reverse=True):
        if counts[item['source']] < per_source:
            counts[item['source']] += 1
            merged.append(item)
    return merged


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def get(url, **kwargs):
    response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=(5, 15), **kwargs)
    response.raise_for_status()
    return response


def feed_items(source, url, now, label=''):
    feed = feedparser.parse(get(url).content)
    if not feed.entries:
        raise ValueError('empty_or_invalid_feed')
    items = []
    for entry in feed.entries[:40]:
        parsed = entry.get('published_parsed') or entry.get('updated_parsed')
        date = datetime(*parsed[:6], tzinfo=timezone.utc) if parsed else None
        title = clean(entry.get('title'))
        content = entry.get('summary') or (entry.get('content') or [{}])[0].get('value', '')
        summary = clean(content)
        if not date or date < now - timedelta(days=14) or not is_ai_relevant(title, summary):
            continue
        item = normalize({'name': title, 'description': summary or title,
            'website': entry.get('link'), 'source': source, 'published_at': date.isoformat(),
            'extra': {'evidence_kind': 'feed_excerpt', 'publisher': label,
                      'feed_url': url, 'retrieved_at': now.isoformat()}}, now)
        if item:
            items.append(item)
    return items


def hn_items(now):
    body = get('https://hn.algolia.com/api/v1/search_by_date', params={
        'query': 'AI', 'tags': 'story', 'hitsPerPage': 60,
        'numericFilters': f'created_at_i>{int((now - timedelta(days=7)).timestamp())}',
    }).json()
    items = []
    for hit in body.get('hits', []):
        if not str(hit.get('objectID', '')).isdigit() or not is_ai_relevant(hit.get('title', ''), hit.get('story_text', '')):
            continue
        item = normalize({'name': hit.get('title'), 'description': hit.get('story_text') or hit.get('title'),
            'website': f"https://news.ycombinator.com/item?id={hit['objectID']}",
            'source': 'hackernews', 'published_at': hit.get('created_at'),
            'extra': {'evidence_kind': 'platform_api', 'external_url': hit.get('url'),
                      'points': hit.get('points'), 'comments': hit.get('num_comments'),
                      'retrieved_at': now.isoformat()}}, now)
        if item:
            items.append(item)
    return items


def search_item(source, row, now, provider):
    url = canonical_url(row.get('url'))
    parsed = urlparse(url)
    host = parsed.hostname or ''
    if not any(host == domain or host.endswith('.' + domain) for domain in SEARCH_DOMAINS[source]):
        return None
    date = parse_date(row.get('published_at'))
    basis = 'search_index'
    if source == 'x':
        match = re.fullmatch(r'/(?:[\w]+/status|i/(?:web/)?status)/(\d{15,20})', parsed.path)
        if not match:
            return None
        # X Snowflake embeds creation time; search crawl time is not publication.
        try:
            date = datetime.fromtimestamp(((int(match[1]) >> 22) + 1288834974657) / 1000, timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
        basis = 'x_snowflake'
    if source == 'reddit' and not re.match(r'/r/[^/]+/comments/[^/]+', parsed.path):
        return None
    if source == 'youtube' and not (parsed.path == '/watch' and parse_qs(parsed.query).get('v')):
        return None
    if not date or not now - timedelta(days=30) <= date <= now:
        return None
    if not is_ai_relevant(row.get('title', ''), row.get('summary', '')):
        return None
    return normalize({'name': row.get('title'), 'description': row.get('summary'),
        'website': url, 'source': source, 'published_at': date.isoformat(),
        'extra': {'evidence_kind': 'search_excerpt', 'search_provider': provider,
                  'publication_basis': basis, 'retrieved_at': now.isoformat()}}, now)


def search_items(source, now):
    # Reuse configured discovery search, at most one request per empty platform.
    domains = SEARCH_DOMAINS[source]
    query = 'AI artificial intelligence latest releases ' + ' OR '.join('site:' + d for d in domains)
    if source == 'x':
        query = 'site:x.com/status AI OpenAI Anthropic new release'
    if os.getenv('TAVILY_API_KEY', '').strip():
        from utils.tavily_client import search_articles
        rows = search_articles(query, 30, 10, now, topic='general', domains=domains)
        provider = 'Tavily'
    elif os.getenv('EXA_API_KEY', '').strip():
        from utils.exa_client import search_articles
        rows = search_articles(query, 30, 10, now)
        provider = 'Exa'
    else:
        raise ValueError('search_not_configured')
    return [item for row in rows if (item := search_item(source, row, now, provider))]


def direct_jobs(now, sources):
    jobs = []
    if 'hackernews' in sources:
        jobs.append(('hackernews', 'Algolia', hn_items, (now,)))
    feeds = []
    if 'reddit' in sources:
        # Reddit exposes a combined subreddit feed. One request avoids a burst
        # of parallel requests competing for the same platform rate limit.
        subs = [sub for sub in load_reddit_subreddits()[:15] if re.fullmatch(r'[A-Za-z0-9_]+', sub)]
        if subs:
            feeds.append(('reddit', f"https://www.reddit.com/r/{'+'.join(subs)}/new/.rss?limit=50", 'Reddit watchlist'))
    if 'youtube' in sources:
        feeds += [('youtube', f'https://www.youtube.com/feeds/videos.xml?channel_id={cid}', cid) for cid in load_youtube_channel_ids()[:15] if re.fullmatch(r'UC[\w-]+', cid)]
    if 'tech_news' in sources:
        feeds += [('tech_news', url, label) for url, label in TechNewsSpider.RSS_FEEDS]
    if 'cn_news' in sources:
        feeds += [('cn_news', row['url'], row['name']) for row in CN_RSS_FEEDS]
    if 'producthunt' in sources:
        feeds.append(('producthunt', 'https://www.producthunt.com/feed', 'Product Hunt'))
    for source, url, label in feeds:
        jobs.append((source, label, feed_items, (source, url, now, label)))
    return jobs


def run(output_dir=CRAWLER / 'data', sources=SOURCES, now=None):
    now = now or datetime.now(timezone.utc)
    output_dir = Path(output_dir)
    snapshot = output_dir / 'blogs_news.json'
    baseline = load_json(snapshot, [])
    fresh = []
    previous = load_json(output_dir / 'news_source_health.json', {})
    report = {'updated_at': now.isoformat(), 'sources': dict(previous.get('sources', {}))}
    report['sources'].update({s: {'status': 'pending', 'fresh_count': 0, 'errors': [],
        'feeds_ok': 0, 'checked_at': now.isoformat()} for s in sources})

    def checkpoint():
        merged = merge_news(baseline, fresh, now)
        atomic_json(snapshot, merged)
        for source, health in report['sources'].items():
            stored = [item for item in merged if item['source'] == source]
            health['stored_count'] = len(stored)
            health['latest_published_at'] = stored[0]['published_at'] if stored else None
        atomic_json(output_dir / 'news_source_health.json', report)
        return merged

    def consume(jobs, mode):
        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = {pool.submit(fn, *args): (source, label) for source, label, fn, args in jobs}
            for future in as_completed(futures):
                source, label = futures[future]
                health = report['sources'][source]
                try:
                    items = future.result()
                    fresh.extend(items)
                    health['feeds_ok'] += 1
                    health['fresh_count'] = len({i['website'] for i in fresh if i['source'] == source})
                    if items:
                        health['status'] = mode
                except Exception as exc:
                    # Never log response bodies, headers, request URLs or credentials.
                    code = getattr(getattr(exc, 'response', None), 'status_code', None)
                    reason = f'HTTP {code}' if code else type(exc).__name__
                    if isinstance(exc, ValueError) and str(exc) in ('search_not_configured', 'empty_or_invalid_feed'):
                        reason = str(exc)
                    health['errors'].append({'endpoint': label, 'reason': reason})
                checkpoint()

    consume(direct_jobs(now, sources), 'direct')
    fallback = [(s, 'search', search_items, (s, now)) for s in sources if not report['sources'][s]['fresh_count']]
    consume(fallback, 'search_fallback')
    for source in sources:
        health = report['sources'][source]
        if not health['fresh_count']:
            health['status'] = 'retained' if health.get('stored_count') else 'unavailable'
    merged = checkpoint()
    summary = ['## News sources', '', '| Source | Status | New | Stored |', '| --- | --- | ---: | ---: |']
    for source, health in report['sources'].items():
        summary.append(f"| {source} | {health['status']} | {health['fresh_count']} | {health['stored_count']} |")
    summary_text = '\n'.join(summary) + '\n'
    (output_dir / 'news_source_health.md').write_text(summary_text, encoding='utf-8')
    print(summary_text)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as handle:
            handle.write(summary_text)
    return merged, report


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv(CRAWLER.parent / '.env')
        load_dotenv(CRAWLER / '.env')
    except ImportError:
        pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=CRAWLER / 'data')
    parser.add_argument('--sources', default=','.join(SOURCES))
    args = parser.parse_args()
    sources = tuple(dict.fromkeys(args.sources.split(',')))
    if set(sources) - set(SOURCES):
        parser.error('Unknown source')
    _, report = run(args.output_dir, sources)
    return 0 if any(h['fresh_count'] for h in report['sources'].values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
