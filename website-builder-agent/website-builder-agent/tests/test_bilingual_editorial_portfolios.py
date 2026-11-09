"""Ensure real bilingual portfolios are not mistaken for generic image recycling."""
import unittest
from utils.cross_route_editorial_risks import audit_cross_route_editorial_risks

PHOTO = "https://craft.example/images/real-oak-door.jpg"
def source():
    return {"source_inventory":{"pages":[{
        "url":"https://craft.example/",
        "source_identity":{"original_content_photos":[
            {"src":PHOTO},
            {"src":"https://craft.example/images/window.jpg"},
            {"src":"https://craft.example/images/stairs.jpg"}]}}]}}

def page(route, twin, lang, role):
    section = ('<section><h1>Heading</h1><img src="'+PHOTO+'"></section>'
               if role != "contact" else '<section><h1>Contact</h1></section>')
    collection = ('<div><button data-filter="all">All</button>'+
                  "".join('<button data-category="doors"><img src="'+PHOTO+'" alt="Work"></button>'
                          for _ in range(7))+'</div>' if role=="gallery" else "")
    return ('<!doctype html><html lang="'+lang+'"><head>'+
            '<link rel="alternate" hreflang="'+lang+'" href="'+
            ('../' if route.endswith('index.html') else '')+'">'+
            '<link rel="alternate" hreflang="'+('sv' if lang=='fi' else 'fi')+
            '" href="'+twin+'"></head><body><main>'+section+collection+
            '</main></body></html>')

def woodtool_page(route, other, lang, role):
    # Use absolute-path local alternate refs: unambiguous independent of route nesting.
    alt='<link rel="alternate" hreflang="fi" href="/'+(
            route if lang=="fi" else other
        )+'"><link rel="alternate" hreflang="sv" href="/'+(
            other if lang=="fi" else route
        )+'">'
    photos=('<button data-filter="all">All</button>'+
            ''.join(f'<button data-category="doors"><img src="{PHOTO}"></button>'
                    for i in range(7))) if role=="gallery" else f'<img src="{PHOTO}">'
    return (f'<!doctype html><html lang="{lang}"><head>{alt}</head>'
            f'<body><main><section><h1>{role}</h1>{photos}</section></main></body></html>')

class BilingualEditorialTests(unittest.TestCase):
    def test_reciprocal_locales_and_real_portfolio_reuse_do_not_count_as_three_distinct_pages(self):
        pairs=[("index.html","sv/index.html","home"),
               ("palvelut/index.html","sv/tjanster/index.html","services"),
               ("tyot/index.html","sv/referenser/index.html","gallery")]
        routes={}
        for fi,sv,role in pairs:
            routes[fi]=woodtool_page(fi,sv,"fi",role)
            routes[sv]=woodtool_page(sv,fi,"sv",role)
        audit=audit_cross_route_editorial_risks(routes,source())
        flags={item["category"] for item in audit["pending"]}
        self.assertNotIn("recycled_business_photography",flags)
        self.assertEqual(audit["observations"]["same_photo_on_3plus_routes"],0)

    def test_unreciprocated_links_cannot_hide_repetition_across_three_real_pages(self):
        routes={}
        for i in range(3):
            route=f"service-{i}/index.html"
            routes[route]=f'<html lang="fi"><head><link rel="alternate" hreflang="sv" href="/nobody/"></head><body><main><section><h1>Service</h1><img src="{PHOTO}"></section></main></body></html>'
        audit=audit_cross_route_editorial_risks(routes,source())
        self.assertIn("recycled_business_photography",
                      {item["category"] for item in audit["pending"]})

if __name__=="__main__":
    unittest.main()
