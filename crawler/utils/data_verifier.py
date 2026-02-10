"""
WeeklyAI data verification utilities.

Goals:
- Deterministic verification for JSON data sources (products/blogs/weekly lists)
- Split issues into ERROR (fail CI) vs WARN (report-only)
- Heuristic-only by default; optional LLM-assisted region verification in scheduled runs
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
from dataclasses import dataclass, field as dc_field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

try:
    # Prefer shared placeholder logic when available.
    from .website_resolver import is_placeholder_url as _is_placeholder_url  # type: ignore
except Exception:
    _PLACEHOLDER_DOMAINS_FALLBACK = {
        "example.com",
        "example.org",
        "example.net",
        "test.com",
        "test.org",
        "localhost",
        "127.0.0.1",
    }

    def _is_placeholder_url(url: str) -> bool:  # type: ignore
        try:
            parsed = urlparse(url or "")
            domain = (parsed.netloc or "").lower()
            if domain.startswith("www."):
                domain = domain[4:]
            if ":" in domain:
                domain = domain.split(":", 1)[0]
            if not domain:
                return True
            if domain in _PLACEHOLDER_DOMAINS_FALLBACK:
                return True
            if domain.endswith(".local"):
                return True
            return False
        except Exception:
            return True


def is_placeholder_url(url: str) -> bool:
    return _is_placeholder_url(url)


CANONICAL_REGION_BUCKETS: Tuple[str, ...] = ("🇺🇸", "🇨🇳", "🇪🇺", "🇯🇵🇰🇷", "🇸🇬", "🌍")
_CANONICAL_BUCKET_SET = set(CANONICAL_REGION_BUCKETS)

# Country flags we map into our canonical buckets for comparison/normalization.
_EU_FLAGS = {
    "🇪🇺",
    "🇩🇪",
    "🇫🇷",
    "🇬🇧",
    "🇮🇪",
    "🇮🇹",
    "🇪🇸",
    "🇵🇹",
    "🇳🇱",
    "🇧🇪",
    "🇸🇪",
    "🇩🇰",
    "🇫🇮",
    "🇳🇴",
    "🇨🇭",
    "🇦🇹",
    "🇵🇱",
    "🇨🇿",
    "🇸🇰",
    "🇭🇺",
    "🇷🇴",
    "🇧🇬",
    "🇬🇷",
}
_JK_FLAGS = {"🇯🇵", "🇰🇷", "🇯🇵🇰🇷"}
_SEA_FLAGS = {"🇸🇬", "🇮🇩", "🇻🇳", "🇹🇭", "🇲🇾", "🇵🇭"}

# Europe-ish ccTLDs (Europe bucket is broader than EU union).
_EUROPE_CCTLDS = {
    "eu",
    "uk",
    "gb",
    "de",
    "fr",
    "nl",
    "be",
    "se",
    "dk",
    "fi",
    "no",
    "ch",
    "at",
    "it",
    "es",
    "pt",
    "ie",
    "pl",
    "cz",
    "sk",
    "hu",
    "ro",
    "bg",
    "gr",
    "ee",
    "lv",
    "lt",
    "si",
    "hr",
    "rs",
    "ua",
}


# Simple placeholder patterns (WARN only).
_DESCRIPTION_PLACEHOLDERS = {
    "tbd",
    "n/a",
    "暂无",
    "待定",
    "未公开",
    "持续更新中",
}


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def is_http_url(value: str) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def is_unknown_value(value: str) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().lower() in {"unknown", "n/a", "na", "none"}


def extract_domain(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""
    try:
        parsed = urlparse(url.strip())
        host = (parsed.netloc or "").lower()
        # urlparse("example.com") -> path only; treat as no domain.
        if not host:
            return ""
        if "@" in host:
            host = host.split("@", 1)[-1]
        if ":" in host:
            host = host.split(":", 1)[0]
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def sha1_file(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bucketize_region(value: str) -> Optional[str]:
    """Map arbitrary region strings/flags into our canonical bucket set."""
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw in _CANONICAL_BUCKET_SET:
        return raw
    if raw in _JK_FLAGS:
        return "🇯🇵🇰🇷"
    if raw in _EU_FLAGS:
        return "🇪🇺"
    if raw in _SEA_FLAGS:
        return "🇸🇬"
    if raw == "🇨🇳":
        return "🇨🇳"
    if raw == "🇺🇸":
        return "🇺🇸"
    # Anything else is treated as "Other/Unknown" bucket for comparisons.
    return "🌍"


def _contains_keyword(text: str, keyword: str) -> bool:
    if not text or not keyword:
        return False
    # If keyword contains non-ascii, do a simple substring match.
    try:
        keyword.encode("ascii")
        keyword_is_ascii = True
    except Exception:
        keyword_is_ascii = False

    if not keyword_is_ascii:
        return keyword in text

    # ASCII keyword: use word boundaries when possible.
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


_TEXT_KEYWORDS: Dict[str, Sequence[str]] = {
    # Keep CN keywords explicit to reduce false positives (avoid ambiguous words like "本土").
    "🇨🇳": ["中国", "北京", "上海", "深圳", "杭州", "广州", "国产"],
    "🇯🇵🇰🇷": [
        "日本",
        "东京",
        "東京",
        "大阪",
        "日语",
        "韓国",
        "韩国",
        "首尔",
        "한국",
        "서울",
        "Japan",
        "Japanese",
        "Korea",
        "Korean",
    ],
    "🇸🇬": ["新加坡", "东南亚", "Singapore", "Southeast Asia", "Indonesia", "Vietnam", "Thailand", "Malaysia"],
    "🇪🇺": ["欧洲", "欧盟", "英国", "伦敦", "Germany", "Berlin", "France", "Paris", "UK", "European", "EU"],
    "🇺🇸": ["美国", "硅谷", "旧金山", "San Francisco", "New York", "USA", "United States", "U.S."],
}


def infer_region_bucket(
    *,
    website: str,
    description: str = "",
    why_matters: str = "",
) -> Tuple[Optional[str], str]:
    """Infer a canonical region bucket from domain + text signals.

    Returns: (bucket or None, reason string)
    """
    domain = extract_domain(website) if is_http_url(website) else ""
    if domain:
        if domain.endswith(".cn"):
            return "🇨🇳", "domain_tld:.cn"
        if domain.endswith(".jp") or domain.endswith(".co.jp") or domain.endswith(".ne.jp"):
            return "🇯🇵🇰🇷", "domain_tld:.jp"
        if domain.endswith(".kr") or domain.endswith(".co.kr"):
            return "🇯🇵🇰🇷", "domain_tld:.kr"
        if domain.endswith(".sg"):
            return "🇸🇬", "domain_tld:.sg"
        if domain.endswith(".us"):
            return "🇺🇸", "domain_tld:.us"

        tld = domain.split(".")[-1]
        if tld in _EUROPE_CCTLDS:
            return "🇪🇺", f"domain_tld:.{tld}"

    text = f"{description or ''} {why_matters or ''}".strip()
    if not text:
        return None, ""

    # Keep original text for CJK substring checks; lowercased for ASCII checks.
    text_lower = text.lower()

    counts: Dict[str, int] = {}
    hits: Dict[str, List[str]] = {}
    for bucket, keywords in _TEXT_KEYWORDS.items():
        counts[bucket] = 0
        hits[bucket] = []
        for kw in keywords:
            hay = text_lower if kw.isascii() else text
            if _contains_keyword(hay, kw):
                counts[bucket] += 1
                hits[bucket].append(kw)

    best_bucket = None
    best_count = 0
    for bucket, cnt in counts.items():
        if cnt > best_count:
            best_count = cnt
            best_bucket = bucket

    if not best_bucket or best_count <= 0:
        return None, ""

    # Avoid ties.
    if list(counts.values()).count(best_count) > 1:
        return None, ""

    example_hits = hits.get(best_bucket, [])[:2]
    reason = "text:" + ",".join(example_hits) if example_hits else "text"
    return best_bucket, reason


def description_has_placeholders(description: str) -> bool:
    if not isinstance(description, str):
        return False
    lowered = description.strip().lower()
    if not lowered:
        return False
    return any(p in lowered for p in _DESCRIPTION_PLACEHOLDERS)


@dataclass(frozen=True)
class Issue:
    severity: str  # "ERROR" | "WARN"
    code: str
    message: str
    file: str
    index: Optional[int] = None
    name: str = ""
    field: str = ""
    suggestion: str = ""
    details: Dict[str, Any] = dc_field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class Report:
    generated_at: str
    mode: str
    check_network: str
    files_scanned: int
    items_scanned: int
    error_count: int
    warn_count: int
    issues: List[Issue] = dc_field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "mode": self.mode,
            "check_network": self.check_network,
            "files_scanned": self.files_scanned,
            "items_scanned": self.items_scanned,
            "error_count": self.error_count,
            "warn_count": self.warn_count,
            "issues": [i.to_dict() for i in self.issues],
        }


def _sorted_issues(issues: Iterable[Issue]) -> List[Issue]:
    def key(i: Issue):
        sev = 0 if i.severity == "ERROR" else 1
        idx = i.index if i.index is not None else 10**9
        return (sev, i.file, idx, i.code, i.name)

    return sorted(list(issues), key=key)


def render_report_md(report: Report, *, max_per_severity: int = 50) -> str:
    issues = _sorted_issues(report.issues)
    errors = [i for i in issues if i.severity == "ERROR"]
    warns = [i for i in issues if i.severity == "WARN"]

    lines: List[str] = []
    lines.append("# WeeklyAI Data Verification Report")
    lines.append("")
    lines.append(f"- Generated (UTC): `{report.generated_at}`")
    lines.append(f"- Mode: `{report.mode}`")
    lines.append(f"- Network checks: `{report.check_network}`")
    lines.append(f"- Files scanned: `{report.files_scanned}`")
    lines.append(f"- Items scanned: `{report.items_scanned}`")
    lines.append(f"- Errors: `{len(errors)}`")
    lines.append(f"- Warnings: `{len(warns)}`")

    if errors:
        lines.append("")
        lines.append(f"## Errors ({len(errors)})")
        for i, issue in enumerate(errors[:max_per_severity], start=1):
            ref = f"[{issue.index}]" if issue.index is not None else ""
            name = f" {issue.name}" if issue.name else ""
            lines.append(f"{i}. `{issue.file}` {ref}{name}: {issue.message} (`{issue.code}`)")
        if len(errors) > max_per_severity:
            lines.append(f"- ... {len(errors) - max_per_severity} more errors (see JSON artifact).")

    if warns:
        lines.append("")
        lines.append(f"## Warnings ({len(warns)})")
        for i, issue in enumerate(warns[:max_per_severity], start=1):
            ref = f"[{issue.index}]" if issue.index is not None else ""
            name = f" {issue.name}" if issue.name else ""
            suggestion = f" (suggest: `{issue.suggestion}`)" if issue.suggestion else ""
            lines.append(f"{i}. `{issue.file}` {ref}{name}: {issue.message} (`{issue.code}`){suggestion}")
        if len(warns) > max_per_severity:
            lines.append(f"- ... {len(warns) - max_per_severity} more warnings (see JSON artifact).")

    if not errors and not warns:
        lines.append("")
        lines.append("✅ No issues found.")

    lines.append("")
    return "\n".join(lines)


def render_report_json(report: Report) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)


def _check_url_reachable(url: str, *, timeout_seconds: int = 6) -> Tuple[bool, str]:
    """Best-effort URL reachability. Returns (ok, reason/status)."""
    if not is_http_url(url):
        return False, "not_http_url"
    try:
        import requests  # lazy import
    except Exception:
        return False, "requests_missing"

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.head(url, timeout=timeout_seconds, allow_redirects=True, headers=headers)
        if 200 <= resp.status_code < 400:
            return True, f"status:{resp.status_code}"
    except Exception:
        pass

    try:
        resp = requests.get(url, timeout=timeout_seconds, allow_redirects=True, headers=headers, stream=True)
        if 200 <= resp.status_code < 400:
            return True, f"status:{resp.status_code}"
        return False, f"status:{resp.status_code}"
    except Exception as e:
        return False, f"error:{type(e).__name__}"


def validate_item_heuristic(
    item: Dict[str, Any],
    *,
    file_path: str,
    index: int,
    check_network: str = "none",
    network_cache: Optional[Dict[str, Tuple[bool, str]]] = None,
    check_region: bool = True,
) -> List[Issue]:
    issues: List[Issue] = []

    name = (item.get("name") or "").strip()
    if not name:
        issues.append(
            Issue(
                severity="ERROR",
                code="missing_name",
                message="missing name",
                file=file_path,
                index=index,
                field="name",
            )
        )
        # Without name, other messages are much less useful; continue checking anyway.

    website = (item.get("website") or "").strip()
    if not website:
        issues.append(
            Issue(
                severity="ERROR",
                code="missing_website",
                message="missing website",
                file=file_path,
                index=index,
                name=name,
                field="website",
            )
        )
    else:
        if not is_http_url(website) and not is_unknown_value(website):
            issues.append(
                Issue(
                    severity="ERROR",
                    code="invalid_website",
                    message="website must be http(s) or 'unknown'",
                    file=file_path,
                    index=index,
                    name=name,
                    field="website",
                    details={"website": website},
                )
            )
        if is_http_url(website) and is_placeholder_url(website):
            issues.append(
                Issue(
                    severity="ERROR",
                    code="website_placeholder",
                    message="website is a placeholder domain",
                    file=file_path,
                    index=index,
                    name=name,
                    field="website",
                    details={"website": website},
                )
            )

        if check_network in {"websites", "all"} and is_http_url(website):
            if network_cache is not None and website in network_cache:
                ok, reason = network_cache[website]
            else:
                ok, reason = _check_url_reachable(website)
                if network_cache is not None:
                    network_cache[website] = (ok, reason)
            if not ok:
                issues.append(
                    Issue(
                        severity="WARN",
                        code="website_unreachable",
                        message=f"website not reachable ({reason})",
                        file=file_path,
                        index=index,
                        name=name,
                        field="website",
                        details={"website": website, "reason": reason},
                    )
                )

    description = (item.get("description") or "").strip()
    if not description:
        issues.append(
            Issue(
                severity="ERROR",
                code="missing_description",
                message="missing description",
                file=file_path,
                index=index,
                name=name,
                field="description",
            )
        )
    elif len(description) < 20:
        issues.append(
            Issue(
                severity="ERROR",
                code="short_description",
                message=f"description too short ({len(description)})",
                file=file_path,
                index=index,
                name=name,
                field="description",
            )
        )
    elif description_has_placeholders(description):
        issues.append(
            Issue(
                severity="WARN",
                code="description_placeholder",
                message="description contains placeholder-like text",
                file=file_path,
                index=index,
                name=name,
                field="description",
                details={"description": description[:120]},
            )
        )

    logo_url = (item.get("logo_url") or item.get("logo") or "").strip()
    if logo_url:
        # Allow site-root relative paths (e.g. "/logos/...") for curated assets.
        if logo_url.startswith("/"):
            pass
        elif not is_http_url(logo_url):
            issues.append(
                Issue(
                    severity="ERROR",
                    code="invalid_logo_url",
                    message="logo_url must be http(s) or an absolute site path (starting with '/') if present",
                    file=file_path,
                    index=index,
                    name=name,
                    field="logo_url",
                    details={"logo_url": logo_url},
                )
            )
        elif check_network in {"logos", "all"}:
            if network_cache is not None and logo_url in network_cache:
                ok, reason = network_cache[logo_url]
            else:
                ok, reason = _check_url_reachable(logo_url)
                if network_cache is not None:
                    network_cache[logo_url] = (ok, reason)
            if not ok:
                issues.append(
                    Issue(
                        severity="WARN",
                        code="logo_unreachable",
                        message=f"logo_url not reachable ({reason})",
                        file=file_path,
                        index=index,
                        name=name,
                        field="logo_url",
                        details={"logo_url": logo_url, "reason": reason},
                    )
                )
    else:
        issues.append(
            Issue(
                severity="WARN",
                code="logo_missing",
                message="missing logo_url",
                file=file_path,
                index=index,
                name=name,
                field="logo_url",
            )
        )

    if check_region:
        # Region checks (WARN only) — primarily for product datasets.
        region_raw = (item.get("region") or "").strip()
        current_bucket = bucketize_region(region_raw) if region_raw else None

        if not region_raw:
            issues.append(
                Issue(
                    severity="WARN",
                    code="region_missing",
                    message="missing region bucket",
                    file=file_path,
                    index=index,
                    name=name,
                    field="region",
                )
            )
        elif region_raw not in _CANONICAL_BUCKET_SET:
            suggested = bucketize_region(region_raw) or ""
            issues.append(
                Issue(
                    severity="WARN",
                    code="region_noncanonical",
                    message="region is not in canonical bucket set",
                    file=file_path,
                    index=index,
                    name=name,
                    field="region",
                    suggestion=suggested,
                    details={"region": region_raw, "bucket": suggested},
                )
            )

        inferred, reason = infer_region_bucket(
            website=website if is_http_url(website) else "",
            description=description,
            why_matters=(item.get("why_matters") or ""),
        )
        if inferred and inferred != "🌍":
            if current_bucket and current_bucket != inferred:
                issues.append(
                    Issue(
                        severity="WARN",
                        code="region_mismatch",
                        message=f"region bucket mismatch (heuristic: {reason})",
                        file=file_path,
                        index=index,
                        name=name,
                        field="region",
                        suggestion=inferred,
                        details={
                            "current_region": region_raw,
                            "current_bucket": current_bucket,
                            "inferred_bucket": inferred,
                            "reason": reason,
                            "website": website,
                        },
                    )
                )
            if (not current_bucket) or (current_bucket == "🌍"):
                issues.append(
                    Issue(
                        severity="WARN",
                        code="region_inferred",
                        message=f"region can be inferred (heuristic: {reason})",
                        file=file_path,
                        index=index,
                        name=name,
                        field="region",
                        suggestion=inferred,
                        details={"reason": reason, "website": website},
                    )
                )

    return issues


def validate_json_file_heuristic(
    path: str,
    *,
    check_network: str = "none",
) -> Tuple[int, List[Issue]]:
    """Validate a JSON file that contains a list of dict items."""
    issues: List[Issue] = []
    items_scanned = 0

    if not os.path.exists(path):
        issues.append(
            Issue(
                severity="ERROR",
                code="missing_file",
                message="data file does not exist",
                file=path,
            )
        )
        return 0, issues

    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        issues.append(
            Issue(
                severity="ERROR",
                code="invalid_json",
                message=f"failed to parse JSON: {type(e).__name__}",
                file=path,
            )
        )
        return 0, issues

    if not isinstance(payload, list):
        issues.append(
            Issue(
                severity="ERROR",
                code="unexpected_root",
                message="JSON root must be a list",
                file=path,
            )
        )
        return 0, issues

    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            issues.append(
                Issue(
                    severity="ERROR",
                    code="unexpected_item",
                    message="item must be an object/dict",
                    file=path,
                    index=idx,
                )
            )
            continue
        items_scanned += 1
        issues.extend(validate_item_heuristic(item, file_path=path, index=idx, check_network=check_network))

    return items_scanned, issues


def verify_backend_snapshot_consistency(
    *,
    repo_root: str,
    crawler_data_dir: str,
    backend_data_dir: str,
) -> List[Issue]:
    """Warn if backend/data snapshot diverges from crawler/data."""
    issues: List[Issue] = []

    pairs = [
        ("products_featured.json", "products_featured.json"),
        ("blogs_news.json", "blogs_news.json"),
        ("industry_leaders.json", "industry_leaders.json"),
        ("last_updated.json", "last_updated.json"),
    ]
    for crawler_name, backend_name in pairs:
        cpath = os.path.join(crawler_data_dir, crawler_name)
        bpath = os.path.join(backend_data_dir, backend_name)
        if not os.path.exists(cpath) or not os.path.exists(bpath):
            continue
        try:
            if sha1_file(cpath) != sha1_file(bpath):
                issues.append(
                    Issue(
                        severity="WARN",
                        code="snapshot_mismatch",
                        message="backend snapshot differs from crawler data",
                        file=os.path.relpath(bpath, repo_root),
                        details={
                            "crawler": os.path.relpath(cpath, repo_root),
                            "backend": os.path.relpath(bpath, repo_root),
                        },
                    )
                )
        except Exception:
            continue

    # dark_horses directory sync check
    crawler_dh = os.path.join(crawler_data_dir, "dark_horses")
    backend_dh = os.path.join(backend_data_dir, "dark_horses")
    if os.path.isdir(crawler_dh) and os.path.isdir(backend_dh):
        crawler_files = {f for f in os.listdir(crawler_dh) if f.endswith(".json")}
        backend_files = {f for f in os.listdir(backend_dh) if f.endswith(".json")}

        for missing in sorted(crawler_files - backend_files):
            issues.append(
                Issue(
                    severity="WARN",
                    code="snapshot_missing",
                    message="backend snapshot missing dark_horses file",
                    file=os.path.relpath(os.path.join(backend_dh, missing), repo_root),
                    details={"expected_from": os.path.relpath(os.path.join(crawler_dh, missing), repo_root)},
                )
            )
        for extra in sorted(backend_files - crawler_files):
            issues.append(
                Issue(
                    severity="WARN",
                    code="snapshot_extra",
                    message="backend snapshot has extra dark_horses file",
                    file=os.path.relpath(os.path.join(backend_dh, extra), repo_root),
                )
            )

        for fname in sorted(crawler_files & backend_files):
            cpath = os.path.join(crawler_dh, fname)
            bpath = os.path.join(backend_dh, fname)
            try:
                if sha1_file(cpath) != sha1_file(bpath):
                    issues.append(
                        Issue(
                            severity="WARN",
                            code="snapshot_mismatch",
                            message="backend snapshot differs from crawler dark_horses file",
                            file=os.path.relpath(bpath, repo_root),
                            details={
                                "crawler": os.path.relpath(cpath, repo_root),
                                "backend": os.path.relpath(bpath, repo_root),
                            },
                        )
                    )
            except Exception:
                continue

    return issues
