"""
Verkkosivujen kuvakaappausten ottaminen.

Käyttää Playwrightia.

Ottaa:
- desktop-kuvakaappauksen
- mobiilikuvasivun

Tämä moduuli ei käytä OpenRouteria eikä Tavilyä.
"""

import os

from playwright.sync_api import sync_playwright


OUTPUT_DIR = "output/screenshots"


def _safe_filename(name: str) -> str:
    """
    Muuttaa yrityksen nimen turvalliseksi tiedostonimeksi.
    """

    value = (name or "website").strip()

    safe = "".join(
        character
        if character.isalnum() or character in "-_"
        else "_"
        for character in value
    )

    safe = safe.strip("_")

    return safe or "website"


def capture_website(
    url: str,
    company_name: str,
) -> dict | None:
    """
    Ottaa desktop- ja mobiilikuvakaappaukset.

    Palauttaa polut molempiin kuviin.
    """

    if not url:
        return None

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    filename = _safe_filename(
        company_name
    )

    desktop_path = os.path.join(
        OUTPUT_DIR,
        f"{filename}_desktop.png",
    )

    mobile_path = os.path.join(
        OUTPUT_DIR,
        f"{filename}_mobile.png",
    )

    print(
        f"  [screenshot] Avataan: {url}"
    )

    try:
        with sync_playwright() as playwright:

            browser = playwright.chromium.launch(
                headless=True,
            )

            # ==================================================
            # DESKTOP
            # ==================================================

            desktop = browser.new_page(
                viewport={
                    "width": 1440,
                    "height": 900,
                },
                device_scale_factor=1,
            )

            try:
                desktop.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )

                desktop.wait_for_timeout(
                    2000
                )

                desktop.screenshot(
                    path=desktop_path,
                    full_page=True,
                )

                print(
                    "  [screenshot] Desktop: OK"
                )

            except Exception as e:
                print(
                    f"  [screenshot] Desktop "
                    f"epäonnistui: {e}"
                )

                desktop_path = ""

            finally:
                desktop.close()

            # ==================================================
            # MOBILE
            # ==================================================

            mobile = browser.new_page(
                viewport={
                    "width": 390,
                    "height": 844,
                },
                device_scale_factor=1,
                is_mobile=True,
                has_touch=True,
            )

            try:
                mobile.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )

                mobile.wait_for_timeout(
                    2000
                )

                mobile.screenshot(
                    path=mobile_path,
                    full_page=True,
                )

                print(
                    "  [screenshot] Mobiili: OK"
                )

            except Exception as e:
                print(
                    f"  [screenshot] Mobiili "
                    f"epäonnistui: {e}"
                )

                mobile_path = ""

            finally:
                mobile.close()

            browser.close()

    except Exception as e:
        print(
            f"  [screenshot] Playwright "
            f"epäonnistui: {e}"
        )

        return None

    if not desktop_path and not mobile_path:
        return None

    return {
        "desktop": desktop_path,
        "mobile": mobile_path,
    }
