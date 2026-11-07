"""Counterexamples, not subjective design scores or real visual approvals."""
import copy
import unittest
from utils.visual_asset_continuity import (
    PROTOCOL, _hash, extract_visual_candidates, validate_visual_plan,
    audit_visual_continuity, visual_candidates,
)
from utils.service_quality import service_brief, validate_service_plan
from utils.source_identity import extract_source_identity
from utils.content_parity import source_inventory_sha256


def fixture():
    source = '<main><img src="/unknown-1.png"><img alt="" src="/unknown-2.png"><img src="/repair.jpg" alt="Products"></main>'
    url = 'https://company.example/shop'
    candidates = extract_visual_candidates(source, url)
    research = {'visual_inventory_protocol': PROTOCOL,
        'source_inventory': {'pages': [{'url': url, 'source_identity': {'visual_assets': candidates}}]},
        'site_architecture': {'pages': [{'path': 'index.html'}]}, 'visual_asset_plan': []}
    for i, asset in enumerate(candidates):
        logo = i < 2
        research['visual_asset_plan'].append({'asset_id': asset['id'], 'role': 'brand_mark' if logo else 'photo',
            'name': 'Maker ' + str(i), 'observed_subject': 'Observed original maker artwork' if logo else 'A hand repairing a shoe',
            'visible_information': ['Maker ' + str(i)] if logo else [],
            'supported_uses': ['brand_mark'] if logo else ['repair_process'],
            'not_depicted': [] if logo else ['retail_selection'],
            'destinations': [{'route': 'index.html', 'selector': '#asset-' + str(i),
                'src': 'assets/' + str(i) + '.png', 'purpose': 'brand_mark' if logo else 'repair_process',
                'expected_alt': 'Maker ' + str(i) if logo else 'A hand repairing a shoe',
                'crop_mode': 'contain' if logo else 'natural'}]})
    pages = {'index.html': '<main><h1>Company</h1>' + ''.join(
        '<img id="asset-'+str(i)+'" src="assets/'+str(i)+'.png" alt="'+('Maker '+str(i) if i < 2 else 'A hand repairing a shoe')+'">'
        for i in range(3)) + '</main>'}
    return research, pages


def reviewed(research, pages):
    """Synthetic manifest, supplied as though bytes were already verified.

    File integrity itself is covered by tests.test_review_bundle. This fixture
    does not claim to identify real photo subjects, inspect crops or a human.
    """
    contract = service_brief(research)['contract_sha256']
    build = 'a' * 64
    bundle = {'artifact_sha256': build, 'contract_sha256': contract,
        'items': [{'id': 'old', 'kind': 'source_visual_capture', 'route': 'https://company.example/shop',
                   'asset_ids': [c['id'] for c in visual_candidates(research)]},
                  {'id': 'd', 'kind': 'new_screenshot', 'route': 'index.html', 'viewport': 'desktop'},
                  {'id': 'm', 'kind': 'new_screenshot', 'route': 'index.html', 'viewport': 'mobile'}]}
    meta = {'artifact_sha256': build, 'contract_sha256': contract,
        'plan_sha256': _hash(research['visual_asset_plan']), 'reviewer_id': 'synthetic-separate-reviewer',
        'independent_of_builder': True, 'checked_at': '2026-11-07', 'open_issues': []}
    research['visual_source_review'] = {**meta,
        'source_sha256': source_inventory_sha256(research['source_inventory']),
        'dynamic_and_background_content_checked': True, 'evidence_ids': ['old'],
        'assets': [{'asset_id': c['id'], 'classification_matches_pixels': True,
                    'observation': 'Synthetic original visual observation', 'evidence_ids': ['old']}
                   for c in visual_candidates(research)]}
    research['visual_placement_review'] = {**meta, 'placements': [
        {'asset_id': row['asset_id'], 'route': use['route'], 'selector': use['selector'], 'viewport': vp,
         'evidence_ids': [ref], **{k: {'result': 'pass', 'observation': 'Synthetic ' + k}
           for k in ('subject_match', 'alt_accuracy', 'crop_integrity', 'visual_information_preserved')}}
        for row in research['visual_asset_plan'] for use in row['destinations']
        for vp, ref in [('desktop', 'd'), ('mobile', 'm')]]}
    return build, contract, bundle


