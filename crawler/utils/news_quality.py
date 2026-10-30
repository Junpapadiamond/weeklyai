"""Conservative publication gates, not a factual truth/credibility score.

Only title and article lead establish relevance. Long descriptions often contain
unrelated sponsors, related-story links and publisher boilerplate.
"""
from datetime import datetime, timedelta, timezone
import re
import unicodedata
from urllib.parse import urlparse, parse_qs

from utils.social_sources import load_x_accounts
from utils.tavily_client import parse_date

POLICY_VERSION = 1
MAX_AGE_DAYS = 30
AI = re.compile(
    r'(?<![a-z0-9])(?:ai|aigc|llms?|gpt(?:-?\d[\w.-]*)?|openai|anthropic|'
    r'chatgpt|deepseek|claude|gemini|qwen|mistral|codex|copilot|hugging\s?face|'
    r'langchain|ollama|opencode|grok|machine learning|deep learning|neural network|'
    r'artificial intelligence|agentic|coding agents?|voice agents?|'
    r'agent runs?|open[- ]weight|text[- ]to[- ](?:speech|video|image))(?![a-z0-9])|'
    r'人工智能|生成式|大模型|语言模型|智能体|具身智能|机器学习|深度学习|自动驾驶|机器人', re.I)
SUBSTANCE = re.compile(
    r'\b(?:releas\w*|launch\w*|announc\w*|introduc\w*|publish\w*|research\w*|'
    r'paper|benchmark\w*|evaluat\w*|experiment\w*|dataset\w*|open[- ]source|'
    r'build|built|building|tested|testing|audit\w*|compar\w*|integrat\w*|deploy\w*|'
    r'pricing|cost|latency|security|vulnerab\w*|funding|valuation|series [a-z]|acquir\w*|weights|'
    r'api|model|workflow|inference|training|study|studies|report|feature|'
    r'architecture|implementation|analysis|analy[sz]\w*)\b|'
    r'发布|开源|研究|论文|评测|测试|模型|产品|融资|收购|上线|更新|漏洞|定价|部署', re.I)
HELP = re.compile(
    r'^(?:\[[^]]+\]\s*)?(?:help\b|please help|can (?:anyone|someone)|'
    r'how (?:do|can|should) i\b|how to (?:stop|fix|improve|use)\b|'
    r'any (?:advice|tips)|i (?:need|want)\b|what (?:am i|should i)|'
    r'hey[, ]|frustration\b|my demand\b)|'
    r'\b(?:what am i missing|looking for (?:help|advice)|unable to|integration issue|diaries)\b|'
    r'求助|请问|怎么解决|有没有人', re.I)
PROMO = re.compile(r'\b(?:giveaway|promo code|coupon code|airdrop|buy followers)\b|'
                   r'优惠券|限时抢购|抽奖送|返现|领券', re.I)
RUMOR = re.compile(r'\b(?:rumou?rs?|reportedly|unreleased|leaked?|preparing|'
                   r'according to|potential release|will release|expected to)\b|'
                   r'据传|传闻|爆料|据悉|或将', re.I)
GARBAGE = re.compile(r'^(?:\[removed\]|\[deleted\]|access denied|just a moment|'
                     r'sign in|log in|subscribe to continue)$', re.I)


def title_key(title):
    return re.sub(r'[^\w]+', '', unicodedata.normalize('NFKC', title).casefold())


def evidence_link(value):
    try:
        p = urlparse(str(value or ''))
        return p.scheme in {'http', 'https'} and bool(p.hostname) and not p.username and not p.password
    except ValueError:
        return False


def is_post_url(source, url):
    p = urlparse(url)
    host = (p.hostname or '').lower().removeprefix('www.')
    if source == 'x':
        return host == 'x.com' and bool(re.fullmatch(r'/\w+/status/\d{15,20}', p.path))
    if source == 'reddit':
        return host == 'reddit.com' and bool(re.match(r'/r/[^/]+/comments/[^/]+(?:/|$)', p.path))
    if source == 'youtube':
        return host == 'youtube.com' and p.path == '/watch' and bool(parse_qs(p.query).get('v'))
    if source == 'hackernews':
        return host == 'news.ycombinator.com' and p.path == '/item' and str(parse_qs(p.query).get('id', [''])[0]).isdigit()
    if source == 'producthunt':
        return host == 'producthunt.com' and bool(re.match(r'/(?:posts|products)/[^/]+', p.path))
    return bool(p.path.strip('/'))


def rejection_reason(item, now):
    source = item.get('source')
    title = str(item.get('name') or '')
    summary = str(item.get('description') or '')
    extra = item.get('extra') or {}
    date = parse_date(item.get('published_at'))
    if source not in {'x', 'reddit', 'youtube', 'hackernews', 'producthunt', 'tech_news', 'cn_news'}:
        return 'unsupported_source'
    if not date or not now - timedelta(days=MAX_AGE_DAYS) <= date <= now:
        return 'outside_news_window'
    if not is_post_url(source, item.get('website', '')):
        return 'not_original_item'
    if len(title_key(title)) < 2 or GARBAGE.match(title) or '\ufffd' in title:
        return 'unusable_title'
    if extra.get('evidence_kind') not in {'feed_excerpt', 'platform_api', 'search_excerpt'}:
        return 'missing_provenance'
    if extra.get('evidence_kind') == 'feed_excerpt' and not evidence_link(extra.get('feed_url')):
        return 'missing_provenance'
    if PROMO.search(title):
        return 'promotion'
    # Video sponsor blocks cannot establish relevance, even in the first lines.
    lead_length = 160 if source == 'cn_news' else 280
    relevant_text = title if source == 'youtube' else title + ' ' + summary[:lead_length]
    if source != 'x' and not AI.search(relevant_text):
        return 'off_topic'
    if source == 'x':
        account = urlparse(item['website']).path.split('/')[1].lower()
        if account not in {a.lower() for a in load_x_accounts()}:
            return 'unvetted_x_author'
        if len(summary) < 40:
            return 'insufficient_excerpt'
        text_without_links = re.sub(r'https?://\S+', '', title)
        if len(title_key(text_without_links)) < 30 or not SUBSTANCE.search(text_without_links):
            return 'no_concrete_signal'
        if not AI.search(text_without_links) and not re.search(
                r'\b(?:releas\w*|launch\w*|announc\w*|research\w*|model|api|'
                r'dataset|benchmark\w*|weights|funding|financing|series [a-z]|valuation)\b',
                text_without_links, re.I):
            return 'no_concrete_signal'
        if extra.get('publication_basis') != 'x_snowflake':
            return 'missing_publication_basis'
        try:
            post_id = int(urlparse(item['website']).path.split('/')[-1])
            created = datetime.fromtimestamp(((post_id >> 22) + 1288834974657) / 1000, timezone.utc)
        except (ValueError, OverflowError, OSError):
            return 'missing_publication_basis'
        if abs((created - date).total_seconds()) > 1:
            return 'publication_date_mismatch'
    if source in {'reddit', 'hackernews'}:
        if HELP.search(title) or HELP.search(summary[:100]):
            return 'personal_help_or_chatter'
        if RUMOR.search(title):
            return 'unverified_rumor'
        raw_links = extra.get('outbound_urls')
        links = [link for link in raw_links if evidence_link(link)] if isinstance(raw_links, list) else []
        external = extra.get('external_url') if evidence_link(extra.get('external_url')) else None
        if not SUBSTANCE.search(title) and not ((links or external) and SUBSTANCE.search(summary[:400])):
            return 'no_concrete_signal'
        if not external and not links and len(summary) < 180:
            return 'insufficient_evidence'
    return None
