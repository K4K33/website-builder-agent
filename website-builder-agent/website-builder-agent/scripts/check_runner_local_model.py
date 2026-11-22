"""CI check: the runner's open model writes a usable sales plan (no private data).

Uses an invented Finnish company text, the real CONTENT_BRIEF and the real
verify_plan, and prints only timings and which plan fields survived.
"""
import os
import sys
import time

from utils import runner_local_model as local
from utils.sales_demo import CONTENT_BRIEF
from utils.sales_demo_pipeline import verify_plan

SOURCE = (
    "Testimaalaus Esimerkki Oy. Teemme sisä- ja ulkomaalaukset, tapetoinnit ja tasoitustyöt "
    "pääkaupunkiseudulla. Kokemusta meillä on vuodesta 2009. Kaikki työt tehdään suojaten huolellisesti "
    "ja siivoten työmaa päivittäin. Talon ulkomaalaus sisältää pesun, kaavinnan, pohjamaalauksen ja kaksi "
    "pintamaalikerrosta. Annamme kirjallisen tarjouksen maksutta. Kotitalousvähennys koskee työn osuutta. "
    "Yhteystiedot: puh. 040 000 0000, info@example.fi. Palvelemme arkisin 7-16."
)


def main() -> int:
    os.environ.setdefault("GITHUB_ACTIONS", "true")
    started = time.monotonic()
    model = local.ensure()
    print("local model ready:", bool(model), model, "%.0fs" % (time.monotonic() - started))
    if not model:
        return 1
    prompt = ("Company: Testimaalaus Esimerkki Oy\nPhotos provided: 0\n"
              "Verified source text (the ONLY allowed facts):\n<<<\n" + SOURCE + "\n>>>")
    started = time.monotonic()
    plan = local.ask_json(CONTENT_BRIEF, prompt, max_tokens=4000, model=model)
    print("plan written: %.0fs" % (time.monotonic() - started))
    print("plan keys:", sorted(plan) if isinstance(plan, dict) else type(plan).__name__)
    try:
        kept, dropped = verify_plan(plan, SOURCE)
    except Exception as exc:  # report, the demo pipeline would hold the job
        print("verify_plan blocked:", type(exc).__name__, str(exc)[:120])
        return 1
    print("kept fields:", sorted(k for k, v in kept.items() if v))
    print("dropped claims:", len(dropped))
    print("headline:", str(kept.get("headline", ""))[:140])
    return 0


if __name__ == "__main__":
    sys.exit(main())
