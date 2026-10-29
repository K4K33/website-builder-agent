"""Require an evidence-backed industry comparison before generating a client site."""

from pathlib import Path
from urllib.parse import urlsplit
from utils.quality import canonical_url


def validate_benchmark(research, target_url=""):
    records = research.get("design_benchmark", []) if isinstance(research, dict) else []
    target = urlsplit(canonical_url(target_url)).hostname
    domains, accepted = set(), []
    for record in records:
        if not isinstance(record, dict):
            continue
        url = canonical_url(record.get("url"))
        domain = urlsplit(url).hostname
        if not domain or domain == target or domain in domains:
            continue
        if not all(isinstance(record.get(key), list) and record[key]
                   and all(isinstance(item, str) and item.strip() for item in record[key])
                   for key in ("observations", "apply", "avoid")):
            continue
        shots = record.get("screenshots") or {}
        if not isinstance(shots, dict) or not any(
            isinstance(path, str) and Path(path).is_file() for path in shots.values()
        ):
            continue
        domains.add(domain)
        accepted.append(record)
    if len(accepted) < 2:
        raise RuntimeError(
            "Design benchmark incomplete: compare at least two independent industry sites "
            "with screenshots, specific observations, applicable ideas and things to avoid. "
            "Research again before building; do not invent comparison evidence."
        )
    return accepted
