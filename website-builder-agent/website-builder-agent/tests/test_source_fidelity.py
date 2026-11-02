"""Blind, unrelated-sector fixtures for agency-wide preservation standards."""
from __future__ import annotations
import unittest
from utils.content_parity import source_inventory_sha256
from utils.source_fidelity import audit_source_fidelity, source_manifest

def fixture():
    inventory={"pages":[
        {"url":"https://atelier.example.org/","title":"Home","text":"Services overview",
         "headings":{"h2":["Sohvien kunnostus","Kankaiden valinta"]},
         "header_assets":[{"src":"/assets/brand.svg","alt":"Original brand"}],
         "footer_assets":[{"src":"/logos/atelier-group.svg","alt":"Association",
                           "href":"https://guild.example.org/"}],
         "links":[{"href":"/palvelut","text":"Palvelut"}]},
        {"url":"https://atelier.example.org/palvelut","title":"Services",
         "text":"Sohvien kunnostus ja materiaalit",
         "headings":{"h2":["Huonekalujen verhoilu"]},"header_assets":[],
         "footer_assets":[],"links":[]},
    ]}
    digest=source_inventory_sha256(inventory)
    map_={"pages":[
        {"source_url":"https://atelier.example.org/","target":"index.html",
         "status":"retain","sections":[
           {"source_heading":"Sohvien kunnostus","target":"index.html#sohvat"},
           {"source_heading":"Kankaiden valinta","target":"index.html#kankaat"}]},
        {"source_url":"https://atelier.example.org/palvelut","target":"index.html#palvelut",
         "status":"merge","sections":[
           {"source_heading":"Huonekalujen verhoilu","target":"index.html#palvelut"}]}
    ]}
    research={"source_inventory":inventory,"source_content_map":map_}
    html="""<!doctype html><html><body><header>
      <img src="/assets/brand.svg" alt="Original brand"></header>
      <main><section id="sohvat"><h2>Sohvat</h2></section>
      <section id="kankaat"><h2>Kankaat</h2></section>
      <section id="palvelut"><h2>Huonekalujen verhoilu</h2></section></main>
      <footer><a href="https://guild.example.org/"><img
      src="/logos/atelier-group.svg" alt="Association"></a></footer>
      </body></html>"""
    return research,html,digest

class SourceFidelityTests(unittest.TestCase):
    def test_auto_manifest_lists_every_source_page_heading_and_footer_logo(self):
        r,h,d=fixture()
        manifest=source_manifest(r)
        self.assertEqual(manifest["source_page_count"],2)
        self.assertEqual(len(manifest["assets"]),2)
        self.assertIn("Kankaiden valinta",manifest["pages"][0]["headings"])

    def test_missing_sponsor_mark_is_hard_failure_even_when_content_review_signed(self):
        r,h,d=fixture()
        r["content_inventory_review"]={"approved":True}
        broken=h.replace('<a href="https://guild.example.org/"><img\n      src="/logos/atelier-group.svg" alt="Association"></a>','')
        result=audit_source_fidelity(broken,r,source_url="https://atelier.example.org/",require_human_review=False)
        self.assertFalse(result["pass"])
        self.assertTrue(any(x["kind"]=="missing_original_affiliation_image"
                            for x in result["missing"]),result["missing"])

    def test_brand_identity_and_original_partner_link_must_remain_together(self):
        r,h,_=fixture()
        changed=h.replace('href="https://guild.example.org/"','href="https://unrelated.example.com/"')
        out=audit_source_fidelity(changed,r,require_human_review=False)
        self.assertTrue(any(x["kind"]=="missing_original_affiliation_image" for x in out["missing"]))
        brand_deleted=h.replace('<img src="/assets/brand.svg" alt="Original brand">','')
        out=audit_source_fidelity(brand_deleted,r,require_human_review=False)
        self.assertTrue(any(x["kind"]=="missing_original_brand_image" for x in out["missing"]))

    def test_original_section_and_page_cannot_disappear_silently(self):
        r,h,_=fixture()
        r["source_content_map"]["pages"][0]["sections"].pop()
        out=audit_source_fidelity(h,r,require_human_review=False)
        self.assertTrue(any(x["kind"]=="omitted_source_topic" for x in out["missing"]))
        r["source_content_map"]["pages"].pop()
        out=audit_source_fidelity(h,r,require_human_review=False)
        self.assertTrue(any(x["kind"]=="source_page" for x in out["missing"]))

    def test_old_site_primary_product_handoff_is_blocked(self):
        r,h,_=fixture()
        h=h.replace('</main>','<a href="https://atelier.example.org/tuotteet/">Katso tuotteet vanhoilta sivuilta</a></main>')
        out=audit_source_fidelity(h,r,source_url="https://atelier.example.org/",require_human_review=False)
        self.assertTrue(any(x["kind"]=="old_site_primary_task_handoff" for x in out["missing"]),out)

    def test_owner_approval_can_remove_specific_mark_not_all(self):
        r,h,d=fixture()
        r["approved_asset_removals"]=[{
          "source_url":"https://atelier.example.org/",
          "original_src":"/logos/atelier-group.svg",
          "source_sha256":d,"reviewer_kind":"client",
          "reviewer":"Client","reason":"Expired agreement"}]
        reduced=h.replace('<a href="https://guild.example.org/"><img\n      src="/logos/atelier-group.svg" alt="Association"></a>','')
        out=audit_source_fidelity(reduced,r,require_human_review=False)
        self.assertFalse(any(x["kind"]=="missing_original_affiliation_image" for x in out["missing"]))

    def test_new_source_snapshot_invalidates_old_asset_waiver(self):
        r,h,d=fixture()
        r["approved_asset_removals"]=[{
          "source_url":"https://atelier.example.org/",
          "original_src":"/logos/atelier-group.svg",
          "source_sha256":d,"reviewer_kind":"client",
          "reviewer":"Client","reason":"No longer associated"}]
        r["source_inventory"]["pages"][0]["text"]="Updated source"
        reduced=h.replace('<a href="https://guild.example.org/"><img\n      src="/logos/atelier-group.svg" alt="Association"></a>','')
        out=audit_source_fidelity(reduced,r,require_human_review=False)
        self.assertTrue(any(x["kind"]=="missing_original_affiliation_image" for x in out["missing"]))

    def test_review_cannot_claim_pass_without_exact_build_and_source_hash(self):
        r,h,d=fixture()
        out=audit_source_fidelity(h,r,source_url="https://atelier.example.org/")
        self.assertFalse(out["pass"])
        self.assertFalse(out["missing"],out["missing"])
        r["source_fidelity_review"]={
          "approved":True,"reviewer_kind":"human","reviewer":"QA lead",
          "checked_at":"2026-11-02T19:00:00+02:00",
          "source_sha256":d,"build_sha256":out["build_sha256"]}
        out=audit_source_fidelity(h,r,source_url="https://atelier.example.org/")
        # Affiliation role and re-use rights remain unverified even after scope check.
        self.assertTrue(out["pending"])
        self.assertFalse(out["missing"])
        out=audit_source_fidelity(h+"changed",r)
        self.assertTrue(any("Exact source" in x for x in out["pending"]))

    def test_no_website_does_not_invent_partners(self):
        r={"research_mode":"verified_no_website"}
        out=audit_source_fidelity("<main>Public facts</main>",r)
        self.assertTrue(out["pass"])
        self.assertEqual(out["manifest"]["source_page_count"],0)

if __name__=="__main__":
    unittest.main()
