"""Private, no-credit Kaurivo customer feedback workflow helpers.

No Gmail, network, message sending, mailbox reading or public issue creation.
The assessment is a triage suggestion; only a person can verify provenance
and approve a change to a customer's website.
"""
from __future__ import annotations

from urllib.parse import quote, urlsplit
from html import escape
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

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
            "Kaurivo"
        ),
        "send_approved": False,
        "send_performed": False,
        "public_testimonial_permission": False,
        "notes": "Human review, verified Kaurivo Gmail account, consent/lawful processing and explicit send approval required.",
    }


def feedback_due_at(sale_confirmed_at: datetime) -> datetime:
    """One calendar day after a verified sale, in Finnish local time."""
    if not isinstance(sale_confirmed_at, datetime) or sale_confirmed_at.tzinfo is None:
        raise ValueError("Use a timezone-aware confirmed sale timestamp.")
    local = sale_confirmed_at.astimezone(ZoneInfo("Europe/Helsinki"))
    tomorrow = local.date() + timedelta(days=1)
    return datetime.combine(tomorrow, local.timetz()).replace(
        tzinfo=ZoneInfo("Europe/Helsinki")
    )


def _stars(value: int) -> str:
    return "★" * value + "☆" * (5 - value)


def draft_after_sale_feedback(*, recipient_email: str, company_name: str,
                              sale_confirmed_at: datetime, now: datetime,
                              sale_verified: bool, relationship_verified: bool,
                              contact_first_name: str = "") -> dict:
    """Draft for Gmail only when one Finnish calendar day has passed.

    Checks neither Gmail nor purchase authenticity itself. Sale + customer
    verification are caller responsibilities. No sending or scheduling occurs.
    The early feedback rates buying/onboarding, never unfinished site quality.
    """
    if not (sale_verified and relationship_verified):
        raise ValueError("Verified sale and actual customer relationship required.")
    due = feedback_due_at(sale_confirmed_at)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("Provide timezone-aware current datetime.")
    if now.astimezone(ZoneInfo("Europe/Helsinki")) < due:
        raise ValueError("Review request is not due until the day after the sale.")
    if not isinstance(recipient_email, str) or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", recipient_email.strip()
    ):
        raise ValueError("Verified recipient address is required.")
    if not isinstance(company_name, str) or not company_name.strip():
        raise ValueError("Confirmed client company is required.")

    greeting = f"Hei {contact_first_name.strip()}," if contact_first_name.strip() else "Hei,"
    subject = "Miten asiointi Kaurivon kanssa alkoi?"
    body = (
        f"{greeting}\n\n"
        "Kiitos luottamuksesta! Haluaisin heti yhteistyön alussa "
        "kuulla, miltä yhteydenpito, tarjous ja ostoprosessi tuntuivat.\n\n"
        "Kuinka arvioisit asioinnin tähän asti asteikolla 1–5 tähteä?\n"
        "★★★★★ = 5 / 5, ★★★★☆ = 4 / 5, ★★★☆☆ = 3 / 5\n"
        "★★☆☆☆ = 2 / 5, ★☆☆☆☆ = 1 / 5\n\n"
        "Vastaa tähän viestiin esimerkiksi näin:\n"
        "4/5 – Kaikki sujui selkeästi, mutta aikatauluista voisi kertoa tarkemmin.\n\n"
        "Yksi lyhyt lause riittää. Myös kriittinen palaute on arvokasta, "
        "eikä tätä arviota julkaista ilman erillistä lupaasi.\n\n"
        "Ystävällisin terveisin,\n"
        "Kaurivo"
    )
    # Optional star links; mailto opens a draft, NEVER records a click as a vote.
    # The primary, more reliable path is replying directly to the Gmail thread.
    star_links = []
    for value in range(1, 6):
        message = f"Arvosana: {value}/5\nLyhyt palaute: "
        link = "mailto:" + SENDER + "?subject=" + quote(subject) + "&body=" + quote(message)
        star_links.append(
            '<a href="' + escape(link, quote=True)
            + '" style="display:inline-block;padding:9px 7px;margin:3px;'
              'border:1px solid #c7d0d5;color:#172027;text-decoration:none;'
              'font-size:17px;font-weight:700;white-space:nowrap"'
            + ' aria-label="' + str(value) + ' tähteä">'
            + _stars(value) + "</a>"
        )
    html_body = (
        '<div style="max-width:540px;margin:0 auto;padding:24px;'
        'background:#f6f7f8;color:#172027;font-family:Arial,sans-serif;'
        'font-size:15px;line-height:1.7">'
        '<div style="font-size:14px;letter-spacing:2px;font-weight:700;'
        'padding-bottom:17px;border-bottom:1px solid #c8d0d5">KAURIVO</div>'
        '<p>' + escape(greeting) + '</p>'
        '<p>Kiitos luottamuksesta! Haluaisin kuulla, miten yhteydenpito,'
        ' tarjous ja ostoprosessi sujuivat.</p>'
        '<p><strong>Montako tähteä antaisit asioinnille tähän asti?</strong></p>'
        '<div>' + "".join(star_links) + '</div>'
        '<p style="font-size:13px;color:#46545f">'
        'Voit klikata tähtimäärää, jolloin sähköpostiluonnos avautuu. '
        'Arvosana tallentuu vasta, kun lähetät viestin.</p>'
        '<p style="font-size:15px;font-weight:700">Kirjallinen palaute '
        '<span style="color:#65717b;font-size:12px;font-weight:400">'
        '(vapaaehtoinen)</span></p>'
        '<a href="' + escape(
            "mailto:" + SENDER + "?subject=" + quote(subject)
            + "&body=" + quote("Arvosana: /5\n\nLyhyt palaute:\n"),
            quote=True
        ) + '" style="display:block;padding:19px 16px;'
        'background:#ffffff;border:1px solid #b6c2cb;border-radius:5px;'
        'color:#64737e;font-size:14px;text-decoration:none">'
        'Kirjoita lyhyt palaute tähän... ↗</a>'
        '<p style="font-size:12px;color:#46545f">'
        'Kentän painaminen avaa sähköpostin oikean kirjoitusnäkymän. '
        'Voit myös vastata suoraan tähän viestiin, esimerkiksi '
        '"4/5 – Kaikki sujui selkeästi". '
        'Tähtivalinta ei itsessään tallenna palautetta.</p>'
        '<p style="font-size:12px;color:#56626b">Arvio koskee vain '
        'asiointia tähän asti, ei vielä keskeneräistä verkkosivustoa. '
        'Palautetta ei julkaista ilman erillistä lupaa.</p>'
        '<p style="padding-top:14px;border-top:1px solid #d4dade">Kaurivo<br>Asiakaskokemus</p></div>'
    )
    return {
        "from": SENDER, "to": recipient_email.strip(),
        "subject": subject, "body": body, "html_body": html_body,
        "due_at": due.isoformat(),
        "feedback_stage": "day_after_confirmed_sale",
        "send_approved": False, "send_performed": False,
        "public_testimonial_permission": False,
        "notes": ("Gmail draft only. Verify actual sale, contact, Kaurivo Gmail sender "
                  "and explicit approval before sending; no scheduled automation active."),
    }


