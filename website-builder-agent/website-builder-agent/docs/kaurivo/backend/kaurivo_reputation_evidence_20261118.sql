-- Kaurivo prospect reputation evidence: public, independently sourced only.
-- Missing evidence is NOT a bad rating and must never be promoted as 4 stars.
-- No personal reviewer data or copied reviews are stored.
ALTER TABLE public.kaurivo_crm_prospects
  ADD COLUMN IF NOT EXISTS reputation_evidence jsonb NOT NULL DEFAULT '{}'::jsonb;

COMMENT ON COLUMN public.kaurivo_crm_prospects.reputation_evidence IS
  'Evidence-based summary only: qualified rating >=4/5 from >=10 independent reviews, trusted source URL and observation date; never derive from follower counts, own-site testimonials or unverified snippets.';

-- A source record cannot be a bare number, list or string.
ALTER TABLE public.kaurivo_crm_prospects
  DROP CONSTRAINT IF EXISTS kaurivo_reputation_evidence_is_object;
ALTER TABLE public.kaurivo_crm_prospects
  ADD CONSTRAINT kaurivo_reputation_evidence_is_object
  CHECK (jsonb_typeof(reputation_evidence) = 'object');
