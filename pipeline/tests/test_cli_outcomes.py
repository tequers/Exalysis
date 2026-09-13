"""Ticket 15: reliable CLI outcomes and exit codes — no real provider calls.

Every scenario below runs the actual entry point (`pipeline.py` via subprocess,
so the exit code checked is the process's real exit status) with
LLM_PROVIDER=anthropic and an empty ANTHROPIC_API_KEY, matching the offline
convention used by test_input_selection.py and test_evaluation.py. Where a
scenario needs a paper to fully process (not just fail at extraction), a small
generated script stubs stage1_extract/stage2_tag_score/build_candidate_analysis
in that subprocess before calling app.main() — the same idea as the inline
"-c" scripts in test_evaluation.py and test_request_limits.py, just written to
a temp file because the stub code is multi-line.
"""

from contextlib import redirect_stdout
from io import StringIO
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PIPELINE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PIPELINE_DIR.parent
sys.path.insert(0, str(PIPELINE_DIR))

from exam_roi.evaluation import CandidateValidationError

with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}):
    app = importlib.import_module("pipeline")

ENV = {**os.environ, "LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": ""}


def run_pipeline(*args):
    """Invoke the real CLI entry point and return the finished process."""
    return subprocess.run(
        [sys.executable, "pipeline/pipeline.py", *args],
        cwd=REPO_ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8",
    )


# A minimal analysis that reaches process_exam_file's save step without any
# model call: stage1/stage2 are stubbed to return trivial-but-valid results,
# and build_candidate_analysis/finalize_candidate_analysis are stubbed to skip
# straight to a candidate shaped well enough for the CLI's own bookkeeping
# (exam_id/year/candidate_status), which is all this ticket's tests exercise.
FAKE_ANALYSIS_SCRIPT = textwrap.dedent("""\
    import sys
    sys.path.insert(0, {pipeline_dir!r})
    from unittest.mock import patch
    import pipeline as app

    def fake_build(*, exam_id, year, year_label, total_marks, analysis, known_topics,
                    source_provenance, model_provenance, processed_at):
        return {{
            "record_kind": "candidate-analysis",
            "candidate_status": {status!r},
            "exam_id": exam_id, "year": year, "year_label": year_label,
            "total_marks": total_marks, "questions": [], "topic_judgments": {{}},
            "per_topic": {{}}, "source_provenance": source_provenance,
            "model_provenance": model_provenance, "processed_at": processed_at,
        }}

    _patches = [
        patch.object(app, "stage1_extract", return_value=(
            [{{"q_id": "Q1", "text": "Use elimination.", "marks": 10, "format": "short_answer"}}],
            2026)),
        patch.object(app, "stage2_tag_score", return_value={{"per_topic": {{}}, "new_topic_names": []}}),
        patch.object(app, "build_candidate_analysis", side_effect=fake_build),
        patch.object(app, "aggregate_taxonomy", return_value={{"topics": {{}}}}),
        patch.object(app, "finalize_candidate_analysis", side_effect=lambda candidate, *a: candidate),
    ]
    for p in _patches:
        p.start()

    sys.argv = {argv!r}
    sys.exit(app.main())
    """)


def run_with_fake_analysis(tmp_path, argv, status="validated"):
    """Run pipeline.py with the LLM stubbed out, for a paper that must succeed."""
    script = tmp_path / "run_cli.py"
    script.write_text(
        FAKE_ANALYSIS_SCRIPT.format(pipeline_dir=str(PIPELINE_DIR), status=status, argv=argv),
        encoding="utf-8",
    )
    return subprocess.run([sys.executable, str(script)], cwd=REPO_ROOT, env=ENV,
                          capture_output=True, text=True, encoding="utf-8")


