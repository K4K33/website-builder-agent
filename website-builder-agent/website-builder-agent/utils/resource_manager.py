"""
Keskitetty resurssienhallinta OpenRouterille ja Tavilylle.

OpenRouter:
- päiväkohtainen turvallinen raja
- turvamarginaali
- käyttö nollautuu uuden UTC-päivän alussa

Tavily:
- kuukausikohtainen turvallinen raja
- käyttöä myös tasataan päivittäin
- turvamarginaali
- käyttö nollautuu uuden kuukauden alussa

Resource Manager ei itse tee verkkopyyntöjä.
"""

import calendar
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path


DATA_FILE = Path(
    os.getenv(
        "RESOURCE_USAGE_FILE",
        "data/resource_usage.json",
    )
)

OPENROUTER_DAILY_LIMIT = int(
    os.getenv(
        "OPENROUTER_DAILY_LIMIT",
        "50",
    )
)

OPENROUTER_SAFETY_MARGIN = int(
    os.getenv(
        "OPENROUTER_SAFETY_MARGIN",
        "5",
    )
)

TAVILY_MONTHLY_LIMIT = int(
    os.getenv(
        "TAVILY_MONTHLY_LIMIT",
        "1000",
    )
)

TAVILY_SAFETY_MARGIN = int(
    os.getenv(
        "TAVILY_SAFETY_MARGIN",
        "50",
    )
)


def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _month_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _empty_state() -> dict:
    return {
        "date": _today_key(),
        "month": _month_key(),
        "providers": {
            "openrouter": {
                "used_today": 0,
            },
            "tavily": {
                "used_this_month": 0,
            },
        },
    }


def _load_state() -> dict:
    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not DATA_FILE.exists():
        return _empty_state()

    try:
        with DATA_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            state = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        state = _empty_state()

    today = _today_key()
    month = _month_key()

    state.setdefault(
        "providers",
        {},
    )

    state["providers"].setdefault(
        "openrouter",
        {},
    )

    state["providers"].setdefault(
        "tavily",
        {},
    )

    if state.get("date") != today:
        state["date"] = today
        state["providers"]["openrouter"][
            "used_today"
        ] = 0

    if state.get("month") != month:
        state["month"] = month
        state["providers"]["tavily"][
            "used_this_month"
        ] = 0

    state["providers"]["openrouter"].setdefault(
        "used_today",
        0,
    )

    state["providers"]["tavily"].setdefault(
        "used_this_month",
        0,
    )

    return state


def _save_state(state: dict) -> None:
    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_file = DATA_FILE.with_suffix(
        ".tmp"
    )

    with temporary_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            state,
            file,
            indent=2,
            ensure_ascii=False,
        )

    temporary_file.replace(DATA_FILE)


def _openrouter_safe_limit() -> int:
    return max(
        0,
        OPENROUTER_DAILY_LIMIT
        - OPENROUTER_SAFETY_MARGIN,
    )


def _tavily_safe_limit() -> int:
    return max(
        0,
        TAVILY_MONTHLY_LIMIT
        - TAVILY_SAFETY_MARGIN,
    )


def _days_in_month() -> int:
    now = datetime.now(timezone.utc)

    return calendar.monthrange(
        now.year,
        now.month,
    )[1]


def _day_of_month() -> int:
    return datetime.now(timezone.utc).day


def _tavily_daily_pace() -> float:
    safe_limit = _tavily_safe_limit()
    days = _days_in_month()

    if safe_limit <= 0 or days <= 0:
        return 0.0

    return safe_limit / days


def _tavily_ideal_cumulative_usage() -> float:
    return (
        _tavily_daily_pace()
        * _day_of_month()
    )


def _tavily_paced_limit() -> int:
    """
    Kuinka paljon Tavilyä saa olla käytetty tähän
    päivään mennessä, jotta kuukausikäyttö pysyy
    tasaisena.

    Pyöristys ylöspäin mahdollistaa normaalin
    pyöristysvirheen ilman että resurssit kuluvat
    ennen kuun loppua.
    """

    safe_limit = _tavily_safe_limit()

    if safe_limit <= 0:
        return 0

    ideal = _tavily_ideal_cumulative_usage()

    return min(
        safe_limit,
        math.ceil(ideal),
    )


def status_openrouter() -> dict:
    state = _load_state()

    used = int(
        state["providers"]["openrouter"].get(
            "used_today",
            0,
        )
    )

    safe_limit = _openrouter_safe_limit()

    remaining = max(
        0,
        safe_limit - used,
    )

    if used >= safe_limit:
        state_name = "stop"
    elif used >= safe_limit * 0.8:
        state_name = "saving"
    else:
        state_name = "normal"

    return {
        "provider": "openrouter",
        "used_today": used,
        "daily_limit": OPENROUTER_DAILY_LIMIT,
        "safe_limit": safe_limit,
        "remaining_today": remaining,
        "state": state_name,
    }


