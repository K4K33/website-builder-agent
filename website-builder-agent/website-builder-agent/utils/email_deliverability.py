"""Inbox, not spam: everything a Kaurivo sales email must satisfy before sending.

Large senders (Temu, Zalando, banks) reach the inbox because they send from
their OWN authenticated domain (SPF, DKIM, DMARC), from links on that domain,
at a steady volume people engage with. Cold B2B email cannot copy their opt-in
lists, so it copies everything else and behaves like one careful person:

- sender on Kaurivo's own domain (never a free Gmail/Outlook mailbox)
- demo links on Kaurivo's own domain (never onrender.com/github.io style hosts,
  which phishing abuses and filters distrust)
- short plain text, at most one or two links, no images or tracking pixels
- a slow daily ramp, weekdays and office hours only
- a free, working way to refuse further messages (Finnish law, every message)

Nothing here sends email. preflight() returns blocking issues; the existing
marketing_compliance gate and a human approval still decide every send.
"""
from __future__ import annotations

from datetime import date, datetime
import os
import re

FREE_MAILBOXES = {"gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "yahoo.com",
                  "icloud.com", "me.com", "suomi24.fi", "luukku.com", "proton.me", "protonmail.com"}
SHARED_HOSTS = ("onrender.com", "github.io", "vercel.app", "netlify.app", "pages.dev", "web.app",
                "firebaseapp.com", "herokuapp.com", "glitch.me", "000webhostapp.com", "wixsite.com",
                "weebly.com", "blogspot.com", "sites.google.com", "bit.ly", "tinyurl.com")
SPAMMY = ("ilmainen!", "ilmaiseksi!", "100 %", "100%", "klikkaa tästä", "klikkaa heti", "toimi heti",
          "viimeinen mahdollisuus", "tarjous voimassa", "€€€", "!!!", "takuuvarmasti", "rahat takaisin")
OPT_OUT = re.compile(r"ei kiitos|en ota (?:enää )?yhteyttä|kieltäydy(?:\s|ä)|jatkoviestei", re.I)
URL = re.compile(r"https?://[^\s<>\"')]+", re.I)

# Daily cap by week since the first send: a new domain earns trust slowly.
RAMP = (10, 15, 25, 35, 50)


def sender() -> str:
    return os.getenv("KAURIVO_SENDER", "").strip() or "hello@kaurivo.com"


def demo_host() -> str:
    """Public host for demo links in emails (own domain once it exists)."""
    return (os.getenv("KAURIVO_DEMO_HOST", "").strip()
            or "https://demo.kaurivo.com").rstrip("/")


RENDER_PREVIEW = "kaurivo-auto-demos-2026.onrender.com"


def public_demo_url(url: str) -> str:
    """The same demo on Kaurivo's own domain (demo.kaurivo.com is a CNAME of
    the Render preview service), so emails never carry an onrender.com link."""
    url = str(url or "").strip()
    return re.sub(r"^https?://" + re.escape(RENDER_PREVIEW) + r"(?=/|$)", demo_host(), url, flags=re.I)


def _domain(address: str) -> str:
    return address.rsplit("@", 1)[-1].strip().casefold() if "@" in address else ""


def preflight(subject: str, body: str, *, from_address: str | None = None, html: str = "") -> list[str]:
    """Blocking deliverability issues (empty list = ready for human review)."""
    issues = []
    address = from_address or sender()
    if _domain(address) in FREE_MAILBOXES or not _domain(address):
        issues.append("Lähettäjä on ilmainen postilaatikko: lähetä Kaurivon omasta verkkotunnuksesta "
                      "(hello@kaurivo.com), jolle on SPF, DKIM ja DMARC.")
    links = URL.findall(body) + URL.findall(html)
    for link in links:
        host = re.sub(r"^https?://", "", link).split("/")[0].casefold()
        if any(host == h or host.endswith("." + h) for h in SHARED_HOSTS):
            issues.append(f"Linkki jaetussa ilmaispalvelussa ({host}): käytä omaa verkkotunnusta.")
    if len(set(links)) > 2:
        issues.append("Liikaa linkkejä: enintään kaksi (demo ja tarvittaessa yksi muu).")
    if re.search(r"<img\b", html, re.I):
        issues.append("Ei kuvia eikä seurantapikseleitä ensimmäisessä viestissä.")
    words = len(re.findall(r"\w+", body))
    if not 40 <= words <= 170:
        issues.append(f"Pituus {words} sanaa: pidä viesti 40–170 sanassa.")
    lowered = (subject + " " + body).casefold()
    hits = [w for w in SPAMMY if w in lowered]
    if hits:
        issues.append("Roskapostin tunnussanoja: " + ", ".join(hits) + ".")
    if re.search(r"\b[A-ZÅÄÖ]{5,}\b", subject + " " + body):
        issues.append("Ei isoilla kirjaimilla huutamista.")
    if body.count("!") > 1 or "!" in subject:
        issues.append("Enintään yksi huutomerkki, ei otsikossa.")
    if not subject.strip() or len(subject) > 60:
        issues.append("Otsikko 1–60 merkkiä.")
    if not OPT_OUT.search(body + " " + html):
        issues.append("Viestistä puuttuu maksuton tapa kieltäytyä jatkoviesteistä (laki vaatii joka viestiin).")
    return issues


def daily_cap(first_send: date | None, today: date | None = None) -> int:
    """How many sales emails may go out today (0 at weekends)."""
    today = today or date.today()
    if today.weekday() >= 5:
        return 0
    if first_send is None:
        return RAMP[0]
    week = max(0, (today - first_send).days // 7)
    return RAMP[min(week, len(RAMP) - 1)]


def within_office_hours(moment: datetime) -> bool:
    """Finnish weekday office hours (local time 8-16)."""
    return moment.weekday() < 5 and 8 <= moment.hour < 16


def dns_records(domain: str, *, mailbox: str = "zoho_eu", demo_target: str = "kaurivo-auto-demos-2026.onrender.com"):
    """DNS records to add at the registrar (DKIM value comes from the mail provider)."""
    domain = domain.strip().strip(".").casefold()
    records = []
    if mailbox == "zoho_eu":
        records += [("MX", domain, "mx.zoho.eu", 10), ("MX", domain, "mx2.zoho.eu", 20),
                    ("MX", domain, "mx3.zoho.eu", 50),
                    ("TXT", domain, "v=spf1 include:zohomail.eu ~all", None),
                    ("TXT", f"zmail._domainkey.{domain}", "<DKIM-arvo Zohon hallintapaneelista>", None)]
    records += [("TXT", f"_dmarc.{domain}", f"v=DMARC1; p=none; rua=mailto:dmarc@{domain}; adkim=r; aspf=r", None),
                ("CNAME", f"demo.{domain}", demo_target, None)]
    return records