def extract_rating_from_reply(message: str) -> int | None:
    """Read explicit 1–5 score in the new reply, never infer sentiment.

    Ignore quoted Gmail history, where example ratings may appear.
    Human review remains necessary for ambiguous or forwarded content.
    """
    if not isinstance(message, str):
        return None
    fresh = []
    for line in message.splitlines():
        trimmed = line.strip()
        if trimmed.startswith(">") or re.search(
            r"^(?:On .+ wrote:|.+ kirjoitti:|Lähettäjä:|From:|"
            r"-{4,}\s*Forwarded message)",
            trimmed, flags=re.I
        ):
            break
        fresh.append(line)
    text = "\n".join(fresh).strip()
    match = re.search(r"(?:arvosana|tähteä|stars?)\s*:\s*([1-5])(?:\s*/\s*5)?\b", text, re.I)
    if match:
        return int(match.group(1))
    match = re.search(r"(?<!\d)([1-5])\s*/\s*5(?!\d)", text)
    if match:
        return int(match.group(1))
    match = re.search(r"(?<![★☆])([★]{1,5})([☆]{0,4})(?![★☆])", text)
    if match and len(match.group(1)) + len(match.group(2)) == 5:
        return len(match.group(1))
    return None


def triage_feedback(message: str, *, relationship_verified: bool = False,
                    project_verified: bool = False, rating: int | None = None) -> dict:
    """Triage a genuine or unconfirmed note without sentiment-based rejection.

    Negative, short and anonymous reports must not be automatically classed
    as fake or discarded. Verification must rely on external, consent-respecting
    client/project records and follow-up, never tone or an AI authenticity score.
    """
    if rating is not None and (type(rating) is not int or not 1 <= rating <= 5):
        raise ValueError("Rating must be 1 to 5 stars.")
    if not isinstance(message, str) or (not message.strip() and rating is None):
        raise ValueError("Feedback text or explicit star rating is required.")
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
        "rating": rating,
        "rating_is_authenticity_evidence": False,
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
