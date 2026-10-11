"""Keep broad technology RSS feeds focused without English substring matches."""
import pytest
from spiders.cn_news_spider import is_ai_relevant


@pytest.mark.parametrize('title', [
    'AirPods Pro 新款耳机上市', 'MacBook Air 发布新配色',
    'The company said retail prices are falling', '充电宝上架，限时优惠',
])
def test_ordinary_tech_news_is_not_ai(title):
    assert not is_ai_relevant(title, '新品发布')


@pytest.mark.parametrize('title', [
    'AI工具发布', 'OpenAI introduces a new API', 'ChatGPT 发布',
    'DeepSeek updates its models', 'Claude adds tools', 'LLMs and agents',
    '新一代GPT-5.4登场', '具身智能机器人获得融资', '自动驾驶算力芯片升级',
])
def test_actual_ai_and_hardware_signals_are_preserved(title):
    assert is_ai_relevant(title, '')


def test_ai_evidence_in_summary_can_qualify_a_generic_headline():
    assert is_ai_relevant('新品发布', '使用大模型为客户自动整理文档。')
