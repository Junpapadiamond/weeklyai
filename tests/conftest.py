"""Keep provider accounting and spider state out of checked-in data during tests."""
import pytest


@pytest.fixture(autouse=True)
def isolate_operational_state(monkeypatch, tmp_path):
    monkeypatch.setenv('API_USAGE_DAILY_FILE', str(tmp_path / 'usage.json'))
    monkeypatch.setenv('SOCIAL_HEALTH_DISABLE_WRITE', 'true')
    monkeypatch.setenv('X_SPIDER_DISABLE_STATE_WRITE', 'true')
