"""V7 first-morning owner-study: independent browser and provenance regressions.

This suite proves what a test browser renders and what public-source fields
are present. It does NOT award a 9.5/10 grade, grant photo rights, prove that
the original domain lacks a website or authorize client outreach.
"""
from __future__ import annotations

import copy
from pathlib import Path
import json
import os
from unittest import TestCase

from scripts.audit_changed_owner_previews import check_source_limited_concept

ROOT=Path(__file__).resolve().parents[1]
SLUG="oskar-haglund-v7"
SITE=ROOT/"docs"/"kaurivo"/"owner-previews"/SLUG
MANIFEST=ROOT/"data"/"owner_previews"/(SLUG+".json")
ROUTES=("index.html","tjanster/index.html","kontakt/index.html")
VIEWPORTS=(320,390,768,1440)


class SourceBoundFirstMorningPreview(TestCase):
    def test_two_independent_business_sources_and_all_routes_pass_release_gate(self):
        data=json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["research_mode"],"official_site_inaccessible_registry_concept")
        self.assertEqual(data["company_name"],"Ab Oskar Haglund Oy")
        self.assertFalse(data["outreach_authorized"])
        self.assertFalse(data["client_approved"])
        self.assertIsNone(data["independent_quality_score"])
        self.assertEqual(sorted(data["release_routes"]),sorted(ROUTES))
        self.assertEqual(check_source_limited_concept(SLUG,data,SITE),[])

    def test_missing_original_brand_or_fake_approval_never_publishes(self):
        valid=json.loads(MANIFEST.read_text(encoding="utf-8"))
        for field,value in (
            ("client_approved",True),
            ("outreach_authorized",True),
            ("independent_quality_score",9.5),
            ("brand_verification","verified"),
            ("photos_verified_for_reuse",True),
            ("official_site_access","verified_present"),
            ("marketing_eligible",True),
        ):
            bad=copy.deepcopy(valid)
            bad[field]=value
            with self.subTest(field=field):
                self.assertNotEqual(check_source_limited_concept(SLUG,bad,SITE),[])

    def test_missing_public_source_never_publishes(self):
        data=json.loads(MANIFEST.read_text(encoding="utf-8"))
        data["source_pages"]=[data["source_pages"][0]]
        self.assertNotEqual(check_source_limited_concept(SLUG,data,SITE),[])
        data["source_pages"]=["https://same.example/a","https://same.example/b"]
        self.assertNotEqual(check_source_limited_concept(SLUG,data,SITE),[])

    def test_historical_transport_category_conflict_blocks_unverified_current_services(self):
        valid=json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(valid["historical_service_conflict"]["status"],
                         "conflicting_historic_industry_evidence")
        self.assertFalse(valid["registry_as_current_service"])
        self.assertEqual(valid["verified_facts"]["services"],[])
        for mut in (
            lambda obj: obj.update(registry_as_current_service=True),
            lambda obj: obj["historical_service_conflict"].update(
                independently_current_services_verified=True),
            lambda obj: obj["verified_facts"].update(
                services=["International freight with dedicated trucks"]),
            lambda obj: obj["historical_service_conflict"].update(
                historical_sources=[]),
        ):
            bad=copy.deepcopy(valid)
            mut(bad)
            self.assertTrue(check_source_limited_concept(SLUG,bad,SITE))

    def test_no_specific_cargo_inquiry_from_registration_or_historical_bus_catalogue(self):
        from bs4 import BeautifulSoup
        for route in ROUTES:
            content=(SITE/route).read_text(encoding="utf-8")
            soup=BeautifulSoup(content,"html.parser")
            visible=soup.get_text(" ",strip=True).casefold()
            for unproven in (
                "transportförfrågan","kuljetustiedustelu","avhämtningsort",
                "noutopaikka","god(s)","tavara / arvioitu","tilaa kuljetus",
                "vuoroliikennettä","tillgänglig lastbil"
            ):
                self.assertNotIn(unproven,visible,route)
            self.assertFalse(soup.select("img[src*=company]"))

    def test_no_client_image_or_made_up_review_is_embedded(self):
        from bs4 import BeautifulSoup
        for route in ROUTES:
            soup=BeautifulSoup((SITE/route).read_text(encoding="utf-8"),"html.parser")
            self.assertFalse(soup.select("img"),route)
            self.assertEqual(len(soup.select("main h1")),1)
            self.assertTrue(soup.select_one("meta[name=robots][content*=noindex]"))
            self.assertIn("Ei yrityksen virallinen sivu",soup.get_text(" ",strip=True))
            self.assertIn("Ab Oskar Haglund Oy",soup.title.get_text(" ",strip=True))
            self.assertTrue(soup.select_one('a[href="tel:+35863153027"]'))
            self.assertTrue(soup.select_one('a[href="mailto:info@oskarhaglund.fi"]'))


