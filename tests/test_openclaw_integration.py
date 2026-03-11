import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_SUMMARY = REPO_ROOT / "ops/openclaw/run_summary.py"
SAFE_RERUN = REPO_ROOT / "ops/openclaw/safe_rerun.py"


def run_python(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_run_summary_optional_failure_is_degraded(tmp_path: Path) -> None:
    events = tmp_path / "events.tsv"
    events.write_text(
        "\n".join(
            [
                "auto_discover\tauto_discover.py --region all\ttrue\tsuccess\t0\t120\t2026-03-11T03:00:00Z\t2026-03-11T03:02:00Z",
                "news_only\tmain.py --news-only\tfalse\tfailed\t1\t45\t2026-03-11T03:02:00Z\t2026-03-11T03:02:45Z",
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "summary.json"

    result = run_python(
        RUN_SUMMARY,
        "--run-id",
        "demo_1",
        "--started-at",
        "2026-03-11T03:00:00Z",
        "--finished-at",
        "2026-03-11T03:10:00Z",
        "--events-file",
        str(events),
        "--output",
        str(output),
        "--report-path",
        "/tmp/a.log",
        "--report-path",
        "/tmp/a.log",
        "--report-path",
        "/tmp/b.log",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "degraded"
    assert len(payload["steps"]) == 2
    assert payload["report_paths"] == ["/tmp/a.log", "/tmp/b.log"]
    assert payload["error_summary"] == [
        {"step_id": "news_only", "name": "main.py --news-only", "exit_code": 1}
    ]


def test_run_summary_required_failure_is_failed(tmp_path: Path) -> None:
    events = tmp_path / "events.tsv"
    events.write_text(
        "sync_to_mongodb\tsync_to_mongodb.py --all\ttrue\tfailed\t2\t8\t2026-03-11T03:00:00Z\t2026-03-11T03:00:08Z",
        encoding="utf-8",
    )
    output = tmp_path / "summary.json"

    result = run_python(
        RUN_SUMMARY,
        "--run-id",
        "demo_2",
        "--started-at",
        "2026-03-11T03:00:00Z",
        "--finished-at",
        "2026-03-11T03:00:08Z",
        "--events-file",
        str(events),
        "--output",
        str(output),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "failed"
    assert payload["error_summary"] == [
        {"step_id": "sync_to_mongodb", "name": "sync_to_mongodb.py --all", "exit_code": 2}
    ]


def test_safe_rerun_rejects_unapproved_step() -> None:
    result = run_python(SAFE_RERUN, "rm_rf_everything")
    assert result.returncode == 2
    assert "not allowed" in result.stdout


def test_safe_rerun_allows_dry_run_for_whitelisted_step() -> None:
    result = run_python(SAFE_RERUN, "rss_to_products", "--dry-run")
    assert result.returncode == 0
    assert "rss_to_products.py" in result.stdout
