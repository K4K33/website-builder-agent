"""
Keskitetty konfiguraatio Website Builder Agentille.

Salaisuuksia ei kovakoodata tähän tiedostoon.
GitHub Actionsissa arvot tulevat GitHub Secrets -ympäristömuuttujista.
Paikallisesti niitä voidaan lukea .env-tiedostosta.
"""

import os
from dotenv import load_dotenv


# Lataa mahdollisen paikallisen .env-tiedoston.
load_dotenv()


# ============================================================
# AI / OpenRouter
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# OpenRouterin ilmaisten mallien reititin.
# Tämän voi myöhemmin vaihtaa tiettyyn malliin ilman
# että muiden agenttien koodia tarvitsee muuttaa.
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free",
)


# ============================================================
# Agentin asetukset
# ============================================================

SCOUT_MAX_RESULTS = int(
    os.getenv("SCOUT_MAX_RESULTS", "10")
)

REQUEST_DELAY = float(
    os.getenv("REQUEST_DELAY", "1.0")
)


# ============================================================
# Kansiot ja tiedostot
# ============================================================

DATA_DIR = "data"
OUTPUT_DIR = "output"

COMPANIES_FILE = os.path.join(
    DATA_DIR,
    "companies.json",
)


# ============================================================
# Yrityksen etenemisvaiheet
# ============================================================

STATUS_FLOW = [
    "found",               # scout löysi
    "researched",          # research-agentti analysoinut
    "built",               # sivusto rakennettu
    "qa_passed",            # QA-agentti hyväksynyt
    "approved",             # käyttäjä hyväksynyt esikatselun
    "outreach_drafted",     # sähköpostiluonnos tehty
    "outreach_approved",    # käyttäjä hyväksynyt sähköpostin
]


# ============================================================
# Käynnistyksen tarkistus
# ============================================================

if not OPENROUTER_API_KEY:
    print(
        "[VAROITUS] OPENROUTER_API_KEY puuttuu. "
        "Lisää se GitHub Secretiksi nimellä OPENROUTER_API_KEY "
        "tai paikalliseen .env-tiedostoon."
    )
