"""Safe, public-only source URLs: Finnish IDN domains must not be excluded."""
import socket
import unittest
from unittest.mock import patch

from scripts.run_kaurivo_demo_queue import safe_company_url, HoldError


def public_dns(host, port, *args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


class InternationalDomainSafetyTests(unittest.TestCase):
    def test_valid_finnish_idn_is_allowed_with_public_dns(self):
        for url, expected_dns in (
            ("https://www.kärryt.net", "www.xn--krryt-gra.net"),
            ("https://www.sähkö-jutech.fi", "www.xn--shk-jutech-q5a2t.fi"),
            ("https://www.xn--krryt-gra.net", "www.xn--krryt-gra.net"),
        ):
            seen = []
            def observe(host, port, *args, **kwargs):
                seen.append(host)
                return public_dns(host, port, *args, **kwargs)
            with self.subTest(url=url), patch(
                "scripts.run_kaurivo_demo_queue.socket.getaddrinfo", observe
            ):
                self.assertEqual(safe_company_url(url), url)
            self.assertEqual(seen, [expected_dns])

    def test_idn_resolving_to_private_ip_is_still_blocked(self):
        def private_dns(host, port, *args, **kwargs):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with patch("scripts.run_kaurivo_demo_queue.socket.getaddrinfo", private_dns):
            with self.assertRaises(HoldError):
                safe_company_url("https://www.kärryt.net")

    def test_non_https_embedded_credentials_and_local_domains_rejected(self):
        for url in (
            "http://www.kärryt.net",
            "https://alice:password@www.kärryt.net",
            "https://hostname.local",
            "https://localhost",
            "https://metadata.google.internal",
            "https://127.0.0.1",
            "https://www.kärryt.net:8443",
        ):
            with self.subTest(url=url), patch(
                "scripts.run_kaurivo_demo_queue.socket.getaddrinfo", public_dns
            ):
                with self.assertRaises(HoldError):
                    safe_company_url(url)

    def test_dns_mixed_public_and_private_is_blocked(self):
        def mixed_dns(host, port, *args, **kwargs):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.20", 443)),
            ]
        with patch("scripts.run_kaurivo_demo_queue.socket.getaddrinfo", mixed_dns):
            with self.assertRaises(HoldError):
                safe_company_url("https://www.kärryt.net")


if __name__ == "__main__":
    unittest.main()
