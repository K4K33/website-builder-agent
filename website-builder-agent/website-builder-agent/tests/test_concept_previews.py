"""Real HTML concept state, not three prose descriptions or fake visual scores."""
import base64
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from tests.test_creative_multipage_originality import creative
from utils.concept_previews import (parse_concepts, write_concepts, load_verified_set,
    blind_order, record_selection, validate_selected_concept)

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')


def fixture():
    research = {**creative(), 'company_facts': {'name': 'Instrument Studio'},
                'site_architecture': {'pages': [{'path': 'index.html'}, {'path': 'work/index.html'}]}}
    variants = {}
    for number in range(1, 4):
        identifier = 'concept_' + str(number)
        pages = {}
        for route in ('index.html', 'work/index.html'):
            link = 'work/index.html' if route == 'index.html' else '../index.html'
            content = ['<section><h1>Instrument Studio</h1><p>Workshop</p></section>',
                       '<article><h1>Instrument Studio</h1><div><p>Workshop</p><p>Repairs</p></div></article>',
                       '<div><h1>Instrument Studio</h1><ul><li>Workshop</li><li>Repairs</li></ul></div>'][number-1]
            pages[route] = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Instrument workshop"><title>Instrument Studio</title><style>body{font:16px Arial;color:#111;background:#fff;margin:20px}a{display:inline-block;padding:12px}main{display:' + ['block','grid','flex'][number-1] + ';flex-direction:column}h1{font-size:32px} @media(max-width:600px){h1{font-size:28px}}</style></head><body><nav><a href="'+link+'">Workshop</a></nav><main>'+content+'</main><footer>Instrument Studio</footer></body></html>'
        variants[identifier] = {'pages': pages}
    return research, {'concepts': variants}


def fake_renderer(file, **kwargs):
    # Deliberately shared paths for same-folder routes, like existing browser QA.
    folder = Path(file).parent / 'qa'; folder.mkdir(exist_ok=True)
    paths = {}
    for vp in ('desktop', 'mobile'):
        shot = folder / (vp + '.png'); shot.write_bytes(PNG); paths[vp] = str(shot)
    return {'pass': True, 'issues': [], 'screenshots': paths}


def selection_report(manifest):
    return {'selected_alias': 'B', 'observations': {a: 'Concrete comparison of customer tasks and real layout for '+a for a in 'ABC'},
            'critical_issues': {a: [] for a in 'ABC'},
            'reviewed_view_ids': [v['id'] for e in manifest['entries'] for v in e['views']]}


