"""Stable owner-facing rubric; scores come from review, never static tests.

All nine dimensions have equal weight. Missing inspection is not a zero,
and an excellent mean cannot erase a failed business task or delivery check.
"""
from decimal import Decimal, ROUND_HALF_UP
import math
import re

DIMENSIONS = (
    ('brand_fidelity', 'Brändiuskollisuus'),
    ('company_specificity', 'Yrityskohtaisuus'),
    ('photography', 'Kuvien laatu ja monipuolisuus'),
    ('visual_composition', 'Visuaalinen sommittelu'),
    ('content_preservation', 'Sisällön säilyminen ja esittäminen'),
    ('commercial_quality', 'Myynnillisyys'),
    ('navigation_technical', 'Navigointi ja tekninen toteutus'),
    ('motion_scroll', '3D, animaatiot ja skrollaus'),
    ('client_handover', 'Valmius asiakkaalle luovutettavaksi'),
)
RUBRIC = 'kaurivo-nine-v3'


def quality_scorecard(review=None, *, artifact_digest=None, contract_digest=None,
                      evidence_bundle=None, blockers=(), pending=()):
    """Accept only a current, separately reviewed, evidenced scorecard.

    The caller must verify the evidence bundle's on-disk bytes. Metadata alone
    is not evidence and this function does not certify reviewer identity.
    """
    review = review if isinstance(review, dict) else {}
    evidence_bundle = evidence_bundle if isinstance(evidence_bundle, dict) else {}
    rows = review.get('scores')
    rows = rows if isinstance(rows, dict) else {}
    known = {item.get('id') for item in evidence_bundle.get('items', [])
             if isinstance(item, dict) and item.get('id')}
    metadata_ok = bool(
        review.get('rubric') == RUBRIC
        and isinstance(artifact_digest, str) and re.fullmatch('[a-f0-9]{64}', artifact_digest)
        and isinstance(contract_digest, str) and re.fullmatch('[a-f0-9]{64}', contract_digest)
        and review.get('artifact_sha256') == artifact_digest
        and review.get('contract_sha256') == contract_digest
        and evidence_bundle.get('artifact_sha256') == artifact_digest
        and evidence_bundle.get('contract_sha256') == contract_digest
        and review.get('independent_of_builder') is True
        and str(review.get('reviewer_id') or '').strip()
        and str(review.get('checked_at') or '').strip()
        and set(rows) == {key for key, _ in DIMENSIONS}
    )
    dimensions, values = [], []
    for key, label in DIMENSIONS:
        record = rows.get(key)
        record = record if isinstance(record, dict) else {}
        score, refs = record.get('score'), record.get('evidence_ids')
        valid = bool(metadata_ok and type(score) in (int, float)
                     and math.isfinite(score) and 0 <= score <= 10
                     and str(record.get('rationale') or '').strip()
                     and isinstance(refs, list) and refs
                     and all(isinstance(ref, str) and ref in known for ref in refs))
        dimensions.append({'key': key, 'label': label,
                           'score': score if valid else None,
                           'rationale': record.get('rationale', ''),
                           'status': 'reviewed' if valid else 'not_verified'})
        if valid:
            values.append(Decimal(str(score)))
    complete = len(values) == len(DIMENSIONS)
    mean = sum(values) / Decimal(len(DIMENSIONS)) if complete else None
    floor_met = bool(complete and min(values) >= Decimal('9'))
    target_met = bool(complete and mean >= Decimal('9.5') and floor_met)
    # Compare the exact mean, never the rounded display value (9.45 != 9.5).
    eligible = bool(target_met
                    and not blockers and not pending and review.get('open_issues') == [])
    return {'rubric': RUBRIC, 'dimensions': dimensions,
            'complete': complete, 'mean': float(mean) if complete else None,
            'display_mean': str(mean.quantize(Decimal('.1'), rounding=ROUND_HALF_UP)) if complete else None,
            'target': 9.5, 'minimum_dimension': 9, 'dimension_floor_met': floor_met,
            'target_met': target_met,
            'release_eligible': eligible,
            'blocking_issue_count': len(blockers), 'pending_issue_count': len(pending),
            'note': 'Equal weights; missing review stays unverified. Passing tests do not create scores.'}
