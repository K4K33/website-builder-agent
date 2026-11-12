"""Goodcaf: private same-digest checkpoint writes must be idempotent.

Supabase Storage sometimes returns HTTP 400 UniqueViolation instead of 409
when POST without upsert targets an existing content-addressed object.
The OIDC Edge endpoint must verify the exact bytes before accepting either.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
EDGE=(ROOT/"docs/kaurivo/backend/demo_worker_edge.ts").read_text(encoding="utf-8")
RUNNER=(ROOT/"scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")
ARCHIVE=(ROOT/"scripts/kaurivo_demo_checkpoint.py").read_text(encoding="utf-8")


class SameDigestCheckpointTests(unittest.TestCase):
    def test_existing_same_job_and_phase_are_verified_not_reuploaded(self):
        self.assertIn('previous.stage===phase',EDGE)
        self.assertIn('previous.object_path===path',EDGE)
        self.assertIn('previous.checksum===checksum',EDGE)
        self.assertIn('previous.byte_count===length',EDGE)
        self.assertIn('if(!reuseExisting){',EDGE)
        self.assertIn('if(reuseExisting){',EDGE)
        self.assertIn('existing.arrayBuffer()',EDGE)
        self.assertIn('bytes.byteLength!==length||await shaHex(bytes)!==checksum',EDGE)

    def test_storage_400_duplicate_is_only_accepted_after_full_blob_check(self):
        self.assertIn('if(stored.status!==400&&stored.status!==409)',EDGE)
        self.assertIn('return reply(503,{ok:false,error:"checkpoint_store"});',EDGE)
        self.assertIn('return reply(503,{ok:false,error:"checkpoint_store_integrity"});',EDGE)
        self.assertIn('const recorded=await rpc("kaurivo_worker_checkpoint_record"',EDGE)
        self.assertLess(EDGE.index('if(reuseExisting){'),
                        EDGE.index('const recorded=await rpc("kaurivo_worker_checkpoint_record"'))
        self.assertIn('await shaHex(data)!==checksum',EDGE)
        self.assertIn('kaurivo_worker_checkpoint_can_write',EDGE)
        self.assertIn('jwtVerify(',EDGE)
        self.assertIn('CHECKPOINT_STAGES.has(phase)',EDGE)

    def test_missing_existing_storage_fails_closed(self):
        self.assertIn('if(!existing.ok)return reply(503,{ok:false,error:"checkpoint_store"});',EDGE)
        self.assertIn('if(recorded!==true)return reply(409',EDGE)
        self.assertIn('x-upsert":"false',EDGE)

    def test_earlier_verified_snapshot_must_not_mask_real_ai_error(self):
        self.assertIn('if "resume" in locals() and resume == "research_partial":',RUNNER)
        self.assertIn('prior verified private research checkpoint retained.',RUNNER)
        self.assertIn('else:\n                            error = checkpoint_error',RUNNER)
        self.assertIn('if error.code in TRANSIENT_RETRY_CODES:',RUNNER)
        self.assertIn('raise CheckpointError("checkpoint digest mismatch")',ARCHIVE)
        self.assertIn('checkpoint belongs to different job or stage',ARCHIVE)

if __name__=="__main__":
    unittest.main()
