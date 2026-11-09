"""Reusable public-browser release proof for ANY Kaurivo multi-route website.

Intended for a manual post-deploy GitHub Actions run, not a predeploy unit test.
Produces a machine-readable report plus screenshot SHA256 for every route at
mobile and desktop. Never sets ci_verified_by_owner=True. The owner must inspect
the evidence and then separately approve it; lack of that approval is HOLD.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from utils.site_integrity import site_sha256


def verify_https_url(url: str) -> str:
    parsed = urlsplit(url)
    hostname = parsed.hostname or ""
    if (parsed.scheme != "https" or not hostname or parsed.username is not None
            or parsed.password is not None or hostname in ("localhost", "localhost.localdomain")
            or hostname.endswith((".local", ".internal", ".invalid", ".test"))
            or parsed.query or parsed.fragment):
        raise ValueError("Use a plain actual public HTTPS URL with no credentials or query.")
    try:
        ip = ipaddress.ip_address(hostname)
        if not ip.is_global:
            raise ValueError("Private/loopback/metadata host not permitted for public QA.")
    except ValueError as err:
        if "not permitted" in str(err):
            raise
    return url.rstrip("/")


def site_routes(site_root: Path):
    root = site_root.resolve()
    routes = sorted({str(p.relative_to(root)) for p in root.rglob("index.html")
                     if p.is_file() and not p.is_symlink()
                     and not any(part.startswith("_") or part.startswith(".")
                                 for part in p.relative_to(root).parts)})
    if "index.html" not in routes:
        raise ValueError("Source site must have a home index.html")
    if not 1 <= len(routes) <= 50:
        raise ValueError("Unexpected number of client-visible routes.")
    return routes


def _html_url(origin: str, route: str):
    return origin + "/" + route[:-len("index.html")]


def run(*, url: str, root: Path, release_marker: str, output: Path, commit: str):
    url = verify_https_url(url)
    if len(release_marker) < 10 or not commit or len(commit) != 40:
        raise ValueError("Provide an exact release marker and 40-digit source commit SHA.")
    root = root.resolve()
    routes = site_routes(root)
    digest = site_sha256(root, routes)
    output.mkdir(parents=True, exist_ok=True)
    ci_url = None
    if all(os.environ.get(k) for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID")):
        ci_url = "/".join([os.environ["GITHUB_SERVER_URL"].rstrip("/"),
                          os.environ["GITHUB_REPOSITORY"], "actions", "runs",
                          os.environ["GITHUB_RUN_ID"]])
    report = {
        "url": url + "/", "site_sha256": digest, "commit_sha": commit,
        "release_marker": release_marker,
        "ci_run_url": ci_url, "ci_verified_by_owner": False,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "pages": [], "errors": [], "warnings": []
    }
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for viewport in (390, 1440):
            context = browser.new_context(viewport={"width":viewport,"height":840},
                                          device_scale_factor=1)
            page = context.new_page()
            for route in routes:
                page_errors, bad_resources = [], []
                def onerror(error):
                    page_errors.append(str(error)[:240])
                def onresponse(resp):
                    if resp.status >= 400 and resp.request.resource_type in (
                        "stylesheet","script","image","font"):
                        bad_resources.append(f"{resp.status} {resp.url[:180]}")
                page.on("pageerror", onerror)
                page.on("response", onresponse)
                item = {"route":route, "viewport":str(viewport)}
                try:
                    response = page.goto(_html_url(url,route),wait_until="load",
                                         timeout=45000)
                    page.wait_for_timeout(650)
                    metrics = page.evaluate("""() => {
                      const body=getComputedStyle(document.body);
                      const header=document.querySelector('header');
                      const title=document.querySelector('main h1');
                      const logo=header?.querySelector('img');
                      const nav=header?.querySelector('nav');
                      const view=(e)=>e?e.getBoundingClientRect():null;
                      const logoBox=view(logo), headBox=view(header);
                      const broken=Array.from(document.images).filter(
                        image=>image.complete && image.naturalWidth===0);
                      return {
                        marker:document.documentElement.getAttribute('data-kaurivo-release'),
                        h1:document.querySelectorAll('main h1').length,
                        stylesheetCount:document.styleSheets.length,
                        font:body.fontFamily,
                        background:body.backgroundColor,
                        logoWidth:logoBox?.width||0,
                        headerWidth:headBox?.width||0,
                        brandText:(header?.innerText||'').trim().length,
                        navCount:nav?.querySelectorAll('a').length||0,
                        overflow:document.documentElement.scrollWidth>innerWidth+2,
                        brokenImages:broken.length,
                        brokenSources:broken.map(i=>i.currentSrc||i.src).slice(0,5),
                        titleVisible:!!title && view(title).height>12,
                        pageWidth:innerWidth
                      };
                    }""")
                    status=response.status if response else None
                    computed = (metrics["stylesheetCount"]>0
                        and metrics["font"].strip().lower() not in
                        ('"times new roman"', 'times new roman', 'serif')
                        and metrics["titleVisible"])
                    nav_valid=metrics["navCount"] >= 1
                    # Explicit mobile menu activation, when component exists.
                    if viewport == 390 and page.locator("[data-menu]").count():
                        toggle=page.locator("[data-menu]").first
                        toggle.click(timeout=4000)
                        nav_valid=nav_valid and (
                            page.locator("[data-nav]").count()>0
                            and page.locator("[data-nav]").first.evaluate(
                                "(e)=>e.classList.contains('open') || "
                                "getComputedStyle(e).visibility==='visible' && "
                                "getComputedStyle(e).display!=='none'"))
                        toggle.click(timeout=4000)
                    has_brand=(metrics["brandText"]>2
                        and metrics["headerWidth"]>60
                        and metrics["logoWidth"] <= viewport*.65)
                    screenshot=output / f"public-{viewport}-{route.replace('/','_')}.png"
                    page.screenshot(path=str(screenshot),full_page=True,
                                    animations="disabled",timeout=25000)
                    item.update({
                        "status": status, "release_marker": metrics["marker"],
                        "computed_styles_valid":computed,
                        "scripts_valid":not page_errors and not bad_resources,
                        "navigation_valid":nav_valid,
                        "responsive_valid":not metrics["overflow"],
                        "visible_brand_valid":has_brand,
                        "broken_images":metrics["brokenImages"],
                        "page_errors":page_errors+bad_resources,
                        "screenshot_sha256":hashlib.sha256(screenshot.read_bytes()).hexdigest(),
                        "metrics":metrics
                    })
                except Exception as error:
                    item.update({"status":None,"release_marker":None,
                        "computed_styles_valid":False,"scripts_valid":False,
                        "navigation_valid":False,"responsive_valid":False,
                        "visible_brand_valid":False,"broken_images":-1,
                        "page_errors":[f"{type(error).__name__}: {str(error)[:250]}"],
                        "screenshot_sha256":None})
                if (item.get("status") != 200 or item.get("release_marker") != release_marker
                    or not all(item.get(k) is True for k in
                        ("computed_styles_valid","scripts_valid",
                         "navigation_valid","responsive_valid","visible_brand_valid"))
                    or item.get("broken_images") != 0 or item.get("page_errors") != []):
                    report["errors"].append(f"{route} @ {viewport}px: live page failed CSS, JS, logo, media, route, markup or version proof.")
                report["pages"].append(item)
                page.remove_listener("pageerror", onerror)
                page.remove_listener("response", onresponse)
            context.close()
        browser.close()
    target = output/"public-release-evidence.json"
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    from utils.release_safety import check_actual_public_website
    gate=check_actual_public_website(
        {**report,"ci_verified_by_owner":True,
         "ci_run_url":ci_url or "https://github.com/manual-review-required"},
        site_digest=digest,routes=set(routes),build_commit=commit)
    # Human approval remains False in actual artifact. This validation only
    # tests structurally whether that proof COULD pass after human review.
    print("PUBLIC_RELEASE_BROWSER",json.dumps({
      "routes":len(routes),"viewports":2,"captures":len(report["pages"]),
      "issues":gate["issues"],"owner_review_required":True,
      "report":str(target)},ensure_ascii=False))
    return 1 if report["errors"] or gate["issues"] else 0


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--url",required=True)
    parser.add_argument("--site-root",required=True)
    parser.add_argument("--release-marker",required=True)
    parser.add_argument("--commit-sha",default=os.environ.get("GITHUB_SHA",""))
    parser.add_argument("--out",default="output/public-release-evidence")
    args=parser.parse_args(argv)
    return run(url=args.url,root=Path(args.site_root),
               release_marker=args.release_marker,
               output=Path(args.out),commit=args.commit_sha)


if __name__=="__main__":
    sys.exit(main())
