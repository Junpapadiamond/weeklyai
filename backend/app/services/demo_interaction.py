"""Strict data-only interactions. No generated code is evaluated or invoked."""
import itertools
import math
import re
from decimal import Decimal


KINDS = {"editor", "records", "form", "review"}
LOCALES = ("zh", "en")
IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,40}\Z")
# These are source-code type constructors, not HTML. Keep the source unchanged;
# only mask the brackets for the legacy representation check on inert review text.
INERT_GENERIC = re.compile(
    r"\b(?:Array|ReadonlyArray|Promise|Record|Map|Set|Partial|Required|Pick|Omit|Readonly)"
    r"\s*<\s*[A-Za-z_$][\w.$]*(?:\s*\[\])?(?:\s*[,|]\s*[A-Za-z_$][\w.$]*(?:\s*\[\])?)*\s*>"
)
INERT_COMPARISON = re.compile(r"(?<=\s)<(?=\s)")


def _fail(path, reason):
    # Paths and constraints only: provider content must not leak into repair logs.
    raise ValueError(f"Invalid interaction at {path}: {reason}")


def _object(value, required, optional=(), path="interaction"):
    if not isinstance(value, dict):
        _fail(path, "expected an object")
    keys = set(value)
    if not set(required) <= keys or keys - set(required) - set(optional):
        _fail(path, "missing or unknown fields")
    return value


def _sequence(value, minimum, maximum, path):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        _fail(path, f"expected {minimum}-{maximum} entries")
    return value


def _id(value, path):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        _fail(path, "expected a 1-40 character identifier")
    return value


def _enum(value, allowed, path):
    if not isinstance(value, str) or value not in allowed:
        _fail(path, "unsupported value")
    return value


def _unique(values, path):
    if len(set(values)) != len(values):
        _fail(path, "duplicate identifiers")


def _copy(value, maximum, path, inert=False):
    _object(value, LOCALES, path=path)
    # Lazy import avoids a cycle when the envelope validator imports this module.
    from app.services.demo_contract import ARTIFACT_UNSAFE_COPY

    result = {}
    for locale in LOCALES:
        text = value[locale]
        if not isinstance(text, str) or not text.strip() or len(text) > maximum:
            _fail(f"{path}.{locale}", f"expected nonempty text up to {maximum} characters")
        checked = text
        if inert:
            checked = INERT_GENERIC.sub(lambda match: match[0].replace("<", "(").replace(">", ")"), checked)
            # Whitespace on BOTH sides denotes an inert less-than operator, not
            # an HTML opening tag. Keep comparisons such as x < y && y > 0.
            checked = INERT_COMPARISON.sub("less-than", checked)
        if ARTIFACT_UNSAFE_COPY.search(checked):
            _fail(f"{path}.{locale}", "URLs, HTML, measured claims and execution claims are unsupported")
        # Preserve code indentation, literal quotes and the user's future patch basis.
        result[locale] = text
    return result


def _options(value, maximum, path, allow_facts=False):
    result = []
    for index, option in enumerate(_sequence(value, 2, maximum, path)):
        at = f"{path}[{index}]"
        _object(option, ("id", "label"), ("facts",) if allow_facts else (), at)
        normalized = {"id": _id(option["id"], at + ".id"), "label": _copy(option["label"], 80, at + ".label")}
        if "facts" in option:
            normalized["facts"] = [_copy(fact, 120, f"{at}.facts[{fact_index}]")
                                   for fact_index, fact in enumerate(_sequence(option["facts"], 1, 5, at + ".facts"))]
        result.append(normalized)
    _unique([option["id"] for option in result], path)
    return result


def _editor(value, path):
    _object(value, ("fields",), path=path)
    fields = []
    for index, field in enumerate(_sequence(value["fields"], 2, 6, path + ".fields")):
        at = f"{path}.fields[{index}]"
        _object(field, ("id", "label", "value"), path=at)
        fields.append({"id": _id(field["id"], at + ".id"), "label": _copy(field["label"], 80, at + ".label"),
                       "value": _copy(field["value"], 1400, at + ".value")})
    _unique([field["id"] for field in fields], path + ".fields")
    return {"fields": fields}


