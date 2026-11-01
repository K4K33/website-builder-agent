"""Static Kotifixi CMS pilot renderer.

This is only a staging test. It never logs in, publishes, runs paid APIs,
changes DNS, contacts a customer or asserts that site facts are confirmed.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
TOKEN = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")
EMAIL = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")
PHONE = re.compile(r"^\+[0-9]{6,18}$")
FIELDS = (
    "seo_title", "seo_description", "hero_heading", "hero_emphasis",
    "hero_intro", "hero_image", "service1_title", "service1_description",
    "service1_image", "service2_title", "service2_description",
    "service2_image", "service3_title", "service3_description",
    "service3_image", "about_image", "pricing_url", "phone_tel",
    "phone_display", "email", "hours", "company_id",
)
IMAGES = {"hero_image", "service1_image", "service2_image", "service3_image", "about_image"}
URLS = IMAGES | {"pricing_url"}


def validated_values(values):
    if not isinstance(values, dict):
        raise ValueError("CMS content must be a JSON object.")
    expected = set(FIELDS)
    missing = expected - set(values)
    if missing:
        raise ValueError("Missing CMS fields: " + ", ".join(sorted(missing)))
    checked = {}
    for key in FIELDS:
        value = values[key]
        if not isinstance(value, str) or not value.strip() or len(value) > 3000:
            raise ValueError("Invalid nonempty CMS text: " + key)
        checked[key] = value.strip()
    if len(checked["seo_description"]) < 30:
        raise ValueError("SEO description must be meaningful.")
    if not EMAIL.fullmatch(checked["email"]):
        raise ValueError("Invalid contact email.")
    if not PHONE.fullmatch(checked["phone_tel"]):
        raise ValueError("Phone link must use international E.164 syntax.")
    for key in URLS:
        value = checked[key]
        p = urlsplit(value)
        if key in IMAGES and value.startswith("/media/"):
            relative = value.lstrip("/")
            if not re.fullmatch(r"media/[a-zA-Z0-9_./-]+", relative) or ".." in Path(relative).parts:
                raise ValueError("Invalid uploaded media path for " + key)
            checked[key] = relative
        elif (p.scheme != "https" or not p.hostname or p.username or p.password):
            raise ValueError("Only HTTPS image and pricing URLs permitted: " + key)
    return checked


def render(*, data_path=None, template_path=None, output_dir=None):
    data_path = Path(data_path) if data_path else HERE / "content" / "site.json"
    template_path = Path(template_path) if template_path else HERE / "index.template.html"
    output_dir = Path(output_dir) if output_dir else HERE / "dist"
    values = validated_values(json.loads(data_path.read_text(encoding="utf-8")))
    template = template_path.read_text(encoding="utf-8")
    tokens = set(TOKEN.findall(template))
    if tokens != set(FIELDS):
        raise ValueError("Template/CMS schema mismatch: " + repr(sorted(tokens ^ set(FIELDS))))
    # All fields inserted as plain text / HTML-attribute text; none as raw HTML.
    rendered = TOKEN.sub(lambda m: html.escape(values[m.group(1)], quote=True), template)
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("Unresolved or unexpected template token.")
    if '<meta name="robots" content="noindex,nofollow">' not in rendered:
        raise ValueError("Pilot must remain visibly noindex.")
    if "CMS -KOEPROJEKTI" not in rendered:
        raise ValueError("Missing visible staging banner.")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(rendered, encoding="utf-8")
    media_src = HERE / "media"
    if media_src.is_dir():
        for path in media_src.rglob("*"):
            if path.is_symlink():
                raise ValueError("Symlink media not permitted.")
        shutil.copytree(media_src, output_dir / "media", dirs_exist_ok=True)
    return output_dir / "index.html"


if __name__ == "__main__":
    print(render())
