import json
from tempfile import TemporaryDirectory
import unittest

from utils.demo_page_drafts import draft_pages, _page_from_response


class DemoPageDraftTests(unittest.TestCase):
    def test_invalid_cached_concept_repairs_only_its_own_route(self):
        from utils.concept_previews import validate_concept_page

        valid = ('<!doctype html><html><head><style>main{display:block}</style></head>'
                 '<body><main><h1>Verified service</h1></main></body></html>')
        invalid = valid.replace('<h1>', '<h2>').replace('</h1>', '</h2>')
        routes = ['index.html', 'services.html']
        with TemporaryDirectory() as root:
            args = dict(root=root, job_id='demo', phase='concept-one', routes=routes,
                        system='design', prompt_for=lambda route: route)
            draft_pages(**args, request=lambda system, prompt: json.dumps({
                'html': invalid if 'services.html' in system else valid}))

            calls = []

            def repair(system, prompt):
                calls.append(system)
                self.assertIn('services.html', system)
                self.assertIn('one h1', system)
                self.assertIn(invalid, prompt)
                return json.dumps({'html': valid})

            def validate(route, body):
                validate_concept_page(route, body, routes)
                return body

            args['prepare_page'] = validate
            self.assertEqual(draft_pages(**args, request=repair), dict.fromkeys(routes, valid))
            self.assertEqual(draft_pages(**args, request=repair), dict.fromkeys(routes, valid))
            self.assertEqual(len(calls), 1)

    def test_concept_structure_is_fixed_without_a_second_model_call(self):
        from utils.concept_previews import prepare_concept_page

        draft = ('<!doctype html><html><head><title>Verified service</title></head><body>'
                 '<nav><a href="index.html">Home</a></nav>'
                 '<section style="color:#203040"><h2>Verified service</h2><p>Verified fact.</p></section>'
                 '<footer>Verified footer</footer></body></html>')
        route = 'index.html'
        with TemporaryDirectory() as root:
            args = dict(root=root, job_id='demo', phase='concept-one', routes=[route],
                        system='design', prompt_for=lambda route: route,
                        prepare_page=lambda route, body: prepare_concept_page(route, body, [route]))
            def generate(system, prompt):
                self.assertNotIn('Repair the prototype', system)
                return json.dumps({'html': draft})
            result = draft_pages(**args, request=generate)[route]
            self.assertIn('<main>', result)
            self.assertIn('<h1>Verified service</h1>', result)
            self.assertIn('color:#203040', result)
            self.assertIn('Verified fact.', result)
            self.assertIn('<style>', result)
            self.assertEqual(draft_pages(**args, request=lambda *_: self.fail('Cache bypassed'))[route], result)

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
