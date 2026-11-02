"""Kaurivo: three first-pass demos must preserve critical source facts.

All checks are offline. Browser presentation on real hardware and photo permission
are separate release gates; this test cannot certify a 9/10 design score.
"""
from pathlib import Path
from urllib.parse import urlparse,unquote
import unittest
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"/"demos"
SITES={
"te-service-v1":{
 "pages":["","palvelut","yritys","yhteys"],
 "required":["TE-Service","Juusjärventie 140","040 703 2405","huolto@te-service.fi","Tony Eriksson","Fixus","Määräaikaishuolto","Katsastuspalvelu","Ilmastointihuolto","Pikahuolto","Sijaisauto","Osamaksu","Renkaat"]},
"ravintola-rosanne-v1":{
 "pages":["","lounas","juhlat","yhteys"],
 "required":["ROSANNE","Laukaantie 22","014 833 030","0500 648 725","ravintola.rosanne@gmail.com","lounas","Kahvila","Grilli Rosanne","27-vuotisjuhlalounas","Kokoushuone","Kokousvälineet","12,50","28,50","2.–6.11.2026"]},
"rakennuspalvelu-rili-v1":{
 "pages":["","palvelut","kohteet","yhteys"],
 "required":["RI","Sandelsinkatu 7","044 260 7539","050 466 5024","pekka.lipsanen@gmail.com","markus.ripatti@gmail.com","Omakotitalot","Vapaa-ajan asunnot","Kylpyhuone","Saunaremont","Liiketilat","Laatoitus","Verohallinnon"]},
}
class ThreeDemosQuality(unittest.TestCase):
 def test_files_and_navigation_and_demo_safety(self):
  for name,meta in SITES.items():
   with self.subTest(site=name):
    pages=[]
    for segment in meta["pages"]:
     path=ROOT/name/segment/"index.html"
     self.assertTrue(path.is_file(),str(path))
     body=path.read_text("utf-8")
     soup=BeautifulSoup(body,"html.parser")
     pages.append(body)
     self.assertEqual(soup.html.get("lang"),"fi")
     robots=soup.select_one('meta[name="robots"]')
     self.assertIn("noindex",robots.get("content",""))
     self.assertIn("KAURIVON SUUNNITTELUKONSEPTI",body)
     self.assertIn("VIRALLINEN",body)
     self.assertIsNotNone(soup.select_one("h1"))
     nav=soup.select_one("nav.nav")
     self.assertIsNotNone(nav)
     self.assertEqual(len(nav.select("a")),4)
     for a in soup.select("a[href]"):
      target=a["href"]
      if target.startswith(("https:","http:","tel:","mailto:","#")):continue
      target_path=(path.parent/target)
      self.assertTrue(target_path.is_dir() or target_path.is_file(),
                      f"Broken {name}:{segment} -> {target}")
     stylesheet=soup.select_one('link[rel="stylesheet"]')
     self.assertTrue((path.parent/stylesheet["href"]).is_file())
     script=soup.select_one('script[src]')
     self.assertTrue((path.parent/script["src"]).is_file())
     self.assertFalse(soup.select("form"),"No fake live form")
    combined=" ".join(pages).lower()
    for term in meta["required"]:
     self.assertIn(term.lower(),combined,f"{name} missing source fact: {term}")
 def test_shared_motion_and_responsive_rules(self):
  css=(ROOT/"_shared/first-pass.css").read_text("utf-8")
  js=(ROOT/"_shared/first-pass.js").read_text("utf-8")
  for marker in ("@media(max-width:900px)","@media(max-width:620px)","prefers-reduced-motion"):
   self.assertIn(marker,css)
  self.assertIn("scroll-behavior:auto",css)
  self.assertNotIn("addEventListener('scroll'",js)
  self.assertIn("aria-expanded",js)
 def test_source_photos_disclosed(self):
  for name in SITES:
   pages=[(ROOT/name/x/"index.html").read_text("utf-8") for x in SITES[name]["pages"]]
   self.assertTrue(any("oikeudet" in p.lower() for p in pages))
   self.assertTrue(any("class=\"photo\"" in p for p in pages))
if __name__=="__main__":unittest.main()
