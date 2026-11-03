"""Zero-cost source visual richness regression tests."""
import unittest
from utils.source_experience import extract_source_experience, source_experience_brief, audit_source_experience_parity
from utils.source_identity import extract_source_identity
from utils.universal_quality import audit_universal_standards

def research_for(html):
    return {"source_inventory":{"pages":[{"url":"https://example.org/", "source_identity":extract_source_identity(html,"https://example.org/")}]}}

class SourceExperienceTests(unittest.TestCase):
    def test_rich_video_gallery_3d_texture_detected(self):
        html = """<html><head><style>.hero{background-image:url('/texture.jpg')}
        .shoe{transform-style:preserve-3d}</style><link rel='stylesheet' href='/theme.css'></head>
        <body><main><div class='swiper'><img src='/a.jpg'><img src='/b.jpg'></div>
        <video controls src='/work.mp4'></video></main></body></html>"""
        result=extract_source_experience(html,"https://example.org/")
        self.assertEqual(result["profile"],"rich")
        self.assertEqual(result["observed_videos"],1)
        self.assertEqual(result["observed_photo_assets"],2)
        self.assertTrue(result["observed_carousel_nodes"])
        self.assertTrue(result["observed_3d"])
        self.assertEqual(result["observed_textured_backgrounds"],["https://example.org/texture.jpg"])
        self.assertTrue(result["browser_inspection_required"])

    def test_sober_source_does_not_force_3d(self):
        brief=source_experience_brief(research_for("<html><main><h1>Workshop</h1></main></html>"))
        self.assertEqual(brief["motion_budget"],"restrained")

    def test_dropping_real_video_blocks_preview(self):
        original="<html><main><video src='/work.mp4' controls></video></main></html>"
        new={"index.html":"<html><main><h1>Workshop</h1><p>43</p></main></html>"}
        report=audit_source_experience_parity(new,research_for(original))
        self.assertTrue(any("video" in s.lower() for s in report["blocking"]))
        universal=audit_universal_standards(new["index.html"],research_for(original),rendered_pages=new)
        self.assertIn("source_experience_parity",universal["blocking_problems"])

    def test_source_photos_cannot_be_replaced_with_numbers_and_svg(self):
        source="<html><main>"+"".join(f"<img src='/work-{i}.jpg'>" for i in range(5))+"</main></html>"
        new={"index.html":"<main><h1>Workshop</h1><p>01 / Craft</p><svg></svg></main>"}
        report=audit_source_experience_parity(new,research_for(source))
        self.assertTrue(any("Photo-rich" in s for s in report["blocking"]))

    def test_gallery_without_equivalent_is_review_required(self):
        source="<main><div class='slick-slider'><img src='/a.jpg'><img src='/b.jpg'></div></main>"
        report=audit_source_experience_parity({"index.html":"<main><h1>Goods</h1></main>"},research_for(source))
        self.assertTrue(any("gallery" in s.lower() for s in report["pending"]))

    def test_external_css_means_visual_unknown_not_zero_effects(self):
        source="<link rel='stylesheet' href='/animations.css'><main><h1>Workshop</h1></main>"
        result=extract_source_experience(source)
        self.assertTrue(result["browser_inspection_required"])
        self.assertEqual(result["profile"],"restrained")

    def test_unverified_original_gets_pending_not_false_pass(self):
        result=audit_source_experience_parity({"index.html":"<main>Workshop</main>"},{})
        self.assertTrue(result["pending"])
        self.assertFalse(result["blocking"])

if __name__ == "__main__":
    unittest.main()
