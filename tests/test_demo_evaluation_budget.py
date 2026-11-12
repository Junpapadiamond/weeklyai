"""Evaluation permission does not reset costs or change production quotas."""
import json

from crawler.tools.evaluate_demo_interactions import EvaluationBudget


def test_imports_three_prior_evaluations_once_and_keeps_failures_in_total(tmp_path):
    for name, requests in [("melius", 1), ("exa", 2), ("lovable", 1)]:
        (tmp_path / f"{name}-raw.json").write_text(json.dumps([{}] * requests), encoding="utf-8")
    path = tmp_path / "budget.sqlite3"
    budget = EvaluationBudget(path, tmp_path)
    assert budget.used() == 3
    assert not budget.acquire("default-exhausted", 3)
    for i in range(6):
        assert budget.acquire(f"revision2:{i}", 9)
    # Failures have no refund in this attempt ledger; recreating the runner,
    # changing its revision or requesting the same product cannot reset it.
    restarted = EvaluationBudget(path, tmp_path)
    assert restarted.used() == 9
    assert not restarted.acquire("revision3:failed-retry", 9)


def test_attempt_cap_is_shared_between_runner_instances(tmp_path):
    a = EvaluationBudget(tmp_path / "budget.sqlite3")
    b = EvaluationBudget(tmp_path / "budget.sqlite3")
    assert a.acquire("one", 3)
    assert b.acquire("two", 3)
    assert a.acquire("three", 3)
    assert not b.acquire("four", 3)
