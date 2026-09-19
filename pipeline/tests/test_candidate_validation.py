"""Deterministic validation checks for ticket 02; no model calls required."""

import copy
from contextlib import redirect_stdout
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch


PIPELINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE))

from exam_roi.evaluation import (
    CandidateValidationError,
    validate_extraction,
    validate_tags,
    validate_topic_scores,
)

with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}):
    app = importlib.import_module("pipeline")


def question(q_id="Q1"):
    return {
        "q_id": q_id,
        "text": "Use elimination to solve the two equations.",
        "marks": 10,
        "format": "short_answer",
        "topics": ["Equations"],
    }


def scores(level=3, conn=1):
    return {"Equations": {
        "question_difficulty": [{
            "q_id": "Q1", "level": level, "quote": "Use elimination",
            "rationale": "This follows a standard multi-step method.", "uncertainties": [],
        }],
        "difficulty_rationale": "The question requires a standard sequence of steps.",
        "assumed_prerequisites": [],
        "prerequisite_evidence": [],
        "Conn": conn,
        "connection_rationale": "No direct downstream use is supported.",
        "connection_evidence": [{"q_id": "Q1", "quote": "Use elimination"}],
        "connection_edges": [],
        "unlocks": [],
        "prerequisites": [],
        "uncertainties": [],
    }}


def tag(topics, quote="Use elimination", uncertainties=None):
    return {
        "topics": topics,
        "quote": quote,
        "rationale": "The cited task directly tests these topics.",
        "uncertainties": uncertainties or [],
    }


class ResponseValidationTests(unittest.TestCase):
    def test_malformed_and_duplicate_key_json_are_rejected(self):
        for raw, message in [
            ('{"questions": [}', "malformed JSON"),
            ('{"tags": {}, "tags": {}, "new_topic_names": []}', "duplicate object key"),
            ('before {"tags": {}, "new_topic_names": []}', "no surrounding prose"),
        ]:
            with self.subTest(raw=raw), self.assertRaisesRegex(CandidateValidationError, message):
                app.parse_json_from(raw)

    def test_extraction_requires_complete_unique_questions_and_supported_values(self):
        valid = {"exam_year": 2026, "questions": [
            {key: value for key, value in question().items() if key != "topics"}
        ]}
        clean, year = validate_extraction(valid, 1990, 2027)
        self.assertEqual(year, 2026)
        self.assertEqual(clean[0]["q_id"], "Q1")

        invalid = []
        bare = copy.deepcopy(valid)["questions"]
        invalid.append(bare)
        duplicate = copy.deepcopy(valid)
        duplicate["questions"].append(copy.deepcopy(duplicate["questions"][0]))
        invalid.append(duplicate)
        unsupported = copy.deepcopy(valid)
        unsupported["questions"][0]["format"] = "essay"
        invalid.append(unsupported)
        wrong_format_type = copy.deepcopy(valid)
        wrong_format_type["questions"][0]["format"] = []
        invalid.append(wrong_format_type)
        nonfinite = copy.deepcopy(valid)
        nonfinite["questions"][0]["marks"] = float("inf")
        invalid.append(nonfinite)
        wrong_type = copy.deepcopy(valid)
        wrong_type["questions"][0]["marks"] = True
        invalid.append(wrong_type)
        missing = copy.deepcopy(valid)
        del missing["questions"][0]["text"]
        invalid.append(missing)

        for candidate in invalid:
            with self.subTest(candidate=candidate), self.assertRaises(CandidateValidationError):
                validate_extraction(candidate, 1990, 2027)

    def test_tags_require_exact_id_coverage_and_one_or_two_distinct_labels(self):
        questions = [question("Q1"), question("Q2")]
        valid = {"tags": {"Q1": tag(["Known"]), "Q2": tag(["Known", "New"])},
                 "new_topic_names": ["New"]}
        tags, new_names = validate_tags(valid, questions, ["Known"])
        self.assertEqual(tags, valid["tags"])
        self.assertEqual(new_names, ["New"])

        invalid = [
            {"tags": {"Q1": tag(["Known"])}, "new_topic_names": []},
            {"tags": {"Q1": tag(["Known"]), "Q2": tag(["Known"]),
                      "Q3": tag(["Known"])},
             "new_topic_names": []},
            {"tags": {"Q1": tag([]), "Q2": tag(["Known"])}, "new_topic_names": []},
            {"tags": {"Q1": tag(["Known", "Known"]), "Q2": tag(["Known"])},
             "new_topic_names": []},
            {"tags": {"Q1": tag(["Known", "New", "Third"]),
                      "Q2": tag(["Known"])},
             "new_topic_names": ["New", "Third"]},
            {"tags": {"Q1": tag(["Undeclared"]), "Q2": tag(["Known"])},
             "new_topic_names": []},
            {"tags": {"Q1": tag(["Known"], quote="invented"),
                      "Q2": tag(["Known"])}, "new_topic_names": []},
        ]
        for candidate in invalid:
            with self.subTest(candidate=candidate), self.assertRaises(CandidateValidationError):
                validate_tags(candidate, questions, ["Known"])

    def test_scores_reject_incomplete_coverage_wrong_types_and_invalid_ranges(self):
        tagged = [question()]
        unsupported_topic = scores()
        unsupported_topic["Equations"]["invented_score"] = 99
        unsupported_evidence = scores()
        unsupported_evidence["Equations"]["question_difficulty"][0]["confidence"] = 0.9
        for candidate in [
            {},
            {"Unexpected": scores()["Equations"]},
            scores(level=None),
            scores(level=7),
            scores(level=2.5),
            scores(conn=0),
            scores(conn=4),
            scores(conn=True),
            unsupported_topic,
            unsupported_evidence,
        ]:
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                validate_topic_scores(candidate, ["Equations"], tagged, ["Equations"])

    def test_scores_accept_conn_that_does_not_match_unlock_count(self):
        result = validate_topic_scores(
            scores(conn=2), ["Equations"], [question()], ["Equations"])

        self.assertEqual(result["Equations"]["Conn"], 2)


