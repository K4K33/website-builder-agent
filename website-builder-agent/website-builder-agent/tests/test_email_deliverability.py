from datetime import date, datetime
import unittest
from unittest.mock import patch

from utils import email_deliverability as d

GOOD = ("Hei,\n\nhuomasin, että Maalaus Valolla on vahvat referenssit, mutta verkkosivuilta niitä on vaikea "
        "löytää. Tein teille luonnoksen siitä, miltä uudet sivut voisivat näyttää: "
        "https://demo.kaurivo.fi/maalaus-valo\n\nHaluaisitteko tällaiset verkkosivut yrityksellenne?\n\n"
        "Jos tämä ei ole ajankohtaista, vastaa vain ei kiitos, niin en ota enää yhteyttä.\n\n"
        "Ystävällisin terveisin\nKaarlo, Kaurivo")


class DeliverabilityTests(unittest.TestCase):
    def test_own_domain_plain_short_message_passes(self):
        self.assertEqual(d.preflight("Luonnos Maalaus Valon sivuista", GOOD, from_address="kaarlo@kaurivo.fi"), [])

    def test_free_mailbox_and_shared_host_links_are_blocked(self):
        body = GOOD.replace("https://demo.kaurivo.fi/maalaus-valo",
                            "https://kaurivo-auto-demos-2026.onrender.com/x/index.html")
        issues = " ".join(d.preflight("Luonnos", body, from_address="hello.kaurivo@gmail.com"))
        self.assertIn("ilmainen postilaatikko", issues)
        self.assertIn("onrender.com", issues)

    def test_refusal_route_images_and_shouting_are_checked(self):
        issues = " ".join(d.preflight("TARJOUS!", GOOD.replace("Jos tämä ei ole ajankohtaista, vastaa vain ei kiitos, "
                                                              "niin en ota enää yhteyttä.", ""),
                                      from_address="kaarlo@kaurivo.fi", html='<img src="x.gif">'))
        for part in ("kieltäytyä", "kuvia", "isoilla", "huutomerkki"):
            self.assertIn(part, issues)

    def test_slow_ramp_weekdays_only(self):
        start = date(2026, 11, 23)  # Monday
        self.assertEqual(d.daily_cap(start, start), 10)
        self.assertEqual(d.daily_cap(start, date(2026, 12, 1)), 15)
        self.assertEqual(d.daily_cap(start, date(2027, 2, 1)), 50)
        self.assertEqual(d.daily_cap(start, date(2026, 11, 28)), 0)  # Saturday
        self.assertTrue(d.within_office_hours(datetime(2026, 11, 24, 9)))
        self.assertFalse(d.within_office_hours(datetime(2026, 11, 24, 19)))

    def test_dns_records_cover_authentication_and_demo_domain(self):
        kinds = {(r[0], r[1]) for r in d.dns_records("kaurivo.fi")}
        self.assertIn(("TXT", "_dmarc.kaurivo.fi"), kinds)
        self.assertIn(("TXT", "zmail._domainkey.kaurivo.fi"), kinds)
        self.assertIn(("CNAME", "demo.kaurivo.fi"), kinds)
        self.assertTrue(any(r[2].startswith("v=spf1") for r in d.dns_records("kaurivo.fi")))

    def test_sender_and_demo_host_follow_configuration(self):
        with patch.dict("os.environ", {"KAURIVO_SENDER": "kaarlo@kaurivo.fi",
                                       "KAURIVO_DEMO_HOST": "https://demo.kaurivo.fi/"}):
            self.assertEqual(d.sender(), "kaarlo@kaurivo.fi")
            self.assertEqual(d.demo_host(), "https://demo.kaurivo.fi")



class PublicDemoUrlTests(unittest.TestCase):
    def test_render_preview_links_move_to_own_domain(self):
        self.assertEqual(d.public_demo_url("https://kaurivo-auto-demos-2026.onrender.com/maalaus-1/index.html"),
                         "https://demo.kaurivo.com/maalaus-1/index.html")
        self.assertEqual(d.public_demo_url("https://example.com/x"), "https://example.com/x")
        self.assertEqual(d.public_demo_url(None), "")
        self.assertEqual(d.preflight("Luonnos", GOOD.replace("https://demo.kaurivo.fi/maalaus-valo",
                         d.public_demo_url("https://kaurivo-auto-demos-2026.onrender.com/m/index.html")),
                         from_address="hello@kaurivo.com"), [])


if __name__ == "__main__":
    unittest.main()