class RealBrowserFirstMorningPreview(TestCase):
    def test_all_routes_in_chromium_desktop_tablet_and_two_mobiles(self):
        from playwright.sync_api import sync_playwright
        output=ROOT/"output"/"oskar-haglund-v7-browser-evidence"
        output.mkdir(parents=True,exist_ok=True)
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True)
            try:
                for viewport in VIEWPORTS:
                    context=browser.new_context(
                        viewport={"width":viewport,"height":850 if viewport>800 else 760},
                        device_scale_factor=1,
                        reduced_motion="reduce",
                        color_scheme="light",
                    )
                    page=context.new_page()
                    errors=[]
                    page.on("pageerror",lambda error:errors.append(str(error)))
                    for route in ROUTES:
                        with self.subTest(viewport=viewport,route=route):
                            page.goto((SITE/route).resolve().as_uri(),wait_until="load")
                            page.wait_for_timeout(80)
                            self.assertEqual(page.locator("main h1").count(),1)
                            self.assertTrue(page.locator("main h1").is_visible())
                            self.assertTrue(page.locator(".demo-band b").is_visible())
                            self.assertEqual(page.locator("html").get_attribute("lang"),"sv")
                            page.screenshot(
                                path=str(output/(route.replace("/","-").replace(".html","")+"-"+str(viewport)+".png")),
                                full_page=True,
                                animations="disabled",
                            )
                            overflow=page.evaluate(
                                "Math.max(document.body.scrollWidth,document.documentElement.scrollWidth)-window.innerWidth"
                            )
                            offenders=page.evaluate("""() => [...document.querySelectorAll('body *')]
                              .map(el=>({name:el.tagName.toLowerCase(),cls:String(el.className?.baseVal??el.className??'').slice(0,65),
                                right:Math.round(el.getBoundingClientRect().right),width:Math.round(el.getBoundingClientRect().width)}))
                              .filter(o=>o.right>window.innerWidth+2).slice(0,12)""")
                            self.assertLessEqual(overflow,2,f"{route} width={viewport} overflow={overflow}; offenders={offenders}")
                            self.assertGreater(page.locator("main").bounding_box()["height"],220)
                            self.assertTrue(page.locator("a[href^='tel:']").count() >= 1)
                            self.assertTrue(page.locator("a[href^='mailto:']").count() >= 1)
                            page.locator('button[data-set-lang="fi"]').click()
                            self.assertEqual(page.locator("html").get_attribute("lang"),"fi")
                            self.assertIn("Ab Oskar Haglund Oy",page.title())
                            self.assertTrue(page.locator('button[data-set-lang="fi"]').get_attribute("aria-pressed")=="true")
                            page.locator('button[data-set-lang="sv"]').click()
                            self.assertEqual(page.locator("html").get_attribute("lang"),"sv")
                            if viewport<=820:
                                toggle=page.locator("[data-menu-toggle]")
                                self.assertTrue(toggle.is_visible())
                                toggle.click()
                                self.assertFalse(page.locator("[data-mobile-drawer]").is_hidden())
                                self.assertEqual(toggle.get_attribute("aria-expanded"),"true")
                                page.keyboard.press("Escape")
                                self.assertTrue(page.locator("[data-mobile-drawer]").is_hidden())
                            self.assertEqual(errors,[],f"{route} width={viewport}: {errors}")
                    context.close()
            finally:
                browser.close()

    def test_source_bounded_email_draft_is_unambiguously_not_a_sent_form(self):
        from bs4 import BeautifulSoup
        page=(SITE/"tjanster/index.html").read_text(encoding="utf-8")
        soup=BeautifulSoup(page,"html.parser")
        form=soup.select_one("form[data-email-builder]")
        self.assertIsNotNone(form)
        self.assertFalse(form.get("action"))
        self.assertIn("e-postutkast",form.get_text(" ",strip=True))
        script=(SITE/"assets/site.js").read_text(encoding="utf-8")
        self.assertIn("encodeURIComponent",script)
        self.assertIn("mailto:",script)
        self.assertIn("preventDefault()",script)
