"""DemoSpec schema and validation.

A demo is data, never code. The model fills this structure; a hand-written
renderer draws it. Three invariants live here rather than in review, because a
review checklist erodes and a validator does not:

1. No unsourced numbers      - every Datum cites evidence or is flagged example.
2. No simulation claiming verification - tier=simulation forces illustrative.
3. No model-supplied URLs reaching the server - live widgets carry an
   endpoint_id resolved against ENDPOINT_REGISTRY, never a URL.

Every prose field is a {zh, en} pair. Literal values a reader copies - a search
query, a product or competitor name - stay plain strings, because translating
them would make them wrong.

Mirrored in frontend-next/src/lib/demo-schema.ts. Keep the two in step.
"""
from __future__ import annotations

import os
import re
from typing import Any

SPEC_VERSION = 1

TIERS = ("sandbox", "simulation", "concept", "tour")
CONFIDENCES = ("verified", "inferred", "illustrative")
VENDOR_STATUSES = ("none", "contacted", "corrected", "key_supplied")
WIDGET_TYPES = (
    "query_response",
    "split_compare",
    "pipeline",
    "spec_matrix",
    "scenario_branch",
    "hotspot_shot",
    "param_dial",
    "transcript",
)

MIN_STEPS, MAX_STEPS = 3, 5

# Live sandbox endpoints, resolved server-side. A spec names a key here; it can
# never name a URL. Populate from env so keys never enter the repository, and so
# an unconfigured deployment simply has no live tier rather than a broken one.
#   DEMO_ENDPOINT_<ID>=<url>|<env var holding the key>
ENDPOINT_REGISTRY: dict[str, dict[str, str]] = {}


def _load_endpoint_registry() -> dict[str, dict[str, str]]:
    """Read approved live endpoints from the environment."""
    registry: dict[str, dict[str, str]] = {}
    for name, value in os.environ.items():
        if not name.startswith("DEMO_ENDPOINT_") or "|" not in value:
            continue
        url, _, key_var = value.partition("|")
        url, key_var = url.strip(), key_var.strip()
        if not url.startswith("https://") or not key_var:
            continue
        registry[name[len("DEMO_ENDPOINT_"):].lower()] = {"url": url, "key_var": key_var}
    return registry


ENDPOINT_REGISTRY.update(_load_endpoint_registry())

_URLISH = re.compile(r"https?://", re.I)


class SpecError(ValueError):
    """Raised with the field path that failed, so a retry can be targeted."""


def _require(condition: bool, path: str, message: str) -> None:
    if not condition:
        raise SpecError(f"{path}: {message}")


def _loc(value: Any, path: str) -> dict[str, str]:
    """A localized string pair. Both locales are required - a demo that renders
    an empty panel in one language is worse than one that fails validation."""
    _require(isinstance(value, dict), path, "must be an object with zh and en")
    out = {}
    for locale in ("zh", "en"):
        text = value.get(locale)
        _require(isinstance(text, str) and text.strip(), f"{path}.{locale}", "required non-empty string")
        out[locale] = text.strip()
    return out


def _text(value: Any, path: str, *, max_len: int = 4000) -> str:
    _require(isinstance(value, str) and value.strip(), path, "required non-empty string")
    _require(len(value) <= max_len, path, f"exceeds {max_len} characters")
    return value.strip()


def _seq(value: Any, path: str, lo: int, hi: int) -> list:
    _require(isinstance(value, list), path, "must be a list")
    _require(lo <= len(value) <= hi, path, f"needs between {lo} and {hi} entries, got {len(value)}")
    return value


def _datum(value: Any, path: str, evidence_count: int) -> dict[str, Any]:
    """Invariant 1. A number the reader sees is sourced, or it is visibly an
    example. There is no third option."""
    _require(isinstance(value, dict), path, "must be an object")
    ref = value.get("evidence_ref")
    is_example = bool(value.get("is_example", False))
    if ref is not None:
        _require(isinstance(ref, int), f"{path}.evidence_ref", "must be an integer index")
        _require(0 <= ref < evidence_count, f"{path}.evidence_ref", f"out of range (evidence has {evidence_count})")
    _require(
        ref is not None or is_example,
        path,
        "every value must cite evidence_ref or set is_example - unsourced numbers are not publishable",
    )
    return {
        "label": _loc(value.get("label"), f"{path}.label"),
        # Prose like "rarely published" belongs in both locales; a figure like
        # "$250M" is simply the same string twice.
        "value": _loc(value.get("value"), f"{path}.value"),
        "evidence_ref": ref,
        "is_example": is_example,
    }


