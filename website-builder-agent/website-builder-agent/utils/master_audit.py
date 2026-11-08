"""Offline whole-site adapter. Never issues a deployment or invents review proof."""
from utils.master_prompt import MASTER_PROMPT_SHA256
from utils.service_quality import service_brief
from utils.universal_quality import audit_universal_standards
from utils.source_fidelity import audit_source_fidelity
from utils.source_identity import audit_price_faq_preservation
from utils.content_parity import audit_content_parity


def audit_site_contract(pages, research, *, company=None, artifact_digest=None, stage="internal_demo"):
    if stage not in ('internal_demo', 'client_release'):
        raise ValueError('Unknown acceptance stage')
    if not isinstance(pages, dict) or not pages or any(
            not isinstance(k, str) or not isinstance(v, str) or not v.strip()
            for k, v in pages.items()):
        raise ValueError('Actual rendered HTML route map required')
    if not isinstance(research, dict):
        raise ValueError('Research contract must be an object')
    company = company or {}
    if company.get('research') is not None and company['research'] != research:
        raise ValueError('Company and research must be the same reviewed contract')
    main = pages.get('index.html') or pages.get('/') or next(iter(pages.values()))
    universal = audit_universal_standards(main, research, company=company,
        stage=stage, rendered_pages=pages, site_bundle_sha256=artifact_digest)
    source = audit_source_fidelity(main, research,
        source_url=company.get('website') or company.get('url') or '', rendered_pages=pages)
    faq = audit_price_faq_preservation(pages, research)
    content = audit_content_parity('\n'.join(pages.values()), research,
        source_url=company.get('website') or company.get('url') or '')
    blocking = {'universal': universal['blocking_problems'],
                'source': source['missing'], 'price_faq': faq['missing'],
                'content': content['missing']}
    pending = {'universal': universal['pending_evidence'],
               'source': source['pending'], 'content': content['review_required']}
    clean = not any(blocking.values())
    verified = clean and not any(pending.values())
    return {'master_prompt_sha256': MASTER_PROMPT_SHA256,
            'contract_sha256': service_brief(research)['contract_sha256'],
            'blocking': blocking, 'pending': pending,
            'preflight_pass': clean,
            'public_demo_ready': clean and universal['public_demo_ready'],
            'client_release_ready': verified and universal['client_release_ready'],
            'quality_scorecard': universal['quality_scorecard'],
            'visual_asset_continuity': universal['visual_asset_continuity'],
            'note': 'Preflight is not acceptance. Known defects block; missing runtime/independent proof remains pending. Hosting does not run this adapter automatically.'}
