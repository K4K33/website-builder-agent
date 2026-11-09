"""Adversarial synthetic trials in unrelated industries; no API calls or ratings."""
import copy
import unittest
from utils.service_quality import (audit_service_quality, service_brief, source_tasks,
                                   validate_service_plan)
from utils.global_feedback import record_owner_feedback
from utils.visual_originality import audit_design_originality


def fixture():
    research = {
        'source_inventory': {'pages': [{'url': 'https://repair.example/',
            'text': 'We repair brass instruments in our workshop.',
            'links': [{'text': 'Book now', 'href': 'https://appointments.example/brass'}],
            'source_identity': {'original_content_photos': [{'src': 'https://repair.example/workshop.jpg'}]}}]},
        'site_architecture': {'pages': [{'path': 'index.html', 'user_task': 'Book an instrument repair'}]},
        'company_facts': {'name': 'Brass Workshop'},
        'company_voice_brief': {'tone': 'Direct workshop language',
            'company_specific_facts': ['We repair brass instruments'],
            'source_excerpts': [{'source_url': 'https://repair.example/',
                                 'text': 'We repair brass instruments'}]},
        'media_purpose_plan': [{'route': 'index.html', 'src': 'https://repair.example/workshop.jpg',
             'observed_subject': 'An instrument being repaired',
             'visitor_task': 'Book an instrument repair', 'rationale': 'Shows the actual offered work'}]}
    task = source_tasks(research)[0]
    research['business_task_plan'] = [{'task_id': task['id'], 'source_route': 'index.html',
        'destination': task['destination'], 'completion_mode': 'existing_platform'}]
    pages = {'index.html': '<main><h1>Brass repairs</h1><img src="https://repair.example/workshop.jpg">'
             '<a href="https://appointments.example/brass">Book your repair</a></main>'}
    return research, pages


def reviews(research, pages, digest='a'*64):
    audit = audit_service_quality(pages, research, artifact_digest=digest)
    ids = [t['id'] for t in source_tasks(research)]
    result = {}
    for domain in ('technical', 'content', 'visual', 'commercial'):
        result[domain] = {'approved': True, 'artifact_sha256': digest,
            'contract_sha256': service_brief(research)['contract_sha256'],
            'reviewer_id': 'independent-reviewer', 'independent_of_builder': True,
            'evidence_reference': 'fixture://evidence-only-not-a-real-review',
            'checked_at': '2026-11-04', 'open_issues': [], 'routes_reviewed': list(pages),
            'task_ids_tested': ids, 'source_new_comparison': 'fixture://comparison',
            'prior_client_comparison': 'fixture://unrelated-sites',
            'media_decisions_reviewed': audit['media_decisions'],
            'voice_excerpts_reviewed': research['company_voice_brief']['source_excerpts'],
            'journey_results': [{'task_id': t['task_id'], 'result': 'pass',
                'completion_evidence': 'fixture://observed-terminal-page',
                'completion_mode': t['completion_mode']} for t in research['business_task_plan']]}
    return result


