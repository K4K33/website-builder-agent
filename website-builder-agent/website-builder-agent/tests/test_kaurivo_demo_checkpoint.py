"""Regression coverage for private, source-fidelity-preserving builder resumes.

Purely local tests, no Supabase calls, paid AI or public repo artifacts.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.kaurivo_demo_checkpoint import (
    CheckpointError, STAGES, make_archive, unpack_archive,
)


JOB = "841a2e44-5eb0-479c-a6a2-0dbe0155842a"
SLUG = "test-company"


def company_for(project, stage="researched"):
    company = {
        "name": "Test Company", "slug": SLUG, "url": "https://example.org/",
        "research": {
            "verified": True,
            "original_screenshots": {"desktop": str(
                project / "output" / "screenshots" /
                ("original-client-" + SLUG + "_desktop.png"))},
        },
    }
    if STAGES.index(stage) >= STAGES.index("concepts"):
        company["concept_previews"] = {"rendered": True}
    if STAGES.index(stage) >= STAGES.index("selected"):
        company["research"]["creative_selection"] = {"selected_alias": "A"}
    if STAGES.index(stage) >= STAGES.index("built"):
        company["build"] = {
            "output_path": "output/" + SLUG + "/index.html",
            "page_paths": ["index.html", "palvelut/index.html"],
            "version": "build-v1",
        }
    return company


def fixture(project, stage):
    screenshot = project / "output" / "screenshots" / (
        "original-client-" + SLUG + "_desktop.png")
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    screenshot.write_bytes(b"\x89PNG\r\n\x1a\nsource-evidence")
    own = project / "output" / SLUG
    own.mkdir(parents=True, exist_ok=True)
    (own / "concept.png").write_bytes(b"concept-art")
    if STAGES.index(stage) >= STAGES.index("built"):
        (own / "index.html").write_text("<!doctype html><html></html>")
        (own / "palvelut").mkdir()
        (own / "palvelut" / "index.html").write_text("<!doctype html>")
    unrelated = project / "output" / "other-company" / "private.json"
    unrelated.parent.mkdir(parents=True, exist_ok=True)
    unrelated.write_text('{"other":"never checkpoint"}')
    secret = project / ".env"
    secret.write_text("SERVICE_ROLE=NEVER_INCLUDE")
    return company_for(project, stage)


class PrivateCheckpointTests(unittest.TestCase):
    def test_blocked_concept_checkpoint_regenerates_from_stored_research(self):
        from utils.kaurivo_checkpoint_stage_recovery import completed_stage_index
        self.assertEqual(completed_stage_index(None), -1)
        self.assertEqual(completed_stage_index("research_partial"), -1)
        self.assertEqual(completed_stage_index("researched"), 0)
        self.assertEqual(completed_stage_index("concepts", {
            "concept_previews": {"status": "blocked"}}), 0)
        self.assertEqual(completed_stage_index("concepts", {
            "concept_previews": {"status": "ready_for_comparison"}}), 1)
        self.assertEqual(completed_stage_index("selected"), 2)
        self.assertEqual(completed_stage_index("built"), 3)

    def test_concept_replay_requires_server_issued_marker_and_checkpoint(self):
        directory = (Path(__file__).resolve().parents[1] / "docs" /
                     "kaurivo" / "backend")
        sql = (directory / "kaurivo_replay_verified_browser_fix_20261116.sql"
               ).read_text(encoding="utf-8")
        self.assertIn("research_fix_deployed", (
            directory / "kaurivo_replay_verified_concept_fix_20261116.sql"
        ).read_text(encoding="utf-8"))
        self.assertIn("c.stage in ('research_partial','researched','concepts')", sql)
        self.assertIn("server-only", sql)
        self.assertIn("has_function_privilege('authenticated'", sql)

    def test_research_roundtrip_to_a_new_runner_without_other_company_or_secrets(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            old, new = Path(a), Path(b)
            company = fixture(old, "researched")
            archive = make_archive(old, SLUG, JOB, "researched", company)
            digest = hashlib.sha256(archive).hexdigest()
            with zipfile.ZipFile(io.BytesIO(archive)) as zf:
                members = zf.namelist()
                self.assertTrue(any(x.startswith("output/screenshots/") for x in members))
                self.assertFalse(any("other-company" in x for x in members))
                self.assertFalse(any(".env" in x for x in members))
                self.assertNotIn("data/companies.json", members)
                self.assertNotIn("SERVICE_ROLE=NEVER_INCLUDE", archive.decode("latin1"))
            restored = unpack_archive(new, SLUG, JOB, "researched", archive, digest,
                                      expected_name="Test Company",
                                      expected_source="https://example.org/")
            self.assertEqual(restored["slug"], SLUG)
            capture = Path(restored["research"]["original_screenshots"]["desktop"])
            self.assertTrue(capture.is_file())
            self.assertTrue(str(capture).startswith(str(new)))
            self.assertFalse((new / ".env").exists())


    def test_checkpoint_keeps_active_concept_and_excludes_obsolete_sets_and_drafts(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            old, new = Path(a), Path(b)
            company = fixture(old, "concepts")
            root = old / "output" / SLUG
            active = root / "_concept_previews" / "set-current"
            active.mkdir(parents=True)
            (active / "manifest.json").write_text('{"status":"ready_for_comparison"}')
            (active / "comparison.html").write_text("<!doctype html><html></html>")
            (active / "variant-1").mkdir()
            (active / "variant-1" / "index.html").write_text("<!doctype html>")
            raw_qa = active / "variant-1" / "qa" / "desktop.png"
            raw_qa.parent.mkdir()
            raw_qa.write_bytes(b"transient-browser-capture")
            proof = active / "variant-1" / "_captures" / "a1" / "desktop.png"
            proof.parent.mkdir(parents=True)
            proof.write_bytes(b"hashed-manifest-proof")
            company["concept_previews"] = {
                "status": "ready_for_comparison",
                "manifest_path": str(active / "manifest.json"),
                "comparison_path": str(active / "comparison.html"),
            }
            # Each old immutable browser render creates many PNG captures.
            # Hundreds of stale captures used to exceed MAX_FILES even
            # though only the latest set was referenced by company state.
            stale = root / "_concept_previews" / "set-old"
            stale.mkdir()
            for n in range(450):
                (stale / f"discarded-{n}.png").write_bytes(b"stale")
            drafts = root / "_demo_page_drafts"
            drafts.mkdir()
            (drafts / "finished-page.json").write_text('{"html":"cached"}')
            archive = make_archive(old, SLUG, JOB, "concepts", company)
            with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
                names = bundle.namelist()
                self.assertTrue(any("set-current/manifest.json" in n for n in names))
                self.assertFalse(any("set-old" in n for n in names))
                self.assertFalse(any("_demo_page_drafts" in n for n in names))
                self.assertFalse(any("/qa/desktop.png" in n for n in names))
                self.assertTrue(any("/_captures/a1/desktop.png" in n for n in names))
            restored = unpack_archive(
                new, SLUG, JOB, "concepts", archive,
                hashlib.sha256(archive).hexdigest(),
                expected_name="Test Company",
                expected_source="https://example.org/",
            )
            self.assertTrue(Path(restored["concept_previews"]["manifest_path"]).is_file())
            self.assertTrue((new / "output" / SLUG / "concept.png").is_file())
            self.assertFalse((new / "output" / SLUG / "_concept_previews" /
                              "set-old").exists())

    def test_partial_concept_failure_retains_model_drafts_for_credit_saving_resume(self):
        with tempfile.TemporaryDirectory() as old:
            project = Path(old)
            company = fixture(project, "researched")
            draft = project / "output" / SLUG / "_demo_page_drafts" / "partial.json"
            draft.parent.mkdir()
            draft.write_text('{"html":"already verified draft"}')
            archive = make_archive(project, SLUG, JOB, "researched", company)
            with zipfile.ZipFile(io.BytesIO(archive)) as zf:
                self.assertIn(f"output/{SLUG}/_demo_page_drafts/partial.json",
                              zf.namelist())

    def test_completed_concept_must_have_real_active_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            company = fixture(project, "concepts")
            company["concept_previews"] = {
                "status": "ready_for_comparison",
                "manifest_path": str(project / "output" / SLUG /
                                     "_concept_previews" / "set-missing" / "manifest.json"),
            }
            with self.assertRaisesRegex(CheckpointError, "active concept manifest missing"):
                make_archive(project, SLUG, JOB, "concepts", company)

    def test_full_build_and_revisions_require_exact_saved_routes(self):
        for stage in ("built", "revised_1", "revised_2"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as a, \
                 tempfile.TemporaryDirectory() as b:
                old, new = Path(a), Path(b)
                company = fixture(old, stage)
                archive = make_archive(old, SLUG, JOB, stage, company)
                result = unpack_archive(new, SLUG, JOB, stage, archive,
                                        hashlib.sha256(archive).hexdigest(),
                                        expected_name="Test Company",
                                        expected_source="https://example.org/")
                self.assertEqual(result["build"]["version"], "build-v1")
                self.assertTrue((new / "output" / SLUG /
                                 "palvelut" / "index.html").is_file())

    def test_stages_refuse_unfinished_work(self):
        for stage in ("concepts", "selected", "built"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as a:
                root = Path(a)
                company = fixture(root, "researched")
                with self.assertRaises(CheckpointError):
                    make_archive(root, SLUG, JOB, stage, company)

    def test_wrong_job_or_company_or_url_or_digest_refused_without_any_write(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            old, new = Path(a), Path(b)
            archive = make_archive(old, SLUG, JOB, "researched",
                                   fixture(old, "researched"))
            digest = hashlib.sha256(archive).hexdigest()
            for job, name, source, sha in [
                ("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "Test Company",
                 "https://example.org/", digest),
                (JOB, "Other Company", "https://example.org/", digest),
                (JOB, "Test Company", "https://other.example/", digest),
                (JOB, "Test Company", "https://example.org/", "0"*64),
            ]:
                with self.subTest(job=job, name=name, source=source, sha=sha):
                    with self.assertRaises(CheckpointError):
                        unpack_archive(new, SLUG, job, "researched", archive, sha,
                                       expected_name=name, expected_source=source)
                    self.assertFalse((new / "output").exists())

    def test_traversal_and_symlink_entries_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root)
            company = fixture(project, "researched")
            legit = make_archive(project, SLUG, JOB, "researched", company)
            with zipfile.ZipFile(io.BytesIO(legit)) as zf:
                entries = [(n, zf.read(n)) for n in zf.namelist()]
            with tempfile.TemporaryDirectory() as target:
                for name in ("output/../../.env", "/tmp/escape.txt",
                             "output/" + SLUG + "//bad.json"):
                    with self.subTest(name=name):
                        modified = io.BytesIO()
                        with zipfile.ZipFile(modified, "w") as zf:
                            for n, raw in entries:
                                zf.writestr(n, raw)
                            zf.writestr(name, b"private")
                        content = modified.getvalue()
                        with self.assertRaises(CheckpointError):
                            unpack_archive(Path(target), SLUG, JOB, "researched",
                                           content, hashlib.sha256(content).hexdigest(),
                                           expected_name="Test Company",
                                           expected_source="https://example.org/")
                        self.assertFalse((Path(target) / "output").exists())

    def test_pack_refuses_symlink_into_private_host_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            company = fixture(root, "researched")
            (root / "output" / SLUG / "link.txt").symlink_to(root / ".env")
            with self.assertRaisesRegex(CheckpointError, "symlink"):
                make_archive(root, SLUG, JOB, "researched", company)

    def test_checkpoint_failure_categories_are_bounded_and_not_raw_storage_responses(self):
        worker = (Path(__file__).resolve().parents[1] /
                  "scripts" / "run_kaurivo_demo_queue.py").read_text()
        checkpoint = worker.split("def save_private_checkpoint(", 1)[1].split(
            "def restore_private_checkpoint(", 1)[0]
        for safe in ("local_file_count", "local_uncompressed_budget",
                     "local_compressed_budget", "local_active_manifest_missing",
                     "edge_timeout", "edge_http_", "edge_ack_not_ok"):
            self.assertIn(safe, checkpoint)
        self.assertNotIn("reply.text", checkpoint)
        self.assertNotIn("response.text", checkpoint)
        self.assertNotIn("str(exc)", checkpoint.split("raise HoldError", 1)[0])

    def test_stage_is_not_a_claim_of_qa_approval(self):
        worker = (Path(__file__).resolve().parents[1] /
                  "scripts" / "run_kaurivo_demo_queue.py").read_text()
        self.assertIn('run_cli(["qa",agent_slug]', worker)
        self.assertIn('save_private_checkpoint("researched",agent_slug)', worker)
        self.assertIn('save_private_checkpoint("concepts",agent_slug)', worker)
        self.assertIn('save_private_checkpoint("selected",agent_slug)', worker)
        self.assertIn('save_private_checkpoint("built",agent_slug)', worker)
        self.assertIn('save_private_checkpoint("revised_"+str(revision+1),agent_slug)',
                      worker)
        self.assertIn('if qa.get("overall_pass") is True:', worker)
        self.assertIn('"quality_gate_build_version_mismatch"', worker)
        self.assertIn('verify_public(url,marker,routes)', worker)
        self.assertNotIn('save_private_checkpoint("internal_preview"', worker)

    def test_private_backend_has_no_public_client_read_policy(self):
        root = Path(__file__).resolve().parents[1]
        sql = (root / "docs" / "kaurivo" / "backend" /
               "demo_private_checkpoints_20261111.sql").read_text()
        edge = (root / "docs" / "kaurivo" / "backend" /
                "demo_worker_edge.ts").read_text()
        self.assertIn("'kaurivo-demo-checkpoints',false", sql)
        self.assertIn('alter table public.kaurivo_demo_checkpoints enable row level security', sql)
        self.assertIn('from public,anon,authenticated', sql)
        self.assertIn('github_run_id=p_run_id', sql)
        self.assertIn('checkpoint_not_claimed', edge)
        self.assertIn('shaHex(data)!==checksum', edge)
        self.assertIn('x-checkpoint-sha256', edge)


if __name__ == "__main__":
    unittest.main()
