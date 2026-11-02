"""Reusable source-to-redesign footer logo/affiliation audit.

This validates explicit *source-researched* manifests, not guesses from words
in arbitrary HTML or image filenames. A public launch also needs legal/brand
permission for each mark.
"""
from __future__ import annotations

from typing import Mapping, Sequence


def audit_footer_affiliations(
    originals: Sequence[Mapping[str, object]],
    rebuilt: Sequence[Mapping[str, object]],
    *,
    production: bool = False,
) -> list[str]:
    """Return missing/mismatched original affiliation problems.

    Manifest entries have `name`, `role`, `logo`, `href` and optional
    `active_verified`, `rights_verified`. The author must source these
    fields from the old website and client confirmation. Empty originals
    require no artificial sponsor block.
    """
    errors: list[str] = []
    new_by_name: dict[str, Mapping[str, object]] = {}
    for item in rebuilt:
        name = str(item.get("name") or "").strip().casefold()
        if not name:
            errors.append("New footer entry lacks a partner/sponsor name.")
        elif name in new_by_name:
            errors.append(f"Duplicate new footer logo: {name}")
        else:
            new_by_name[name] = item
    for original in originals:
        name = str(original.get("name") or "").strip()
        if not name:
            errors.append("Original footer logo requires a researched name.")
            continue
        fresh = new_by_name.get(name.casefold())
        if fresh is None:
            errors.append(f"Missing original footer affiliation: {name}")
            continue
        for field in ("role", "logo", "href"):
            a = str(original.get(field) or "").strip()
            b = str(fresh.get(field) or "").strip()
            if not a:
                errors.append(f"Research original {name} {field} before release.")
            elif a != b:
                errors.append(f"{name}: {field} changed or omitted.")
        if production:
            if fresh.get("active_verified") is not True:
                errors.append(f"{name}: active relationship not verified.")
            if fresh.get("rights_verified") is not True:
                errors.append(f"{name}: logo publication rights not verified.")
    return errors