def status_tavily() -> dict:
    state = _load_state()

    used = int(
        state["providers"]["tavily"].get(
            "used_this_month",
            0,
        )
    )

    safe_limit = _tavily_safe_limit()

    remaining = max(
        0,
        safe_limit - used,
    )

    daily_pace = _tavily_daily_pace()
    ideal_cumulative = _tavily_ideal_cumulative_usage()
    paced_limit = _tavily_paced_limit()

    if used >= safe_limit:
        state_name = "stop"
    elif used >= paced_limit:
        state_name = "saving"
    elif used > ideal_cumulative:
        state_name = "saving"
    else:
        state_name = "normal"

    return {
        "provider": "tavily",
        "used_this_month": used,
        "monthly_limit": TAVILY_MONTHLY_LIMIT,
        "safe_limit": safe_limit,
        "remaining_this_month": remaining,
        "daily_pace": round(
            daily_pace,
            2,
        ),
        "ideal_cumulative_usage": round(
            ideal_cumulative,
            2,
        ),
        "paced_limit_today": paced_limit,
        "state": state_name,
    }


def status(provider: str) -> dict:
    if provider == "openrouter":
        return status_openrouter()

    if provider == "tavily":
        return status_tavily()

    raise ValueError(
        f"Tuntematon resurssipalvelu: {provider}"
    )


def reserve(provider: str) -> bool:
    """
    Varaa yhden resurssin juuri ennen todellista
    API-pyyntöä.

    OpenRouter:
        yksi request = yksi käyttö

    Tavily:
        yksi reserve = yksi credit

    Palauttaa:
        True  = pyyntö saa lähteä
        False = pyyntö estetään
    """

    state = _load_state()

    if provider == "openrouter":

        safe_limit = _openrouter_safe_limit()

        used = int(
            state["providers"]["openrouter"].get(
                "used_today",
                0,
            )
        )

        if used >= safe_limit:
            print(
                "[RESOURCE] OpenRouter: "
                f"päivän turvallinen raja saavutettu "
                f"({used}/{safe_limit}) -> "
                "pyyntö estetty."
            )

            return False

        state["providers"]["openrouter"][
            "used_today"
        ] = used + 1

        _save_state(state)

        print(
            "[RESOURCE] OpenRouter: "
            f"varattu 1 request "
            f"({used + 1}/{safe_limit} tänään)"
        )

        return True

    if provider == "tavily":

        safe_limit = _tavily_safe_limit()

        used = int(
            state["providers"]["tavily"].get(
                "used_this_month",
                0,
            )
        )

        if used >= safe_limit:
            print(
                "[RESOURCE] Tavily: "
                f"kuukauden turvallinen raja saavutettu "
                f"({used}/{safe_limit}) -> "
                "pyyntö estetty."
            )

            return False

        paced_limit = _tavily_paced_limit()

        if used >= paced_limit:
            print(
                "[RESOURCE] Tavily: "
                f"päivätahti saavutettu "
                f"({used}/{paced_limit} tähän päivään "
                "mennessä) -> pyyntö estetty."
            )

            return False

        state["providers"]["tavily"][
            "used_this_month"
        ] = used + 1

        _save_state(state)

        print(
            "[RESOURCE] Tavily: "
            f"varattu 1 credit "
            f"({used + 1}/{safe_limit} tässä kuussa)"
        )

        return True

    raise ValueError(
        f"Tuntematon resurssipalvelu: {provider}"
    )


def report() -> dict:
    return {
        "openrouter": status_openrouter(),
        "tavily": status_tavily(),
    }


def print_report() -> None:
    data = report()

    print("=== RESOURCE MANAGER ===")

    openrouter = data["openrouter"]

    print(
        "openrouter: "
        f"{openrouter['used_today']}/"
        f"{openrouter['safe_limit']} käytetty tänään, "
        f"{openrouter['remaining_today']} jäljellä, "
        f"tila={openrouter['state']}"
    )

    tavily = data["tavily"]

    print(
        "tavily: "
        f"{tavily['used_this_month']}/"
        f"{tavily['safe_limit']} käytetty tässä kuussa, "
        f"{tavily['remaining_this_month']} jäljellä, "
        f"tila={tavily['state']}"
    )

    print(
        "Tavily päivätahti: "
        f"{tavily['daily_pace']} creditia/päivä"
    )

    print(
        "Tavily tavoite tähän päivään mennessä: "
        f"{tavily['ideal_cumulative_usage']} creditia"
    )

    print(
        "Tavily sallittu kumulatiivinen käyttö tänään: "
        f"{tavily['paced_limit_today']} creditia"
    )


if __name__ == "__main__":
    print_report()