class ServiceQualityTests(unittest.TestCase):
    def test_new_protocol_blocks_unmapped_tasks_before_builder(self):
        r, p = fixture(); r['service_quality_protocol'] = 'v1'
        validate_service_plan(r)
        r.pop('business_task_plan')
        with self.assertRaisesRegex(RuntimeError, 'before Builder'):
            validate_service_plan(r)

    def test_invented_task_id_and_duplicate_plan_fail(self):
        for change in ('invent', 'duplicate'):
            r, p = fixture()
            if change == 'invent': r['business_task_plan'][0]['task_id'] = 'invented'
            else: r['business_task_plan'] *= 2
            with self.assertRaises(RuntimeError): validate_service_plan(r)

    def test_two_bookings_of_same_kind_are_both_preserved(self):
        r, p = fixture()
        r['source_inventory']['pages'][0]['links'].append({'text': 'Book now', 'href': 'https://appointments.example/woodwind'})
        self.assertEqual(len(source_tasks(r)), 2)
        r.pop('business_task_plan')
        out = audit_service_quality(p, r)
        self.assertTrue(any(x['kind'] == 'lost_business_task' for x in out['blocking']))

    def test_bare_fact_source_url_is_blocked_not_a_crashing_exception(self):
        r, p = fixture()
        r['fact_sources'] = ['https://repair.example/']
        out = audit_service_quality(p, r)
        self.assertIn('invalid_fact_source_entry', [row['kind'] for row in out['blocking']])
        self.assertFalse(out['client_ready'])

    def test_text_backed_fact_source_record_is_accepted(self):
        r, p = fixture()
        r['fact_sources'] = [{'url': 'https://repair.example/',
                              'text': 'We repair brass instruments in our workshop.'}]
        out = audit_service_quality(p, r)
        self.assertNotIn('invalid_fact_source_entry', [row['kind'] for row in out['blocking']])

    def test_phone_link_cannot_replace_booking(self):
        r, p = fixture(); p['index.html'] = '<main><a href="tel:1234567">Call us</a></main>'
        self.assertTrue(audit_service_quality(p, r)['blocking'])

    def test_booking_root_cannot_replace_exact_destination(self):
        r, p = fixture(); r['business_task_plan'][0]['destination'] = 'https://appointments.example/'
        p['index.html'] = '<main><a href="https://appointments.example/">Book</a></main>'
        self.assertTrue(any(x['kind'] == 'changed_external_task_destination'
                            for x in audit_service_quality(p, r)['blocking']))

    def test_missing_internal_target_and_anchor_are_blocked(self):
        for destination in ('missing/index.html', '#missing'):
            r, p = fixture(); r['source_inventory']['pages'][0]['links'][0]['href'] = '/booking'
            task = source_tasks(r)[0]
            r['business_task_plan'][0].update(task_id=task['id'], destination=destination)
            p['index.html'] = f'<main><a href="{destination}">Book</a></main>'
            self.assertTrue(audit_service_quality(p, r)['blocking'])

    def test_contact_form_cannot_be_replaced_by_mailto_or_search_form(self):
        for new in ('<a href="mailto:office@example.org">Email</a>', '<form><input type="search"></form>'):
            r, p = fixture()
            r['source_inventory']['pages'][0]['links'] = []
            r['source_inventory']['pages'][0]['forms'] = [{'action': '/contact', 'method': 'post',
                'fields': [{'type': 'email'}, {'type': 'textarea'}]}]
            task = source_tasks(r)[0]
            r['business_task_plan'] = [{'task_id': task['id'], 'source_route': 'index.html',
                'destination': '/contact', 'completion_mode': 'form_submission'}]
            p['index.html'] = '<main>'+new+'</main>'
            self.assertTrue(any(x['kind'] == 'form_replaced_with_weaker_action'
                                for x in audit_service_quality(p, r)['blocking']))

    def test_source_image_and_alt_are_not_subject_approval(self):
        r, p = fixture(); r.pop('media_purpose_plan')
        p['index.html'] = p['index.html'].replace('<img ', '<img alt="perfect relevant work" ')
        self.assertTrue(any(x['kind'] == 'lead_image_task_relevance_unreviewed'
                            for x in audit_service_quality(p, r)['pending']))

    def test_wrong_image_assignment_does_not_cover_rendered_hero(self):
        r, p = fixture(); r['media_purpose_plan'][0]['src'] = 'https://repair.example/other.jpg'
        self.assertTrue(any(x['kind'] == 'lead_image_task_relevance_unreviewed'
                            for x in audit_service_quality(p, r)['pending']))

    def test_invented_voice_quote_is_blocked(self):
        r, p = fixture(); r['company_voice_brief']['source_excerpts'][0]['text'] = 'Award winning since 1900'
        self.assertTrue(any(x['kind'] == 'invented_voice_source' for x in audit_service_quality(p, r)['blocking']))

    def test_technical_pass_does_not_approve_other_domains(self):
        r, p = fixture(); r['service_quality_reviews'] = {'technical': reviews(r, p)['technical']}
        out = audit_service_quality(p, r, artifact_digest='a'*64)
        self.assertEqual(out['domains']['technical'], 'reviewed')
        self.assertEqual(out['domains']['visual'], 'pending')
        self.assertFalse(out['client_ready'])

    def test_all_four_domain_records_and_full_bundle_are_required(self):
        r, p = fixture(); r['service_quality_reviews'] = reviews(r, p)
        self.assertTrue(audit_service_quality(p, r, artifact_digest='a'*64)['client_ready'])
        self.assertFalse(audit_service_quality(p, r)['client_ready'])
        self.assertFalse(audit_service_quality(p, r, artifact_digest='b'*64)['client_ready'])

    def test_changed_task_plan_subject_or_voice_invalidates_reviews(self):
        for field in ('media_purpose_plan', 'company_voice_brief', 'business_task_plan'):
            r, p = fixture(); r['service_quality_reviews'] = reviews(r, p)
            if field == 'media_purpose_plan': r[field][0]['observed_subject'] = 'Potted plant'
            elif field == 'company_voice_brief': r[field]['tone'] = 'Generic luxury'
            else: r[field][0]['completion_mode'] = 'local_flow'
            self.assertFalse(audit_service_quality(p, r, artifact_digest='a'*64)['client_ready'])

    def test_checkboxes_without_actual_journey_result_remain_pending(self):
        r, p = fixture(); r['service_quality_reviews'] = reviews(r, p)
        r['service_quality_reviews']['commercial'].pop('journey_results')
        self.assertFalse(audit_service_quality(p, r, artifact_digest='a'*64)['client_ready'])

    def test_feedback_defaults_to_service_wide_but_local_scope_is_respected(self):
        ledger = {'schema_version': 1, 'user_rules': []}
        self.assertEqual(record_owner_feedback(ledger, text='business_task continuity')['scope'], 'universal')
        self.assertEqual(record_owner_feedback(ledger, text='Purple for this client', applies_to_all=False)['scope'], 'company')
        rule = record_owner_feedback(ledger, text='business_task continuity', checker='business_task_continuity',
                                     regression_test='tests/test_service_quality.py')
        self.assertEqual(rule['validation_status'], 'implemented_not_field_validated')

    def test_repeated_typography_plus_hero_gets_visual_flag_not_fake_score(self):
        html = '<main><section><div><h1>Something <em>special</em></h1></div><div><img src="work.jpg"></div></section></main>'
        css = 'h1{font-family:Georgia,serif}'
        out = audit_design_originality(html, site_slug='workshop', stylesheet_text=css,
                additional_sites={'bakery': html}, additional_styles={'bakery': css})
        self.assertTrue(out['review_flags'])
        self.assertNotIn('score', out)
        self.assertTrue(out['pass'])
        out = audit_design_originality(html.replace('<em>special</em>', 'special'), site_slug='workshop',
                stylesheet_text=css, additional_sites={'bakery': html}, additional_styles={'bakery': css})
        self.assertFalse(out['review_flags'])