def _number(value, path):
    if type(value) not in (int, float):
        _fail(path, "expected a finite number")
    try:
        finite = math.isfinite(value)
    except (OverflowError, ValueError):
        finite = False
    if not finite:
        _fail(path, "expected a finite number")
    return value


def _records(value, path):
    _object(value, ("columns", "rows", "view"), ("group_by", "calculation"), path)
    columns = []
    for index, column in enumerate(_sequence(value["columns"], 2, 5, path + ".columns")):
        at = f"{path}.columns[{index}]"
        _object(column, ("id", "label", "type"), ("unit", "options"), at)
        kind = _enum(column["type"], {"text", "number", "select"}, at + ".type")
        result = {"id": _id(column["id"], at + ".id"), "label": _copy(column["label"], 80, at + ".label"), "type": kind}
        if kind == "number":
            if "unit" not in column or "options" in column:
                _fail(at, "numeric columns require units and cannot have options")
            result["unit"] = _copy(column["unit"], 80, at + ".unit")
        elif kind == "select":
            if "options" not in column or "unit" in column:
                _fail(at, "select columns require options and cannot have units")
            result["options"] = _options(column["options"], 6, at + ".options")
        elif "unit" in column or "options" in column:
            _fail(at, "text columns cannot have units or options")
        columns.append(result)
    _unique([column["id"] for column in columns], path + ".columns")
    by_column = {column["id"]: column for column in columns}
    rows = []
    for index, row in enumerate(_sequence(value["rows"], 2, 6, path + ".rows")):
        at = f"{path}.rows[{index}]"
        _object(row, ("id", "cells"), ("evidence",), at)
        _object(row["cells"], by_column, path=at + ".cells")
        cells = {}
        for column in columns:
            key = column["id"]
            # Column IDs are validated, but avoid embedding model strings in paths.
            cell_path = at + ".cells"
            if column["type"] == "text":
                cells[key] = _copy(row["cells"][key], 1400, cell_path)
            elif column["type"] == "number":
                cells[key] = _number(row["cells"][key], cell_path)
            else:
                cells[key] = _enum(row["cells"][key], {option["id"] for option in column["options"]}, cell_path)
        result = {"id": _id(row["id"], at + ".id"), "cells": cells}
        if "evidence" in row:
            evidence = _object(row["evidence"], ("text", "quote"), path=at + ".evidence")
            result["evidence"] = {field: _copy(evidence[field], 1400, at + ".evidence." + field) for field in ("text", "quote")}
            if any(result["evidence"]["quote"][locale] not in result["evidence"]["text"][locale] for locale in LOCALES):
                _fail(at + ".evidence.quote", "quote must occur in evidence in both languages")
        rows.append(result)
    _unique([row["id"] for row in rows], path + ".rows")
    result = {"columns": columns, "rows": rows, "view": _enum(value["view"], {"table", "board"}, path + ".view")}
    if result["view"] == "board" and "group_by" not in value:
        _fail(path + ".group_by", "board requires a select grouping column")
    if "group_by" in value:
        grouping = _id(value["group_by"], path + ".group_by")
        if grouping not in by_column or by_column[grouping]["type"] != "select":
            _fail(path + ".group_by", "grouping must reference a select column")
        result["group_by"] = grouping
    if "calculation" in value:
        at = path + ".calculation"
        calculation = _object(value["calculation"], ("op", "label"), ("column", "left", "right"), at)
        operation = _enum(calculation["op"], {"sum", "difference", "count"}, at + ".op")
        required = ("op", "label") + (() if operation == "count" else ("column",)) + (("left", "right") if operation == "difference" else ())
        _object(calculation, required, path=at)
        normalized = {"op": operation, "label": _copy(calculation["label"], 80, at + ".label")}
        if operation != "count":
            column = _id(calculation["column"], at + ".column")
            if column not in by_column or by_column[column]["type"] != "number":
                _fail(at + ".column", "calculation requires a numeric column")
            normalized["column"] = column
        if operation == "difference":
            row_ids = {row["id"] for row in rows}
            for side in ("left", "right"):
                normalized[side] = _id(calculation[side], at + "." + side)
                if normalized[side] not in row_ids:
                    _fail(at + "." + side, "calculation row is unresolved")
            if normalized["left"] == normalized["right"]:
                _fail(at, "difference requires two distinct rows")
        result["calculation"] = normalized
    return result


