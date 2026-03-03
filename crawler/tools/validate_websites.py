#!/usr/bin/env python3
"""
Validate and repair product websites.

Strategy:
  1) Validate auto-resolved websites by name/domain consistency.
  2) Probe selected websites for reachability and parked-domain pages.
  3) Repair with strong-signal candidates (www variant / source_url extraction).
  4) Mark unresolved websites for manual verification.
"""

import argparse
import json
import os
import re
import sys
from urllib.parse import urlparse


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
FEATURED_FILE = os.path.join(DATA_DIR, "products_featured.json")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    import requests  # type: ignore
    import urllib3  # type: ignore

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    requests = None  # type: ignore

try:
    from utils.website_resolver import extract_official_website_from_source
except Exception:
    extract_official_website_from_source = None  # type: ignore

AUTO_SOURCES = {"source_url", "weekly_match"}
UNKNOWN_VALUES = {"unknown", "n/a", "na", "none", "null", "undefined", ""}
LOW_CONF_LOGO_SOURCES = {"bing", "google_favicon", "duckduckgo", "icon_horse", "clearbit"}
LOW_CONF_LOGO_HOST_MARKERS = ("favicon.bing.com", "google.com/s2/favicons", "icons.duckduckgo.com", "icon.horse", "logo.clearbit.com")
FOR_SALE_PATTERNS = (
    "domain for sale",
    "for sale on",
    "buy this domain",
    "this domain is for sale",
    "sedo",
    "afternic",
    "dan.com",
    "hugedomains",
    "undeveloped",
)
CHECK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WeeklyAI Bot)",
    "Accept-Language": "en-US,en;q=0.9",
}


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _normalize_website(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.lower() in UNKNOWN_VALUES:
        return ""
    if not re.match(r"^https?://", raw, flags=re.IGNORECASE):
        if "." not in raw:
            return ""
        raw = f"https://{raw}"
    return raw


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(_normalize_website(url))
        domain = (parsed.netloc or "").lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if ":" in domain:
            domain = domain.split(":", 1)[0]
        return domain
    except Exception:
        return ""


def _name_tokens(name: str):
    raw = str(name or "").strip().lower()
    if not raw:
        return []

    tokens = re.findall(r"[a-z0-9]{3,}", raw)
    normalized = _normalize_name(raw)
    if len(normalized) >= 4:
        tokens.append(normalized)
    deduped = []
    seen = set()
    for token in tokens:
        if token not in seen:
            seen.add(token)
            deduped.append(token)
    return deduped


def _should_validate(item: dict) -> bool:
    source = (item.get("website_source") or "").strip().lower()
    return source in AUTO_SOURCES


def _domain_matches_name(domain: str, tokens) -> bool:
    if not domain:
        return False
    if not tokens:
        return True
    return any(token in domain for token in tokens)


def _is_low_confidence_logo(item: dict) -> bool:
    source = str(item.get("logo_source") or "").strip().lower()
    if source in LOW_CONF_LOGO_SOURCES:
        return True
    logo_url = str(item.get("logo_url") or item.get("logo") or "").strip().lower()
    if not logo_url:
        return True
    return any(marker in logo_url for marker in LOW_CONF_LOGO_HOST_MARKERS)


def _should_probe(item: dict, scope: str) -> bool:
    if scope == "all":
        return True
    if scope == "auto":
        return _should_validate(item) or bool(item.get("needs_verification"))
    # scope == "provider"
    if _should_validate(item) or bool(item.get("needs_verification")):
        return True
    return _is_low_confidence_logo(item)


def _is_for_sale_html(html: str) -> bool:
    if not html:
        return False
    lowered = html.lower()
    return any(pattern in lowered for pattern in FOR_SALE_PATTERNS)


def _probe_url(url: str, timeout: int = 6):
    """Return (ok, final_url, reason, html_snippet)."""
    if not requests:
        return False, "", "requests_missing", ""
    target = _normalize_website(url)
    if not target:
        return False, "", "invalid_url", ""

    try:
        resp = requests.get(
            target,
            timeout=timeout,
            allow_redirects=True,
            headers=CHECK_HEADERS,
            verify=False,
        )
    except Exception as e:
        return False, "", f"error:{type(e).__name__}", ""

    final_url = str(resp.url or target).strip()
    status = int(resp.status_code or 0)
    content_type = str(resp.headers.get("Content-Type") or "").lower()
    html = ""
    if "text/html" in content_type or "application/xhtml" in content_type:
        try:
            html = (resp.text or "")[:16000]
        except Exception:
            html = ""

    if 200 <= status < 400:
        return True, final_url, f"status:{status}", html
    return False, final_url, f"status:{status}", html


def _website_variants(url: str):
    variants = []
    normalized = _normalize_website(url)
    if not normalized:
        return variants

    try:
        parsed = urlparse(normalized)
    except Exception:
        return variants

    scheme = "https"
    host = (parsed.netloc or "").strip()
    if not host:
        return variants

    path = parsed.path or ""
    if parsed.query:
        path = f"{path}?{parsed.query}"

    hosts = [host]
    if host.startswith("www."):
        hosts.append(host[4:])
    else:
        hosts.append(f"www.{host}")

    seen = set()
    for candidate_host in hosts:
        candidate = f"{scheme}://{candidate_host}{path}"
        if candidate in seen:
            continue
        seen.add(candidate)
        variants.append(candidate)
    return variants


def _resolve_from_source(item: dict, aggressive: bool = False) -> str:
    if not extract_official_website_from_source:
        return ""
    source_url = str(item.get("source_url") or "").strip()
    name = str(item.get("name") or "").strip()
    if not source_url or not name:
        return ""
    try:
        resolved = extract_official_website_from_source(source_url, name, aggressive=aggressive)
    except Exception:
        return ""
    return _normalize_website(resolved)


def _clear_logo(item: dict) -> None:
    if item.get("logo_url"):
        item["logo_url"] = ""
    if item.get("logo_source"):
        item["logo_source"] = ""


def _apply_website(item: dict, website: str, source: str) -> None:
    item["website"] = website
    if source:
        item["website_source"] = source
    if item.get("needs_verification"):
        item["needs_verification"] = False


def _mark_unknown(item: dict) -> None:
    item["website"] = "unknown"
    item["needs_verification"] = True
    item["website_source"] = ""
    _clear_logo(item)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and repair websites")
    parser.add_argument("--input", default=FEATURED_FILE, help="Input JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    parser.add_argument(
        "--scope",
        choices=["auto", "provider", "all"],
        default="provider",
        help="Which items to probe by network (default: provider)",
    )
    parser.add_argument("--timeout", type=int, default=6, help="Network timeout seconds")
    parser.add_argument("--aggressive", action="store_true", help="Use aggressive source_url resolution")
    parser.add_argument(
        "--keep-for-sale",
        action="store_true",
        help="Keep parked domain URLs instead of forcing website='unknown'",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Missing {args.input}")
        return 1

    with open(args.input, "r", encoding="utf-8") as f:
        products = json.load(f)

    changed = 0
    mismatch_fixed = 0
    mismatch_unknown = 0
    repaired_variant = 0
    repaired_source = 0
    parked_unknown = 0
    flagged_unreachable = 0
    probed = 0

    for item in products:
        if not isinstance(item, dict):
            continue
        original_state = json.dumps(item, ensure_ascii=False, sort_keys=True)

        website = _normalize_website(item.get("website") or "")
        if website:
            item["website"] = website
        else:
            continue

        name = str(item.get("name") or "").strip()
        tokens = _name_tokens(name)
        domain = _extract_domain(website)

        # 1) Name-domain consistency check for auto-resolved URLs.
        if _should_validate(item) and tokens and not _domain_matches_name(domain, tokens):
            replacement = _resolve_from_source(item, aggressive=args.aggressive)
            if replacement and _domain_matches_name(_extract_domain(replacement), tokens):
                _apply_website(item, replacement, "source_url")
                _clear_logo(item)
                mismatch_fixed += 1
            else:
                _mark_unknown(item)
                mismatch_unknown += 1

        website = _normalize_website(item.get("website") or "")
        if not website:
            if json.dumps(item, ensure_ascii=False, sort_keys=True) != original_state:
                changed += 1
            continue

        # 2) Optional reachability + parked-domain repair.
        if _should_probe(item, args.scope):
            probed += 1
            ok, final_url, reason, html = _probe_url(website, timeout=max(2, args.timeout))
            is_for_sale = _is_for_sale_html(html)
            normalized_final = _normalize_website(final_url) or website

            if ok and not is_for_sale:
                if normalized_final != website:
                    _apply_website(item, normalized_final, "redirect")
            else:
                repaired = False

                for candidate in _website_variants(website):
                    ok2, final2, _reason2, html2 = _probe_url(candidate, timeout=max(2, args.timeout))
                    if not ok2:
                        continue
                    if _is_for_sale_html(html2):
                        continue
                    repaired_url = _normalize_website(final2) or _normalize_website(candidate)
                    if repaired_url:
                        _apply_website(item, repaired_url, "validated_variant")
                        _clear_logo(item)
                        repaired_variant += 1
                        repaired = True
                        break

                if not repaired:
                    replacement = _resolve_from_source(item, aggressive=args.aggressive)
                    if replacement:
                        ok3, final3, _reason3, html3 = _probe_url(replacement, timeout=max(2, args.timeout))
                        if ok3 and not _is_for_sale_html(html3):
                            repaired_url = _normalize_website(final3) or replacement
                            _apply_website(item, repaired_url, "source_url")
                            _clear_logo(item)
                            repaired_source += 1
                            repaired = True

                if not repaired:
                    item["needs_verification"] = True
                    if is_for_sale and not args.keep_for_sale:
                        _mark_unknown(item)
                        parked_unknown += 1
                    else:
                        flagged_unreachable += 1
                    if reason:
                        item["website_check_reason"] = reason

        if json.dumps(item, ensure_ascii=False, sort_keys=True) != original_state:
            changed += 1

    dry = "[DRY RUN] " if args.dry_run else ""
    print(f"{dry}Validated products: {len(products)} | changed: {changed} | probed: {probed}")
    print(
        f"{dry}mismatch_fixed={mismatch_fixed} mismatch_unknown={mismatch_unknown} "
        f"repaired_variant={repaired_variant} repaired_source={repaired_source} "
        f"parked_unknown={parked_unknown} flagged_unreachable={flagged_unreachable}"
    )
    if not args.dry_run and changed:
        with open(args.input, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"Saved {args.input}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