def _widget(value: Any, path: str, evidence_count: int) -> dict[str, Any]:
    _require(isinstance(value, dict), path, "must be an object")
    kind = value.get("type")
    _require(kind in WIDGET_TYPES, f"{path}.type", f"must be one of {', '.join(WIDGET_TYPES)}")
    out: dict[str, Any] = {"type": kind}

    if kind == "query_response":
        mode = value.get("mode")
        _require(mode in ("live", "cached"), f"{path}.mode", "must be live or cached")
        endpoint_id = value.get("endpoint_id")
        if mode == "live":
            # Invariant 3. A live widget names a registry key, never a URL.
            _require(isinstance(endpoint_id, str) and endpoint_id, f"{path}.endpoint_id", "live mode requires endpoint_id")
            _require(
                endpoint_id in ENDPOINT_REGISTRY,
                f"{path}.endpoint_id",
                f"'{endpoint_id}' is not a registered endpoint - live demos may only call approved endpoints",
            )
            _require(not _URLISH.search(endpoint_id), f"{path}.endpoint_id", "must be a registry id, not a URL")
        presets = _seq(value.get("presets"), f"{path}.presets", 1, 5)
        out["mode"] = mode
        out["endpoint_id"] = endpoint_id if mode == "live" else None
        out["allow_free_input"] = bool(value.get("allow_free_input", False))
        out["presets"] = [
            {
                "query": _text(p.get("query"), f"{path}.presets[{i}].query", max_len=300),
                # A cached preset must ship its answer; a live one fetches at runtime.
                "response": _loc(p.get("response"), f"{path}.presets[{i}].response")
                if mode == "cached" else {"zh": "", "en": ""},
            }
            for i, p in enumerate(presets)
        ]

    elif kind == "split_compare":
        out["input"] = _text(value.get("input"), f"{path}.input", max_len=300)
        for side in ("left", "right"):
            pane = value.get(side)
            _require(isinstance(pane, dict), f"{path}.{side}", "must be an object")
            out[side] = {
                "title": _loc(pane.get("title"), f"{path}.{side}.title"),
                "body": _loc(pane.get("body"), f"{path}.{side}.body"),
            }
        out["takeaway"] = _loc(value.get("takeaway"), f"{path}.takeaway")

    elif kind == "pipeline":
        stages = _seq(value.get("stages"), f"{path}.stages", 2, 6)
        out["stages"] = [
            {
                "name": _loc(s.get("name"), f"{path}.stages[{i}].name"),
                "input": _loc(s.get("input"), f"{path}.stages[{i}].input"),
                "output": _loc(s.get("output"), f"{path}.stages[{i}].output"),
            }
            for i, s in enumerate(stages)
        ]

    elif kind == "spec_matrix":
        competitors = _seq(value.get("competitors"), f"{path}.competitors", 1, 3)
        rows = _seq(value.get("rows"), f"{path}.rows", 3, 10)
        out["subject"] = _text(value.get("subject"), f"{path}.subject", max_len=120)
        out["competitors"] = [_text(c, f"{path}.competitors[{i}]", max_len=120) for i, c in enumerate(competitors)]
        out["rows"] = []
        for i, row in enumerate(rows):
            _require(isinstance(row, dict), f"{path}.rows[{i}]", "must be an object")
            values = row.get("values")
            _require(isinstance(values, list), f"{path}.rows[{i}].values", "must be a list")
            _require(
                len(values) == len(competitors) + 1,
                f"{path}.rows[{i}].values",
                f"needs one value for the subject plus each competitor ({len(competitors) + 1}), got {len(values)}",
            )
            out["rows"].append({
                "spec": _loc(row.get("spec"), f"{path}.rows[{i}].spec"),
                "values": [_datum(v, f"{path}.rows[{i}].values[{j}]", evidence_count) for j, v in enumerate(values)],
            })

    elif kind == "scenario_branch":
        branches = _seq(value.get("branches"), f"{path}.branches", 2, 4)
        out["branches"] = [
            {
                "persona": _loc(b.get("persona"), f"{path}.branches[{i}].persona"),
                "situation": _loc(b.get("situation"), f"{path}.branches[{i}].situation"),
                "outcome": _loc(b.get("outcome"), f"{path}.branches[{i}].outcome"),
            }
            for i, b in enumerate(branches)
        ]

    elif kind == "hotspot_shot":
        shot = _text(value.get("shot_url"), f"{path}.shot_url", max_len=600)
        _require(shot.startswith("https://"), f"{path}.shot_url", "must be an https URL")
        hotspots = _seq(value.get("hotspots"), f"{path}.hotspots", 2, 6)
        out["shot_url"] = shot
        out["hotspots"] = []
        for i, h in enumerate(hotspots):
            _require(isinstance(h, dict), f"{path}.hotspots[{i}]", "must be an object")
            coords = {}
            for axis in ("x", "y"):
                raw = h.get(axis)
                _require(isinstance(raw, (int, float)) and not isinstance(raw, bool),
                         f"{path}.hotspots[{i}].{axis}", "must be a number")
                _require(0 <= float(raw) <= 100, f"{path}.hotspots[{i}].{axis}", "must be a percentage 0-100")
                coords[axis] = float(raw)
            out["hotspots"].append({**coords, "note": _loc(h.get("note"), f"{path}.hotspots[{i}].note")})

    elif kind == "param_dial":
        for field in ("min", "max", "step"):
            raw = value.get(field)
            _require(isinstance(raw, (int, float)) and not isinstance(raw, bool), f"{path}.{field}", "must be a number")
        lo, hi, step = float(value["min"]), float(value["max"]), float(value["step"])
        _require(hi > lo, f"{path}.max", "must be greater than min")
        _require(step > 0 and step <= (hi - lo), f"{path}.step", "must be positive and fit within the range")
        outputs = _seq(value.get("outputs"), f"{path}.outputs", 1, 4)
        out.update({
            "param": _loc(value.get("param"), f"{path}.param"),
            "min": lo, "max": hi, "step": step,
            "unit": _text(value.get("unit"), f"{path}.unit", max_len=24),
            "formula_note": _loc(value.get("formula_note"), f"{path}.formula_note"),
            "outputs": [_datum(o, f"{path}.outputs[{i}]", evidence_count) for i, o in enumerate(outputs)],
        })

    elif kind == "transcript":
        turns = _seq(value.get("turns"), f"{path}.turns", 3, 12)
        out["turns"] = []
        for i, turn in enumerate(turns):
            _require(isinstance(turn, dict), f"{path}.turns[{i}]", "must be an object")
            speaker = turn.get("speaker")
            _require(speaker in ("user", "product"), f"{path}.turns[{i}].speaker", "must be user or product")
            out["turns"].append({"speaker": speaker, "text": _loc(turn.get("text"), f"{path}.turns[{i}].text")})

    return out