def _form(value, path):
    _object(value, ("title", "fields", "submit_label", "confirmation"), path=path)
    fields = []
    for index, field in enumerate(_sequence(value["fields"], 2, 5, path + ".fields")):
        at = f"{path}.fields[{index}]"
        _object(field, ("id", "label", "type", "required"), path=at)
        if type(field["required"]) is not bool:
            _fail(at + ".required", "expected a boolean")
        fields.append({"id": _id(field["id"], at + ".id"), "label": _copy(field["label"], 80, at + ".label"),
                       "type": _enum(field["type"], {"text", "email", "number"}, at + ".type"), "required": field["required"]})
    _unique([field["id"] for field in fields], path + ".fields")
    return {"title": _copy(value["title"], 80, path + ".title"), "fields": fields,
            "submit_label": _copy(value["submit_label"], 80, path + ".submit_label"),
            "confirmation": _copy(value["confirmation"], 300, path + ".confirmation")}


def _review(value, path):
    _object(value, ("base", "patches"), path=path)
    base = _copy(value["base"], 1400, path + ".base", inert=True)
    patches = []
    intervals = {locale: [] for locale in LOCALES}
    for index, patch in enumerate(_sequence(value["patches"], 2, 4, path + ".patches")):
        at = f"{path}.patches[{index}]"
        _object(patch, ("id", "label", "before", "after"), path=at)
        result = {"id": _id(patch["id"], at + ".id"), "label": _copy(patch["label"], 80, at + ".label"),
                  "before": _copy(patch["before"], 700, at + ".before", inert=True),
                  "after": _copy(patch["after"], 700, at + ".after", inert=True)}
        for locale in LOCALES:
            before = result["before"][locale]
            # str.count ignores overlapping occurrences ("aa" within "aaa").
            positions = [match.start() for match in re.finditer("(?=" + re.escape(before) + ")", base[locale])]
            if len(positions) != 1:
                _fail(at + ".before." + locale, "patch must occur exactly once in base")
            if before == result["after"][locale]:
                _fail(at + ".after." + locale, "patch must change text")
            start, end = positions[0], positions[0] + len(before)
            if any(start < previous_end and previous_start < end for previous_start, previous_end in intervals[locale]):
                _fail(at + ".before." + locale, "patches must not overlap")
            intervals[locale].append((start, end))
        patches.append(result)
    _unique([patch["id"] for patch in patches], path + ".patches")
    return {"base": base, "patches": patches}


def _content(kind, artifact, locale):
    """Causal comparison excludes IDs, decorative labels and explanatory briefs."""
    if kind == "editor":
        return [field["value"][locale] for field in artifact["fields"]]
    if kind == "form":
        return [{"type": field["type"], "required": field["required"]} for field in artifact["fields"]]
    if kind == "review":
        return {"base": artifact["base"][locale], "patches": [
            {"before": patch["before"][locale], "after": patch["after"][locale]} for patch in artifact["patches"]]}
    columns = artifact["columns"]
    result = {"types": [column["type"] for column in columns], "rows": []}
    for row in artifact["rows"]:
        cells = []
        for column in columns:
            value = row["cells"][column["id"]]
            if column["type"] == "text":
                value = value[locale]
            elif column["type"] == "select":
                value = [option["id"] for option in column["options"]].index(value)
            cells.append(value)
        # Evidence is an on-demand disclosure. Changing only its hidden text
        # cannot satisfy the promise that a choice changes the visible result.
        result["rows"].append({"cells": cells})
    if "calculation" in artifact:
        calculation = artifact["calculation"]
        derived = {"op": calculation["op"]}
        if "column" in calculation:
            derived["columnIndex"] = [column["id"] for column in columns].index(calculation["column"])
        for side in ("left", "right"):
            if side in calculation:
                derived[side + "RowIndex"] = [row["id"] for row in artifact["rows"]].index(calculation[side])
        result["calculation"] = derived
    return result


