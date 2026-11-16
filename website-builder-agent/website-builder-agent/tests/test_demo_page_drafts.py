import json
from tempfile import TemporaryDirectory
import unittest

from utils.demo_page_drafts import draft_pages, _page_from_response


class DemoPageDraftTests(unittest.TestCase):
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
