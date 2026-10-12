"""Versioned data-only product experiences. The model cannot emit executable code."""
import hashlib
import json
import re
from urllib.parse import urlparse

VERSION = 2
WIDGETS = {"choice", "review", "dial", "compare", "app"}
WORKSPACES = {"video", "image", "search", "document", "board"}
ARTIFACTS = {"excerpt", "sequence", "comparison", "list", "text"}

# These checks reject known unsafe representations, not establish factual truth.
# The renderer must still label every artifact as fictional and not vendor output.
ARTIFACT_UNSAFE_COPY = re.compile(
    r"https?://|www\.|javascript:|data:|<\s*/?\s*[a-z][^>]*>"
    r"|\d+(?:\.\d+)?\s*[%％]"
    r"|\b(?:accuracy|precision|recall|latency|throughput|speedup|response time)\s*(?:[:=]|of|is)?\s*\d"
    r"|\b\d+(?:\.\d+)?\s*(?:ms|milliseconds|times faster)\b|Exported:"
    r"|\b(?:agent deployed|connected (?:to |the )?(?:vendor|account|SEC|data stream)|"
    r"interviews? (?:completed|conducted)|(?:completed|conducted) interviews?|"
    r"video (?:generated|rendered)|(?:file|image|video) (?:saved|exported)|"
    r"saved (?:locally|to (?:your |the )?(?:device|computer))|"
    r"contract delivered)\b"
    r"|已(?:部署|连接|开展访谈|完成访谈|导出|保存本地)|文件已保存|视频已生成",
    re.I,
)


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


def _artifact(value):
    """Bounded, plain-text examples; no URLs, media, markup or executable fields."""
    if not isinstance(value, dict) or not isinstance(value.get("kind"), str) or value["kind"] not in ARTIFACTS:
        raise ValueError("Unsupported artifact kind")
    result = {"kind": value["kind"]}
    for field, maximum in (("input_label", 40), ("output_label", 40), ("input", 220), ("output", 220)):
        result[field] = _copy(value.get(field), maximum)
    if "emphasis" in value:
        emphasis = _copy(value["emphasis"], 100)
        if any(emphasis[locale] not in result["input"][locale] for locale in ("zh", "en")):
            raise ValueError("Artifact emphasis must occur in its input in both languages")
        result["emphasis"] = emphasis
    if "items" in value:
        items = value["items"]
        if (value["kind"] not in {"sequence", "list"} or not isinstance(items, list)
                or not 2 <= len(items) <= 4 or any(not isinstance(item, dict) for item in items)):
            raise ValueError("Artifact items require a sequence or list with 2–4 items")
        result["items"] = [{"label": _copy(item.get("label"), 60), "detail": _copy(item.get("detail"), 160)}
                           for item in items]
    copies = [copy for field, copy in result.items() if field not in {"kind", "items"}]
    copies.extend(copy for item in result.get("items", []) for copy in item.values())
    if any(ARTIFACT_UNSAFE_COPY.search(text) for copy in copies for text in copy.values()):
        raise ValueError("Artifact text cannot contain URLs, markup, measured claims or completed vendor execution")
    return result


def validate_experience(value, allowed_sources=None):
    if not isinstance(value, dict) or value.get("version") != VERSION or value.get("confidence") != "illustrative":
        raise ValueError("Invalid experience version or confidence")
    if value.get("tier") not in ("workflow", "concept"):
        raise ValueError("Unsupported experience tier")
    steps = value.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 6:
        raise ValueError("An experience needs 1–6 example sections")
    validated = []
    seen = set()
    previous_options = {}
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
            if any(re.search(r"\d+(?:\.\d+)?\s*[%％]|已导出|已保存本地|文件已保存|视频已生成|Exported:|saved (?:locally|to (?:your |the )?(?:device|computer))", text, re.I) for text in output.values()):
                raise ValueError("Unsupported measured or executed outcome")
            choice = {"id": str(index), "label": _copy(option.get("label"), 80), "output": output}
            if "artifact" in option:
                choice["artifact"] = _artifact(option["artifact"])
            when = option.get("when")
            if when is not None:
                if (not isinstance(when, dict) or when.get("step_id") not in previous_options
                        or when.get("option_id") not in previous_options[when["step_id"]]):
                    raise ValueError("Option condition must reference an earlier choice")
                choice["when"] = {"step_id": when["step_id"], "option_id": when["option_id"]}
            choices.append(choice)
        conditional_steps = {o["when"]["step_id"] for o in choices if "when" in o}
        if len(conditional_steps) > 1 or (conditional_steps and all("when" in o for o in choices)
                and {o["when"]["option_id"] for o in choices} != previous_options[next(iter(conditional_steps))]):
            raise ValueError("Each earlier choice needs an available outcome")
        previous_options[step_id] = {o["id"] for o in choices}
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
    result = {"version": VERSION, "confidence": "illustrative", "tier": value["tier"],
            "headline": _copy(value.get("headline"), 120), "scenario": _copy(value.get("scenario"), 400),
            "steps": validated, "takeaway": _copy(value.get("takeaway"), 500), "sources": links}
    if "focus_step_id" in value:
        focus_step_id = _text(value["focus_step_id"], 40)
        if focus_step_id not in seen:
            raise ValueError("Focus step must reference an existing step")
        result["focus_step_id"] = focus_step_id
    context = value.get("product_context")
    if context is not None:
        if not isinstance(context, dict) or any(context.get(key) not in [s["url"] for s in links] for key in ("source_url", "trial_url")):
            raise ValueError("Product context links must be cited sources")
        result["product_context"] = {key: _copy(context.get(key), 300) for key in ("job", "input", "output", "trial_note")}
        result["product_context"].update(source_url=context["source_url"], trial_url=context["trial_url"])
    workspace = value.get("workspace")
    if workspace is not None:
        if not isinstance(workspace, dict) or workspace.get("kind") not in WORKSPACES:
            raise ValueError("Unsupported workspace")
        result["workspace"] = {"kind": workspace["kind"], "label": _copy(workspace.get("label"), 80),
                               "initial": _copy(workspace.get("initial"), 200)}
    return result