class Stage2CorrectionTests(unittest.TestCase):
    def test_invalid_tag_quote_gets_one_complete_correction_attempt(self):
        invalid_tags = {"tags": {"Q1": tag(["Equations"], quote="invented quote")},
                        "new_topic_names": []}
        valid_tags = {"tags": {"Q1": tag(["Equations"])}, "new_topic_names": []}
        client = Mock(side_effect=[
            json.dumps(invalid_tags), json.dumps(valid_tags), json.dumps(scores()),
        ])
        output = io.StringIO()

        with redirect_stdout(output):
            result = app.stage2_tag_score(
                [question()], {"topics": {"Equations": {"Diff": 3, "Conn": 1}}},
                10, client=client,
            )

        self.assertEqual(client.call_count, 3)
        correction_prompt = client.call_args_list[1].args[1]
        self.assertIn("Q1 tag quote is absent from its source question", correction_prompt)
        self.assertIn("Return the complete corrected JSON", correction_prompt)
        self.assertIn("correction attempt 1/1", output.getvalue())
        self.assertEqual(result["questions"][0]["topic_tagging"]["quote"], "Use elimination")


class RejectionSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.context = app.setup_course_folder(self.folder)
        self.context.parsed_dir.mkdir()
        self.paper = self.folder / "paper.txt"
        self.paper.write_text(question()["text"], encoding="utf-8")
        app.save_taxonomy({"topics": {"Accepted": {"Diff": 2, "Conn": 1}}}, course=self.context)
        self.accepted = self.context.parsed_dir / "paper.json"
        self.accepted.write_text(json.dumps({
            "exam_id": "paper", "per_topic": {},
            "source_path": str(self.paper.resolve()), "sentinel": "accepted"
        }), encoding="utf-8")

    def test_rejected_reparse_leaves_accepted_paper_and_taxonomy_unchanged(self):
        before_taxonomy = self.context.taxonomy_file.read_bytes()
        before_paper = self.accepted.read_bytes()
        extraction = {"exam_year": 2026, "questions": [
            {key: value for key, value in question().items() if key != "topics"}
        ]}
        incomplete_tags = {"tags": {}, "new_topic_names": []}
        with patch.object(app, "call_llm", side_effect=[
                json.dumps(extraction), json.dumps(incomplete_tags),
                json.dumps(incomplete_tags)]):
            with self.assertRaisesRegex(CandidateValidationError, "missing IDs: Q1") as raised:
                app.process_exam_file(self.paper, force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        self.assertEqual(raised.exception.disposition, "correction_required")
        self.assertEqual(self.context.taxonomy_file.read_bytes(), before_taxonomy)
        self.assertEqual(self.accepted.read_bytes(), before_paper)

    def test_unresolved_difficulty_requests_review_without_changing_state(self):
        before_taxonomy = self.context.taxonomy_file.read_bytes()
        before_paper = self.accepted.read_bytes()
        unresolved = scores(level=None)
        with patch.object(app, "stage1_extract", return_value=([{
                key: value for key, value in question().items() if key != "topics"
             }], 2026)), \
             patch.object(app, "_stage2_tag", return_value=({"Q1": tag(["Equations"])}, ["Equations"])), \
             patch.object(app, "call_llm", return_value=json.dumps(unresolved)):
            with self.assertRaises(CandidateValidationError) as raised:
                app.process_exam_file(self.paper, force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        self.assertEqual(raised.exception.disposition, "needs_review")
        self.assertEqual(self.context.taxonomy_file.read_bytes(), before_taxonomy)
        self.assertEqual(self.accepted.read_bytes(), before_paper)

    def test_valid_candidate_records_contract_source_and_model_provenance(self):
        q = question()
        q.pop("topics")
        with patch.object(app, "stage1_extract", return_value=([q], 2026)), \
             patch.object(app, "_stage2_tag", return_value=({"Q1": tag(["Equations"])}, ["Equations"])), \
             patch.object(app, "call_llm", return_value=json.dumps(scores())):
            app.process_exam_file(self.paper, force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        self.assertEqual(json.loads(self.accepted.read_text(encoding="utf-8"))["sentinel"], "accepted")
        candidate_path = self.context.candidates_dir / "paper.json"
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        self.assertEqual(candidate["record_kind"], "candidate-analysis")
        self.assertEqual(candidate["candidate_status"], "validated")
        self.assertEqual(candidate["source_provenance"]["file_name"], "paper.txt")
        self.assertEqual(len(candidate["source_provenance"]["sha256"]), 64)
        self.assertEqual(candidate["model_provenance"], {
            "provider": "injected-callable",
            "extraction_model": "injected-callable",
            "analysis_model": "injected-callable",
        })
        self.assertEqual(candidate["proposed_taxonomy_changes"]["new_topic_names"], ["Equations"])
        self.assertIn("Equations", candidate["proposed_taxonomy_changes"]["topics"])
        self.assertEqual(candidate["questions"][0]["topics"], ["Equations"])
        self.assertEqual(candidate["questions"][0]["topic_tagging"]["quote"], "Use elimination")
        self.assertTrue(candidate["topic_judgments"]["Equations"]["difficulty_rationale"])

    def test_explicit_uncertainty_saves_needs_review_candidate_only(self):
        q = question()
        q.pop("topics")
        uncertain_tag = tag(["Equations"], uncertainties=["The wording may also test matrices."])
        with patch.object(app, "stage1_extract", return_value=([q], 2026)), \
             patch.object(app, "_stage2_tag", return_value=({"Q1": uncertain_tag}, ["Equations"])), \
             patch.object(app, "call_llm", return_value=json.dumps(scores())):
            app.process_exam_file(self.paper, force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        candidate = json.loads((self.context.candidates_dir / "paper.json").read_text(encoding="utf-8"))
        self.assertEqual(candidate["candidate_status"], "needs-review")
        self.assertEqual(json.loads(self.accepted.read_text(encoding="utf-8"))["sentinel"], "accepted")
        self.assertEqual(app.load_taxonomy(course=self.context), {"topics": {"Accepted": {"Diff": 2, "Conn": 1}}})

    def test_dependency_cycle_saves_needs_review_candidate(self):
        text = "A and B depend on each other."
        self.paper.write_text(text, encoding="utf-8")
        q = {"q_id": "Q1", "text": text, "marks": 10, "format": "short_answer"}

        def topic_score(name, prerequisite, dependent):
            return {
                "question_difficulty": [{"q_id": "Q1", "level": 3, "quote": text,
                    "rationale": "A standard multi-step method is required.", "uncertainties": []}],
                "difficulty_rationale": "The task uses a standard method.",
                "assumed_prerequisites": [], "prerequisite_evidence": [],
                "Conn": 2, "connection_rationale": "One direct dependent is supported.",
                "connection_evidence": [{"q_id": "Q1", "quote": text}],
                "connection_edges": [
                    {"prerequisite": "A", "dependent": "B", "q_id": "Q1", "quote": text,
                     "rationale": "The task states the dependency."},
                    {"prerequisite": "B", "dependent": "A", "q_id": "Q1", "quote": text,
                     "rationale": "The task states the dependency."},
                ],
                "unlocks": [dependent], "prerequisites": [prerequisite], "uncertainties": [],
            }

        answer = {"A": topic_score("A", "B", "B"), "B": topic_score("B", "A", "A")}
        tags = {"Q1": tag(["A", "B"], quote=text)}
        with patch.object(app, "stage1_extract", return_value=([q], 2026)), \
             patch.object(app, "_stage2_tag", return_value=(tags, ["A", "B"])), \
             patch.object(app, "call_llm", return_value=json.dumps(answer)):
            app.process_exam_file(self.paper, force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        candidate = json.loads((self.context.candidates_dir / "paper.json").read_text(encoding="utf-8"))
        self.assertEqual(candidate["candidate_status"], "needs-review")
        self.assertTrue(candidate["proposed_taxonomy_changes"]["topics"]["A"]
                        ["connection_review_required"])

    def test_provenance_hashes_the_exact_source_snapshot_analyzed(self):
        original = self.paper.read_bytes()
        q = question()
        q.pop("topics")

        def extract_then_change_source(_text, _total_marks, **_kwargs):
            self.paper.write_text("changed after extraction", encoding="utf-8")
            return [q], 2026

        with patch.object(app, "stage1_extract", side_effect=extract_then_change_source), \
             patch.object(app, "_stage2_tag", return_value=({"Q1": tag(["Equations"])}, ["Equations"])), \
             patch.object(app, "call_llm", return_value=json.dumps(scores())):
            app.process_exam_file(self.paper, force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        candidate = json.loads((self.context.candidates_dir / "paper.json").read_text(encoding="utf-8"))
        self.assertEqual(candidate["source_provenance"]["sha256"], hashlib.sha256(original).hexdigest())


if __name__ == "__main__":
    unittest.main()