class VisualAssetContinuityTests(unittest.TestCase):
    def audit(self, research, pages, proof=None):
        build, contract, bundle = proof or ('a' * 64, service_brief(research)['contract_sha256'], None)
        return audit_visual_continuity(pages, research, artifact_digest=build,
            contract_digest=contract, review_bundle=bundle)

    def test_unlabelled_and_lazy_graphics_are_candidates_not_auto_decoration(self):
        out = extract_source_identity('<main><img src="data:image/gif;base64,x" data-src="/a.png"><img src="/b.gif"></main>', 'https://company.example')
        assets = out['visual_assets']
        self.assertEqual(len(assets), 2)
        self.assertTrue(all(c['classification'] == 'unresolved' for c in assets))
        self.assertTrue(assets[0]['src'].endswith('/a.png'))

    def test_no_silent_seventy_image_inventory_limit(self):
        html = ''.join('<img src="/image-'+str(i)+'.jpg">' for i in range(100))
        self.assertEqual(len(extract_visual_candidates(html, 'https://company.example')), 100)

    def test_inline_svg_and_background_information_included(self):
        out = extract_visual_candidates('<svg><title>A maker</title><path d="M1 1"/></svg><div style="background-image:url(/mark.png)"></div>', 'https://company.example')
        self.assertEqual({c['kind'] for c in out}, {'inline_svg', 'background'})

    def test_only_same_wix_asset_size_variants_share_identity(self):
        a = extract_visual_candidates('<img src="https://static.wixstatic.com/media/id.png/v1/fill/w_50/id.png">', 'https://company.example')
        b = extract_visual_candidates('<img src="https://static.wixstatic.com/media/id.png">', 'https://company.example')
        c = extract_visual_candidates('<img src="https://static.wixstatic.com/media/other.png">', 'https://company.example')
        self.assertEqual(a[0]['id'], b[0]['id']); self.assertNotEqual(a[0]['id'], c[0]['id'])

    def test_unknown_artwork_blocks_before_builder(self):
        r, _ = fixture(); r['visual_asset_plan'][0]['role'] = 'unresolved'
        with self.assertRaisesRegex(RuntimeError, 'unresolved'): validate_service_plan(r)

    def test_missing_and_duplicate_candidate_cannot_be_ignored(self):
        for change in ('missing', 'duplicate'):
            r, _ = fixture()
            if change == 'missing': r['visual_asset_plan'].pop()
            else: r['visual_asset_plan'].append(copy.deepcopy(r['visual_asset_plan'][0]))
            with self.assertRaisesRegex(RuntimeError, 'exactly once'): validate_visual_plan(r)

    def test_brand_text_is_not_logo_artwork(self):
        r, p = fixture(); p['index.html'] = '<main><p>Maker 0 Maker 1</p></main>'
        self.assertIn('source_visual_placement_missing', [x['kind'] for x in self.audit(r,p)['blocking']])

    def test_essential_source_mark_cannot_have_empty_destination(self):
        r, _ = fixture(); r['visual_asset_plan'][0]['destinations'] = []
        with self.assertRaisesRegex(RuntimeError, 'disappear'): validate_visual_plan(r)

    def test_wrong_subject_after_first_image_is_rejected(self):
        r, _ = fixture(); r['visual_asset_plan'][2]['destinations'][0]['purpose'] = 'retail_selection'
        with self.assertRaisesRegex(RuntimeError, 'subject'): validate_visual_plan(r)

    def test_every_output_image_requires_placement(self):
        r, p = fixture(); p['index.html'] += '<img src="assets/extra.jpg" alt="Unknown product">'
        self.assertIn('unplanned_visual_placement', [x['kind'] for x in self.audit(r,p)['blocking']])

    def test_hidden_artwork_is_not_visible_preservation(self):
        r, p = fixture(); p['index.html'] = p['index.html'].replace('<img id="asset-0"', '<img hidden id="asset-0"')
        self.assertIn('hidden_visual_substitute', [x['kind'] for x in self.audit(r,p)['blocking']])

    def test_cropped_logo_fails_even_with_positive_review(self):
        r, p = fixture(); p['index.html'] = p['index.html'].replace('<img id="asset-0"','<img style="object-fit:cover" id="asset-0"')
        proof = reviewed(r,p)
        self.assertIn('cropped_brand_mark', [x['kind'] for x in self.audit(r,p,proof)['blocking']])

    def test_misleading_alt_does_not_become_observed_subject(self):
        r, p = fixture(); p['index.html'] = p['index.html'].replace('alt="A hand repairing a shoe"','alt="Shop products"')
        self.assertIn('image_alt_mismatch', [x['kind'] for x in self.audit(r,p)['blocking']])

    def test_plan_alone_is_never_visual_acceptance(self):
        r, p = fixture(); out = self.audit(r,p)
        self.assertFalse(out['blocking']); self.assertFalse(out['ready']); self.assertTrue(out['pending'])

    def test_synthetic_complete_observations_can_pass(self):
        r, p = fixture(); self.assertTrue(self.audit(r,p,reviewed(r,p))['ready'])

    def test_mobile_crop_failure_and_wrong_route_capture_stay_pending(self):
        for change in ('crop','wrong_route','unbacked'):
            r, p = fixture(); proof=reviewed(r,p)
            row=r['visual_placement_review']['placements'][-1]
            if change=='crop': row['crop_integrity']={'result':'fail','observation':'Product cut off'}
            elif change=='wrong_route': proof[2]['items'][-1]['route']='other.html'
            else: row['evidence_ids']=['made-up-reference']
            self.assertFalse(self.audit(r,p,proof)['ready'])

    def test_source_capture_must_show_original_page_not_homepage(self):
        r,p=fixture(); proof=reviewed(r,p); proof[2]['items'][0]['route']='https://company.example/'
        self.assertFalse(self.audit(r,p,proof)['ready'])

    def test_changed_source_or_plan_or_build_invalidates_review(self):
        for change in ('source','plan','build'):
            r,p=fixture(); proof=reviewed(r,p)
            if change=='source': r['source_inventory']['pages'][0]['text']='New source content'
            elif change=='plan': r['visual_asset_plan'][2]['observed_subject']='Different observed work'
            else: proof=('b'*64, proof[1], proof[2])
            self.assertFalse(self.audit(r,p,proof)['ready'])

    def test_decorative_reclassification_requires_source_observation(self):
        r,p=fixture(); r['visual_asset_plan'][0].update(role='decorative',visible_information=[])
        self.assertFalse(self.audit(r,p)['ready'])

    def test_bad_selector_is_reported_not_crashed(self):
        r,p=fixture(); r['visual_asset_plan'][0]['destinations'][0]['selector']='[[invalid'
        self.assertIn('invalid_visual_selector',[x['kind'] for x in self.audit(r,p)['blocking']])

    def test_source_capture_without_named_asset_cannot_certify_logo(self):
        r,p=fixture(); proof=reviewed(r,p); proof[2]['items'][0]['asset_ids']=[]
        self.assertFalse(self.audit(r,p,proof)['ready'])

    def test_empty_alt_is_allowed_for_observed_decorative_image(self):
        r,p=fixture(); row=r['visual_asset_plan'][0]; row['role']='decorative'
        row['destinations'][0]['expected_alt']=''
        p['index.html']=p['index.html'].replace('alt="Maker 0"','alt=""')
        self.assertTrue(self.audit(r,p,reviewed(r,p))['ready'])

    def test_model_generated_visual_reviews_are_discarded(self):
        from utils.service_quality import reset_generated_review_claims
        r,p=fixture(); reviewed(r,p); reset_generated_review_claims(r)
        self.assertNotIn('visual_source_review',r); self.assertNotIn('visual_placement_review',r)

    def test_same_artwork_across_pages_keeps_all_source_routes(self):
        r,p=fixture();second=copy.deepcopy(r['source_inventory']['pages'][0])
        second['url']='https://company.example/about'
        for asset in second['source_identity']['visual_assets']:
            asset['source_url']=second['url']
        r['source_inventory']['pages'].append(second)
        self.assertEqual(len(visual_candidates(r)),3)
        self.assertEqual(len(visual_candidates(r)[0]['source_urls']),2)
        validate_visual_plan(r)

    def test_manual_sites_adapter_rejects_text_logo_and_missing_acceptance(self):
        import contextlib, io, json, runpy
        from tempfile import TemporaryDirectory
        from pathlib import Path
        main=runpy.run_path(str(Path(__file__).resolve().parents[1]/'scripts/audit_visual_continuity.py'))['main']
        r,p=fixture()
        with TemporaryDirectory() as directory:
            root=Path(directory);rp=root/'research.json';pp=root/'pages.json'
            rp.write_text(json.dumps(r));pp.write_text(json.dumps(p))
            args=['--research',str(rp),'--pages',str(pp)]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args),0)
                self.assertEqual(main(args+['--stage','acceptance']),1)
                p['index.html']='<p>Maker 0 Maker 1</p>';pp.write_text(json.dumps(p))
                self.assertEqual(main(args),1)

    def test_image_only_information_can_be_preserved_as_accessible_text(self):
        r,p=fixture(); row=r['visual_asset_plan'][0];row.update(role='information_graphic',
            visible_information=['Opening hours 10–17'],destinations=[],
            text_destinations=[{'route':'index.html','selector':'#hours','information':['Opening hours 10–17']}])
        p['index.html']=p['index.html'].replace('<img id="asset-0" src="assets/0.png" alt="Maker 0">','<p id="hours">Opening hours 10–17</p>')
        self.assertTrue(self.audit(r,p,reviewed(r,p))['ready'])
        p['index.html']=p['index.html'].replace('Opening hours 10–17','Opening hours unknown')
        self.assertIn('image_only_information_lost',[x['kind'] for x in self.audit(r,p)['blocking']])

    def test_positive_numerical_score_does_not_erase_missing_artwork(self):
        from utils.universal_quality import audit_universal_standards
        r,p=fixture(); r['quality_scorecard']={'scores':{k:10 for k in ('brand_fidelity','content_preservation')}}
        p['index.html']='<main><h1>Company</h1><p>Maker 0 Maker 1</p></main>'
        result=audit_universal_standards(p['index.html'],r,rendered_pages=p)
        self.assertIn('visual_information_continuity',result['blocking_categories'])
        self.assertFalse(result['internal_review_ready']); self.assertFalse(result['client_release_ready'])

if __name__ == '__main__': unittest.main()