class ServiceIntegrationTests(unittest.TestCase):
    def test_universal_gate_blocks_lost_tasks_on_unseen_hospitality_fixture(self):
        from utils.universal_quality import audit_universal_standards
        research = {'source_inventory': {'pages': [{'url': 'https://lodging.example/',
                    'links': [{'text': 'Reservation', 'href': 'https://booking.example/cabin-42'}]}]}}
        out = audit_universal_standards('<main><h1>Cabins</h1><a href="mailto:host@example.org">Email</a></main>', research)
        self.assertIn('business_task_continuity', out['blocking_problems'])

    def test_javascript_task_destination_fails_before_builder(self):
        r, p = fixture(); r['business_task_plan'][0]['destination'] = 'javascript:void(0)'
        with self.assertRaises(RuntimeError): validate_service_plan(r)

    def test_forged_overall_pass_cannot_bypass_delivery_review(self):
        import hashlib
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from agents.qa import approve_company
        from utils.site_integrity import site_sha256
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'index.html'; path.write_text('<main><h1>Workshop</h1></main>')
            company = {'status': 'qa_passed', 'research': {'service_quality_protocol': 'v1'},
                       'build': {'version': 1, 'output_path': str(path), 'page_paths': ['index.html']},
                       'qa': {'overall_pass': True, 'build_version': 1,
                              'html_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                              'site_sha256': site_sha256(Path(folder), ['index.html'])}}
            with patch('agents.qa.get_company', return_value=('new-workshop', company)), \
                 patch('agents.qa.upsert_company') as save, patch('agents.qa.set_status') as status:
                with self.assertRaisesRegex(RuntimeError, 'Service quality acceptance'):
                    approve_company('new-workshop')
                save.assert_not_called(); status.assert_not_called()

    def test_new_review_metadata_does_not_erase_missing_subject_plan(self):
        r, p = fixture(); r['media_purpose_plan'] = []
        r['service_quality_reviews'] = reviews(r, p)
        self.assertFalse(audit_service_quality(p, r, artifact_digest='a'*64)['client_ready'])

    def test_model_generated_review_claims_are_removed(self):
        from utils.service_quality import reset_generated_review_claims
        value = {'service_quality_reviews': {'visual': {'approved': True}}, 'company_facts': {'name': 'Real'}}
        reset_generated_review_claims(value)
        self.assertNotIn('service_quality_reviews', value)
        self.assertEqual(value['service_quality_protocol'], 'v1')
        self.assertEqual(value['company_facts']['name'], 'Real')

    def test_source_forms_and_fact_sources_changes_invalidate_contract(self):
        r, p = fixture(); before = service_brief(r)['contract_sha256']
        r['source_inventory']['pages'][0]['forms'] = [{'fields': [{'type': 'number', 'name': 'guests'}]}]
        self.assertNotEqual(service_brief(r)['contract_sha256'], before)
        before = service_brief(r)['contract_sha256']
        r['fact_sources'] = [{'url': 'https://registry.example/', 'text': 'Updated verified source'}]
        self.assertNotEqual(service_brief(r)['contract_sha256'], before)

    def test_swedish_booking_and_quote_are_discovered(self):
        r = {'source_inventory': {'pages': [{'url': 'https://verkstad.example/', 'links': [
            {'text': 'Offertförfrågan', 'href': '/offert'},
            {'text': 'Boka bord', 'href': 'https://bokning.example/bord'}]}]}}
        self.assertEqual({t['kind'] for t in source_tasks(r)}, {'quotation', 'booking'})

    def test_booking_form_without_a_textarea_is_still_a_business_task(self):
        r = {'source_inventory': {'pages': [{'url': 'https://cabin.example/', 'forms': [
            {'action': '/book', 'method': 'post', 'fields': [{'type': 'email'}, {'type': 'date'}]}]}]}}
        self.assertEqual(source_tasks(r)[0]['kind'], 'booking_form')

    def test_malformed_model_voice_and_review_fields_fail_closed(self):
        for value in ('approved', ['approved'], True):
            r, p = fixture(); r['company_voice_brief'] = value
            self.assertFalse(audit_service_quality(p, r)['client_ready'])
            r, p = fixture(); r['service_quality_reviews'] = {'visual': value}
            self.assertFalse(audit_service_quality(p, r, artifact_digest='a'*64)['client_ready'])
        r, p = fixture(); r['company_voice_brief']['source_excerpts'] = ['fake']
        self.assertTrue(audit_service_quality(p, r)['blocking'])

    def test_malformed_task_plan_is_rejected_before_spending(self):
        r, p = fixture(); r['business_task_plan'] = {'task_id': 'bad'}
        with self.assertRaisesRegex(RuntimeError, 'must be a list'): validate_service_plan(r)

    def test_legacy_missing_route_list_does_not_bypass_full_bundle_check(self):
        import hashlib
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from agents.qa import approve_company
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'index.html'; path.write_text('<main><h1>Workshop</h1></main>')
            company = {'status': 'qa_passed', 'research': {'service_quality_protocol': 'v1'},
                       'build': {'version': 1, 'output_path': str(path)},
                       'qa': {'overall_pass': True, 'build_version': 1,
                              'html_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                              'site_sha256': 'a'*64}}
            with patch('agents.qa.get_company', return_value=('new-workshop', company)), \
                 patch('agents.qa.upsert_company') as save:
                with self.assertRaisesRegex(RuntimeError, 'complete bundle changed'):
                    approve_company('new-workshop')
                save.assert_not_called()

    def test_www_alias_is_not_mistaken_for_an_external_booking_platform(self):
        r, p = fixture()
        r['source_inventory']['pages'][0]['url'] = 'https://www.repair.example/'
        r['company_voice_brief']['source_excerpts'][0]['source_url'] = 'https://www.repair.example/'
        r['source_inventory']['pages'][0]['links'][0]['href'] = 'https://repair.example/booking'
        task = source_tasks(r)[0]
        r['business_task_plan'][0].update(task_id=task['id'], destination='#booking', completion_mode='local_flow')
        p['index.html'] = '<main><a href="#booking">Book</a><section id="booking">Choose a time</section></main>'
        self.assertFalse(audit_service_quality(p, r)['blocking'])
