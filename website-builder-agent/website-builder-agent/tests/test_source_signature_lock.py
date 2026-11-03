"""Regressions: original multi-page visual identity cannot disappear silently.

No company names, real images, paid APIs or self-rated design quality.
"""
import unittest

from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest
from utils.source_identity import extract_source_identity
from utils.source_signature_lock import (
    audit_source_signature_lock, signature_from_source,
)


def original():
    host = "https://atelier.example"
    home = {
        "url": host+"/",
        "source_identity": {
            "original_logo_candidates": [host+"/media/official-logo.png"],
            "original_content_photos": [
                {"src": host+"/media/workshop.jpg", "role": "unclassified", "alt": "Workshop"}
            ],
            "source_experience": {"observed_videos": 1},
        },
    }
    team = {
        "url": host+"/team/",
        "source_identity": {
            "original_content_photos": [
                {"src": host+"/media/alex.jpg", "role": "staff_portrait", "alt": "Alex"},
                {"src": host+"/media/mira.jpg", "role": "staff_portrait", "alt": "Mira"},
            ],
        },
    }
    gallery = {
        "url": host+"/gallery/",
        "source_identity": {"original_content_photos": [
            {"src": host+f"/media/project-{n}.jpg", "role": "gallery_photo"}
            for n in range(1, 6)
        ]},
    }
    return {"source_inventory":{"pages":[home,team,gallery]}}


def page(content):
    return ("<!doctype html><html lang='fi'><body>"
            "<header><img src='https://atelier.example/media/official-logo.png' alt='official logo'></header>"
            "<main><h1>Crafted furniture</h1>"+content+"</main></body></html>")


def pages():
    h="https://atelier.example/media/"
    return {
        "index.html":page(
            f'<video controls src="{h}workshop.mp4"></video>'
            f'<img src="{h}workshop.jpg" alt="Wood workshop">'
        ),
        "team/index.html":page(
            f'<img src="{h}alex.jpg" alt="Alex">'
            f'<img src="{h}mira.jpg" alt="Mira">'
        ),
        "gallery/index.html":page("".join(
            f'<img src="{h}project-{n}.jpg" alt="Project {n}">'
            for n in range(1, 6)
        )),
    }


def kinds(report):
    return {item["kind"] for item in report["blocking"]}


class SourceSignatureLockTests(unittest.TestCase):
    def test_source_roles_are_grounded_in_actual_image_ancestors(self):
        html = """<main><div class="team-member"><img src="/people/mira.jpg" alt="Mira"></div>
          <div class="portfolio-gallery"><img src="/work/desk.jpg" alt="desk"></div>
          <img src="/decor.jpg" alt="decorative background"></main>"""
        source=extract_source_identity(html,"https://atelier.example/")
        roles={row["src"].split("/")[-1]:row["role"]
               for row in source["original_content_photos"]}
        self.assertEqual(roles["mira.jpg"],"staff_portrait")
        self.assertEqual(roles["desk.jpg"],"gallery_photo")
        self.assertEqual(roles["decor.jpg"],"unclassified")

    def test_correct_multiroute_site_does_not_lose_original_media(self):
        report=audit_source_signature_lock(pages(), original())
        self.assertFalse(report["blocking"],report)
        self.assertTrue(report["pending"])

    def test_plain_text_brand_is_not_original_logo(self):
        p=pages()
        p["index.html"]=p["index.html"].replace(
            '<img src="https://atelier.example/media/official-logo.png" alt="official logo">',
            '<strong>Atelier</strong>')
        result=audit_source_signature_lock(p,original())
        self.assertIn("source_logo_lost",kinds(result))
        self.assertTrue(any(x.get("route")=="index.html" for x in result["blocking"]))

    def test_team_text_cards_do_not_replace_source_people(self):
        p=pages()
        p["team/index.html"]=page("<article><h2>Alex</h2><p>Founder</p></article>"
                                   "<article><h2>Mira</h2><p>Owner</p></article>")
        result=audit_source_signature_lock(p,original())
        self.assertIn("staff_portrait_lost",kinds(result))
        self.assertEqual(sum(x["kind"]=="staff_portrait_lost" for x in result["blocking"]),2)

    def test_sparse_gallery_and_old_site_link_cannot_pass(self):
        p=pages()
        p["gallery/index.html"]=page(
            "<img src='https://atelier.example/media/project-1.jpg'>"
            "<a href='https://atelier.example/gallery/'>See all work on old site</a>")
        result=audit_source_signature_lock(p,original())
        self.assertEqual(sum(x["kind"]=="original_gallery_photo_lost" for x in result["blocking"]),4)

    def test_video_lost_even_if_other_scripts_exist(self):
        p=pages()
        p["index.html"]=page('<img src="https://atelier.example/media/workshop.jpg">'
                             '<script src="assets/main.js"></script>')
        result=audit_source_signature_lock(p,original())
        self.assertIn("source_video_lost",kinds(result))

    def test_customer_exception_requires_exact_original_source_and_build(self):
        research=original()
        p=pages()
        p["team/index.html"]=p["team/index.html"].replace(
            '<img src="https://atelier.example/media/mira.jpg" alt="Mira">',"")
        source_hash=source_inventory_sha256(research["source_inventory"])
        build_hash=site_digest(p)
        research["source_signature_exceptions"]=[{
            "kind":"staff_portrait","original":"https://atelier.example/media/mira.jpg",
            "source_sha256":source_hash,"build_sha256":build_hash,
            "reviewer_kind":"client","approved":True,"reviewer":"Owner",
            "checked_at":"2026-11-04","reason":"Owner requests a portrait-free public profile."
        }]
        self.assertNotIn("staff_portrait_lost",kinds(audit_source_signature_lock(p,research)))
        p["team/index.html"]+=" "
        self.assertIn("staff_portrait_lost",kinds(audit_source_signature_lock(p,research)))

    def test_no_website_cannot_invent_identity(self):
        report=audit_source_signature_lock({"index.html":page("Hello")},
                                           {"research_mode":"verified_no_website"})
        self.assertFalse(report["blocking"])
        self.assertFalse(report["pending"])

    def test_missing_observations_stay_review_required_not_fake_green(self):
        research={"source_inventory":{"pages":[{"url":"https://atelier.example/"}]}}
        report=audit_source_signature_lock(pages(),research)
        self.assertFalse(report["blocking"])
        self.assertTrue(any("lack identity" in s for s in report["pending"]))

    def test_source_rgb_image_richness_is_preserved(self):
        research={"source_inventory":{"pages":[{
            "url":"https://atelier.example/",
            "source_identity":{"original_content_photos":[
                {"src":f"https://atelier.example/p{i}.jpg"}
                for i in range(10)
            ]}
        }]}}
        report=audit_source_signature_lock({"index.html":page(
            '<img src="https://atelier.example/p0.jpg">')},research)
        self.assertIn("original_photographic_depth_lost",kinds(report))

    def test_browser_observed_video_counts_if_html_source_misses_it(self):
        research=original()
        research["source_inventory"]["pages"][0]["source_identity"]["source_experience"]["observed_videos"]=0
        research["original_experience_profile"]={
            "capture_method":"browser",
            "source_sha256":source_inventory_sha256(research["source_inventory"]),
            "features":{"video":{"present":True,"source_url":"https://atelier.example/",
                                 "observation":"Video verified on loaded page"}},
        }
        source=signature_from_source(research)
        self.assertEqual(source["video_pages"],["https://atelier.example/"])


if __name__=="__main__":
    unittest.main()
