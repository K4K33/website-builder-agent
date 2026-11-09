"""Credit-free adapter for rendered Sites/CMS/external builder output.

Does not publish, mutate sources, assign scores or certify the whole release.
Preflight rejects known defects; acceptance additionally requires independently
reviewed, verified capture files. Research/HTML-only input cannot pass acceptance.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.visual_asset_continuity import audit_visual_continuity
from utils.service_quality import service_brief
from utils.premium_quality_gate import site_digest
from utils.review_bundle import current_review_bundle


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research', required=True, help='Source inventory and visual_asset_plan JSON')
    parser.add_argument('--pages', required=True, help='JSON mapping every route to actual rendered HTML')
    parser.add_argument('--stage', choices=('preflight', 'acceptance'), default='preflight')
    parser.add_argument('--company', help='Actual company/review-bundle reference JSON for acceptance')
    parser.add_argument('--artifact', help='Exact deployment archive, hashed locally for evidence binding')
    args = parser.parse_args(argv)
    research = json.loads(Path(args.research).read_text(encoding='utf-8'))
    pages = json.loads(Path(args.pages).read_text(encoding='utf-8'))
    if not isinstance(research, dict) or not isinstance(pages, dict) or not pages or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in pages.items()):
        parser.error('Expected research object and nonempty rendered HTML route map')
    digest = hashlib.sha256(Path(args.artifact).read_bytes()).hexdigest() if args.artifact else site_digest(pages)
    bundle, error = None, None
    if args.company:
        company = json.loads(Path(args.company).read_text(encoding='utf-8'))
        if company.get('research') != research:
            parser.error('Company and research must be the same exact reviewed contract')
        try:
            bundle = current_review_bundle(company, pages, artifact_digest=digest)
        except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
            error = str(exc)
    out = audit_visual_continuity(pages, research, artifact_digest=digest,
        contract_digest=service_brief(research)['contract_sha256'], review_bundle=bundle)
    if error:
        out['pending'].append({'kind': 'review_bundle_unverified', 'reason': error})
        out['ready'] = False
    out['stage'] = args.stage
    out['whole_site_release_approved'] = False
    print(json.dumps(out, ensure_ascii=False, indent=2))
    # No-source input cannot silently claim the visual review applicable/pass.
    accepted = out['applicable'] and (out['ready'] if args.stage == 'acceptance' else not out['blocking'])
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())
