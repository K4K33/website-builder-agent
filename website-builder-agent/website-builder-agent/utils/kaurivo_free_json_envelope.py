"""Deterministically unwrap full JSON objects from limited free LLM output.

Syntax-only handling. We NEVER invent source facts, fields or data; incomplete
or multiple JSON objects fail closed into original stage/source quality gates.
This is not a JSON repair/generation model.
"""
from __future__ import annotations

import json

MAX_JSON_INPUT_CHARS = 160_000


class InvalidModelJSON(ValueError):
    """Safe category only; never embed untrusted prompt or model response."""


def _trim_code_fence(raw: str) -> str:
    value = raw.strip()
    if not value.startswith("```"):
        return value
    lines = value.splitlines()
    if lines and lines[0].strip().lower() in ("```", "```json"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _remove_only_trailing_commas(value: str) -> str:
    """Remove commas immediately before ] or } OUTSIDE quoted JSON strings.

    This doesn't fill in missing fields, rewrite values, close structures or
    change company names/services/quotes.
    """
    result = []
    inside = False
    escaped = False
    for i, char in enumerate(value):
        if inside:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                inside = False
            continue
        if char == '"':
            inside = True
            result.append(char)
            continue
        if char == ',':
            pos = i + 1
            while pos < len(value) and value[pos] in " \t\n\r":
                pos += 1
            if pos < len(value) and value[pos] in ("}", "]"):
                continue
        result.append(char)
    return "".join(result)


def parse_complete_model_json(raw: str) -> dict | list:
    """Accept valid JSON or an unambiguous COMPLETE object inside a wrapper.

    Accept a preamble/fence/trailing prose or extraneous trailing comma only
    when exactly one complete parseable object remains. Multiple or truncated
    objects fail; downstream stage validators still enforce source fidelity.
    """
    if not isinstance(raw, str) or not raw.strip() or len(raw) > MAX_JSON_INPUT_CHARS:
        raise InvalidModelJSON("invalid length or empty model JSON")
    cleaned = _trim_code_fence(raw)
    first_error = None
    for candidate in (cleaned, _remove_only_trailing_commas(cleaned)):
        try:
            obj = json.loads(candidate)
            if isinstance(obj, (dict, list)):
                return obj
        except json.JSONDecodeError as exc:
            first_error = exc

    # A single complete JSON document with harmless leading/trailing prose.
    # This is a *syntax* recovery; it doesn't regenerate or extrapolate data.
    decoder = json.JSONDecoder()
    for pos, char in enumerate(cleaned):
        if char not in "{[":
            continue
        chunk = cleaned[pos:]
        for candidate in (chunk, _remove_only_trailing_commas(chunk)):
            try:
                obj, used = decoder.raw_decode(candidate)
                if not isinstance(obj, (dict, list)):
                    continue
                # Ambiguous second JSON document must never be ignored.
                tail = candidate[used:].strip()
                if tail.startswith("```"):
                    tail = tail[3:].strip()
                if tail:
                    if any(mark in tail for mark in ("{", "[")):
                        continue
                # Reject a data-looking preamble: a second independently
                # parseable JSON value must not be silently discarded.
                preamble = cleaned[:pos].strip()
                if preamble.startswith("{") or preamble.startswith("["):
                    continue
                return obj
            except json.JSONDecodeError:
                continue
    # Only report safe parser location; never raw source/user content.
    category = first_error.msg if first_error else "not a JSON document"
    safe_categories = {
        "Expecting value": "missing_value",
        "Expecting ',' delimiter": "invalid_delimiter",
        "Expecting property name enclosed in double quotes": "invalid_property_name",
        "Unterminated string starting at": "unterminated_string",
        "Extra data": "extra_data",
    }
    message = safe_categories.get(category, "invalid_structure")
    raise InvalidModelJSON("model JSON invalid: "+message)
