import json
from tempfile import TemporaryDirectory
import unittest

from utils.demo_page_drafts import draft_pages, _page_from_response


class DemoPageDraftTests(unittest.TestCase):
    def test_truncation_switches_to_sections_and_resume_reuses_finished_parts(self):
        shell = ('<!doctype html><html><body><main>'
                 '<div data-kaurivo-section-slot="hero"></div>'
                 '<div data-kaurivo-section-slot="services"></div>'
                 '</main></body></html>')
        calls = []

        def full(*_):
            calls.append("full")
            raise RuntimeError("OpenRouter response truncated; output rejected.")

        def small(system, prompt):
            if "HTML shell" in system:
                calls.append("shell")
                return json.dumps({"shell": shell})
            part = "hero" if "section hero" in system else "services"
            calls.append(part)
            if part == "services" and calls.count(part) == 1:
                raise RuntimeError("temporary provider failure")
            return json.dumps({"section": f'<section id="{part}"><h2>{part}</h2></section>'})

        with TemporaryDirectory() as root:
            args = dict(root=root, job_id="demo", phase="build", routes=["index.html"],
                        system="design", prompt_for=lambda route: route,
                        request=full, section_request=small)
            with self.assertRaisesRegex(RuntimeError, "temporary"):
                draft_pages(**args)
            page = draft_pages(**args)["index.html"]
            self.assertLess(page.index('id="hero"'), page.index('id="services"'))
            self.assertNotIn("data-kaurivo-section-slot", page)
            self.assertEqual(calls, ["full", "shell", "hero", "services", "services"])

    def test_wrong_section_id_cannot_be_assembled(self):
        from utils.demo_sections import _section
        with self.assertRaisesRegex(RuntimeError, "mismatched"):
            _section('<section id="wrong"><h2>Wrong</h2></section>', "hero")

    def test_reuses_only_complete_pages_from_same_job_and_prompt(self):
        with TemporaryDirectory() as root:
            calls = []

            def request(system, prompt):
                route = prompt.splitlines()[2]
                calls.append(route)
                if route == "services.html" and len(calls) == 2:
                    raise RuntimeError("free provider interrupted")
                return json.dumps({"pages": {route: "<!doctype html><html></html>"}})

            args = dict(root=root, job_id="first", phase="build",
                        routes=["index.html", "services.html"], system="design",
                        prompt_for=lambda route: route, request=request)
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                draft_pages(**args)
            pages = draft_pages(**args)
            self.assertEqual(set(pages), {"index.html", "services.html"})
            self.assertEqual(calls, ["index.html", "services.html", "services.html"])
            draft_pages(**{**args, "job_id": "different"})
            self.assertEqual(calls[-2:], ["index.html", "services.html"])

    def test_rejects_wrong_pages(self):
        with TemporaryDirectory() as root:
            with self.assertRaisesRegex(RuntimeError, "differ"):
                draft_pages(
                    root=root, job_id="job", phase="concept", routes=["index.html"],
                    system="design", prompt_for=lambda route: route,
                    request=lambda *_: '{"pages":{"wrong.html":"<!doctype html><html></html>"}}',
                )

    def test_reads_single_html_or_exact_legacy_concept_route(self):
        route = "services.html"
        html = "<!doctype html><html><body><main>Verified service</main></body></html>"
        values = [
            {"html": html},
            {"concepts": {"chosen": {"pages": {route: html}}}},
        ]
        for response in values:
            self.assertEqual(_page_from_response(json.dumps(response), route, "chosen")[1],
                             {route: html})
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            _page_from_response(json.dumps({"html": html[:-7]}), route, "chosen")
