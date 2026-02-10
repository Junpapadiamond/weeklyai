#!/usr/bin/env python3
"""
Verify WeeklyAI JSON data sources (heuristic-only by default).

Usage:
  python crawler/tools/verify_data_sources.py --mode heuristic --check-network none \
    --report-json /tmp/data_report.json --report-md /tmp/data_report.md

Hybrid mode:
  --mode llm performs an extra LLM-assisted region verification for suspected region issues.
  (Designed for scheduled workflows where PERPLEXITY_API_KEY / ZHIPU_API_KEY are available.)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from glob import glob
from typing import Any, Dict, List, Optional, Sequence, Tuple


def _repo_root() -> str:
    # crawler/tools/verify_data_sources.py -> crawler/tools -> crawler -> repo_root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _ensure_import_paths() -> None:
    repo_root = _repo_root()
    crawler_root = os.path.join(repo_root, "crawler")
    if crawler_root not in sys.path:
        sys.path.insert(0, crawler_root)


def _load_json_list(path: str) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    if not os.path.exists(path):
        return [], "missing_file"
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        return [], f"invalid_json:{type(e).__name__}"
    if not isinstance(payload, list):
        return [], "unexpected_root"
    out: List[Dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict):
            out.append(item)
        else:
            # Keep shape; validator will emit issues.
            out.append({"__non_dict_item__": item})
    return out, None


def _save_json_list(path: str, payload: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _domain_from_website(website: str) -> str:
    try:
        from utils.data_verifier import extract_domain, is_http_url
    except Exception:
        return ""
    return extract_domain(website) if is_http_url(website) else ""


def _likely_cn(*, suggested_bucket: str, current_bucket: str, website: str, text: str) -> bool:
    if suggested_bucket == "🇨🇳" or current_bucket == "🇨🇳":
        return True
    d = _domain_from_website(website)
    if d.endswith(".cn"):
        return True
    # Very light heuristic: presence of explicit CN terms.
    for kw in ("中国", "北京", "上海", "深圳", "杭州"):
        if kw and kw in text:
            return True
    return False


def _llm_verify_region(
    *,
    name: str,
    website: str,
    current_bucket: str,
    suggested_bucket: str,
    description: str,
    why_matters: str,
    threshold: float = 0.75,
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Returns: (result_dict or None, provider_name)
    Result dict shape:
      {"bucket_region": "...", "confidence": 0.0, "evidence_urls": [...], "reason": "..."}
    """
    from utils.data_verifier import CANONICAL_REGION_BUCKETS

    text = f"{description or ''} {why_matters or ''}".strip()
    prefer_glm = _likely_cn(
        suggested_bucket=suggested_bucket or "",
        current_bucket=current_bucket or "",
        website=website or "",
        text=text,
    )

    # Lazy imports so heuristic runs don't require provider deps to be initialized.
    provider_name = ""
    client = None
    search_region = "us"
    if suggested_bucket == "🇨🇳" or prefer_glm:
        search_region = "cn"
    elif suggested_bucket == "🇪🇺":
        search_region = "eu"
    elif suggested_bucket == "🇯🇵🇰🇷":
        search_region = "jp"
    elif suggested_bucket == "🇸🇬":
        search_region = "sea"
    elif suggested_bucket == "🇺🇸":
        search_region = "us"

    if prefer_glm:
        try:
            from utils.glm_client import GLMClient

            glm = GLMClient()
            if glm.is_available():
                client = glm
                provider_name = "glm"
        except Exception:
            client = None

    if client is None:
        try:
            from utils.perplexity_client import PerplexityClient

            pplx = PerplexityClient()
            if pplx.is_available():
                client = pplx
                provider_name = "perplexity"
        except Exception:
            client = None

    if client is None:
        return None, provider_name

    domain = _domain_from_website(website or "")
    q = f"{name} company headquarters country official website"
    if domain:
        q = f"{q} site:{domain}"

    try:
        results = client.search_by_region(q, search_region, max_results=6)
    except TypeError:
        # Some clients use different signature, fall back.
        results = client.search_by_region(query=q, region=search_region, max_results=6)
    except Exception:
        results = []

    sources: List[str] = []
    try:
        sources = [r.url for r in results if getattr(r, "url", None)]
    except Exception:
        sources = []

    try:
        formatted = client.format_results_for_prompt(results)
    except Exception:
        formatted = "\n\n".join([getattr(r, "format_for_prompt")() for r in results if hasattr(r, "format_for_prompt")])

    prompt = f"""You are verifying a company's region bucket for WeeklyAI.

Product name: {name}
Website: {website}
Current region bucket: {current_bucket}
Heuristic suggested bucket: {suggested_bucket}

Buckets:
- 🇺🇸 (United States)
- 🇨🇳 (China)
- 🇪🇺 (Europe)
- 🇯🇵🇰🇷 (Japan/Korea)
- 🇸🇬 (Southeast Asia)
- 🌍 (Other/Unknown)

Rules:
- Use ONLY the Search Results below.
- evidence_urls must be URLs from the Search Results.
- confidence must be in [0, 1].
- If unsure, set bucket_region to 🌍 and confidence < {threshold}.

Return JSON only:
{{
  "bucket_region": "🇺🇸|🇨🇳|🇪🇺|🇯🇵🇰🇷|🇸🇬|🌍",
  "confidence": 0.0,
  "evidence_urls": ["https://..."],
  "reason": "short"
}}

Search Results:
{formatted}
"""

    try:
        out = client.analyze(prompt, temperature=0.0, max_tokens=800)
    except Exception:
        out = {}

    if isinstance(out, list) and out and isinstance(out[0], dict):
        out = out[0]
    if not isinstance(out, dict):
        return None, provider_name

    bucket_region = str(out.get("bucket_region") or "").strip()
    if bucket_region not in set(CANONICAL_REGION_BUCKETS):
        return None, provider_name

    try:
        confidence = float(out.get("confidence") or 0.0)
    except Exception:
        confidence = 0.0

    evidence_urls = out.get("evidence_urls") or []
    if not isinstance(evidence_urls, list):
        evidence_urls = []
    evidence_urls = [str(u).strip() for u in evidence_urls if isinstance(u, str) and u.strip().startswith(("http://", "https://"))]

    # Filter evidence URLs to ones we actually saw in search sources (best-effort).
    if sources:
        src_set = set(sources)
        evidence_urls = [u for u in evidence_urls if u in src_set]

    reason = str(out.get("reason") or "").strip()
    return {
        "bucket_region": bucket_region,
        "confidence": confidence,
        "evidence_urls": evidence_urls,
        "reason": reason,
        "query": q,
        "search_region": search_region,
    }, provider_name


