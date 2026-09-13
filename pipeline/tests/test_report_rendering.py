"""Ticket 18: report rendering extracted behind exam_roi.reports, offline.

Every scenario runs against synthetic course data in a tempfile course folder —
never the real Courses/ tree or any repo path — and asserts on SEMANTIC content
(openpyxl cell values, JSON data), never on binary workbook identity, per
docs/adr/0008-modular-pipeline-architecture.md. Two scenarios run the actual
`pipeline.py` entry point via subprocess, matching the offline convention used
by test_cli_outcomes.py and test_input_selection.py: LLM_PROVIDER=anthropic
with an empty ANTHROPIC_API_KEY, so nothing here reaches a real provider.
"""

import copy
import importlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PIPELINE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PIPELINE_DIR.parent
sys.path.insert(0, str(PIPELINE_DIR))

with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}):
    app = importlib.import_module("pipeline")

import exam_roi.reports as reports
from exam_roi.evaluation import CONTRACT_VERSION

ENV = {**os.environ, "LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": ""}


# ── Synthetic course fixture: two accepted exams sharing "Algebra", one topic
#    ("Calculus") depending on it, and one topic ("Geometry") appearing once —
#    enough to exercise ranking, tiering, prerequisites, and per-exam audit
#    columns without any model call. ──────────────────────────────────────────

def _qd(q_id, level, quote, rationale):
    return {"q_id": q_id, "level": level, "quote": quote, "rationale": rationale, "uncertainties": []}


def _judgment(question_difficulty, difficulty_rationale, assumed_prerequisites,
              prerequisite_evidence, connection_evidence, connection_edges, unlocks, prerequisites):
    return {
        "question_difficulty": question_difficulty, "difficulty_rationale": difficulty_rationale,
        "assumed_prerequisites": assumed_prerequisites, "prerequisite_evidence": prerequisite_evidence,
        "Conn": 1 if not unlocks else 2 if len(unlocks) <= 2 else 3,
        "connection_rationale": "See connection_evidence.", "connection_evidence": connection_evidence,
        "connection_edges": connection_edges, "unlocks": unlocks, "prerequisites": prerequisites,
        "uncertainties": [],
    }


_CALC_QUOTE = "using first principles, given the algebraic simplification rules."

EXAM_2023 = {
    "evaluation_contract_version": CONTRACT_VERSION,
    "exam_id": "exam_2023", "year": 2023, "year_label": None, "total_marks": 15,
    "source_file": "exam_2023.txt", "processed_at": "2026-01-01T00:00:00",
    "questions": [
        {"q_id": "Q1", "text": "Solve the linear equation 2x+3=7 for x.",
         "marks": 10, "format": "short_answer", "topics": ["Algebra"]},
        {"q_id": "Q2", "text": "Calculate the area of a triangle with base 4 and height 5.",
         "marks": 5, "format": "explain_derive", "topics": ["Geometry"]},
    ],
    "topic_judgments": {
        "Algebra": _judgment(
            [_qd("Q1", 3, "Solve the linear equation 2x+3=7 for x.", "Basic algebraic manipulation.")],
            "Single-step algebraic solving.", [], [],
            [{"q_id": "Q1", "quote": "Solve the linear equation 2x+3=7 for x."}], [], [], []),
        "Geometry": _judgment(
            [_qd("Q2", 2, "Calculate the area of a triangle with base 4 and height 5.", "Direct formula use.")],
            "Simple direct computation from a known formula.", [], [],
            [{"q_id": "Q2", "quote": "Calculate the area of a triangle with base 4 and height 5."}], [], [], []),
    },
    "per_topic": {
        "Algebra": {"marks_total": 10.0, "mark_fraction": round(10 / 15, 4),
                    "format_distribution": {"short_answer": 1.0}, "dominant_format": "short_answer",
                    "Diff": 3, "Conn": 1, "prerequisites": [],
                    "evaluation_contract_version": CONTRACT_VERSION,
                    "difficulty_contract_version": CONTRACT_VERSION, "is_new_topic": True},
        "Geometry": {"marks_total": 5.0, "mark_fraction": round(5 / 15, 4),
                     "format_distribution": {"explain_derive": 1.0}, "dominant_format": "explain_derive",
                     "Diff": 2, "Conn": 1, "prerequisites": [],
                     "evaluation_contract_version": CONTRACT_VERSION,
                     "difficulty_contract_version": CONTRACT_VERSION, "is_new_topic": True},
    },
}

