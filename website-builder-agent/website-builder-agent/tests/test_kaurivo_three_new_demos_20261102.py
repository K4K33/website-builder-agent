"""Three new cross-industry Kaurivo concept sites; zero paid API calls.

These tests verify source fidelity, unique CSS, no fake forms, mobile-aware
navigation and route existence. They do not certify 9.5 visual quality,
photo rights, remote image availability or customer acceptance.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
import unittest

ROOT=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"/"demos"
CASES={
  "visan-pyorahuolto-v1":{
     "pages":("","palvelut","yhteys"),
     "original":"https://visainen.com/",
     "required":("02 231 1191","visa@visainen.com","Yliopistonkatu 8","20100 Turku"),
     "image_expected":"photo-1673870861514",
  },
  "kukkakauppa-villiviini-v1":{
     "pages":("","tilaustyot","yhteys"),
     "original":"https://www.kukkakauppavilliviini.com/",
     "required":("040 7577 790","info@kukkakauppavilliviini.fi","Koritie 2","Villähde"),
     "image_expected":"598e53_9dfa8025440d4c62a574d3957913ab5b",
  },
  "verhoomo-kudelma-v1":{
     "pages":("","verhoilu","yhteys"),
     "original":"https://www.kudelma.fi/home",
     "required":("040 151 6577","verhoomo@kudelma.fi","Tehdaskartanonkatu 46","33400 Tampere"),
     "image_expected":"photo-1770198459003",
  }
}

class NewIndustryDemoQuality(unittest.TestCase):
 def test_every_route_is_complete_and_local_links_resolve(self):
  layouts=[]
  for site,case in CASES.items():
   css=ROOT/site/"assets"/"style.css"
   js=ROOT/site/"assets"/"app.js"
   self.assertTrue(css.is_file())
   self.assertTrue(js.is_file())
   layouts.append(css.read_text("utf-8"))
   for page in case["pages"]:
    path=ROOT/site/page/"index.html"
    self.assertTrue(path.is_file(),str(path))
    raw=path.read_text("utf-8")
    soup=BeautifulSoup(raw,"html.parser")
    with self.subTest(site=site,page=page):
     self.assertEqual(soup.html.get("lang"),"fi")
     self.assertEqual(len(soup.find_all("h1")),1)
     self.assertEqual(len(soup.find_all("main")),1)
     self.assertEqual(len(soup.find_all("nav")),1)
     self.assertIn("noindex",soup.select_one('meta[name="robots"]').get("content",""))
     self.assertTrue(soup.select_one('meta[name="viewport"]'))
     self.assertFalse(soup.find("form"),"Demo must not pretend to submit leads")
     self.assertIn("Kaurivon itsenäinen",raw)
     self.assertIn(case["original"],raw)
     self.assertNotIn('href="#"',raw)
     self.assertIn("aria-expanded",raw)
     for a in soup.find_all("a",href=True):
      href=a["href"].strip()
      if href.startswith("#"):
       self.assertIsNotNone(soup.find(id=href[1:]))
      elif href.startswith(("mailto:","tel:","http:","https:")):
       continue
      elif href.startswith("/website-builder-agent/"):
       path_part=urlsplit(href).path.removeprefix("/website-builder-agent/kaurivo/demos/")
       target=ROOT/unquote(path_part)
       if target.suffix:
        self.assertTrue(target.is_file(),f"{site}/{page}: {href}")
       else:
        self.assertTrue((target/"index.html").is_file(),f"{site}/{page}: {href}")
      else:
       self.fail(f"Unsafe/unknown navigation target: {href}")
  for i,left in enumerate(layouts):
   for right in layouts[i+1:]:
    self.assertNotEqual(left,right)
    self.assertLess(abs(len(left)-len(right))/max(len(left),len(right)),.9)

 def test_verified_facts_and_image_disclosure(self):
  for site,case in CASES.items():
   html=" ".join(
    (ROOT/site/page/"index.html").read_text("utf-8")
    for page in case["pages"]
   )
   for fact in case["required"]:
    self.assertIn(fact,html,f"{site}: missing {fact}")
   self.assertIn(case["image_expected"],html)
   self.assertIn("Kuvituskuva",html)
   self.assertIn("ei ",html.lower())
   self.assertNotIn("Lorem ipsum",html)
   self.assertNotIn("kymmenien vuosien",html.lower())

 def test_mobile_interaction_has_static_fallback_and_reduced_motion(self):
  for site in CASES:
   css=(ROOT/site/"assets"/"style.css").read_text("utf-8")
   js=(ROOT/site/"assets"/"app.js").read_text("utf-8")
   self.assertIn("@media(max-width:700px)",css)
   self.assertIn("prefers-reduced-motion:reduce",css)
   self.assertIn(".js .nav{display:none",css)
   self.assertIn("aria-expanded",js)
   self.assertIn("Escape",js)

if __name__=="__main__": unittest.main()
