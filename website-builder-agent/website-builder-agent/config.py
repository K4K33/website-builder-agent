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

# No-billing default. A free cloud provider is allowed only when the
# exact stage model is a documented $0 OpenRouter free variant, or Tavily is
# explicitly verified as a non-billing account with a hard free-plan stop.
# A free model may be weaker than the required premium owner-preview quality.
def free_only():
    return os.getenv("FREE_ONLY", "1").strip().lower() not in {"0", "false", "no"}


def ai_backend():
    mode = os.getenv("AI_BACKEND", "ollama").strip().lower()
    if mode not in {"openrouter", "ollama"}:
        raise RuntimeError("AI_BACKEND must be 'openrouter' or 'ollama'.")
    return mode


def backend_for_stage(stage=None):
    """Optional free-tier hybrid: local Builder/QA plus free OpenRouter Research."""
    default = ai_backend()
    key = f"{stage.upper()}_AI_BACKEND" if stage else ""
    mode = os.getenv(key, default).strip().lower() if key else default
    if mode not in {"openrouter", "ollama"}:
        raise RuntimeError("Stage AI backend must be 'openrouter' or 'ollama'.")
    return mode


def is_zero_cost_openrouter_model(model: str) -> bool:
    """Never trust a bare $0 price claim or a paid model with a similar name."""
    value = str(model or "").strip().lower()
    return bool(value == "openrouter/free" or
                (value.endswith(":free") and "/" in value and
                 " " not in value and not value.startswith("/")))


def tavily_free_plan_confirmed(*, scheduled: bool = False) -> bool:
    """Operators must confirm the *account* cannot spill into paid credits.

    A local usage counter alone is not a billing guarantee if the account has
    a card or pay-as-you-go. For scheduled jobs use the separate server-side
    atomic free-credit reservation ledger.
    """
    flag = ("KAURIVO_TAVILY_FREE_PLAN_CONFIRMED" if scheduled
            else "TAVILY_FREE_PLAN_CONFIRMED")
    return free_only() and os.getenv(flag, "").strip() == "1"


# All paid OpenRouter models are forbidden in FREE_ONLY, including when a
# funded key is already present. Builder and visual QA still require exact
# model IDs so an unpredictable free router cannot silently weaken quality.
def model_for_stage(stage=None):
    if backend_for_stage(stage) == "ollama":
        stage_key = f"OLLAMA_{stage.upper()}_MODEL" if stage else ""
        model = (os.getenv(stage_key, "").strip() if stage_key else "")
        model = model or os.getenv("OLLAMA_MODEL", "").strip()
        if not model or (stage in {"builder", "qa"}
                         and not os.getenv(stage_key, "").strip()):
            raise RuntimeError(
                f"Configure a locally installed Ollama model for stage {stage or 'default'}; "
                "Builder and visual QA need explicit OLLAMA_BUILDER_MODEL / OLLAMA_QA_MODEL."
            )
        if model.lower().endswith(":cloud"):
            raise RuntimeError("Ollama cloud models are disabled; local-only inference required.")
        return model
    model = os.getenv(f"{stage.upper()}_MODEL", "").strip() if stage else ""
    model = model or OPENROUTER_MODEL
    if free_only() and not is_zero_cost_openrouter_model(model):
        raise RuntimeError(
            "FREE_ONLY forbids paid OpenRouter models. Select an exact ':free' "
            "model ID or 'openrouter/free' for non-critical research."
        )
    if stage in {"builder", "qa"} and model == "openrouter/free":
        raise RuntimeError(
            f"Set an exact model for {stage}: a changing free router cannot "
            "be trusted for deterministic Builder and visual QA."
        )
    if stage in {"builder", "qa"} and not os.getenv(f"{stage.upper()}_MODEL", "").strip():
        raise RuntimeError(
            f"Set {stage.upper()}_MODEL explicitly to a vision/code-capable model."
        )
    return model


BUILDER_MAX_TOKENS = int(os.getenv("BUILDER_MAX_TOKENS", "16000"))
AI_MAX_OUTPUT_TOKENS = int(os.getenv("AI_MAX_OUTPUT_TOKENS", "24000"))
QA_MIN_VISUAL_SCORE = int(os.getenv("QA_MIN_VISUAL_SCORE", "85"))
if not 0 <= QA_MIN_VISUAL_SCORE <= 100:
    raise ValueError("QA_MIN_VISUAL_SCORE pitää olla välillä 0–100")

# A general model QA pass (legacy 85/100) is NOT a premium owner-preview
# acceptance. The stricter 95/100 floor applies to EVERY visual dimension
# before the Builder may mark a first client review ready. External independent
# >=9.5/10 evidence and client permissions remain separate later gates.
QA_MIN_OWNER_PREVIEW_VISUAL_SCORE = int(
    os.getenv("QA_MIN_OWNER_PREVIEW_VISUAL_SCORE", "95")
)
if not 90 <= QA_MIN_OWNER_PREVIEW_VISUAL_SCORE <= 100:
    raise ValueError("QA_MIN_OWNER_PREVIEW_VISUAL_SCORE must be 90..100")


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
# Only local, explicitly supplied images can be packaged into a generated
# website. No third-party hotlinks or image downloads by the Builder.
MEDIA_INTAKE_DIR = os.getenv("KAURIVO_MEDIA_INTAKE_DIR", "media_intake")

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

if not OPENROUTER_API_KEY and any(backend_for_stage(stage) == "openrouter"
                                  for stage in ("research", "builder", "qa")):
    print(
        "[VAROITUS] OPENROUTER_API_KEY puuttuu. "
        "Lisää se GitHub Secretiksi nimellä OPENROUTER_API_KEY "
        "tai paikalliseen .env-tiedostoon."
    )