EXAM_2024 = {
    "evaluation_contract_version": CONTRACT_VERSION,
    "exam_id": "exam_2024", "year": 2024, "year_label": None, "total_marks": 20,
    "source_file": "exam_2024.txt", "processed_at": "2026-01-02T00:00:00",
    "questions": [
        {"q_id": "Q1", "text": "Differentiate f(x) = x^2 + 2x " + _CALC_QUOTE,
         "marks": 15, "format": "write_code_or_proof", "topics": ["Calculus"]},
        {"q_id": "Q2", "text": "Solve the quadratic equation x^2 - 5x + 6 = 0.",
         "marks": 5, "format": "mcq", "topics": ["Algebra"]},
    ],
    "topic_judgments": {
        "Calculus": _judgment(
            [_qd("Q1", 5, "Differentiate f(x) = x^2 + 2x " + _CALC_QUOTE, "First-principles derivation.")],
            "Multi-step derivation from first principles.", ["Algebra"],
            [{"prerequisite": "Algebra", "q_id": "Q1", "quote": _CALC_QUOTE,
              "rationale": "Requires algebraic manipulation background."}],
            [{"q_id": "Q1", "quote": "Differentiate f(x) = x^2 + 2x " + _CALC_QUOTE}],
            [{"prerequisite": "Algebra", "dependent": "Calculus", "q_id": "Q1", "quote": _CALC_QUOTE,
              "rationale": "Differentiation requires algebraic manipulation."}],
            [], ["Algebra"]),
        "Algebra": _judgment(
            [_qd("Q2", 3, "Solve the quadratic equation x^2 - 5x + 6 = 0.", "Standard quadratic solving.")],
            "Standard factoring/quadratic formula use.", [], [],
            [{"q_id": "Q2", "quote": "Solve the quadratic equation x^2 - 5x + 6 = 0."}], [], [], []),
    },
    "per_topic": {
        "Calculus": {"marks_total": 15.0, "mark_fraction": round(15 / 20, 4),
                     "format_distribution": {"write_code_or_proof": 1.0}, "dominant_format": "write_code_or_proof",
                     "Diff": 5, "Conn": 1, "prerequisites": ["Algebra"],
                     "evaluation_contract_version": CONTRACT_VERSION,
                     "difficulty_contract_version": CONTRACT_VERSION, "is_new_topic": True},
        "Algebra": {"marks_total": 5.0, "mark_fraction": round(5 / 20, 4),
                    "format_distribution": {"mcq": 1.0}, "dominant_format": "mcq",
                    "Diff": 3, "Conn": 1, "prerequisites": [],
                    "evaluation_contract_version": CONTRACT_VERSION,
                    "difficulty_contract_version": CONTRACT_VERSION, "is_new_topic": False},
    },
}


def write_course(course_dir: Path):
    """A course folder with two accepted exams and an empty taxonomy — rebuild
    recomputes the taxonomy from topic_judgments, exactly as the real CLI does."""
    parsed = course_dir / "parsed"
    parsed.mkdir(parents=True)
    (parsed / "exam_2023.json").write_text(json.dumps(EXAM_2023), encoding="utf-8")
    (parsed / "exam_2024.json").write_text(json.dumps(EXAM_2024), encoding="utf-8")
    (course_dir / "taxonomy.json").write_text(json.dumps({"topics": {}}), encoding="utf-8")


def dump_xlsx(path: Path) -> dict:
    """Semantic cell content only — never bytes — per acceptance criterion 6."""
    from openpyxl import load_workbook
    wb = load_workbook(str(path), data_only=True)
    return {
        name: [[cell.value for cell in row] for row in wb[name].iter_rows()]
        for name in wb.sheetnames
    }


class ReportsPackageInterfaceTests(unittest.TestCase):
    """The seam itself: what exam_roi.reports promises and refuses to do."""

    def test_module_docstring_states_ownership_and_restrictions(self):
        doc = reports.__doc__ or ""
        for phrase in ("write_xlsx", "write_json", "must NOT",
                       "model", "taxonomy", "course-folder globals"):
            self.assertIn(phrase, doc)

    def test_write_functions_require_an_explicit_destination_argument(self):
        for fn in (reports.write_xlsx, reports.write_json):
            params = list(inspect.signature(fn).parameters)
            self.assertIn("destination", params)

    def test_module_has_no_course_or_output_path_globals(self):
        # The old globals this ticket retires — reports must never read them.
        for name in ("COURSE_FOLDER", "OUTPUT_XLSX", "OUTPUT_JSON", "TAXONOMY_FILE"):
            self.assertFalse(hasattr(reports, name), f"reports must not define {name}")

    def test_module_never_references_a_model_or_llm_call(self):
        source = inspect.getsource(reports)
        for token in ("call_llm", "anthropic", "openai", "ModelClient"):
            self.assertNotIn(token, source)

    def test_importing_reports_needs_no_credentials_and_touches_no_streams(self):
        # A real subprocess, with every *_API_KEY variable stripped, so this
        # actually exercises "no credentials required" rather than assuming it.
        env = {k: v for k, v in os.environ.items() if "API_KEY" not in k}
        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "import exam_roi.reports\n"
            "assert sys.stdout.encoding is not None\n"  # reconfigure() was not called
            "print('import-ok')\n" % str(PIPELINE_DIR)
        )
        result = subprocess.run([sys.executable, "-c", script], env=env,
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "import-ok")

    def test_pipeline_imports_shared_helpers_from_reports_rather_than_duplicating(self):
        self.assertIs(app.exam_labels, reports.exam_labels)
        self.assertIs(app.weighted_fmt, reports.weighted_fmt)
        self.assertIs(app.write_xlsx, reports.write_xlsx)
        self.assertIs(app.write_json, reports.write_json)


