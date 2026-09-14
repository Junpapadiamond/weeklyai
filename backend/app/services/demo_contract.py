"""Versioned data-only product experiences. The model cannot emit executable code."""
import hashlib
import json
import re
from urllib.parse import urlparse

VERSION = 2
WIDGETS = {"choice", "review", "dial", "compare", "app"}


def product_key(product):
    identity = str(product.get("website") or product.get("name", "")).lower().rstrip("/")
    return hashlib.sha256(identity.encode()).hexdigest()[:24]


def fingerprint(product):
    fields = {key: product.get(key) for key in ("name", "website", "description", "description_en", "why_matters", "source_url", "categories", "is_hardware")}
    return hashlib.sha256(json.dumps([VERSION, fields], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]


def cache_key(product):
    return f"{product_key(product)}-{fingerprint(product)}"


def safe_url(value):
    try:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and bool(parsed.hostname) and not parsed.username and not parsed.password
    except (ValueError, TypeError):
        return False


def _text(value, maximum=400):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum:
        raise ValueError("Invalid text")
    return value.strip()


def _copy(value, maximum=400):
    if not isinstance(value, dict):
        raise ValueError("Bilingual copy required")
    return {locale: _text(value.get(locale), maximum) for locale in ("zh", "en")}


def validate_experience(value, allowed_sources=None):
    if not isinstance(value, dict) or value.get("version") != VERSION or value.get("confidence") != "illustrative":
        raise ValueError("Invalid experience version or confidence")
    if value.get("tier") not in ("workflow", "concept"):
        raise ValueError("Unsupported experience tier")
    steps = value.get("steps")
    if not isinstance(steps, list) or not 3 <= len(steps) <= 6:
        raise ValueError("An experience needs 3–6 steps")
    validated = []
    seen = set()
    for step in steps:
        if not isinstance(step, dict) or step.get("widget") not in WIDGETS:
            raise ValueError("Unsupported widget")
        step_id = _text(step.get("id"), 40)
        if step_id in seen or not step_id.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Step identifiers must be unique")
        seen.add(step_id)
        options = step.get("options")
        if not isinstance(options, list) or not 1 <= len(options) <= 4:
            raise ValueError("Each step needs 1–4 interactive outcomes")
        choices = []
        for index, option in enumerate(options):
            if not isinstance(option, dict):
                raise ValueError("Invalid option")
            output = _copy(option.get("output"), 700)
            if any(re.search(r"\d+(?:\.\d+)?\s*[%％]|已导出|Exported:", text, re.I) for text in output.values()):
                raise ValueError("Unsupported measured or executed outcome")
            choices.append({"id": str(index), "label": _copy(option.get("label"), 80), "output": output})
        item = {"id": step_id, "widget": step["widget"], "title": _copy(step.get("title"), 80),
                "instruction": _copy(step.get("instruction"), 300), "options": choices,
                "example_data": True}
        if step["widget"] == "dial":
            dial = step.get("dial")
            if not isinstance(dial, dict) or any(type(dial.get(key)) is not int for key in ("min", "max", "initial", "factor")):
                raise ValueError("Invalid scenario dial")
            if not 0 <= dial["min"] < dial["max"] <= 1000 or not dial["min"] <= dial["initial"] <= dial["max"] or not 1 <= dial["factor"] <= 100:
                raise ValueError("Unbounded scenario dial")
            item["dial"] = {key: dial[key] for key in ("min", "max", "initial", "factor")}
            item["dial"]["unit"] = _copy(dial.get("unit"), 40)
            item["dial"]["result_label"] = _copy(dial.get("result_label"), 80)
        if step["widget"] == "app":
            if step.get("app_kind") not in ("tasks", "timer", "expenses"):
                raise ValueError("Invalid app preview")
            item["app_kind"] = step["app_kind"]
        validated.append(item)
    sources = value.get("sources")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 6:
        raise ValueError("Evidence is required")
    links = []
    for source in sources:
        if not isinstance(source, dict) or not safe_url(source.get("url")):
            raise ValueError("Invalid source")
        url = source["url"]
        if allowed_sources is not None and url not in allowed_sources:
            raise ValueError("The model cannot invent sources")
        links.append({"url": url, "label": _copy(source.get("label"), 100)})
    return {"version": VERSION, "confidence": "illustrative", "tier": value["tier"],
            "headline": _copy(value.get("headline"), 120), "scenario": _copy(value.get("scenario"), 400),
            "steps": validated, "takeaway": _copy(value.get("takeaway"), 500), "sources": links}
