"""Conservative Finnish B2B email marketing checks.

Use this gate immediately before any future Gmail send. Merely generating a
draft never establishes permission to send. No email is transmitted here.
Reference: Finnish Act on Electronic Communications Services 917/2014,
sections 200, 202, 203, and GDPR (including Articles 14 and 21).
"""
from __future__ import annotations

from email.utils import parseaddr
from html import escape
import re
from urllib.parse import quote

SENDER = "hello.kaurivo@gmail.com"
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_address(value: object) -> str:
    """A normalized comparison key, NOT proof that an address exists."""
    raw = str(value or "").strip()
    display, parsed = parseaddr(raw)
    # Prevent display-name injection: explicit address only.
    if display or parsed != raw or not EMAIL_PATTERN.fullmatch(raw):
        return ""
    return raw.casefold()


def marketing_issues(
    recipient: dict | None,
    *,
    suppressed_addresses=(),
    sender: str = SENDER,
) -> list[str]:
    """Return all fail-closed concerns; an empty list allows *review*, not sending.

    The calling system must provide current human-verified evidence and a
    persistent, private suppression register. Never infer address type or
    natural-person consent from a generic business-directory listing.
    """
    if not isinstance(recipient, dict):
        return ["Missing individually reviewed recipient and compliance evidence."]
    issues = []
    address = normalize_address(recipient.get("address"))
    if not address:
        issues.append("Missing or invalid recipient email address.")
    if sender != SENDER:
        issues.append("Sender must be the connected Kaurivo business mailbox.")
    if recipient.get("opted_out") is True or recipient.get("do_not_contact") is True:
        issues.append("The recipient has objected to marketing.")
    blocked = {normalize_address(value) for value in suppressed_addresses}
    if address and address in blocked:
        issues.append("The recipient is in the suppression register.")
    if recipient.get("suppression_registry_checked") is not True:
        issues.append("Current, persistent opt-out register must be checked before send.")
    if recipient.get("reviewed_by_human") is not True:
        issues.append("Recipient and commercial relevance require human review.")
    source = str(recipient.get("source_url") or "")
    if not source.startswith("https://") or " " in source:
        issues.append("Record a traceable HTTPS source for the contact address.")
    if recipient.get("privacy_information_ready") is not True:
        issues.append("GDPR transparency/information duties have not been verified.")
    if recipient.get("optout_handling_ready") is not True:
        issues.append("A free, monitored opt-out reply route is required.")

    kind = recipient.get("classification")
    evidence = str(recipient.get("consent_evidence") or "").strip()
    if kind == "legal_entity_generic":
        if recipient.get("verified_legal_entity") is not True:
            issues.append("Generic mailbox must belong to a verified legal entity.")
    elif kind == "legal_entity_named_employee":
        if recipient.get("verified_legal_entity") is not True:
            issues.append("Verify the employing legal entity.")
        role_ok = (recipient.get("role_relevance_documented") is True
                   and bool(str(recipient.get("role_relevance_reason") or "").strip()))
        if not (role_ok or evidence):
            issues.append("Named employee requires proven substantial job relevance or documented prior consent.")
    elif kind == "natural_person":
        # Includes sole traders/individuals unless a separately documented
        # statutory customer-relationship exception is evaluated manually.
        if not evidence:
            issues.append("Natural-person marketing requires documented prior consent.")
    else:
        issues.append("Unknown address class: do not treat it as generic B2B.")
    return issues


def assert_marketing_ready(recipient: dict | None, *, suppressed_addresses=(), sender=SENDER) -> None:
    issues = marketing_issues(recipient, suppressed_addresses=suppressed_addresses, sender=sender)
    if issues:
        raise RuntimeError("Commercial email blocked: " + " ".join(issues))


def make_optout_footer() -> tuple[str, str]:
    """Readable HTML + plaintext footer for each commercial email.

    This mailto route is ONLY valid while someone monitors replies and
    applies opt-outs to a durable private suppression register.
    """
    subject = quote("Kieltäydyn Kaurivon jatkoviesteistä")
    href = f"mailto:{SENDER}?subject={subject}"
    text = f"Kieltäydy jatkoviesteistä maksutta vastaamalla tähän viestiin tai osoitteeseen {SENDER}."
    html = (
        '<p style="font-size:12px;line-height:1.6;color:#64748b">'
        f'<a href="{escape(href, quote=True)}" style="color:#64748b;text-decoration:underline">'
        'Kieltäydy jatkoviesteistä</a> · Kaurivo · '
        f'{escape(SENDER)}</p>'
    )
    return text, html


def company_is_suppressed(company: dict) -> bool:
    """Unambiguous company-level do-not-contact request also blocks drafts."""
    return (company.get("marketing_opt_out") is True
            or company.get("do_not_contact") is True)
