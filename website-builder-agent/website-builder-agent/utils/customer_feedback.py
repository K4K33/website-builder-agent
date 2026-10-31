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
                              contact_first_name: str = "", invitation_ref: str = "") -> dict:
    """Prepare private post-sale Gmail message linked to a real feedback page.

    The five HTML star links PRESELECT the rating on Kaurivo's site.
    Neither a click nor a draft saves an evaluation. Only a successful
    form submission counts. This function never sends or schedules mail.
    """
    if not (sale_verified and relationship_verified):
        raise ValueError("Verified sale and customer relationship required.")
    due = feedback_due_at(sale_confirmed_at)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise ValueError("A timezone-aware current datetime is required.")
    if now.astimezone(ZoneInfo("Europe/Helsinki")) < due:
        raise ValueError("Feedback request not due until one day after the sale.")
    if not isinstance(recipient_email, str) or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", recipient_email.strip()
    ):
        raise ValueError("Verified recipient email address required.")
    if not isinstance(company_name, str) or not company_name.strip():
        raise ValueError("Confirmed company required.")
    if invitation_ref and not re.fullmatch(r"[A-Za-z0-9_-]{4,50}", invitation_ref):
        raise ValueError("Invitation reference must be non-personal opaque ID.")

    base_url = "https://k4k33.github.io/website-builder-agent/kaurivo/feedback/"
    def feedback_url(value: int | None = None) -> str:
        params = ["lang=fi"]
        if value is not None:
            params.append(f"rating={value}")
        if invitation_ref:
            params.append("ref=" + quote(invitation_ref, safe=""))
        return base_url + "?" + "&".join(params)

    subject = "Kaurivo | Miten asiointi sujui?"
    greeting = f"Hei {contact_first_name.strip()}," if contact_first_name.strip() else "Hei,"
    body = (
        f"{greeting}\n\n"
        "Kiitos luottamuksesta! Haluaisimme kuulla, "
        "miten yhteydenpito, tarjous ja kaupanteko sujuivat.\n\n"
        "Valitse 1–5 tähteä ja kirjoita lyhyt palaute Kaurivon sivulla:\n"
        + feedback_url() + "\n\n"
        "Vastaaminen vie vain hetken. Palaute auttaa meitä kehittämään "
        "palvelua ja pysyy yksityisenä.\n\n"
        "Arvio koskee asiointia tähän asti, ei vielä keskeneräistä verkkosivustoa.\n\n"
        "Kaurivo\nAsiakaskokemus"
    )

    cells = []
    for value in range(1, 6):
        link = escape(feedback_url(value), quote=True)
        cells.append(
            '<td width="20%" align="center" style="padding:0 4px">'
            '<a href="' + link + '" aria-label="' + str(value) + ' tähteä"'
            ' style="display:block;border:1px solid #cbd3d9;'
            'background:#f7f9fb;border-radius:5px;padding:12px 3px;'
            'text-decoration:none;color:#202a34">'
            '<span style="display:block;color:#b78f43;font-size:22px">★</span>'
            '<span style="display:block;font-size:11px;font-weight:700">'
            + str(value) + '/5</span></a></td>'
        )
    url = escape(feedback_url(), quote=True)
    html_body = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"'
        ' style="background:#edf0f2;font-family:Arial,Helvetica,sans-serif">'
        '<tr><td align="center" style="padding:22px 12px">'
        '<table role="presentation" width="560" cellpadding="0" cellspacing="0"'
        ' style="width:100%;max-width:560px;background:white;color:#1c2730">'
        '<tr><td style="background:#0c121a;padding:27px 29px;color:#f6f8fa">'
        '<div style="font-size:23px;letter-spacing:4px;font-weight:800">'
        'KAURIVO</div><div style="font-size:10px;letter-spacing:2px;'
        'color:#adbdc9;margin-top:7px">ASIAKASKOKEMUS</div></td></tr>'
        '<tr><td style="padding:32px 29px 16px">'
        '<div style="font-size:31px;font-weight:800;line-height:1.17">'
        'Miten asiointi sujui?</div>'
        '<p style="font-size:15px;line-height:1.8;color:#4a5b68">'
        'Kiitos luottamuksesta! Miten tarjous, yhteydenpito ja '
        'kaupanteko sujuivat tähän asti?</p></td></tr>'
        '<tr><td style="padding:5px 23px 24px">'
        '<div style="background:#f3f5f6;border:1px solid #dbe1e5;'
        'padding:22px 15px">'
        '<p style="text-align:center;font-size:15px;font-weight:700">'
        'Anna arvosana 1–5 tähteä</p>'
        '<table role="presentation" width="100%" cellpadding="0" '
        'cellspacing="0"><tr>' + "".join(cells) + '</tr></table>'
        '<p style="font-size:12px;color:#657481;line-height:1.7;text-align:center">'
        'Tähti avaa Kaurivon palautelomakkeen valmiiksi valitulla '
        'arvosanalla. Gmail ei avaudu.</p>'
        '<p style="font-size:15px;font-weight:700;margin:24px 0 10px">'
        'Kirjallinen palaute</p>'
        '<a href="' + url + '" style="display:block;padding:18px 15px;'
        'background:#fff;border:1px solid #bcc8d0;border-radius:5px;'
        'font-size:14px;color:#65747e;text-decoration:none">'
        'Kirjoita lyhyt palaute tähän... ↗</a>'
        '<p style="font-size:12px;color:#657481;line-height:1.7">'
        'Lomakkeella tähdet syttyvät valittaessa. '
        'Palaute tallentuu vasta Lähetä-painikkeesta.</p>'
        '</div></td></tr>'
        '<tr><td style="padding:3px 29px 30px;font-size:13px;'
        'line-height:1.7;color:#52636f">'
        'Arvio koskee asiointia tähän asti, ei keskeneräistä '
        'verkkosivustoa. Palautetta ei julkaista ilman erillistä lupaa.'
        '<p style="margin-top:23px;color:#1f2b35"><strong>Kaurivo</strong>'
        '<br>Asiakaskokemus</p></td></tr>'
        '</table></td></tr></table>'
    )
    return {
        "from": SENDER, "to": recipient_email.strip(),
        "subject": subject, "body": body, "html_body": html_body,
        "form_url": feedback_url(),
        "due_at": due.isoformat(),
        "feedback_stage": "day_after_confirmed_sale",
        "send_approved": False, "send_performed": False,
        "public_testimonial_permission": False,
        "notes": ("Gmail draft only. Link requires a verified backend before durable "
                  "first-party storage; no scheduled send exists yet."),
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
