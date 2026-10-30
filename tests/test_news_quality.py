from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'crawler'))
from utils.news_quality import rejection_reason

NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)


def item(title, summary='', source='tech_news', **extra):
    urls = {'youtube': 'https://youtube.com/watch?v=abc', 'reddit': 'https://reddit.com/r/LocalLLaMA/comments/abc/release',
            'hackernews': 'https://news.ycombinator.com/item?id=123', 'producthunt': 'https://producthunt.com/products/abc'}
    return {'name': title, 'description': summary, 'source': source,
            'website': urls.get(source, 'https://example.com/article'), 'published_at': NOW.isoformat(),
            'extra': {'evidence_kind': 'feed_excerpt', 'feed_url': 'https://example.com/feed', **extra}}


@pytest.mark.parametrize('title,summary,source', [
    ('Prime Numbers explained by Mathematician', 'Sponsor: use ChatGPT to work faster', 'youtube'),
    ('Airline retail discount', 'An airline said its retail sale starts today', 'tech_news'),
    ('OPPO Find X10 全新配色开售，5499 元起', '天玑芯片与全新屏幕，限时上市。', 'cn_news'),
    ('闪迪第一财季将投50亿美元用于股票回购', '公司财报业绩增长。' * 50 + 'AI 数据中心', 'cn_news'),
    ('Travel agents announce new packages', 'Agents automate booking.', 'tech_news'),
])
def test_relevance_cannot_come_from_sponsors_generic_chips_or_footer(title, summary, source):
    assert rejection_reason(item(title, summary, source), NOW) == 'off_topic'


@pytest.mark.parametrize('title,summary,source', [
    ('Gemini now edits documents', 'Generate and edit files directly.', 'tech_news'),
    ('A tiny tool nobody knows', 'Open-source neural network inference for local deployment.', 'tech_news'),
    ('AssemblyAI', 'text-to-speech built for voice agents', 'producthunt'),
    ('国产机器人发布开源控制模型', '原文介绍控制模型。', 'cn_news'),
    ('DeepSeek releases new weights', 'Research paper and benchmark results.', 'youtube'),
])
def test_concrete_ai_signals_do_not_require_popularity(title, summary, source):
    assert rejection_reason(item(title, summary, source), NOW) is None


@pytest.mark.parametrize('title', ['How to stop Claude Code loading a skill automatically',
                                  'Qwen 3.8 what am I missing here?', 'MY DEMAND: SHUT ME DOWN NOW'])
def test_personal_help_and_chatter_are_not_news(title):
    assert rejection_reason(item(title, 'Claude Code API integration ' * 12, 'reddit'), NOW) == 'personal_help_or_chatter'


def test_community_release_requires_evidence_but_no_votes():
    row = item('I built an open-source AI model evaluator', 'Code and results.', 'reddit')
    assert rejection_reason(row, NOW) == 'insufficient_evidence'
    row['extra']['outbound_urls'] = ['https://github.com/example/evaluator']
    assert rejection_reason(row, NOW) is None
    row['extra']['outbound_urls'] = ['javascript:alert(1)']
    assert rejection_reason(row, NOW) == 'insufficient_evidence'


def test_search_excerpt_is_not_verification_of_an_unknown_x_author():
    snowflake = (int(NOW.timestamp() * 1000) - 1288834974657) << 22
    row = item('Anthropic releases new AI model with public evaluation results', 'New model weights and public evaluation results are available.', 'x',
               evidence_kind='search_excerpt', publication_basis='x_snowflake')
    row['website'] = f'https://x.com/RandomNews/status/{snowflake}'
    assert rejection_reason(row, NOW) == 'unvetted_x_author'
    row['website'] = f'https://x.com/AnthropicAI/status/{snowflake}'
    assert rejection_reason(row, NOW) is None
    row['published_at'] = (NOW - timedelta(days=1)).isoformat()
    assert rejection_reason(row, NOW) == 'publication_date_mismatch'


def test_expired_or_provenance_free_retained_items_cannot_reenter():
    row = item('New AI model released')
    row['published_at'] = (NOW - timedelta(days=31)).isoformat()
    assert rejection_reason(row, NOW) == 'outside_news_window'
    row['published_at'] = NOW.isoformat()
    row['extra'] = {}
    assert rejection_reason(row, NOW) == 'missing_provenance'