class ReportsRenderWithoutCourseStateTests(unittest.TestCase):
    """Rendering runs on a bare snapshot: no setup_course_folder(), no globals."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rows = [{
            "topic": "Algebra", "per_exam": {"exam_2023": {"present": 1, "mark_fraction": 0.6667,
                                                            "marks_total": 10.0, "fmt_score": 2.0}},
            "Freq": 1.0, "G_Marks": 0.6667, "Conn": 1, "Diff": 3, "Fmt": 2.0, "priority": 22.2,
            "rank": 1, "tier": "★ Tier 1", "appearances": 1, "prerequisites": "",
            "difficulty_contract_version": CONTRACT_VERSION, "review_notes": "",
        }]
        self.exam_list = [{"exam_id": "exam_2023", "year": 2023, "total_marks": 15,
                           "source_file": "exam_2023.txt", "processed_at": "2026-01-01T00:00:00",
                           "per_topic": {"Algebra": {}}}]
        self.taxonomy = {"topics": {"Algebra": {"Diff": 3, "Conn": 1}}}

    def test_writes_to_the_exact_destinations_given_not_any_default_location(self):
        out_dir = Path(self.tmp.name) / "wherever"
        out_dir.mkdir()
        xlsx_path = out_dir / "custom.xlsx"
        json_path = out_dir / "custom.json"

        reports.write_xlsx(self.rows, self.exam_list, self.taxonomy, xlsx_path)
        reports.write_json(self.rows, json_path)

        self.assertTrue(xlsx_path.exists())
        self.assertTrue(json_path.exists())
        # Nothing else was created alongside — no implicit default filenames.
        self.assertEqual(sorted(p.name for p in out_dir.iterdir()), ["custom.json", "custom.xlsx"])

    def test_does_not_mutate_the_supplied_taxonomy_or_rows(self):
        taxonomy_before = copy.deepcopy(self.taxonomy)
        rows_before = copy.deepcopy(self.rows)
        destination = Path(self.tmp.name) / "out.xlsx"

        reports.write_xlsx(self.rows, self.exam_list, self.taxonomy, destination)

        self.assertEqual(self.taxonomy, taxonomy_before)
        self.assertEqual(self.rows, rows_before)


class RebuildReportSemanticContentTests(unittest.TestCase):
    """cmd_rebuild's real output, read back and checked cell-by-cell / value-by-value."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.course = Path(self.tmp.name) / "course"
        write_course(self.course)
        from io import StringIO
        from contextlib import redirect_stdout
        with redirect_stdout(StringIO()):
            app.setup_course_folder(self.course)
            self.exit_code = app.cmd_rebuild(None)
        self.ranked = json.loads((self.course / "Exam_ROI_Pipeline.json").read_text(encoding="utf-8"))
        self.sheets = dump_xlsx(self.course / "Exam_ROI_Pipeline.xlsx")

    def test_rebuild_exits_ok(self):
        self.assertEqual(self.exit_code, app.EXIT_OK)

    def test_json_topics_ranked_by_descending_priority_with_contiguous_ranks(self):
        priorities = [row["priority"] for row in self.ranked]
        self.assertEqual(priorities, sorted(priorities, reverse=True))
        self.assertEqual([row["rank"] for row in self.ranked], list(range(1, len(self.ranked) + 1)))
        self.assertEqual({row["topic"] for row in self.ranked}, {"Algebra", "Calculus", "Geometry"})

    def test_json_frequency_and_prerequisites_reflect_the_two_exams(self):
        by_topic = {row["topic"]: row for row in self.ranked}
        # Algebra appears in both exams, Calculus and Geometry in one each.
        self.assertEqual(by_topic["Algebra"]["Freq"], 1.0)
        self.assertEqual(by_topic["Calculus"]["Freq"], 0.5)
        self.assertEqual(by_topic["Geometry"]["Freq"], 0.5)
        self.assertEqual(by_topic["Calculus"]["prerequisites"], "Algebra")
        self.assertEqual(by_topic["Algebra"]["prerequisites"], "")

    def test_json_per_exam_breakdown_carries_presence_and_marks(self):
        by_topic = {row["topic"]: row for row in self.ranked}
        algebra_2023 = by_topic["Algebra"]["per_exam"]["exam_2023"]
        self.assertEqual(algebra_2023["present"], 1)
        self.assertEqual(algebra_2023["mark_fraction"], round(10 / 15, 4))
        geometry_2024 = by_topic["Geometry"]["per_exam"]["exam_2024"]
        self.assertEqual(geometry_2024["present"], 0)

    def test_exactly_one_tier1_topic_for_three_topics(self):
        tier1 = [row for row in self.ranked if row["tier"]]
        self.assertEqual(len(tier1), 1)
        self.assertEqual(tier1[0]["tier"], "★ Tier 1")
        # The highest-priority topic is the one ranked first, and it is Tier 1.
        self.assertEqual(tier1[0]["topic"], self.ranked[0]["topic"])

    def test_xlsx_has_the_three_expected_sheets(self):
        self.assertEqual(set(self.sheets), {"ROI Scores", "Taxonomy", "Exam Log"})

    def test_xlsx_roi_scores_headers_and_row_order_match_the_json(self):
        rows = self.sheets["ROI Scores"]
        headers = rows[2]
        self.assertEqual(headers[0], "Rank")
        self.assertEqual(headers[1], "Tier")
        self.assertEqual(headers[2], "Topic")
        self.assertIn("Priority", headers)
        # Data rows start at sheet row 4 (index 3) and follow the JSON's rank order.
        data_topics = [row[2] for row in rows[3:3 + len(self.ranked)]]
        self.assertEqual(data_topics, [row["topic"] for row in self.ranked])

    def test_xlsx_roi_scores_priority_cell_matches_json_for_top_topic(self):
        rows = self.sheets["ROI Scores"]
        priority_col = self.sheets["ROI Scores"][2].index("Priority")
        top_row = rows[3]
        self.assertEqual(top_row[priority_col], self.ranked[0]["priority"])

    def test_xlsx_taxonomy_sheet_lists_every_topic_with_diff_and_conn(self):
        rows = self.sheets["Taxonomy"]
        self.assertEqual(rows[1], ["Topic", "Diff (1–6)", "Diff contract", "Conn (1–3)",
                                   "First seen", "Appearances", "Prerequisites"])
        data = {row[0]: row for row in rows[2:] if row[0]}
        self.assertEqual(set(data), {"Algebra", "Calculus", "Geometry"})
        self.assertEqual(data["Calculus"][6], "Algebra")  # Prerequisites column

    def test_xlsx_exam_log_sheet_lists_both_exams(self):
        rows = self.sheets["Exam Log"]
        self.assertEqual(rows[1][0], "Exam ID")
        exam_ids = {row[0] for row in rows[2:] if row[0]}
        self.assertEqual(exam_ids, {"exam_2023", "exam_2024"})


