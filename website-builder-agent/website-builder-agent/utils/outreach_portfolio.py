"""Verified Kaurivo work examples allowed in personalized outreach.

A demo proposal must NEVER be presented as a paid client project.
Sales numbers, testimonials and client relationships cannot be inferred.
Only owner-approved, evidenced cases are passed to the sales prompt.
"""
from urllib.parse import urlsplit


def _https(url):
    if not isinstance(url, str) or len(url) > 2000:
        return False
    parts = urlsplit(url.strip())
    return (parts.scheme == "https" and bool(parts.hostname)
            and not parts.username and not parts.password)


def approved_portfolio_examples(records, limit=2):
    """Return examples suitable for truthful outbound messaging, without network.

    Schema:
      project_name: str
      project_type: 'demo' or 'client_work'
      improvements: list[str] (1-3 specific demonstrated improvements)
      proof_url: real public HTTPS link to the finished work
      verified_by_human: true
      approved_for_outreach: true
      client_reference_permission: true (mandatory for client_work)

    For all cases the owner must first verify that the URLs actually work.
    No outcome, endorsement or ROI fields are forwarded to the model.
    """
    if not isinstance(records, list):
        return []
    approved = []
    for record in records:
        if not isinstance(record, dict):
            continue
        if (record.get("verified_by_human") is not True
                or record.get("approved_for_outreach") is not True):
            continue
        kind = record.get("project_type")
        if kind not in {"demo", "client_work"}:
            continue
        if kind == "client_work" and record.get("client_reference_permission") is not True:
            continue
        name = record.get("project_name")
        points = record.get("improvements")
        url = record.get("proof_url")
        if (not isinstance(name, str) or not 2 <= len(name.strip()) <= 80
                or any(c in name for c in "\r\n")
                or not _https(url)
                or not isinstance(points, list)
                or not 1 <= len(points) <= 3
                or not all(isinstance(p, str) and 4 <= len(p.strip()) <= 180
                           and "\n" not in p for p in points)):
            continue
        approved.append({
            "project_name": name.strip(),
            "project_type": kind,
            "description": "Suunnitteludemo, ei asiakastoimeksianto"
            if kind == "demo" else "Todennettu asiakastyö, lupa referenssin käyttöön",
            "improvements": [p.strip() for p in points],
            "proof_url": url.strip(),
        })
        if len(approved) >= limit:
            break
    return approved
