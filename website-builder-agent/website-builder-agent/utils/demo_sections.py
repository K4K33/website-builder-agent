"""Assemble one draft from a model-authored shell and resumable sections."""
from pathlib import Path
import re

from bs4 import BeautifulSoup, Tag

from utils.kaurivo_free_json_envelope import parse_complete_model_json
from utils.site_architecture import MAX_JSON_BYTES

SLOT = "data-kaurivo-section-slot"


def _response(path, key, request, system, prompt, validate):
    def parse(raw):
        if len(raw.encode("utf-8")) > MAX_JSON_BYTES:
            raise RuntimeError("Oversized section response.")
        data = parse_complete_model_json(raw)
        value = data.get(key) if isinstance(data, dict) else None
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError("Missing section response field: " + key)
        return validate(value.strip())

    if path.is_file() and path.stat().st_size <= MAX_JSON_BYTES:
        try:
            return parse(path.read_text(encoding="utf-8"))
        except (RuntimeError, ValueError, UnicodeError):
            pass
    raw = request(system, prompt)
    output = parse(raw)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(raw, encoding="utf-8")
    temporary.replace(path)
    return output


def _shell(html):
    if not html.lower().startswith("<!doctype html>") or not html.lower().endswith("</html>"):
        raise RuntimeError("Incomplete demo page shell.")
    document = BeautifulSoup(html, "html.parser")
    mains = document.find_all("main")
    slots = document.find_all(attrs={SLOT: True})
    ids = [slot[SLOT] for slot in slots]
    if (len(mains) != 1 or not slots or len(slots) > 20 or len(set(ids)) != len(ids)
            or any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,79}", name) for name in ids)
            or any(slot.parent is not mains[0] or slot.name != "div" or
                   slot.find(True) or slot.get_text(strip=True)
                   for slot in slots)
            or len(mains[0].find_all(recursive=False)) != len(slots)
            or mains[0].get_text(strip=True)):
        raise RuntimeError("Demo shell requires unique empty section slots in main.")
    return document, slots


def _section(html, slot_id):
    if re.search(r"<!doctype|</?(?:html|body|main|head)(?:\s|>)", html, re.I):
        raise RuntimeError("A demo section cannot replace document structure.")
    parsed = BeautifulSoup(html, "html.parser")
    content = [node for node in parsed.contents if str(node).strip()]
    if (len(content) != 1 or not isinstance(content[0], Tag)
            or content[0].name != "section" or content[0].get("id") != slot_id
            or parsed.find(attrs={SLOT: True}) or not html.lower().endswith("</section>")):
        raise RuntimeError("Missing, mismatched or incomplete demo section: " + slot_id)
    return content[0]


def assemble_sections(path: Path, route, system, prompt, request):
    task = (
        f"Author only the HTML shell for {route}. Return JSON with one key shell. "
        "Include a complete document with company-specific metadata, shared responsive "
        "styles, navigation and footer. Inside the single main element place only "
        "empty direct child divs marked data-kaurivo-section-slot. Set each value to "
        "a unique content section ID based on the page requirements. Keep their intended "
        "order, group related content, and leave the divs completely empty."
    )
    document, slots = _response(path.with_suffix(".shell.json"), "shell", request,
                                task + "\n\n" + system, prompt + "\n\n" + task, _shell)
    shell_context = str(document)
    for slot in slots:
        slot_id = slot[SLOT]
        task = (
            f"Author only section {slot_id} for {route}. Return JSON with one key section "
            f'containing one complete <section id="{slot_id}"> element. Use the shared '
            "styles, follow the design and evidence for this section, and scope any "
            "section-specific styles to its ID."
        )
        fragment = _response(
            path.with_suffix(f".section-{slot_id}.json"), "section", request,
            task + "\n\n" + system,
            prompt + "\n\nPAGE SHELL:\n" + shell_context + "\n\n" + task,
            lambda html: _section(html, slot_id),
        )
        slot.replace_with(fragment)
    return str(document)