def main() -> int:
    _ensure_import_paths()

    from utils.data_verifier import (
        Issue,
        Report,
        bucketize_region,
        now_iso_utc,
        render_report_md,
        render_report_json,
        validate_item_heuristic,
        verify_backend_snapshot_consistency,
    )

    parser = argparse.ArgumentParser(description="Verify WeeklyAI JSON data sources")
    parser.add_argument("--mode", choices=["heuristic", "llm"], default="heuristic", help="Verification mode")
    parser.add_argument(
        "--check-network",
        choices=["none", "logos", "websites", "all"],
        default="none",
        help="Enable best-effort reachability checks (WARN only)",
    )
    parser.add_argument("--apply-fixes", action="store_true", help="Apply safe fixes in-place (only where supported)")
    parser.add_argument(
        "--skip-backend-snapshot-check",
        action="store_true",
        help="Skip backend/data vs crawler/data consistency warnings",
    )
    parser.add_argument(
        "--llm-max-items",
        type=int,
        default=int(os.getenv("DATA_VERIFY_LLM_MAX_ITEMS", "25")),
        help="Max items to verify with LLM in --mode llm (cost/latency control)",
    )
    parser.add_argument("--report-json", default="", help="Write a JSON report to this path")
    parser.add_argument("--report-md", default="", help="Write a Markdown report to this path")
    args = parser.parse_args()

    repo_root = _repo_root()
    crawler_data_dir = os.path.join(repo_root, "crawler", "data")
    backend_data_dir = os.path.join(repo_root, "backend", "data")

    # Default scope
    paths: List[str] = [
        os.path.join(crawler_data_dir, "products_featured.json"),
        os.path.join(crawler_data_dir, "blogs_news.json"),
    ]
    paths.extend(sorted(glob(os.path.join(crawler_data_dir, "dark_horses", "*.json"))))
    paths.extend(sorted(glob(os.path.join(crawler_data_dir, "rising_stars", "*.json"))))

    issues: List[Issue] = []
    files_scanned = 0
    items_scanned = 0

    # Keep loaded payloads for optional apply-fixes.
    loaded: Dict[str, List[Dict[str, Any]]] = {}
    item_index: Dict[Tuple[str, int], Dict[str, Any]] = {}
    network_cache: Dict[str, Tuple[bool, str]] = {}

    for path in paths:
        files_scanned += 1
        payload, err = _load_json_list(path)
        loaded[path] = payload

        if err:
            sev = "ERROR" if err.startswith(("missing_file", "invalid_json", "unexpected_root")) else "WARN"
            issues.append(Issue(severity=sev, code=err, message=err, file=os.path.relpath(path, repo_root)))
            continue

        for idx, item in enumerate(payload):
            if "__non_dict_item__" in item:
                issues.append(
                    Issue(
                        severity="ERROR",
                        code="unexpected_item",
                        message="item must be an object/dict",
                        file=os.path.relpath(path, repo_root),
                        index=idx,
                    )
                )
                continue
            items_scanned += 1
            item_index[(path, idx)] = item
            issues.extend(
                validate_item_heuristic(
                    item,
                    file_path=os.path.relpath(path, repo_root),
                    index=idx,
                    check_network=args.check_network,
                    network_cache=network_cache if args.check_network != "none" else None,
                    check_region=(os.path.basename(path) != "blogs_news.json"),
                )
            )

    # Backend snapshot consistency (WARN only)
    if not args.skip_backend_snapshot_check:
        issues.extend(
            verify_backend_snapshot_consistency(
                repo_root=repo_root,
                crawler_data_dir=crawler_data_dir,
                backend_data_dir=backend_data_dir,
            )
        )

    # LLM-assisted region verification (scheduled runs)
    if args.mode == "llm":
        # Collect unique items with region-related warnings.
        region_codes = {"region_mismatch", "region_missing", "region_noncanonical", "region_inferred"}
        candidates: List[Tuple[str, int]] = []
        seen = set()
        for iss in issues:
            if iss.code not in region_codes:
                continue
            if iss.index is None:
                continue
            # iss.file is relpath; item_index keys use absolute file path.
            abs_path = os.path.join(repo_root, iss.file)
            key = (abs_path, int(iss.index))
            if key in seen:
                continue
            if key not in item_index:
                continue
            seen.add(key)
            candidates.append(key)

        confirmed_mismatch: Dict[Tuple[str, int], Dict[str, Any]] = {}
        llm_notes: Dict[Tuple[str, int], Dict[str, Any]] = {}

        if args.llm_max_items > 0 and len(candidates) > args.llm_max_items:
            skipped = len(candidates) - args.llm_max_items
            issues.append(
                Issue(
                    severity="WARN",
                    code="llm_limit_reached",
                    message=f"LLM verification limited to {args.llm_max_items} items; skipped {skipped}",
                    file="crawler/tools/verify_data_sources.py",
                )
            )
            candidates = candidates[: args.llm_max_items]

        for abs_path, idx in candidates:
            item = item_index.get((abs_path, idx))
            if not item:
                continue

            name = (item.get("name") or "").strip()
            website = (item.get("website") or "").strip()
            description = (item.get("description") or "").strip()
            why_matters = (item.get("why_matters") or "").strip()

            region_raw = (item.get("region") or "").strip()
            current_bucket = bucketize_region(region_raw) or "🌍"

            # Suggested bucket from heuristic inference, if present in the existing issues list.
            suggested_bucket = ""
            for iss in issues:
                if iss.index == idx and os.path.join(repo_root, iss.file) == abs_path and iss.suggestion:
                    if iss.code in {"region_mismatch", "region_inferred"}:
                        suggested_bucket = iss.suggestion
                        break

            result, provider = _llm_verify_region(
                name=name,
                website=website,
                current_bucket=current_bucket,
                suggested_bucket=suggested_bucket or current_bucket,
                description=description,
                why_matters=why_matters,
            )
            if not result:
                continue

            llm_notes[(abs_path, idx)] = {"provider": provider, **result}

            if result.get("confidence", 0.0) >= 0.75 and result.get("evidence_urls"):
                bucket_region = result.get("bucket_region")
                if bucket_region and bucket_region != current_bucket:
                    confirmed_mismatch[(abs_path, idx)] = {"provider": provider, **result}

        # Rewrite issues list:
        # - Remove heuristic region_mismatch for LLM-confirmed items
        # - Add an explicit LLM-confirmed warning with evidence
        new_issues: List[Issue] = []
        for iss in issues:
            if iss.code == "region_mismatch" and iss.index is not None:
                abs_path = os.path.join(repo_root, iss.file)
                key = (abs_path, int(iss.index))
                if key in confirmed_mismatch:
                    continue
            new_issues.append(iss)

        for (abs_path, idx), info in confirmed_mismatch.items():
            rel_file = os.path.relpath(abs_path, repo_root)
            item = item_index.get((abs_path, idx), {})
            new_issues.append(
                Issue(
                    severity="WARN",
                    code="region_llm_confirmed_mismatch",
                    message=f"LLM confirmed region mismatch (confidence {info.get('confidence'):.2f})",
                    file=rel_file,
                    index=idx,
                    name=(item.get("name") or "").strip(),
                    field="region",
                    suggestion=str(info.get("bucket_region") or ""),
                    details={
                        "provider": info.get("provider"),
                        "bucket_region": info.get("bucket_region"),
                        "confidence": info.get("confidence"),
                        "evidence_urls": info.get("evidence_urls"),
                        "reason": info.get("reason"),
                        "query": info.get("query"),
                        "search_region": info.get("search_region"),
                    },
                )
            )

        issues = new_issues

        # Optional: apply fixes (in-place) for canonicalization + confirmed LLM mismatches.
        if args.apply_fixes:
            changed_files = set()

            # 1) Canonicalize non-canonical region flags to bucket.
            for iss in issues:
                if iss.code != "region_noncanonical" or iss.index is None or not iss.suggestion:
                    continue
                abs_path = os.path.join(repo_root, iss.file)
                item = item_index.get((abs_path, int(iss.index)))
                if not item:
                    continue
                if (item.get("region") or "").strip() != iss.suggestion:
                    item["region"] = iss.suggestion
                    changed_files.add(abs_path)

            # 2) Apply LLM-confirmed mismatches and store evidence.
            from utils.data_verifier import is_http_url as _is_http_url
            from utils.data_verifier import now_iso_utc as _now_iso

            for (abs_path, idx), info in confirmed_mismatch.items():
                item = item_index.get((abs_path, idx))
                if not item:
                    continue
                bucket_region = str(info.get("bucket_region") or "").strip()
                if not bucket_region:
                    continue

                item["region"] = bucket_region
                extra = item.get("extra")
                if not isinstance(extra, dict):
                    extra = {}
                    item["extra"] = extra
                ver = extra.get("verification")
                if not isinstance(ver, dict):
                    ver = {}
                    extra["verification"] = ver
                ver["region"] = {
                    "bucket_region": bucket_region,
                    "confidence": info.get("confidence"),
                    "evidence_urls": info.get("evidence_urls"),
                    "reason": info.get("reason"),
                    "query": info.get("query"),
                    "provider": info.get("provider"),
                    "verified_at": _now_iso(),
                }

                # Clear needs_verification if it was only set for uncertainty (best-effort).
                website = (item.get("website") or "").strip()
                if item.get("needs_verification") is True and _is_http_url(website):
                    item["needs_verification"] = False

                changed_files.add(abs_path)

            for abs_path in sorted(changed_files):
                _save_json_list(abs_path, loaded.get(abs_path, []))

    error_count = sum(1 for i in issues if i.severity == "ERROR")
    warn_count = sum(1 for i in issues if i.severity == "WARN")

    report = Report(
        generated_at=now_iso_utc(),
        mode=args.mode,
        check_network=args.check_network,
        files_scanned=files_scanned,
        items_scanned=items_scanned,
        error_count=error_count,
        warn_count=warn_count,
        issues=issues,
    )

    if args.report_json:
        os.makedirs(os.path.dirname(args.report_json), exist_ok=True)
        with open(args.report_json, "w", encoding="utf-8") as f:
            f.write(render_report_json(report))

    if args.report_md:
        os.makedirs(os.path.dirname(args.report_md), exist_ok=True)
        with open(args.report_md, "w", encoding="utf-8") as f:
            f.write(render_report_md(report))

    print(f"files_scanned={files_scanned} items_scanned={items_scanned} errors={error_count} warnings={warn_count}")
    if error_count:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
