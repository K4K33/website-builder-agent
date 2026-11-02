"""Offline Kaurivo V3 cross-industry regression test.

Site builders retain distinct visual structure, source facts and actual logos.
These tests do not prove remote photo load, content licensing, independent visual
quality, editable CMS or customer production readiness.
"""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import unittest
from bs4 import BeautifulSoup

BASE=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"/"demos"
SITES={
"te-service-v3":["","huollot","yhteys"],
"ravintola-rosanne-v3":["","juhlat","yhteys"],
"rakennuspalvelu-rili-v3":["","kohteet","palvelut","yhteys"],
}

class NewCrossIndustrySites(unittest.TestCase):
 def test_pages_links_no_decorative_numbers_and_meta(self):
  for site,routes in SITES.items():
   for route in routes:
    with self.subTest(site=site,page=route):
     p=BASE/site/route/"index.html"
     self.assertTrue(p.is_file(),str(p))
     html=p.read_text(encoding="utf-8")
     soup=BeautifulSoup(html,"html.parser")
     self.assertEqual(soup.html.get("lang"),"fi")
     self.assertEqual(len(soup.find_all("h1")),1)
     self.assertEqual(len(soup.find_all("nav")),1)
     self.assertIn("noindex",soup.select_one('meta[name="robots"]').get("content",""))
     self.assertFalse(soup.find_all("form"))
     self.assertNotRegex(html,r"<small>\s*0[1-9]\s*</small>")
     self.assertIsNotNone(soup.select_one("main"))
     for element in soup.find_all(["a","link","script","img"]):
      href=(element.get("href") or element.get("src") or "").strip()
      if not href or href.startswith(("http:","https:","tel:","mailto:","data:")):
       continue
      if href.startswith("#"):
       self.assertTrue(soup.find(id=href[1:]),f"{p} broken #{href}")
       continue
      dest=(p.parent/unquote(urlsplit(href).path))
      if href.endswith("/"):
       dest=dest/"index.html"
      self.assertTrue(dest.is_file(),f"{p} -> {href} missing")

 def test_not_color_changes_of_one_generic_template(self):
  from utils.design_distinctness import compare_site_designs
  pages={site:(BASE/site/"index.html").read_text("utf-8") for site in SITES}
  keys=list(pages)
  for i,a in enumerate(keys):
   for b in keys[i+1:]:
    result=compare_site_designs(pages[a],pages[b])
    self.assertFalse(result["too_similar"],f"{a}/{b}: {result}")

 def test_TE_core_services_and_contacts(self):
  data=" ".join((BASE/"te-service-v3"/x/"index.html").read_text("utf-8")
                for x in SITES["te-service-v3"])
  for value in ("Määräaikaishuolto","Katsastuspalvelu","Pikahuolto",
                "Ilmastointihuolto","Sijaisauto","Fixus-lasku","Rengastyöt",
                "Juusjärventie 140","040 703 2405","huolto@te-service.fi",
                "Tony Eriksson","Fixus"):
   self.assertIn(value.casefold(),data.casefold())

 def test_Rosanne_original_logo_full_menu_and_event_details(self):
  site=BASE/"ravintola-rosanne-v3"
  photo=site/"assets"/"rosanne-logo.png"
  self.assertTrue(photo.is_file())
  self.assertTrue(photo.read_bytes().startswith(b"\x89PNG"))
  data=" ".join((site/x/"index.html").read_text("utf-8")
                for x in SITES["ravintola-rosanne-v3"])
  for value in ("Ti 3.11.","To 5.11.","27-vuotisjuhlalounas","Uunimuikut",
                "Broilerikeitto","Kermaperunoita","Palapaisti",
                "G = gluteeniton","M = maidoton","12,50",
                "28,50","014 833 030","Laukaantie 22"):
   self.assertIn(value.casefold(),data.casefold())

 def test_RILI_logo_work_photos_services_and_partner(self):
  site=BASE/"rakennuspalvelu-rili-v3"
  data=" ".join((site/x/"index.html").read_text("utf-8")
                for x in SITES["rakennuspalvelu-rili-v3"])
  for value in ("rili%20vaaka-01.png","saunaremontin%20toteutus",
                "Omakotitalojen urakointi","Vapaa-ajan asuntojen",
                "Kylpyhuoneiden","Laatoitukset","Liiketilojen",
                "044 260 7539","050 466 5024","Sandelsinkatu 7",
                "vinyyliverhous.fi"):
   self.assertIn(value.casefold(),data.casefold())
  self.assertIn("ei ole vielä varmistettu",data.casefold())

if __name__=="__main__":unittest.main()
