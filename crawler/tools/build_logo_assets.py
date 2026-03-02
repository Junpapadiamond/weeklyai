#!/usr/bin/env python3
"""
Build stable logo assets for products_featured.json.

Pipeline:
1) Discover icon candidates from official website (apple-touch-icon/icon/shortcut icon)
2) Discover manifest icons
3) Fallback to /favicon.ico
4) Validate image payload + minimum dimensions
5) Convert to 256x256 PNG
6) Upload to object storage (S3-compatible) and write CDN URL back to product records

This tool upgrades logo_cache.json from legacy `domain -> string` into
`domain -> object` records and writes a coverage report.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    from PIL import Image, UnidentifiedImageError
except ImportError:  # pragma: no cover - runtime dependency guard
    Image = None
    UnidentifiedImageError = Exception

try:
    import boto3
except ImportError:  # pragma: no cover - runtime dependency guard
    boto3 = None

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "crawler" / "data"
DEFAULT_INPUT = DATA_DIR / "products_featured.json"
DEFAULT_CACHE = DATA_DIR / "logo_cache.json"
DEFAULT_REPORT = DATA_DIR / "logo_coverage_report.json"
BACKUP_PREFIX = "products_featured.pre_logo_migration"

ICON_REL_PRIORITY = (
    "apple-touch-icon",
    "icon",
    "shortcut icon",
)

VALID_LOGO_STATUS = {"ok", "missing", "failed"}
VALID_LOGO_SOURCE = {"site_icon", "apple_touch_icon", "manifest_icon", "favicon_ico", "manual"}


@dataclass
class Config:
    mode: str
    write: bool
    input_path: Path
    cache_path: Path
    report_path: Path
    backup_dir: Path
    min_ok_rate: float
    fetch_timeout: int
    recheck_days: int
    failure_retry_threshold: int
    failure_slow_retry_days: int
    storage_provider: str
    cdn_base_url: str
    s3_bucket: str
    s3_region: str
    s3_endpoint: str
    s3_access_key_id: str
    s3_secret_access_key: str
    user_agent: str


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def read_bool_env(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "")).strip().lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return default


def read_int_env(name: str, default: int, minimum: int = 0) -> int:
    raw = str(os.getenv(name, "")).strip()
    if not raw:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


def normalize_website(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    lowered = raw.lower()
    if lowered in {"", "unknown", "n/a", "na", "none", "null", "undefined", "tbd"}:
        return ""
    if not re.match(r"^https?://", raw, re.IGNORECASE):
        if "." not in raw:
            return ""
        raw = f"https://{raw}"
    try:
        parsed = urlparse(raw)
    except Exception:
        return ""
    host = (parsed.netloc or "").strip().lower()
    if not host or "." not in host:
        return ""
    return raw


def normalize_domain(website: str) -> str:
    if not website:
        return ""
    try:
        parsed = urlparse(website)
    except Exception:
        return ""
    host = (parsed.netloc or "").lower()
    host = re.sub(r"^www\.", "", host).split(":")[0]
    if not host or "." not in host:
        return ""
    return host


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, payload: Any) -> None:
    ensure_parent_dir(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_cache_record(domain: str, value: Any) -> Dict[str, Any]:
    del domain  # reserved for future domain-level cache validation

    def _as_non_negative_int(raw: Any) -> int:
        try:
            value_int = int(raw or 0)
        except (TypeError, ValueError):
            return 0
        return max(0, value_int)

    if isinstance(value, dict):
        record = {
            "cdn_url": str(value.get("cdn_url") or "").strip(),
            "hash": str(value.get("hash") or "").strip(),
            "status": str(value.get("status") or "").strip().lower() or "missing",
            "checked_at": str(value.get("checked_at") or "").strip(),
            "fail_count": _as_non_negative_int(value.get("fail_count")),
            "last_error": str(value.get("last_error") or "").strip(),
            "source": str(value.get("source") or "").strip(),
            "object_key": str(value.get("object_key") or "").strip(),
        }
    else:
        url = str(value or "").strip()
        status = "ok" if url else "missing"
        record = {
            "cdn_url": url,
            "hash": "",
            "status": status,
            "checked_at": "",
            "fail_count": 0,
            "last_error": "",
            "source": "manual" if status == "ok" else "",
            "object_key": "",
        }

    if record["status"] not in VALID_LOGO_STATUS:
        record["status"] = "missing"
    if record["source"] and record["source"] not in VALID_LOGO_SOURCE:
        record["source"] = "manual"
    return record


def load_logo_cache(cache_path: Path) -> Dict[str, Dict[str, Any]]:
    raw = load_json(cache_path, {})
    cache: Dict[str, Dict[str, Any]] = {}
    if not isinstance(raw, dict):
        return cache

    for key, value in raw.items():
        domain = normalize_domain(normalize_website(key) or key)
        if not domain:
            continue
        cache[domain] = normalize_cache_record(domain, value)
    return cache


def should_retry(record: Dict[str, Any], cfg: Config) -> bool:
    status = str(record.get("status") or "").strip().lower()
    checked_at = parse_iso_datetime(str(record.get("checked_at") or ""))
    fail_count = int(record.get("fail_count") or 0)
    now = datetime.now(timezone.utc)

    if cfg.mode == "backfill":
        return True

    if status == "ok":
        if not checked_at:
            return True
        return now - checked_at >= timedelta(days=cfg.recheck_days)

    if status in {"missing", "failed"}:
        if not checked_at:
            return True
        if fail_count >= cfg.failure_retry_threshold:
            return now - checked_at >= timedelta(days=cfg.failure_slow_retry_days)
        return now - checked_at >= timedelta(days=1)

    return True


def discover_homepage_html(session: requests.Session, website: str, timeout: int, user_agent: str) -> str:
    headers = {"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml"}
    try:
        response = session.get(website, headers=headers, timeout=timeout, allow_redirects=True)
    except Exception:
        return ""
    if not (200 <= response.status_code < 400):
        return ""
    content_type = str(response.headers.get("content-type") or "").lower()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        return ""
    return response.text or ""


def icon_rel_priority(rel_tokens: Iterable[str]) -> int:
    text = " ".join(token.strip().lower() for token in rel_tokens if token)
    for idx, marker in enumerate(ICON_REL_PRIORITY):
        if marker in text:
            return idx
    return len(ICON_REL_PRIORITY)


def extract_icon_candidates(html: str, website: str) -> List[Tuple[str, str]]:
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = []

    icon_tags = soup.find_all("link", href=True)
    icon_candidates: List[Tuple[int, str, str]] = []
    manifest_url = ""

    for tag in icon_tags:
        rel_tokens = [str(item).strip().lower() for item in tag.get("rel", [])]
        rel_text = " ".join(rel_tokens)
        href = str(tag.get("href") or "").strip()
        if not href:
            continue

        if "manifest" in rel_text and not manifest_url:
            manifest_url = urljoin(website, href)

        if "icon" not in rel_text:
            continue

        icon_type = "site_icon"
        if "apple-touch-icon" in rel_text:
            icon_type = "apple_touch_icon"

        priority = icon_rel_priority(rel_tokens)
        icon_candidates.append((priority, icon_type, urljoin(website, href)))

    icon_candidates.sort(key=lambda item: item[0])
    links.extend((icon_type, url) for _, icon_type, url in icon_candidates)

    if manifest_url:
        links.append(("manifest", manifest_url))

    return links


def extract_manifest_icons(session: requests.Session, manifest_url: str, timeout: int, user_agent: str) -> List[str]:
    headers = {"User-Agent": user_agent, "Accept": "application/manifest+json,application/json"}
    try:
        response = session.get(manifest_url, headers=headers, timeout=timeout, allow_redirects=True)
    except Exception:
        return []
    if not (200 <= response.status_code < 400):
        return []

    try:
        payload = response.json()
    except Exception:
        return []

    if not isinstance(payload, dict):
        return []

    icons = payload.get("icons")
    if not isinstance(icons, list):
        return []

    result = []
    for icon in icons:
        if not isinstance(icon, dict):
            continue
        src = str(icon.get("src") or "").strip()
        if not src:
            continue
        result.append(urljoin(manifest_url, src))
    return result


def fetch_image_bytes(session: requests.Session, url: str, timeout: int, user_agent: str) -> Tuple[bytes, str]:
    headers = {"User-Agent": user_agent, "Accept": "image/*,*/*;q=0.8"}
    response = session.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
    response.raise_for_status()
    content_type = str(response.headers.get("content-type") or "").lower()
    if "image" not in content_type and "octet-stream" not in content_type and "svg" not in content_type:
        raise ValueError(f"invalid_content_type:{content_type or 'unknown'}")
    data = response.content
    if not data:
        raise ValueError("empty_payload")
    return data, content_type


def convert_to_png_256(payload: bytes, content_type: str) -> bytes:
    if Image is None:  # pragma: no cover - runtime dependency guard
        raise RuntimeError("Pillow is required for logo conversion")

    try:
        with Image.open(io.BytesIO(payload)) as img:
            img.load()
            width, height = img.size
            if width < 32 or height < 32:
                raise ValueError(f"image_too_small:{width}x{height}")

            image = img.convert("RGBA")
            image.thumbnail((256, 256), Image.Resampling.LANCZOS)

            canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            offset = ((256 - image.width) // 2, (256 - image.height) // 2)
            canvas.paste(image, offset, image)

            out = io.BytesIO()
            canvas.save(out, format="PNG", optimize=True)
            return out.getvalue()
    except UnidentifiedImageError as exc:
        raise ValueError("unidentified_image") from exc


def object_key_for(domain: str, payload: bytes) -> Tuple[str, str]:
    digest = hashlib.sha1(payload).hexdigest()
    return f"logos/products/{domain}/{digest}.png", digest


class S3Uploader:
    def __init__(self, cfg: Config) -> None:
        if boto3 is None:  # pragma: no cover - runtime dependency guard
            raise RuntimeError("boto3 is required for S3 logo upload")
        if not cfg.s3_bucket:
            raise RuntimeError("LOGO_S3_BUCKET is required when LOGO_STORAGE_PROVIDER=s3")

        client_kwargs: Dict[str, Any] = {
            "region_name": cfg.s3_region or None,
            "aws_access_key_id": cfg.s3_access_key_id or None,
            "aws_secret_access_key": cfg.s3_secret_access_key or None,
        }
        if cfg.s3_endpoint:
            client_kwargs["endpoint_url"] = cfg.s3_endpoint

        self._bucket = cfg.s3_bucket
        self._client = boto3.client("s3", **client_kwargs)

    def upload(self, object_key: str, payload: bytes) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=object_key,
            Body=payload,
            ContentType="image/png",
            CacheControl="public, max-age=31536000, immutable",
        )


class LocalUploader:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def upload(self, object_key: str, payload: bytes) -> None:
        target = self._base_dir / object_key
        ensure_parent_dir(target)
        target.write_bytes(payload)


def join_cdn_url(base: str, object_key: str) -> str:
    if not base:
        return f"/{object_key}"
    return f"{base.rstrip('/')}/{object_key.lstrip('/')}"


def mark_logo_metadata(
    product: Dict[str, Any],
    status: str,
    source: str,
    checked_at: str,
    error: str = "",
) -> None:
    product["logo_status"] = status
    product["logo_source"] = source if source in VALID_LOGO_SOURCE else ""
    product["logo_last_checked_at"] = checked_at
    if error:
        product["logo_error_reason"] = error
    else:
        product.pop("logo_error_reason", None)


def build_candidates(session: requests.Session, website: str, domain: str, cfg: Config) -> List[Tuple[str, str]]:
    html = discover_homepage_html(session, website, timeout=cfg.fetch_timeout, user_agent=cfg.user_agent)
    discovered = extract_icon_candidates(html, website)

    candidates: List[Tuple[str, str]] = []
    seen: set[str] = set()

    for icon_type, url in discovered:
        if not url or url in seen:
            continue
        if icon_type == "manifest":
            manifest_icons = extract_manifest_icons(session, url, timeout=cfg.fetch_timeout, user_agent=cfg.user_agent)
            for manifest_url in manifest_icons:
                if manifest_url and manifest_url not in seen:
                    candidates.append(("manifest_icon", manifest_url))
                    seen.add(manifest_url)
            continue

        candidates.append((icon_type, url))
        seen.add(url)

    fallback = f"https://{domain}/favicon.ico"
    if fallback not in seen:
        candidates.append(("favicon_ico", fallback))

    return candidates


def resolve_logo_asset(
    session: requests.Session,
    website: str,
    domain: str,
    cfg: Config,
) -> Tuple[Optional[bytes], str, str]:
    candidates = build_candidates(session, website, domain, cfg)
    if not candidates:
        return None, "", "no_candidate"

    errors = []
    for source, candidate in candidates:
        try:
            raw, content_type = fetch_image_bytes(session, candidate, timeout=cfg.fetch_timeout, user_agent=cfg.user_agent)
            png_payload = convert_to_png_256(raw, content_type)
            return png_payload, source, ""
        except Exception as exc:
            errors.append(f"{source}:{type(exc).__name__}")

    return None, "", errors[-1] if errors else "no_valid_icon"


def configure(args: argparse.Namespace) -> Config:
    storage_provider = str(os.getenv("LOGO_STORAGE_PROVIDER", "s3")).strip().lower() or "s3"
    cdn_base_url = str(os.getenv("LOGO_CDN_BASE_URL", "")).strip()

    try:
        min_ok_rate = float(os.getenv("LOGO_MIN_OK_RATE", "0.97") or "0.97")
    except ValueError:
        min_ok_rate = 0.97
    min_ok_rate = min(max(min_ok_rate, 0.0), 1.0)

    write = True
    if args.dry_run:
        write = False

    return Config(
        mode=args.mode,
        write=write,
        input_path=Path(args.input).resolve(),
        cache_path=Path(args.cache).resolve(),
        report_path=Path(args.report).resolve(),
        backup_dir=Path(args.backup_dir).resolve(),
        min_ok_rate=min_ok_rate,
        fetch_timeout=read_int_env("LOGO_FETCH_TIMEOUT", 8, minimum=1),
        recheck_days=read_int_env("LOGO_RECHECK_DAYS", 7, minimum=1),
        failure_retry_threshold=read_int_env("LOGO_FAILURE_RETRY_THRESHOLD", 3, minimum=1),
        failure_slow_retry_days=read_int_env("LOGO_FAILURE_SLOW_RETRY_DAYS", 7, minimum=1),
        storage_provider=storage_provider,
        cdn_base_url=cdn_base_url,
        s3_bucket=str(os.getenv("LOGO_S3_BUCKET", "")).strip(),
        s3_region=str(os.getenv("LOGO_S3_REGION", "")).strip(),
        s3_endpoint=str(os.getenv("LOGO_S3_ENDPOINT", "")).strip(),
        s3_access_key_id=str(os.getenv("LOGO_S3_ACCESS_KEY_ID", "")).strip(),
        s3_secret_access_key=str(os.getenv("LOGO_S3_SECRET_ACCESS_KEY", "")).strip(),
        user_agent=str(
            os.getenv(
                "LOGO_FETCH_USER_AGENT",
                "Mozilla/5.0 (compatible; WeeklyAI-LogoBot/1.0; +https://weeklyai.example)",
            )
        ).strip(),
    )


def uploader_for(cfg: Config):
    if cfg.storage_provider == "s3":
        return S3Uploader(cfg)
    if cfg.storage_provider == "local":
        local_dir = DATA_DIR / "logos"
        return LocalUploader(local_dir)
    raise RuntimeError(f"Unsupported LOGO_STORAGE_PROVIDER: {cfg.storage_provider}")


def ensure_logo_fields(product: Dict[str, Any], checked_at: str) -> None:
    if str(product.get("logo_status") or "").strip().lower() not in VALID_LOGO_STATUS:
        product["logo_status"] = "missing"
    if str(product.get("logo_source") or "").strip() not in VALID_LOGO_SOURCE:
        product["logo_source"] = ""
    if not str(product.get("logo_last_checked_at") or "").strip():
        product["logo_last_checked_at"] = checked_at


def backup_input_file(cfg: Config) -> Optional[Path]:
    if not cfg.write:
        return None
    cfg.backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = cfg.backup_dir / f"{BACKUP_PREFIX}.{stamp}.json"
    backup_path.write_bytes(cfg.input_path.read_bytes())
    return backup_path


def run(cfg: Config) -> int:
    if Image is None:
        print("ERROR: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
        return 2

    products = load_json(cfg.input_path, [])
    if not isinstance(products, list):
        print(f"ERROR: invalid products file: {cfg.input_path}", file=sys.stderr)
        return 2

    cache = load_logo_cache(cfg.cache_path)
    uploader = uploader_for(cfg)
    checked_at = now_utc_iso()

    backup_path = backup_input_file(cfg)
    if backup_path:
        print(f"backup_created={backup_path}")

    metrics = {
        "total": len(products),
        "processed": 0,
        "skipped_cached": 0,
        "new_failures": 0,
        "recovered": 0,
        "logo_ok": 0,
        "logo_missing": 0,
        "logo_failed": 0,
    }
    failures: List[Dict[str, str]] = []

    session = requests.Session()

    for product in products:
        if not isinstance(product, dict):
            continue

        website = normalize_website(product.get("website"))
        domain = normalize_domain(website)
        if not domain:
            mark_logo_metadata(product, status="missing", source="", checked_at=checked_at, error="invalid_website")
            product["logo_url"] = ""
            metrics["logo_missing"] += 1
            continue

        existing = cache.get(domain, normalize_cache_record(domain, {}))
        if not should_retry(existing, cfg):
            metrics["skipped_cached"] += 1
            cached_url = str(existing.get("cdn_url") or "").strip()
            cached_status = str(existing.get("status") or "missing")
            cached_source = str(existing.get("source") or "")
            if cached_url and cached_status == "ok":
                product["logo_url"] = cached_url
            elif cached_status != "ok":
                product["logo_url"] = ""
            mark_logo_metadata(
                product,
                status=cached_status if cached_status in VALID_LOGO_STATUS else "missing",
                source=cached_source,
                checked_at=str(existing.get("checked_at") or checked_at),
                error=str(existing.get("last_error") or ""),
            )
            if cached_status == "ok":
                metrics["logo_ok"] += 1
            elif cached_status == "failed":
                metrics["logo_failed"] += 1
            else:
                metrics["logo_missing"] += 1
            continue

        metrics["processed"] += 1

        payload, source, error = resolve_logo_asset(session, website=website, domain=domain, cfg=cfg)
        if payload is None:
            previous_status = str(existing.get("status") or "")
            fail_count = int(existing.get("fail_count") or 0) + 1
            cache[domain] = {
                **existing,
                "cdn_url": "",
                "status": "failed",
                "checked_at": checked_at,
                "fail_count": fail_count,
                "last_error": error or "logo_resolution_failed",
                "source": "",
                "object_key": "",
            }
            product["logo_url"] = ""
            mark_logo_metadata(
                product,
                status="failed",
                source="",
                checked_at=checked_at,
                error=error or "logo_resolution_failed",
            )
            if previous_status == "ok":
                metrics["new_failures"] += 1
            metrics["logo_failed"] += 1
            failures.append(
                {
                    "name": str(product.get("name") or ""),
                    "website": website,
                    "reason": error or "logo_resolution_failed",
                }
            )
            continue

        object_key, digest = object_key_for(domain, payload)
        try:
            uploader.upload(object_key=object_key, payload=payload)
        except Exception as exc:
            fail_count = int(existing.get("fail_count") or 0) + 1
            cache[domain] = {
                **existing,
                "cdn_url": "",
                "status": "failed",
                "checked_at": checked_at,
                "fail_count": fail_count,
                "last_error": f"upload_failed:{type(exc).__name__}",
                "source": "",
                "object_key": "",
            }
            product["logo_url"] = ""
            mark_logo_metadata(
                product,
                status="failed",
                source="",
                checked_at=checked_at,
                error=f"upload_failed:{type(exc).__name__}",
            )
            metrics["logo_failed"] += 1
            failures.append(
                {
                    "name": str(product.get("name") or ""),
                    "website": website,
                    "reason": f"upload_failed:{type(exc).__name__}",
                }
            )
            continue

        cdn_url = join_cdn_url(cfg.cdn_base_url, object_key)
        previous_status = str(existing.get("status") or "")
        cache[domain] = {
            "cdn_url": cdn_url,
            "hash": digest,
            "status": "ok",
            "checked_at": checked_at,
            "fail_count": 0,
            "last_error": "",
            "source": source if source in VALID_LOGO_SOURCE else "site_icon",
            "object_key": object_key,
        }
        product["logo_url"] = cdn_url
        mark_logo_metadata(
            product,
            status="ok",
            source=source,
            checked_at=checked_at,
            error="",
        )
        if previous_status in {"failed", "missing"}:
            metrics["recovered"] += 1
        metrics["logo_ok"] += 1

    session.close()

    # Keep fields present for records that were not touched by branch logic above.
    for product in products:
        if isinstance(product, dict):
            ensure_logo_fields(product, checked_at=checked_at)

    covered = metrics["logo_ok"] + metrics["logo_missing"] + metrics["logo_failed"]
    if covered < metrics["total"]:
        metrics["logo_missing"] += metrics["total"] - covered

    ok_rate = (metrics["logo_ok"] / metrics["total"]) if metrics["total"] else 0.0
    report = {
        "generated_at": checked_at,
        "mode": cfg.mode,
        "storage_provider": cfg.storage_provider,
        "cdn_base_url": cfg.cdn_base_url,
        "threshold_ok_rate": cfg.min_ok_rate,
        "ok_rate": round(ok_rate, 6),
        "metrics": metrics,
        "failures": failures,
    }

    print(f"logo_total={metrics['total']}")
    print(f"logo_ok={metrics['logo_ok']}")
    print(f"logo_missing={metrics['logo_missing']}")
    print(f"logo_failed={metrics['logo_failed']}")
    print(f"ok_rate={ok_rate:.4f}")
    print(f"new_failures={metrics['new_failures']}")
    print(f"recovered={metrics['recovered']}")

    if cfg.write:
        save_json(cfg.input_path, products)
        save_json(cfg.cache_path, cache)
        save_json(cfg.report_path, report)
        print(f"products_saved={cfg.input_path}")
        print(f"cache_saved={cfg.cache_path}")
        print(f"report_saved={cfg.report_path}")
    else:
        print("dry_run=true")

    if ok_rate < cfg.min_ok_rate:
        print(
            f"WARNING: ok_rate below threshold ({ok_rate:.2%} < {cfg.min_ok_rate:.2%})",
            file=sys.stderr,
        )

    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build stable logo assets and update product logo_url fields")
    parser.add_argument("--mode", choices=["incremental", "backfill"], default="incremental")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--cache", default=str(DEFAULT_CACHE))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--backup-dir", default=str(DATA_DIR))
    parser.add_argument("--write", action="store_true", help="Compatibility flag; writes are enabled by default")
    parser.add_argument("--dry-run", action="store_true", help="Do not persist products/cache/report")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    cfg = configure(args)
    return run(cfg)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
