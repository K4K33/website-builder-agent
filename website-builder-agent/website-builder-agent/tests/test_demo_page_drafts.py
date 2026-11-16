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

    def test_prototype_navigation_rewrites_aliases_and_disables_unbuilt_routes(self):
        from bs4 import BeautifulSoup
        from utils.concept_previews import prepare_concept_page

        page = ('<!doctype html><html><head><style>main{display:block}</style></head><body>'
                '<nav><a href="/">Home</a><a href="/services/">Services</a>'
                '<a href="/gallery.html" class="nav-link" tabindex="0">Gallery</a></nav>'
                '<main><h1>Verified service</h1></main></body></html>')
        routes = ['index.html', 'services/index.html']
        result = prepare_concept_page(routes[1], page, routes)
        links = BeautifulSoup(result, 'html.parser').select('nav a')
        self.assertEqual(links[0]['href'], '../index.html')
        self.assertEqual(links[1]['href'], 'index.html')
        self.assertEqual(links[2].get_text(), 'Gallery')
        self.assertEqual(links[2]['class'], ['nav-link'])
        self.assertEqual(links[2]['aria-disabled'], 'true')
        self.assertNotIn('href', links[2].attrs)
        self.assertNotIn('tabindex', links[2].attrs)
        unsafe = page.replace('/gallery.html', 'javascript:alert(1)')
        with self.assertRaisesRegex(RuntimeError, 'unapproved external scheme'):
            prepare_concept_page(routes[1], unsafe, routes)


    def test_approved_media_is_retained_and_normalized_for_nested_preview_routes(self):
        from bs4 import BeautifulSoup
        from utils.concept_previews import prepare_concept_page, validate_concept_media

        route = 'services/index.html'
        allowed = {'assets/brand-abcdef.png'}
        html = ('<!doctype html><html><head>'
                '<style>main{background:url("assets/brand-abcdef.png")}</style></head>'
                '<body><main><h1>Verified heading</h1>'
                '<img src="/assets/brand-abcdef.png" srcset="https://untrusted.invalid/a.png 2x">'
                '</main></body></html>')
        cleaned = prepare_concept_page(route, html, [route], allowed)
        self.assertIn('../assets/brand-abcdef.png', cleaned)
        self.assertNotIn('untrusted.invalid', cleaned)
        self.assertEqual(
            BeautifulSoup(cleaned, 'html.parser').select_one('img')['src'],
            '../assets/brand-abcdef.png')
        validate_concept_media(route, cleaned, allowed)

    def test_unapproved_images_and_css_urls_cannot_block_queued_concept(self):
        from bs4 import BeautifulSoup
        from utils.concept_previews import prepare_concept_page, validate_concept_media

        html = ('<!doctype html><html><head><style>'
                'main{background:url("https://unknown.invalid/hero.webp")}'
                '</style></head><body><main><h1>Verified heading</h1>'
                '<img src="assets/unverified-photo.webp" alt="Unverified">'
                '<div style="mask-image:url(data:image/svg+xml;base64,AAAA)">Content</div>'
                '</main></body></html>')
        cleaned = prepare_concept_page('index.html', html, ['index.html'], set())
        soup = BeautifulSoup(cleaned, 'html.parser')
        self.assertFalse(soup.select('img[src]'))
        self.assertIsNotNone(soup.select_one('[data-kaurivo-media-pending]'))
        self.assertNotIn('unknown.invalid', cleaned)
        self.assertNotIn('data:image/', cleaned)
        self.assertIn('background:none', cleaned)
        self.assertIn('mask-image:none', cleaned)
        validate_concept_media('index.html', cleaned, set())

    def test_concept_media_still_rejects_unchecked_image_set_and_imports(self):
        from utils.concept_previews import validate_concept_media
        for css in ('@import "https://unknown.invalid/style.css";',
                    'main{background:image-set("https://unknown.invalid/a.png" 1x)}'):
            page = ('<!doctype html><html><head><style>' + css +
                    '</style></head><body><main><h1>Verified</h1></main></body></html>')
            with self.assertRaisesRegex(RuntimeError, 'external stylesheets or image-set'):
                validate_concept_media('index.html', page, set())

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
