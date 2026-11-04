"""Prevent repeat Penny Lane-style editorial monotony across ANY industry.

These are truthful review flags, not automatic AI aesthetic scores.
"""
import unittest
from utils.cross_route_editorial_risks import audit_cross_route_editorial_risks
from utils.universal_quality import audit_universal_standards


def page(title, picture, cta, *, hero_photo=False):
    hero=f"<img src='{picture}' alt='real image'>" if hero_photo else ""
    return (f'<!doctype html><html><body><header>Client name</header><main>'
            f'<section class="hero"><h1>{title}</h1>{hero}</section>'
            f'<section><img src="{picture}" alt="Product"><p>Real business facts.</p></section>'
            f'<section><h2>{cta}</h2></section></main></body></html>')


def research():
    return {"source_inventory":{"pages":[{
        "url":"https://shop.example/",
        "source_identity":{"original_content_photos":[
            {"src":"https://shop.example/1.jpg"},
            {"src":"https://shop.example/2.jpg"},
            {"src":"https://shop.example/3.jpg"},
        ]}
    }]}}


class CrossRouteEditorialRisksTests(unittest.TestCase):
    def test_repeated_same_photo_text_intro_and_call_to_action_are_review_flags(self):
        picture="https://shop.example/1.jpg"
        routes={
            "index.html":page("Our world",picture,"Come visit our showroom"),
            "products/index.html":page("New arrivals",picture,"Come visit our showroom"),
            "repairs/index.html":page("Repaired things",picture,"Come visit our showroom"),
            "about/index.html":page("About our shop",picture,"Come visit our showroom"),
        }
        result=audit_cross_route_editorial_risks(routes,research())
        kinds={row["category"] for row in result["pending"]}
        self.assertIn("recycled_business_photography",kinds)
        self.assertIn("repeated_text_only_subpage_openings",kinds)
        self.assertIn("repeated_full_width_call_to_action_copy",kinds)
        self.assertTrue(result["observations"]["same_photo_on_3plus_routes"])

    def test_varied_business_images_distinct_openings_and_copy_get_no_flags(self):
        routes={}
        for idx,(title,location) in enumerate([
            ("Real shop","store"),("Care","care"),("Sale","sale"),("Our people","team")
        ]):
            name=f"{location}/index.html"
            image=f"https://shop.example/unique-{idx}.jpg"
            routes[name]=page(title,image,f"{title} appointment",hero_photo=True)
        result=audit_cross_route_editorial_risks(routes,research())
        self.assertFalse(result["pending"],result)

    def test_no_source_photography_does_not_force_image_hero(self):
        no_source={"source_inventory":{"pages":[{
            "url":"https://office.example/","source_identity":{"original_content_photos":[]}
        }]}}
        routes={
            f"route{i}/index.html":page(str(i),f"/asset{i}.jpg",f"Unique call {i}")
            for i in range(5)
        }
        result=audit_cross_route_editorial_risks(routes,no_source)
        self.assertNotIn("repeated_text_only_subpage_openings",
                         {item["category"] for item in result["pending"]})

    def test_single_page_has_no_cross_route_penalty(self):
        self.assertFalse(audit_cross_route_editorial_risks({
            "index.html":page("Example","/photo.jpg","Come and find us")
        },research())["pending"])

    def test_cross_site_universal_check_marks_review_required_not_fake_design_score(self):
        picture="https://shop.example/1.jpg"
        routes={
            x:page("Collection",picture,"Welcome to the historical showroom")
            for x in ("index.html","shop/index.html","about/index.html")
        }
        report=audit_universal_standards(
            routes["index.html"], research=research(),
            rendered_pages=routes,stage="internal_demo")
        self.assertIn("cross_route_visual_rhythm",report["pending_evidence"])
        self.assertNotIn("cross_route_visual_rhythm",report["blocking_problems"])


if __name__ == "__main__":
    unittest.main()