def _number_text(value):
    """Mirror ordinary browser number display for fact references, never units."""
    number = float(value)
    if number == 0:
        return "0"
    shortest = repr(number)
    if 1e-6 <= abs(number) < 1e21:
        text = format(Decimal(shortest), "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    mantissa, exponent = shortest.lower().split("e")
    return mantissa.removesuffix(".0") + "e" + ("+" if int(exponent) >= 0 else "-") + str(abs(int(exponent)))


def _fact_values(kind, artifact, locale):
    """Only literal substantive leaves count; labels/briefs cannot fake binding."""
    if kind == "editor":
        return [field["value"][locale] for field in artifact["fields"]]
    if kind == "form":
        return [artifact["title"][locale]] + [field["label"][locale] for field in artifact["fields"]]
    if kind == "review":
        return [artifact["base"][locale]]
    values = []
    for row in artifact["rows"]:
        for column in artifact["columns"]:
            cell = row["cells"][column["id"]]
            if column["type"] == "text":
                values.append(cell[locale])
            elif column["type"] == "number":
                values.append(_number_text(cell))
            else:
                values.append(next(option["label"][locale] for option in column["options"] if option["id"] == cell))
        if "evidence" in row:
            values.extend(row["evidence"][field][locale] for field in ("text", "quote"))
    return values


def _fact_states(kind, artifact, locale):
    if kind != "review":
        yield _fact_values(kind, artifact, locale)
        return
    # A fact present in the source may disappear after accepting a built-in
    # patch. Check every reachable preview, including the unchanged source.
    # Four non-overlapping patches bound this to sixteen text-only states.
    base = artifact["base"][locale]
    positioned = [(base.index(patch["before"][locale]), index, patch)
                  for index, patch in enumerate(artifact["patches"])]
    for mask in range(1 << len(positioned)):
        merged = base
        for start, index, patch in sorted(positioned, reverse=True):
            if mask & (1 << index):
                merged = merged[:start] + patch["after"][locale] + merged[start + len(patch["before"][locale]):]
        yield [merged]


def _validate_facts(kind, inputs, variants):
    if kind == "editor" and len(inputs) == 2 and not any(all(option.get("facts") for option in item["options"]) for item in inputs):
        _fail("interaction.inputs", "two-input editors need one input whose every option declares binding facts")
    for index, variant in enumerate(variants):
        selected = [fact for item in inputs for option in item["options"]
                    if option["id"] == variant["when"][item["id"]] for fact in option.get("facts", [])]
        unselected = [fact for item in inputs for option in item["options"]
                      if option["id"] != variant["when"][item["id"]] for fact in option.get("facts", [])]
        for locale in LOCALES:
            selected_text = {fact[locale] for fact in selected}
            for values in _fact_states(kind, variant["artifact"], locale):
                if any(not any(fact in value for value in values) for fact in selected_text):
                    _fail(f"interaction.variants[{index}].artifact", f"selected facts must occur in substantive {locale} values in every patch state")
                if any(fact[locale] not in selected_text and any(fact[locale] in value for value in values) for fact in unselected):
                    _fail(f"interaction.variants[{index}].artifact", f"unselected exclusive facts cannot occur in {locale} values in any patch state")


def validate_interaction(value):
    """Return only supported normalized fields; reject incomplete or inert choices."""
    _object(value, ("kind", "input_label", "output_label", "inputs", "variants"))
    kind = _enum(value["kind"], KINDS, "interaction.kind")
    inputs = []
    for index, item in enumerate(_sequence(value["inputs"], 0, 2, "interaction.inputs")):
        path = f"interaction.inputs[{index}]"
        _object(item, ("id", "label", "options"), path=path)
        inputs.append({"id": _id(item["id"], path + ".id"), "label": _copy(item["label"], 80, path + ".label"),
                       "options": _options(item["options"], 3, path + ".options", allow_facts=True)})
    input_ids = [item["id"] for item in inputs]
    _unique(input_ids, "interaction.inputs")
    combinations = list(itertools.product(*[[option["id"] for option in item["options"]] for item in inputs]))
    if len(combinations) > 4:
        _fail("interaction.inputs", "at most four combinations are supported")
    variants = []
    by_combination = {}
    validator = {"editor": _editor, "records": _records, "form": _form, "review": _review}[kind]
    for index, variant in enumerate(_sequence(value["variants"], len(combinations), len(combinations), "interaction.variants")):
        path = f"interaction.variants[{index}]"
        _object(variant, ("when", "brief", "artifact"), path=path)
        _object(variant["when"], input_ids, path=path + ".when")
        when = {}
        for item in inputs:
            when[item["id"]] = _enum(variant["when"][item["id"]], {option["id"] for option in item["options"]}, path + ".when")
        combination = tuple(when[key] for key in input_ids)
        if combination in by_combination:
            _fail(path + ".when", "duplicate combination")
        normalized = {"when": when, "brief": _copy(variant["brief"], 300, path + ".brief"),
                      "artifact": validator(variant["artifact"], path + ".artifact")}
        by_combination[combination] = normalized
        variants.append(normalized)
    if set(by_combination) != set(combinations):
        _fail("interaction.variants", "every input combination needs exactly one variant")
    for left, right in itertools.combinations(combinations, 2):
        if sum(a != b for a, b in zip(left, right)) != 1:
            continue
        for locale in LOCALES:
            before = _content(kind, by_combination[left]["artifact"], locale)
            after = _content(kind, by_combination[right]["artifact"], locale)
            if before == after:
                _fail("interaction.variants", f"each input must change artifact content in {locale}")
    _validate_facts(kind, inputs, variants)
    return {"kind": kind, "input_label": _copy(value["input_label"], 80, "interaction.input_label"),
            "output_label": _copy(value["output_label"], 80, "interaction.output_label"), "inputs": inputs, "variants": variants}


def interaction_snapshot(normalized):
    """A bounded v2 artifact for compatibility; the runtime uses the full payload."""
    initial = {item["id"]: item["options"][0]["id"] for item in normalized["inputs"]}
    variant = next(variant for variant in normalized["variants"] if variant["when"] == initial)
    artifact = variant["artifact"]

    def short(text, maximum=220):
        return text if len(text) <= maximum else text[:maximum - 1].rstrip() + "…"

    from app.services.demo_contract import ARTIFACT_UNSAFE_COPY

    outputs = {}
    for locale in LOCALES:
        if normalized["kind"] == "editor":
            text = "\n".join(field["label"][locale] + ": " + field["value"][locale] for field in artifact["fields"])
        elif normalized["kind"] == "review":
            text = "\n".join(patch["label"][locale] for patch in artifact["patches"])
        elif normalized["kind"] == "form":
            text = artifact["title"][locale] + "\n" + " / ".join(field["label"][locale] for field in artifact["fields"])
        else:
            # Do not turn permitted numeric cells and a percent-like unit into an
            # apparent measured claim in the legacy renderer's prose snapshot.
            text = " / ".join(column["label"][locale] for column in artifact["columns"])
            text += "\n" + (f"{len(artifact['rows'])} 条可编辑示例记录" if locale == "zh" else f"{len(artifact['rows'])} editable example records")
        # Joining two individually safe fields can accidentally form a legacy
        # claim phrase (for example a label followed by a number). The full
        # interaction remains unchanged; this compatibility summary stays a
        # truthful description of the available local artifact.
        if ARTIFACT_UNSAFE_COPY.search(text):
            text = "打开完整示例以编辑这份准备好的产物。" if locale == "zh" else "Open the full example to edit this prepared artifact."
        outputs[locale] = short(text)
    return {"kind": "text", "input_label": {"zh": "示例输入", "en": "Example input"},
            "output_label": {"zh": "可交互产物", "en": "Interactive artifact"},
            "input": {locale: short(variant["brief"][locale]) for locale in LOCALES}, "output": outputs}