class ConceptPreviewTests(unittest.TestCase):
    def write(self, folder, research=None, data=None, renderer=fake_renderer):
        r, value = fixture(); r = research or r; value = data or value
        return r, write_concepts(json.dumps(value), r, output_parent=folder,
            producer='synthetic-unit-fixture-not-a-client', renderer=renderer)

    def test_three_real_two_page_sets_produce_twelve_required_views(self):
        with TemporaryDirectory() as folder:
            r, ref = self.write(folder); path, m = load_verified_set(ref, r, allowed_root=folder)
            self.assertEqual(len(m['entries']), 3)
            self.assertEqual(sum(len(e['views']) for e in m['entries']), 12)
            self.assertTrue((path.parent/'comparison.html').is_file())
            self.assertFalse(m['premium_approval'])

    def test_prose_or_missing_pages_cannot_replace_actual_html(self):
        r, value = fixture()
        for raw in ('{"concepts":{"concept_1":"beautiful layout"}}', '{}'):
            with self.assertRaises(RuntimeError): parse_concepts(raw, r)
        value['concepts']['concept_1']['pages'].pop('work/index.html')
        with self.assertRaises(RuntimeError): parse_concepts(json.dumps(value), r)

    def test_palette_or_text_only_variants_are_rejected(self):
        r, value = fixture()
        pages = value['concepts']['concept_1']['pages']
        for ident in ('concept_2', 'concept_3'):
            value['concepts'][ident]['pages'] = {p: h.replace('Workshop', ident).replace('#fff', '#eee') for p, h in pages.items()}
        with self.assertRaisesRegex(RuntimeError, 'changed colour or prose'): parse_concepts(json.dumps(value), r)

    def test_scripts_forms_redirects_and_inline_handlers_are_blocked(self):
        for bad in ('<script>alert(1)</script>', '<form></form>', '<iframe src="file:///private"></iframe>',
                    '<meta http-equiv="refresh" content="0;url=file:///private">', '<p onclick="alert(1)">Bad</p>'):
            r, value = fixture()
            value['concepts']['concept_1']['pages']['index.html'] += bad
            with self.assertRaises(RuntimeError): parse_concepts(json.dumps(value), r)

    def test_unstaged_image_or_css_file_reads_are_blocked(self):
        for bad in ('<img src="file:///private/image.png">', '<style>main{background:url(file:///private/image.png)}</style>',
                    '<style>@import "https://example.org/style.css";</style>'):
            with TemporaryDirectory() as folder:
                r, value = fixture(); value['concepts']['concept_1']['pages']['index.html'] += bad
                with self.assertRaises(RuntimeError): self.write(folder, r, value)

    def test_unknown_producer_is_blocked(self):
        r, value = fixture()
        with TemporaryDirectory() as folder, self.assertRaises(RuntimeError):
            write_concepts(json.dumps(value), r, output_parent=folder, producer='', renderer=fake_renderer)

    def test_missing_or_fake_screenshots_never_become_comparison_ready(self):
        for renderer in (lambda p, **kwargs: {'pass': True, 'screenshots': {}},
                         lambda p, **kwargs: {'pass': False, 'issues': ['browser unavailable'], 'screenshots': {}}):
            with TemporaryDirectory() as folder:
                r, ref = self.write(folder, renderer=renderer)
                self.assertEqual(ref['status'], 'blocked')
                with self.assertRaises(RuntimeError): load_verified_set(ref, r, allowed_root=folder)

    def test_html_and_screenshot_changes_invalidate_selection(self):
        for kind in ('html', 'screenshot'):
            with TemporaryDirectory() as folder:
                r, ref = self.write(folder); path, m = load_verified_set(ref, r, allowed_root=folder)
                target = m['entries'][0]['files'][0]['path'] if kind == 'html' else m['entries'][0]['views'][0]['path']
                (path.parent / target).write_bytes(b'changed')
                with self.assertRaises(RuntimeError): load_verified_set(ref, r, allowed_root=folder)

    def test_changed_facts_or_design_plan_invalidates_comparison(self):
        with TemporaryDirectory() as folder:
            r, ref = self.write(folder); r['company_facts']['name'] = 'Different company'
            with self.assertRaises(RuntimeError): load_verified_set(ref, r, allowed_root=folder)

    def test_model_cannot_select_without_viewing_all_twelve(self):
        with TemporaryDirectory() as folder:
            r, ref = self.write(folder); _, m = load_verified_set(ref, r, allowed_root=folder)
            report = selection_report(m); report['reviewed_view_ids'].pop()
            with self.assertRaises(RuntimeError): record_selection(ref, r, report, allowed_root=folder, reviewer='fixture')

    def test_winner_with_critical_issue_is_rejected(self):
        with TemporaryDirectory() as folder:
            r, ref = self.write(folder); _, m = load_verified_set(ref, r, allowed_root=folder)
            report = selection_report(m); report['critical_issues']['B'] = ['Wrong brand']
            with self.assertRaises(RuntimeError): record_selection(ref, r, report, allowed_root=folder, reviewer='fixture')

    def test_real_choice_updates_direction_but_never_premium_approval(self):
        with TemporaryDirectory() as folder:
            r, ref = self.write(folder); _, m = load_verified_set(ref, r, allowed_root=folder)
            selected = blind_order(m)['B']['id']
            ref, choice = record_selection(ref, r, selection_report(m), allowed_root=folder, reviewer='fixture')
            r['creative_selection'] = choice; r['visual_concepts_protocol'] = 'v1'
            verified = validate_selected_concept({'research': r, 'concept_previews': ref}, allowed_root=folder)
            self.assertEqual(choice['selected_id'], selected)
            self.assertFalse(verified['premium_approval'])

    def test_new_protocol_cannot_bypass_comparison_before_build(self):
        r, _ = fixture(); r['visual_concepts_protocol'] = 'v1'
        with TemporaryDirectory() as folder, self.assertRaises(RuntimeError):
            validate_selected_concept({'research': r}, allowed_root=folder)

    def test_two_routes_in_same_folder_do_not_overwrite_captured_views(self):
        r, data = fixture(); r['site_architecture']['pages'][1]['path'] = 'detail.html'
        for concept in data['concepts'].values():
            detail = concept['pages'].pop('work/index.html').replace('../index.html', 'index.html')
            concept['pages']['detail.html'] = detail
            concept['pages']['index.html'] = concept['pages']['index.html'].replace('work/index.html','detail.html')
        with TemporaryDirectory() as folder:
            _, ref = self.write(folder, r, data)
            _, m = load_verified_set(ref, r, allowed_root=folder)
            self.assertEqual(len({v['path'] for e in m['entries'] for v in e['views']}), 12)