def validate_spec(raw: Any) -> dict[str, Any]:
    """Validate and normalize a DemoSpec. Raises SpecError naming the field."""
    _require(isinstance(raw, dict), "spec", "must be an object")
    _require(raw.get("version") == SPEC_VERSION, "version", f"must be {SPEC_VERSION}")

    tier = raw.get("tier")
    _require(tier in TIERS, "tier", f"must be one of {', '.join(TIERS)}")
    confidence = raw.get("confidence")
    _require(confidence in CONFIDENCES, "confidence", f"must be one of {', '.join(CONFIDENCES)}")

    # Invariant 2. A reconstruction can never present itself as verified.
    if tier == "simulation":
        _require(
            confidence == "illustrative",
            "confidence",
            "tier=simulation forces confidence=illustrative - a reconstruction cannot claim verification",
        )

    evidence_raw = raw.get("evidence") or []
    _require(isinstance(evidence_raw, list), "evidence", "must be a list")
    evidence = []
    for i, item in enumerate(evidence_raw):
        _require(isinstance(item, dict), f"evidence[{i}]", "must be an object")
        url = _text(item.get("source_url"), f"evidence[{i}].source_url", max_len=600)
        _require(url.startswith(("http://", "https://")), f"evidence[{i}].source_url", "must be an http(s) URL")
        evidence.append({"claim": _text(item.get("claim"), f"evidence[{i}].claim", max_len=400), "source_url": url})

    # A sandbox demo asserts real behavior, so it must show its sources.
    if tier == "sandbox":
        _require(evidence, "evidence", "a sandbox demo must cite at least one source")

    steps_raw = _seq(raw.get("steps"), "steps", MIN_STEPS, MAX_STEPS)
    seen_ids: set[str] = set()
    steps = []
    for i, step in enumerate(steps_raw):
        _require(isinstance(step, dict), f"steps[{i}]", "must be an object")
        step_id = _text(step.get("id"), f"steps[{i}].id", max_len=40)
        _require(step_id not in seen_ids, f"steps[{i}].id", f"duplicate step id '{step_id}'")
        seen_ids.add(step_id)
        steps.append({
            "id": step_id,
            "label": _loc(step.get("label"), f"steps[{i}].label"),
            "narration": _loc(step.get("narration"), f"steps[{i}].narration"),
            "widget": _widget(step.get("widget"), f"steps[{i}].widget", len(evidence)),
        })

    vendor_status = raw.get("vendor_status", "none")
    _require(vendor_status in VENDOR_STATUSES, "vendor_status", f"must be one of {', '.join(VENDOR_STATUSES)}")

    reviewed_by = raw.get("reviewed_by")
    _require(reviewed_by is None or isinstance(reviewed_by, str), "reviewed_by", "must be a string or null")

    return {
        "version": SPEC_VERSION,
        "product_slug": _text(raw.get("product_slug"), "product_slug", max_len=160),
        "product_name": _text(raw.get("product_name"), "product_name", max_len=160),
        "tier": tier,
        "title": _loc(raw.get("title"), "title"),
        "premise": _loc(raw.get("premise"), "premise"),
        "steps": steps,
        "evidence": evidence,
        "confidence": confidence,
        "vendor_status": vendor_status,
        "generated_at": str(raw.get("generated_at") or ""),
        "model": str(raw.get("model") or ""),
        "reviewed_by": reviewed_by,
    }


def resolve_endpoint(endpoint_id: str) -> dict[str, str] | None:
    """Look up an approved live endpoint. The only path from a spec to a URL."""
    entry = ENDPOINT_REGISTRY.get(endpoint_id)
    if not entry:
        return None
    key = os.environ.get(entry["key_var"], "").strip()
    if not key:
        return None
    return {"url": entry["url"], "key": key}