class CliRebuildFromBothWorkingDirectoriesTests(unittest.TestCase):
    """Acceptance criterion 2: the real entry point, invoked from repo root and
    from pipeline/, with actual subprocess runs — not just an in-process call."""

    def test_rebuild_produces_identical_semantic_output_from_either_cwd(self):
        outputs = {}
        for label, cwd, entry in (
            ("repo_root", REPO_ROOT, "pipeline/pipeline.py"),
            ("pipeline_dir", PIPELINE_DIR, "pipeline.py"),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                course = Path(tmp) / "course"
                write_course(course)
                result = subprocess.run(
                    [sys.executable, entry, str(course), "rebuild"],
                    cwd=cwd, env=ENV, capture_output=True, text=True, encoding="utf-8",
                )
                self.assertEqual(result.returncode, app.EXIT_OK, result.stdout + result.stderr)
                outputs[label] = {
                    "json": json.loads((course / "Exam_ROI_Pipeline.json").read_text(encoding="utf-8")),
                    "xlsx": dump_xlsx(course / "Exam_ROI_Pipeline.xlsx"),
                }

        self.assertEqual(outputs["repo_root"]["json"], outputs["pipeline_dir"]["json"])
        self.assertEqual(outputs["repo_root"]["xlsx"], outputs["pipeline_dir"]["xlsx"])


if __name__ == "__main__":
    unittest.main()
