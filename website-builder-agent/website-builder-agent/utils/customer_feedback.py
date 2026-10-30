"""Private, no-credit Kaurivo customer feedback workflow helpers.

No Gmail, network, message sending, mailbox reading or public issue creation.
The assessment is a triage suggestion; only a person can verify provenance
and approve a change to a customer's website.
"""
from __future__ import annotations

from urllib.parse import urlsplit

SENDER = "hello.kaurivo@gmail.com"
DEMO_REVIEW_URL = "https://k4k33.github.io/website-builder-agent/kaurivo/demo-review/"

CATEGORY_TERMS = {
    "mobile_usability": ("mobile", "iphone", "puhel", "mobiil", "tablet", "valikko", "menu", "nav"),
    "speed_and_performance": ("slow", "lag", "hidas", "nopeus", "lataa", "load", "performance"),
    "functionality": ("bug", "ei toimi", "broken", "doesn't work", "does not work",
                      "error", "virhe", "lomake", "form", "lähet", "submit"),
    "content_and_brand": ("brand", "bränd", "logo", "colour", "color", "väri",
                          "teksti", "kuva", "photo", "sisält", "content", "background", "tausta", "green"),
    "editing_and_handover": ("wordpress", "cms", "edit", "päivit", "muokat", "ohje", "handover"),
    "communication": ("viest", "reply", "response", "vastau", "kommunik", "aikataul"),
}

SEVERE_TERMS = ("security", "tietoturv", "data leak", "tietovuoto", "maksu ei",
                "cannot submit", "can't submit", "ei voi lähettää", "lomake ei toimi",
                "broken payment", "ei toimi puhelimella", "sivu ei toimi")


def _safe_https_url(value: str) -> bool:
    if not isinstance(value, str):
        return False
    parts = urlsplit(value)
    return (parts.scheme == "https" and bool(parts.hostname)
            and not parts.username and not parts.password)


def demo_review_invitation(demo_url: str, *, intake_activated: bool = False) -> str:
    """Optional text for an approved one-to-one outreach email.

    Form link is advertised only after the receiving mailbox has been
    activated and an end-to-end submission has been verified.
    """
    if not _safe_https_url(demo_url):
        raise ValueError("Verified public HTTPS demo URL is required.")
    if intake_activated:
        return (
            f"Demo: {demo_url}\n"
            "Jos pidätte ehdotuksesta, voitte kertoa mitä lopullisella "
            f"sivustolla pitää ehdottomasti olla: {DEMO_REVIEW_URL}\n"
            "Voitte myös vastata tähän sähköpostiin suoraan."
        )
    return (
        f"Demo: {demo_url}\n"
        "Jos jokin ominaisuus tai sisältö on lopullisessa sivustossa "
        "ehdottoman tärkeä, voitte kertoa sen vastaamalla suoraan "
        "tähän sähköpostiin."
    )


def draft_completed_project_feedback(*, recipient_email: str, company_name: str,
                                     project_completed: bool, relationship_verified: bool,
                                     contact_first_name: str = "") -> dict:
    """Prepare, never send, a private Gmail feedback request after handover."""
    if not (project_completed and relationship_verified):
        raise ValueError("Confirmed completed client project and verified relationship required.")
    if not isinstance(recipient_email, str) or not recipient_email.strip() or "@" not in recipient_email:
        raise ValueError("Client recipient email is required.")
    if not company_name or not company_name.strip():
        raise ValueError("Real client company is required.")
    greeting = f"Hei {contact_first_name.strip()}," if contact_first_name.strip() else "Hei,"
    return {
        "from": SENDER,
        "to": recipient_email.strip(),
        "subject": "Miten verkkosivuprojektimme sujui?",
        "body": (
            f"{greeting}\n\n"
            "Nyt kun verkkosivunne ovat valmistuneet, "
            "haluaisin kuulla, miten yhteistyö ja lopputulos sujuivat teidän näkökulmastanne.\n\n"
            "Mikä meni erityisen hyvin?\n"
            "Oliko jotain hankalaa tai sellaista, jonka tekisit eri tavalla?\n"
            "Mikä olisi tärkein asia, jonka Kaurivon kannattaisi jatkossa tehdä paremmin?\n\n"
            "Voit vastata suoraan tähän sähköpostiin, vaikka vain parilla lauseella. "
            "Myös kriittinen palaute on erittäin arvokasta.\n\n"
            "Kiitos jo etukäteen!\n"
            "Kaarlo Kaurivolta"
        ),
        "send_approved": False,
        "send_performed": False,
        "public_testimonial_permission": False,
        "notes": "Human review, verified Kaurivo Gmail account, consent/lawful processing and explicit send approval required.",
    }


def triage_feedback(message: str, *, relationship_verified: bool = False,
                    project_verified: bool = False) -> dict:
    """Triage a genuine or unconfirmed note without sentiment-based rejection.

    Negative, short and anonymous reports must not be automatically classed
    as fake or discarded. Verification must rely on external, consent-respecting
    client/project records and follow-up, never tone or an AI authenticity score.
    """
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Non-empty feedback text required.")
    text = message.strip()
    lower = text.lower()
    categories = [name for name, terms in CATEGORY_TERMS.items()
                  if any(term in lower for term in terms)]
    urgent = any(term in lower for term in SEVERE_TERMS)
    verified = bool(relationship_verified and project_verified)
    specificity = "specific" if (len(text) >= 45 and (categories or any(ch.isdigit() for ch in text))) else "needs_context"
    if urgent:
        next_action = "Prioritize reproduction and safe fix; contact client to confirm details."
        priority = "urgent_review"
    elif specificity == "specific":
        next_action = "Review evidence with owner; plan or test a specific improvement."
        priority = "normal_review"
    else:
        next_action = "Ask a short clarifying question; retain the note for later patterns."
        priority = "clarify"
    return {
        "source_status": "verified_client_project" if verified else "unverified_source",
        "specificity": specificity,
        "categories": categories or ["general_experience"],
        "priority": priority,
        "next_action": next_action,
        "human_review_required": True,
        "publish_permitted": False,
        "auto_revise_or_send": False,
        "limitations": (
            "Categorization is keyword-assisted only. No authenticity, truth, "
            "legal validity or product change is confirmed by this assessment."
        ),
    }
