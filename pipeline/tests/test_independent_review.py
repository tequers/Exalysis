"""Offline review contracts, correction bounds, and candidate persistence."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_roi.evaluation import CONTRACT_TEXT, contract_metadata
from exam_roi.llm import ModelClient, RequestLimits, TruncatedResponse
from exam_roi.review import CATEGORIES, candidate_digest, review_candidate
from test_candidate_validation import app, question, scores, tag


SOURCE = question()["text"] + "\nQ2 Explain the omitted result. [5 marks]"


def response(category=None, disposition="correction_required"):
    return {
        "disposition": disposition if category else "no_issue",
        "findings": [{
            "category": name,
            "disposition": disposition if name == category else "no_issue",
            "severity": "error" if name == category else "info",
            "rationale": "The source task supports this assessment under the contract.",
            "evidence": ["Q2 Explain the omitted result." if name == "extraction_omissions"
                         else "Use elimination"],
        } for name in CATEGORIES],
    }


def candidate():
    return {**contract_metadata(), "record_kind": "candidate-analysis",
            "candidate_status": "validated", "exam_id": "paper", "questions": [question()],
            "source_provenance": {"sha256": "source-snapshot"}}


class ReviewTests(unittest.TestCase):
    def test_clean_review_receives_source_candidate_contract_and_records_identity(self):
        original = candidate()
        complete = Mock(return_value=json.dumps(response()))
        sdk = Mock()
        client = ModelClient(sdk, "openai", "review-model", RequestLimits(), provider="review-host")
        with patch.object(ModelClient, "__call__", complete):
            reviewed, record = review_candidate(original, SOURCE, enabled=True, client=client)
        self.assertEqual(reviewed, original)
        self.assertEqual(record["disposition"], "no_issue")
        self.assertEqual(record["model"], "review-model")
        self.assertEqual(record["provider"], "review-host")
        self.assertEqual(record["evaluation_contract_version"], contract_metadata()["evaluation_contract_version"])
        system, user = complete.call_args.args
        self.assertIn(CONTRACT_TEXT, system)
        self.assertEqual(json.loads(user), {"source_text": SOURCE, "candidate": original})
        evidence = record["attempts"][0]["result"]["findings"][0]["evidence"][0]
        self.assertEqual(SOURCE[evidence["char_start"]:evidence["char_end"]], evidence["quote"])
        self.assertEqual(record["attempts"][0]["candidate_sha256"], candidate_digest(original))
        self.assertNotIn("independent_review", original)

    def test_disabled_review_makes_no_calls(self):
        client = Mock()
        _, record = review_candidate(candidate(), SOURCE, client=client)
        self.assertFalse(record["enabled"])
        self.assertEqual(record["disposition"], "disabled")
        self.assertEqual(record["attempts"], [])
        client.assert_not_called()

    def test_seeded_findings_in_each_category_block_clean_outcome(self):
        defects = {
            "extraction_omissions": lambda data: data.update(questions=[]),
            "unsupported_claims": lambda data: data["questions"][0].update(text="Prove an invented theorem."),
            "mark_allocation": lambda data: data["questions"][0].update(marks=999),
            "topic_consistency": lambda data: data["questions"][0].update(topics=["Unrelated topic"]),
            "difficulty_rubric": lambda data: data.update(topic_judgments={"Equations": scores(level=6)["Equations"]}),
            "connection_rubric": lambda data: data.update(topic_judgments={"Equations": scores(conn=3)["Equations"]}),
        }
        for category in CATEGORIES:
            with self.subTest(category=category):
                original = candidate()
                defects[category](original)
                reviewer = Mock(return_value=json.dumps(response(category)))
                reviewed, record = review_candidate(original, SOURCE, enabled=True,
                    client=reviewer)
                self.assertEqual(json.loads(reviewer.call_args.args[1])["candidate"], original)
                self.assertEqual(record["disposition"], "needs_review")
                self.assertEqual(record["reason"], "correction_limit_reached")
                self.assertEqual(reviewed, original)
                self.assertEqual(record["attempts"][0]["result"]["disposition"], "correction_required")

    def test_disagreement_abstains_without_requesting_correction(self):
        correct = Mock()
        _, record = review_candidate(candidate(), SOURCE, enabled=True, max_corrections=2,
            correct=correct, client=Mock(return_value=json.dumps(response("difficulty_rubric", "needs_review"))))
        self.assertEqual(record["disposition"], "needs_review")
        correct.assert_not_called()

    def test_malformed_reviews_never_pass(self):
        bad_reviews = ["not json", '{"disposition":"no_issue","findings":[]}',
                       '{"disposition": 1, "disposition": 2, "findings": []}']
        mutations = [
            lambda data: data.update(disposition="no_issue"),
            lambda data: data["findings"][0].update(evidence=[]),
            lambda data: data["findings"][0].update(evidence=["invented quote"]),
            lambda data: data["findings"][0].update(severity="info"),
            lambda data: data["findings"][0].update(disposition=[]),
            lambda data: data["findings"][0].update(category="unknown"),
            lambda data: data["findings"][0].update(category=CATEGORIES[1]),
            lambda data: data.update(corrected_candidate=candidate()),
        ]
        for mutate in mutations:
            data = response(CATEGORIES[0])
            mutate(data)
            bad_reviews.append(json.dumps(data))
        for raw in bad_reviews:
            with self.subTest(raw=raw):
                _, record = review_candidate(candidate(), SOURCE, enabled=True, client=Mock(return_value=raw))
                self.assertEqual(record["reason"], "reviewer_failed")
                self.assertEqual(record["disposition"], "needs_review")

    def test_missing_unavailable_truncated_or_oversized_reviewer_never_passes(self):
        for client in (None, Mock(side_effect=RuntimeError("offline")),
                       Mock(side_effect=TruncatedResponse("cut off"))):
            _, record = review_candidate(candidate(), SOURCE, enabled=True, client=client)
            self.assertEqual(record["reason"], "reviewer_failed")
        client = Mock()
        _, record = review_candidate(candidate(), SOURCE, enabled=True, client=client,
                                      limits=RequestLimits(100, 20, 1))
        self.assertEqual(record["reason"], "reviewer_failed")
        client.assert_not_called()

    def test_corrections_are_separate_revisions_with_fresh_reviews(self):
        original = candidate()
        revised = candidate()
        revised["questions"].append({"q_id": "Q2", "text": "Explain the omitted result."})
        correct = Mock(return_value=revised)
        reviewer = Mock(side_effect=[json.dumps(response(CATEGORIES[0])), json.dumps(response())])
        result, record = review_candidate(original, SOURCE, enabled=True, client=reviewer,
                                          correct=correct, max_corrections=1)
        self.assertEqual(result, revised)
        self.assertEqual(record["disposition"], "no_issue")
        self.assertEqual(record["correction_attempts"], 1)
        self.assertEqual(len(record["attempts"]), 2)
        self.assertEqual(record["attempts"][0]["candidate"], original)
        self.assertEqual(record["attempts"][1]["candidate"], revised)
        self.assertEqual(json.loads(reviewer.call_args.args[1])["candidate"], revised)

    def test_retry_exhaustion_and_failed_correction_preserve_last_candidate(self):
        correct = Mock(side_effect=lambda old, findings: old)
        result, record = review_candidate(candidate(), SOURCE, enabled=True,
            client=Mock(return_value=json.dumps(response(CATEGORIES[0]))), correct=correct, max_corrections=2)
        self.assertEqual(record["disposition"], "needs_review")
        self.assertEqual(record["reason"], "correction_limit_reached")
        self.assertEqual(correct.call_count, 2)
        self.assertEqual(len(record["attempts"]), 3)
        for correction in (Mock(side_effect=ValueError("invalid candidate")),
                           Mock(return_value={**candidate(), "exam_id": "other"})):
            result, record = review_candidate(candidate(), SOURCE, enabled=True,
                client=Mock(return_value=json.dumps(response(CATEGORIES[0]))), correct=correction, max_corrections=1)
            self.assertEqual(result, candidate())
            self.assertEqual(record["reason"], "correction_failed")

    def test_contract_mismatch_and_invalid_bounds(self):
        old = {**candidate(), "evaluation_contract_version": "old"}
        client = Mock()
        _, record = review_candidate(old, SOURCE, enabled=True, client=client)
        self.assertEqual(record["reason"], "reviewer_failed")
        client.assert_not_called()
        for bound in (-1, 3, True, 1.5):
            with self.assertRaises(ValueError):
                review_candidate(candidate(), SOURCE, max_corrections=bound)


class ReviewPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = io.StringIO()
        self.redirect = redirect_stdout(self.output)
        self.redirect.__enter__()
        self.addCleanup(self.redirect.__exit__, None, None, None)
        self.folder = Path(self.temp.name)
        self.context = app.setup_course_folder(self.folder)
        self.paper = self.folder / "paper.txt"
        self.paper.write_text(SOURCE, encoding="utf-8")
        app.save_taxonomy({"topics": {}}, course=self.context)
        self.taxonomy_before = self.context.taxonomy_file.read_bytes()
        self.context.parsed_dir.mkdir()
        self.accepted = self.context.parsed_dir / "paper.json"
        self.accepted.write_text(json.dumps({"exam_id": "paper", "per_topic": {}}), encoding="utf-8")
        self.accepted_before = self.accepted.read_bytes()

    def run_candidate(self, reviewer=None, score_responses=None, **kwargs):
        q = question()
        q.pop("topics")
        if reviewer is None:
            configured = app.configure_reviewer(dict(app.os.environ), "anthropic")
            reviewer = configured.pop("reviewer_client")
            kwargs.update(configured)
        with patch.object(app, "stage1_extract", return_value=([q], 2026)), \
             patch.object(app, "_stage2_tag", return_value=({"Q1": tag(["Equations"])}, ["Equations"])), \
             patch.object(app, "call_llm", return_value=json.dumps(scores()), side_effect=score_responses):
            app.process_exam_file(self.paper, force=True, review_enabled=True,
                                  reviewer_client=reviewer, **kwargs, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        self.assertEqual(self.context.taxonomy_file.read_bytes(), self.taxonomy_before)
        self.assertEqual(self.accepted.read_bytes(), self.accepted_before)
        return json.loads((self.context.candidates_dir / "paper.json").read_text(encoding="utf-8"))

    def test_review_failure_is_saved_and_visible(self):
        saved = self.run_candidate(Mock(side_effect=RuntimeError("offline")))
        self.assertEqual(saved["candidate_status"], "needs-review")
        self.assertEqual(saved["independent_review"]["reason"], "reviewer_failed")
        self.assertIn("reviewer_failed", self.output.getvalue())

    def test_clean_review_does_not_accept_or_clear_existing_uncertainty(self):
        saved = self.run_candidate(Mock(return_value=json.dumps(response())))
        self.assertEqual(saved["candidate_status"], "validated")
        self.assertEqual(saved["record_kind"], "candidate-analysis")
        self.assertEqual(saved["independent_review"]["disposition"], "no_issue")
        original_finalize = app.finalize_candidate_analysis
        def uncertain_candidate(*args):
            result = original_finalize(*args)
            result["candidate_status"] = "needs-review"
            return result
        with patch.object(app, "finalize_candidate_analysis", side_effect=uncertain_candidate):
            saved = self.run_candidate(Mock(return_value=json.dumps(response())))
        self.assertEqual(saved["candidate_status"], "needs-review")

    def test_cli_configuration_uses_separate_model_and_budget(self):
        with patch.dict(app.os.environ, {"LLM_REVIEW_PROVIDER": "openai", "LLM_REVIEW_MODEL": "separate",
                "LLM_REVIEW_CONTEXT_TOKENS": "250000", "LLM_REVIEW_MAX_OUTPUT_TOKENS": "4000"}), \
             patch.object(app, "configured_model_client", return_value=Mock(return_value=json.dumps(response()))) as factory:
            saved = self.run_candidate()
        self.assertEqual(factory.call_args.args, ("openai", "separate", RequestLimits(250000, 4000, 1024)))
        self.assertEqual(saved["independent_review"]["model"], "separate")
        self.assertEqual(saved["independent_review"]["provider"], "openai")

    def test_bad_config_and_missing_credentials_are_saved_as_review_failures(self):
        with patch.dict(app.os.environ, {"LLM_REVIEW_CONTEXT_TOKENS": "bad"}):
            saved = self.run_candidate()
        self.assertEqual(saved["independent_review"]["reason"], "reviewer_failed")
        with patch.dict(app.os.environ, {"LLM_REVIEW_PROVIDER": "openai", "LLM_REVIEW_MODEL": "separate",
                                        "OPENAI_API_KEY": ""}):
            saved = self.run_candidate()
        self.assertEqual(saved["independent_review"]["reason"], "reviewer_failed")

    def test_pipeline_rebuilds_then_reviews_corrections_and_retains_history(self):
        reviewer = Mock(side_effect=[json.dumps(response("difficulty_rubric")), json.dumps(response())])
        with patch.object(app, "_with_review_feedback", wraps=app._with_review_feedback) as feedback:
            saved = self.run_candidate(reviewer, max_corrections=1,
                score_responses=[json.dumps(scores(level=4)), json.dumps(scores(level=3))])
        history = saved["independent_review"]["attempts"]
        self.assertEqual(history[0]["candidate"]["per_topic"]["Equations"]["Diff"], 4)
        self.assertEqual(history[1]["candidate"]["per_topic"]["Equations"]["Diff"], 3)
        self.assertEqual(feedback.call_count, 2)
        self.assertEqual(reviewer.call_count, 2)
        self.assertEqual(saved["independent_review"]["correction_attempts"], 1)
        self.assertEqual(len(saved["independent_review"]["attempts"]), 2)

    def test_invalid_analyzer_correction_is_not_saved_as_a_revision(self):
        reviewer = Mock(return_value=json.dumps(response("difficulty_rubric")))
        saved = self.run_candidate(reviewer, max_corrections=1,
            score_responses=[json.dumps(scores()), json.dumps(scores(level=7))])
        self.assertEqual(saved["candidate_status"], "needs-review")
        self.assertEqual(saved["independent_review"]["reason"], "correction_failed")
        self.assertEqual(saved["per_topic"]["Equations"]["Diff"], 3)
        self.assertEqual(reviewer.call_count, 1)

    def test_feedback_reaches_analyzer_and_counts_toward_request_budget(self):
        analyzer = Mock(return_value="complete answer")
        feedback = response("difficulty_rubric")
        request = app._with_review_feedback(2, analyzer, RequestLimits(), feedback)
        request["client"]("system", "source", max_tokens=100)
        self.assertIn(json.dumps(feedback), analyzer.call_args.args[1])
        analyzer.reset_mock()
        request = app._with_review_feedback(2, analyzer, RequestLimits(100, 20, 1), feedback)
        with self.assertRaises(ValueError):
            request["client"]("system", "source", max_tokens=20)
        analyzer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
