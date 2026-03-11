#!/usr/bin/env python3
"""Run approved rerun commands only. Arbitrary shell execution is disallowed."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def discover_repo_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely rerun approved pipeline steps.")
    parser.add_argument("step", nargs="?", help="Allowed step id to rerun.")
    parser.add_argument("--list", action="store_true", help="List allowed step ids.")
    parser.add_argument("--dry-run", action="store_true", help="Print command without executing.")
    parser.add_argument(
        "--actor",
        default=os.getenv("OPENCLAW_ACTOR", "unknown"),
        help="Actor for audit logging.",
    )
    parser.add_argument(
        "--reason",
        default="",
        help="Free text reason for audit logging.",
    )
    parser.add_argument(
        "--python-bin",
        default=os.getenv("PYTHON_BIN", "/usr/bin/python3"),
        help="Python binary path.",
    )
    return parser.parse_args()


def build_allowed_steps(repo_dir: Path, python_bin: str) -> dict[str, list[str]]:
    return {
        "rss_to_products": [
            python_bin,
            str(repo_dir / "crawler/tools/rss_to_products.py"),
            "--input",
            str(repo_dir / "crawler/data/blogs_news.json"),
            "--sources",
            "youtube,x",
            "--enrich-featured",
        ],
        "sync_to_mongodb": [
            python_bin,
            str(repo_dir / "crawler/tools/sync_to_mongodb.py"),
            "--all",
        ],
    }


def write_audit(
    *,
    repo_dir: Path,
    actor: str,
    step: str,
    reason: str,
    dry_run: bool,
    allowed: bool,
    command: list[str] | None,
    exit_code: int,
) -> None:
    audit_path = repo_dir / "crawler/logs/openclaw_safe_rerun_audit.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "actor": actor,
        "step": step,
        "reason": reason,
        "dry_run": dry_run,
        "allowed": allowed,
        "command": command or [],
        "exit_code": exit_code,
    }
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def main() -> int:
    args = parse_args()
    repo_dir = discover_repo_dir()
    allowed_steps = build_allowed_steps(repo_dir, args.python_bin)

    if args.list:
        print("Allowed step ids:")
        for step_id in sorted(allowed_steps):
            print(f"  - {step_id}")
        return 0

    if not args.step:
        print("step is required unless --list is provided")
        return 1

    command = allowed_steps.get(args.step)
    if command is None:
        print(f"step '{args.step}' is not allowed")
        write_audit(
            repo_dir=repo_dir,
            actor=args.actor,
            step=args.step,
            reason=args.reason,
            dry_run=args.dry_run,
            allowed=False,
            command=None,
            exit_code=2,
        )
        return 2

    if args.dry_run:
        print(" ".join(command))
        write_audit(
            repo_dir=repo_dir,
            actor=args.actor,
            step=args.step,
            reason=args.reason,
            dry_run=True,
            allowed=True,
            command=command,
            exit_code=0,
        )
        return 0

    result = subprocess.run(command, cwd=repo_dir)
    write_audit(
        repo_dir=repo_dir,
        actor=args.actor,
        step=args.step,
        reason=args.reason,
        dry_run=False,
        allowed=True,
        command=command,
        exit_code=result.returncode,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
