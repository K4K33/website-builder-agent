"""
Keskitetty konfiguraatio. Lukee arvot .env-tiedostosta (katso .env.example).
Ei kovakoodattuja salaisuuksia tähän tiedostoon.
"""
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

SCOUT_MAX_RESULTS = int(os.getenv("SCOUT_MAX_RESULTS", "10"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))

# Kansiot
DATA_DIR = "data"
OUTPUT_DIR = "output"
COMPANIES_FILE = os.path.join(DATA_DIR, "companies.json")

# Statuspolku, jota yritys etenee agenttien läpi.
STATUS_FLOW = [
    "found",            # scout löysi
    "researched",       # research-agentti analysoinut
    "built",            # sivusto rakennettu
    "qa_passed",        # QA-agentti hyväksynyt (automaattitarkistukset)
    "approved",         # KÄYTTÄJÄ on hyväksynyt esikatselun
    "outreach_drafted",  # sähköpostiluonnos tehty
    "outreach_approved",  # KÄYTTÄJÄ hyväksynyt sähköpostin lähetettäväksi
]

if not ANTHROPIC_API_KEY:
    print(
        "[VAROITUS] ANTHROPIC_API_KEY puuttuu. Kopioi .env.example -> .env "
        "ja täytä oma API-avaimesi, muuten agentit eivät toimi."
    )