class CommandLevelExitCodeTests(unittest.TestCase):
    """The five scenarios ticket 15 requires, asserted on the real exit code."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmp_path = Path(self.tmp.name)
        self.course = self.tmp_path / "course"

    def paper(self, name, text="Use elimination to solve the equations."):
        path = self.tmp_path / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_all_success_batch_exits_zero_and_retains_the_saved_candidate(self):
        good = self.paper("good.txt")
        result = run_with_fake_analysis(
            self.tmp_path,
            ["pipeline.py", str(self.course), "add-exam", str(good)],
        )
        self.assertEqual(result.returncode, app.EXIT_OK, result.stdout + result.stderr)
        self.assertIn("Saved candidate", result.stdout)
        self.assertNotIn("failed", result.stdout.lower())
        saved = self.course / "candidates" / "good.json"
        self.assertTrue(saved.exists(), "a successful paper must keep its saved candidate")
        self.assertEqual(json.loads(saved.read_text(encoding="utf-8"))["candidate_status"], "validated")

    def test_all_failure_batch_exits_nonzero_and_does_not_claim_success(self):
        # Empty text fails extraction before any model call — fully offline,
        # and it never reaches process_exam_file's save step.
        first = self.paper("empty_one.txt", text="")
        second = self.paper("empty_two.txt", text="   ")
        result = run_pipeline(str(self.course), "add-exam", str(first), str(second))

        self.assertEqual(result.returncode, app.EXIT_PAPER_FAILURE, result.stdout + result.stderr)
        # Ticket 15, criterion 4: an all-failed batch must not read as "nothing to
        # add" (which implies nothing was wrong) or as a success of any kind.
        self.assertNotIn("Nothing new to add", result.stdout)
        self.assertIn("failed", result.stdout.lower())
        self.assertIn("empty_one.txt", result.stdout)
        self.assertIn("empty_two.txt", result.stdout)
        self.assertFalse((self.course / "candidates").exists() and
                         any((self.course / "candidates").iterdir()),
                         "no candidate should be saved when every paper failed")

    def test_mixed_batch_exits_nonzero_and_keeps_the_successful_candidate(self):
        bad = self.paper("bad.txt", text="")
        good = self.paper("good.txt")
        result = run_with_fake_analysis(
            self.tmp_path,
            ["pipeline.py", str(self.course), "add-exam", str(good), str(bad)],
        )
        self.assertEqual(result.returncode, app.EXIT_PAPER_FAILURE, result.stdout + result.stderr)
        # Partial success: the paper that succeeded keeps its saved candidate...
        self.assertTrue((self.course / "candidates" / "good.json").exists())
        # ...and the one that failed is named, not silently dropped.
        self.assertIn("bad.txt", result.stdout)
        self.assertIn("1 processed", result.stdout)
        self.assertIn("1 failed", result.stdout)

    def test_setup_error_before_any_processing_exits_the_setup_code(self):
        # An existing plain file where a course folder is expected: rejected by
        # setup_course_folder before add-exam/rebuild/status ever runs.
        not_a_folder = self.tmp_path / "course_is_a_file"
        not_a_folder.write_text("not a folder", encoding="utf-8")
        result = run_pipeline(str(not_a_folder), "status")

        self.assertEqual(result.returncode, app.EXIT_SETUP_ERROR, result.stdout + result.stderr)
        self.assertIn("COURSE_FOLDER is not a folder", result.stderr)

    def test_export_failure_reports_its_own_code_and_preserves_parsed_state(self):
        # One accepted exam, enough for rebuild to reach the write step.
        self.course.mkdir()
        parsed = self.course / "parsed"
        parsed.mkdir()
        accepted = {
            "exam_id": "old", "year": 2024, "total_marks": 100,
            "source_file": "old.txt", "questions": [],
            "per_topic": {"Legacy": {"marks_total": 20, "mark_fraction": 0.2,
                                     "format_distribution": {"short_answer": 1}}},
        }
        (parsed / "old.json").write_text(json.dumps(accepted), encoding="utf-8")
        taxonomy_before = json.dumps({"topics": {}})
        (self.course / "taxonomy.json").write_text(taxonomy_before, encoding="utf-8")
        # A directory in the spreadsheet's place makes the write fail deterministically,
        # without touching real disk-full/permission conditions.
        (self.course / "Exam_ROI_Pipeline.xlsx").mkdir()

        result = run_pipeline(str(self.course), "rebuild")

        self.assertEqual(result.returncode, app.EXIT_EXPORT_FAILURE, result.stdout + result.stderr)
        self.assertIn("Export failed", result.stdout)
        self.assertTrue((parsed / "old.json").exists())
        self.assertEqual((self.course / "taxonomy.json").read_text(encoding="utf-8"), taxonomy_before)


class RecoveryClassificationTests(unittest.TestCase):
    """In-process checks that failures/skips map to the recovery kind ticket 15
    asks for, including the 'rejected candidate' state (CandidateValidationError)
    that only the reusable evaluation module can currently produce."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        app.setup_course_folder(Path(self.tmp.name))

    def args(self, *paths):
        return SimpleNamespace(paths=[str(p) for p in paths], recursive=False, year=None,
                               exam_id=None, total_marks=None, force=False,
                               review=False, review_corrections=0, dry_run=False)

    def paper(self, name="paper.txt"):
        path = Path(self.tmp.name) / name
        path.write_text("Use elimination.", encoding="utf-8")
        return path

    def test_correction_required_rejection_recommends_reprocessing(self):
        paper = self.paper()
        error = CandidateValidationError("candidate analysis", "marks do not reconcile")
        self.assertEqual(error.disposition, "correction_required")
        out = StringIO()
        with patch.object(app, "process_exam_file", side_effect=error), redirect_stdout(out):
            code = app.cmd_add_exam(self.args(paper))
        self.assertEqual(code, app.EXIT_PAPER_FAILURE)
        self.assertIn("rejected", out.getvalue())
        self.assertIn("rerun add-exam", out.getvalue())

    def test_needs_review_rejection_recommends_a_human_review(self):
        paper = self.paper()
        error = CandidateValidationError("candidate analysis", "ambiguous evidence",
                                         disposition="needs_review")
        out = StringIO()
        with patch.object(app, "process_exam_file", side_effect=error), redirect_stdout(out):
            code = app.cmd_add_exam(self.args(paper))
        self.assertEqual(code, app.EXIT_PAPER_FAILURE)
        self.assertIn("rejected", out.getvalue())
        self.assertIn("review", out.getvalue().lower())

    def test_pending_review_outcome_is_saved_not_skipped_or_failed(self):
        paper = self.paper()
        out = StringIO()
        with patch.object(app, "process_exam_file",
                          return_value=app.ExamOutcome.SAVED_PENDING_REVIEW) as mock, \
             redirect_stdout(out):
            code = app.cmd_add_exam(self.args(paper))
        mock.assert_called_once()
        self.assertEqual(code, app.EXIT_OK)
        self.assertIn("pending review", out.getvalue())

    def test_skip_reasons_are_told_apart_in_the_batch_summary(self):
        accepted_paper = self.paper("accepted.txt")
        candidate_paper = self.paper("candidate.txt")
        outcomes = iter([app.ExamOutcome.SKIPPED_ACCEPTED, app.ExamOutcome.SKIPPED_CANDIDATE])
        out = StringIO()
        with patch.object(app, "process_exam_file", side_effect=lambda *a, **k: next(outcomes)), \
             redirect_stdout(out):
            code = app.cmd_add_exam(self.args(accepted_paper, candidate_paper))
        self.assertEqual(code, app.EXIT_OK)
        self.assertIn("already accepted", out.getvalue())
        self.assertIn("already a candidate", out.getvalue())


if __name__ == "__main__":
    unittest.main()
