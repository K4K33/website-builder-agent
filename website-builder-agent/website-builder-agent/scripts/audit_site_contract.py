"""Whole-contract offline check for rendered output from any builder, including Sites."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.master_audit import audit_site_contract


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research', required=True)
    parser.add_argument('--pages', required=True, help='Every route and its actual rendered HTML')
    parser.add_argument('--company', help='Company with actual delivery/review evidence')
    parser.add_argument('--artifact', help='Exact deployment archive')
    parser.add_argument('--stage', choices=('preflight', 'public_demo', 'client_release'), default='preflight')
    args = parser.parse_args(argv)
    if args.stage != 'preflight' and not args.artifact:
        parser.error('Acceptance requires the exact artifact; local HTML alone is not publication proof')
    research = json.loads(Path(args.research).read_text(encoding='utf-8'))
    pages = json.loads(Path(args.pages).read_text(encoding='utf-8'))
    company = json.loads(Path(args.company).read_text(encoding='utf-8')) if args.company else None
    digest = hashlib.sha256(Path(args.artifact).read_bytes()).hexdigest() if args.artifact else None
    out = audit_site_contract(pages, research, company=company, artifact_digest=digest)
    out['stage'] = args.stage
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out[{'preflight': 'preflight_pass', 'public_demo': 'public_demo_ready',
                     'client_release': 'client_release_ready'}[args.stage]] else 1


if __name__ == '__main__':
    raise SystemExit(main())
