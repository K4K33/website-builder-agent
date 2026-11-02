"""Run ALL repository tests and classify failures by the strongest trace evidence.

Zero external services or paid credits. Never edits code, skips tests or alters gates.
A PR cannot be green unless *every discovered test* passes.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
RULES = (
    (r"UnboundLocalError.*local variable", "python_import_scope", "Python variable shadows an imported module"),
    (r"Creative preflight|creative_directions", "creative_preflight", "Incomplete creative directions/selection"),
    (r"Source inventory missing|no researched source pages|neither source website|source_coverage", "source_evidence", "Missing verified source-site or no-site research evidence"),
    (r"Scout returned no company|previously tested company|unseen company", "trial_identity", "No eligible first-pass company identity in test/pipeline"),
    (r"horizontal overflow|scrollWidth|not less than or equal", "responsive_overflow", "Mobile viewport content exceeds its usable width"),
    (r"Broken .* ->|missing linked page|missing target section", "navigation", "Broken internal link or missing page/anchor"),
    (r"overall_pass.*False|Pipeline failed QA", "qa_gate", "An explicit QA gate rejected the build; inspect full QA evidence"),
    (r"connection refused|timed out|ERR_CERT|Temporary failure|network", "network", "External service or network failure"),
    (r"ModuleNotFoundError|ImportError", "dependencies", "Missing or incompatible dependency"),
    (r"AssertionError", "assertion", "Assertion mismatch; inspect expected and actual values"),
)
FRAME = re.compile(r'File "([^"]+)", line (\d+), in ([^\n]+)')


def classify_issue(trace: str) -> dict:
    """Return an evidence-based hypothesis, never pretend a guess is proven."""
    for pattern, key, explanation in RULES:
        if re.search(pattern, trace, flags=re.IGNORECASE):
            break
    else:
        key, explanation = "unclassified", "Requires developer investigation; no rule matched"
    frames = FRAME.findall(trace)
    code_frames = [
        {"file": path.replace(str(ROOT) + "/", ""), "line": int(lineno), "function": name}
        for path, lineno, name in frames
        if "/tests/" not in path.replace(chr(92), "/") and not path.endswith("unittest/case.py")
    ]
    terminal = next(
        (line.strip() for line in reversed(trace.splitlines())
         if line.strip() and not line.strip().startswith(("File ", "Traceback ", "2026-", "During handling"))),
        "No exception message captured",
    )
    return {
        "category": key,
        "explanation": explanation,
        "likely_source": code_frames[-1] if code_frames else None,
        "exception": terminal[:900],
        "confidence": "heuristic; verify against stack trace and actual code",
    }


class DiagnosticResult(unittest.TextTestResult):
    def grouped_failures(self) -> dict:
        groups = defaultdict(list)
        for kind, items in (("failure", self.failures), ("error", self.errors)):
            for test, traceback_text in items:
                diagnosis = classify_issue(traceback_text)
                groups[diagnosis["category"]].append({
                    "test": str(test),
                    "kind": kind,
                    **diagnosis,
                    "trace_excerpt": traceback_text[-2200:],
                })
        return dict(sorted(groups.items()))


def render_markdown(report: dict) -> str:
    lines = [
        "# Kaurivo full-suite quality diagnostics",
        "",
        f"Tests run: **{report['tests_run']}**",
        f"Failures: **{report['failures']}**; errors: **{report['errors']}**",
        f"Skipped: **{report['skipped']}** (reported, never counted as verified tests)",
        f"Result: **{'PASS' if report['passed'] else 'FAIL'}**",
        "",
        "Root causes are evidence-based hypotheses, NOT automatically proven fixes.",
        "",
    ]
    for category, entries in report["groups"].items():
        lines.extend([f"## {category} ({len(entries)})", ""])
        for item in entries:
            loc = item["likely_source"]
            where = (f"{loc['file']}:{loc['line']}" if loc else "unknown source file")
            lines.append(f"- `{item['test']}` — {where}; {item['exception'][:240]}")
        lines.append("")
    if not report["passed"]:
        lines.append("**Merge/release blocked until failures AND errors both equal 0.**")
    return "\n".join(lines) + "\n"


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="output/quality-diagnostics.json")
    parser.add_argument("--markdown", default="output/quality-diagnostics.md")
    args = parser.parse_args()
    os.chdir(ROOT)
    # Executing from scripts/ otherwise drops the project root from sys.path.
    # Match python -m unittest discover so EVERY original test can import utils/agents.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py",
                                                  top_level_dir=str(ROOT / "tests"))
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2,
                                    resultclass=DiagnosticResult).run(suite)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "passed": result.wasSuccessful() and result.testsRun > 0,
        "groups": result.grouped_failures(),
    }
    for target, payload in ((args.json, json.dumps(report, ensure_ascii=False, indent=2)),
                            (args.markdown, render_markdown(report))):
        path = ROOT / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")
    print("\n" + render_markdown(report))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as output:
            output.write(render_markdown(report))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
