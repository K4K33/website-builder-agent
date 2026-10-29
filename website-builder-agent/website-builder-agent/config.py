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

# Default remains the existing cloud client to avoid breaking older projects.
# Kaurivo can opt into local inference WITHOUT touching OAVIR's OpenRouter credits.
# FREE_ONLY forbids OpenRouter calls, including accidentally selected paid models.
def ai_backend():
    mode = os.getenv("AI_BACKEND", "openrouter").strip().lower()
    if mode not in {"openrouter", "ollama"}:
        raise RuntimeError("AI_BACKEND must be 'openrouter' or 'ollama'.")
    if os.getenv("FREE_ONLY", "").strip().lower() in {"1", "true", "yes"} and mode != "ollama":
        raise RuntimeError("FREE_ONLY requires AI_BACKEND=ollama; no cloud AI requests permitted.")
    return mode


# Each stage has an explicit model; Builder and visual QA cannot silently use
# a random free router. Set exact provider model IDs after choosing the model.
def model_for_stage(stage=None):
    if ai_backend() == "ollama":
        # Keep local and cloud model configurations distinct: never interpret an
        # OpenRouter model ID as a local model name.
        stage_key = f"OLLAMA_{stage.upper()}_MODEL" if stage else ""
        model = (os.getenv(stage_key, "").strip() if stage_key else "")
        model = model or os.getenv("OLLAMA_MODEL", "").strip()
        if not model or (stage in {"builder", "qa"} and not os.getenv(stage_key, "").strip()):
            raise RuntimeError(
                f"Configure a locally installed Ollama model for stage {stage or 'default'}; "
                "Builder and visual QA need explicit OLLAMA_BUILDER_MODEL / OLLAMA_QA_MODEL."
            )
        if model.lower().endswith(":cloud"):
            raise RuntimeError("Ollama cloud models are disabled; local-only inference required.")
        return model
    model = os.getenv(f"{stage.upper()}_MODEL", "").strip() if stage else ""
    model = model or OPENROUTER_MODEL
    if stage in {"builder", "qa"} and (model == "openrouter/free" or model.endswith(":free")):
        raise RuntimeError(
            f"Aseta {stage.upper()}_MODEL laadukkaaksi, täsmälliseksi malliksi. "
            "Rakentaja ja visuaalinen QA eivät käytä vaihtuvaa ilmaismallia."
        )
    return model


BUILDER_MAX_TOKENS = int(os.getenv("BUILDER_MAX_TOKENS", "16000"))
AI_MAX_OUTPUT_TOKENS = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "24000"))
QA_MIN_VISUAL_SCORE = int(os.getenv("QA_MIN_VISUAL_SCORE", "85"))
if not 0 <= QA_MIN_VISUAL_SCORE <= 100:
    raise ValueError("QA_MIN_VISUAL_SCORE pitää olla välillä 0–100")


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

if not OPENROUTER_API_KEY and ai_backend() == "openrouter":
    print(
        "[VAROITUS] OPENROUTER_API_KEY puuttuu. "
        "Lisää se GitHub Secretiksi nimellä OPENROUTER_API_KEY "
        "tai paikalliseen .env-tiedostoon."
    )
