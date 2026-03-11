#!/usr/bin/env python3
"""Build a normalized OpenClaw payload from daily update step events."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) < 8:
            continue

        step_id, name, required_raw, status, exit_code_raw, duration_raw, started_at, finished_at = (
            parts[:8]
        )
        event = {
            "step_id": step_id,
            "name": name,
            "required": parse_bool(required_raw),
            "status": status,
            "exit_code": int(exit_code_raw),
            "duration_seconds": int(duration_raw),
            "started_at": started_at,
            "finished_at": finished_at,
        }
        events.append(event)
    return events


def compute_overall_status(events: list[dict[str, Any]]) -> str:
    required_failures = [e for e in events if e["required"] and e["status"] == "failed"]
    optional_failures = [e for e in events if (not e["required"]) and e["status"] == "failed"]

    if required_failures:
        return "failed"
    if optional_failures:
        return "degraded"
    return "success"


def build_error_summary(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for event in events:
        if event["status"] != "failed":
            continue
        summary.append(
            {
                "step_id": event["step_id"],
                "name": event["name"],
                "exit_code": event["exit_code"],
            }
        )
    return summary


def build_payload(
    *,
    run_id: str,
    started_at: str,
    finished_at: str,
    steps: list[dict[str, Any]],
    report_paths: list[str],
) -> dict[str, Any]:
    normalized_report_paths = [p for p in dict.fromkeys(report_paths) if p]
    return {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "overall_status": compute_overall_status(steps),
        "steps": steps,
        "report_paths": normalized_report_paths,
        "error_summary": build_error_summary(steps),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build OpenClaw summary payload.")
    parser.add_argument("--run-id", required=True, help="Unique run identifier.")
    parser.add_argument("--started-at", required=True, help="Run start timestamp (ISO 8601).")
    parser.add_argument("--finished-at", required=True, help="Run finish timestamp (ISO 8601).")
    parser.add_argument("--events-file", required=True, help="TSV file with step events.")
    parser.add_argument("--output", required=True, help="Summary output JSON path.")
    parser.add_argument(
        "--report-path",
        action="append",
        default=[],
        help="Report file path to include in payload. Can be passed multiple times.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    events_file = Path(args.events_file)
    steps = parse_events(events_file)
    payload = build_payload(
        run_id=args.run_id,
        started_at=args.started_at,
        finished_at=args.finished_at,
        steps=steps,
        report_paths=args.report_path,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[openclaw] run summary written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
