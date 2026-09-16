"""Exercise real stage prompts and validation with offline response transcripts."""

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline as app
import staged_evaluation as evaluation


FIXTURES = Path(__file__).parent / "fixtures" / "staged_evaluation"
CASE_PATH = FIXTURES / "equations-case.json"


def synthetic_responses(case, level=3):
    """Handwritten protocol examples, never claimed to be reviewed model truth."""
    extraction = deepcopy(case["frozen_stage1"])
    for question in extraction["questions"]:
        question.pop("source_context", None)
    tags = {"tags": {}, "new_topic_names": []}
    difficulty = []
    for index, question in enumerate(extraction["questions"]):
        tags["tags"][question["q_id"]] = {
            "topics": ["Linear equations"], "quote": question["text"],
            "rationale": "The task explicitly tests linear equations.", "uncertainties": [],
        }
        difficulty.append({"q_id": question["q_id"], "level": 1 if index == 0 else level,
                           "quote": question["text"], "rationale": "Definition recall." if index == 0
                           else "Apply elimination and substitution in sequence.", "uncertainties": []})
    scores = {"Linear equations": {
        "question_difficulty": difficulty,
        "difficulty_rationale": "Definition recall and a standard solution method.",
        "assumed_prerequisites": [], "prerequisite_evidence": [], "Conn": 1,
        "connection_rationale": "No other downstream topic is tested.",
        "connection_evidence": [{"q_id": "Q1", "quote": "Define a linear equation."}],
        "connection_edges": [], "unlocks": [], "prerequisites": [], "uncertainties": [],
    }}
    return extraction, tags, scores


def synthetic_capture(case, responses=None):
    extraction, tags, scores = responses or synthetic_responses(case)

    def factory(name, stage):
        values = iter([extraction] if stage == 1 else [tags, scores])
        return lambda system, user, max_tokens: json.dumps(next(values))

    return evaluation.evaluate_case(case, client_factory=factory, provider="synthetic-test",
                                    model="handwritten-protocol-example",
                                    generated_at="2026-09-15T00:00:00+00:00")


class StagedEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.case = evaluation.read_json(CASE_PATH)

    def assertPassed(self, report):
        self.assertEqual(report["status"], "passed", json.dumps(report["runs"], indent=2))

    def test_real_independent_and_chained_stages_capture_validated_results(self):
        before = deepcopy(self.case)
        report = synthetic_capture(self.case)
        self.assertPassed(report)
        self.assertEqual(self.case, before)
        self.assertEqual(set(report["runs"]), set(evaluation.RUNS))
        self.assertEqual(report["human_review"], {"status": "pending"})
        self.assertEqual(report["runs"]["stage1"]["result"], self.case["frozen_stage1"])
        self.assertEqual(report["runs"]["stage2"]["input"], self.case["frozen_stage1"])
        chained = report["runs"]["chain_stage2"]
        self.assertEqual(chained["input"], report["runs"]["chain_stage1"]["result"])
        self.assertEqual(chained["result"]["record_kind"], "candidate-analysis")
        self.assertEqual(chained["result"]["per_topic"]["Linear equations"]["marks_total"], 10)
        self.assertEqual(chained["result"]["per_topic"]["Linear equations"]["Diff"], 1)
        self.assertEqual(len(chained["calls"]), 2)
        for name, stage in evaluation.RUNS.items():
            record = report["runs"][name]
            for call in record["calls"]:
                self.assertEqual(call["request"]["system"], app._S1_SYSTEM if stage == 1 else app._S2_SYSTEM)
                self.assertEqual(call["prompt_sha256"], evaluation.digest(call["request"]))
                self.assertTrue(call["generated_at"])
                self.assertEqual(call["model"], "handwritten-protocol-example")

    def test_replay_uses_no_credentials_network_or_provider(self):
        report = synthetic_capture(self.case)
        with patch.dict(os.environ, {}, clear=True), \
             patch("socket.socket", side_effect=AssertionError("Network forbidden")), \
             patch.object(app, "configure_model_clients", side_effect=AssertionError("Provider forbidden")):
            replayed = evaluation.replay(report, require_reference=False)
        self.assertPassed(replayed)
        for name in evaluation.RUNS:
            self.assertEqual(replayed["runs"][name]["result"], report["runs"][name]["result"])

    def test_stage1_failure_cannot_be_hidden_by_independent_stage2(self):
        extraction, tags, scores = synthetic_responses(self.case)
        extraction["questions"][0]["marks"] = 3
        report = synthetic_capture(self.case, (extraction, tags, scores))
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["runs"]["stage1"]["status"], "failed")
        self.assertEqual(report["runs"]["stage2"]["status"], "passed")
        self.assertEqual(report["runs"]["chain_stage2"]["status"], "failed")
        self.assertIn("result", report["runs"]["chain_stage2"])
        self.assertTrue(report["runs"]["stage1"]["exact_failures"])

    def test_missing_questions_and_invalid_evidence_fail_at_production_boundaries(self):
        for fault in ("missing_question", "invented_quote", "malformed_json"):
            with self.subTest(fault=fault):
                extraction, tags, scores = synthetic_responses(self.case)
                if fault == "missing_question":
                    extraction["questions"].pop()
                elif fault == "invented_quote":
                    tags["tags"]["Q1"]["quote"] = "This was not printed"
                if fault == "malformed_json":
                    report = evaluation.evaluate_case(
                        self.case, extraction_client=lambda *a, **k: "{broken",
                        analysis_client=lambda *a, **k: "{broken")
                else:
                    report = synthetic_capture(self.case, (extraction, tags, scores))
                self.assertEqual(report["status"], "failed")
                stage = "stage2" if fault == "invented_quote" else "stage1"
                self.assertEqual(report["runs"][stage]["error_type"], "CandidateValidationError")

    def test_documented_judgment_choices_are_separate_from_exact_arithmetic(self):
        tolerated = synthetic_capture(self.case, synthetic_responses(self.case, level=2))
        self.assertPassed(tolerated)
        rejected = synthetic_capture(self.case, synthetic_responses(self.case, level=4))
        self.assertEqual(rejected["runs"]["stage2"]["exact_failures"], [])
        self.assertTrue(rejected["runs"]["stage2"]["judgment_failures"])
        self.case["expectations"]["local_values"]["/per_topic/Linear equations/marks_total"] = 11
        arithmetic = synthetic_capture(self.case)
        self.assertTrue(arithmetic["runs"]["stage2"]["exact_failures"])
        self.assertEqual(arithmetic["runs"]["stage2"]["judgment_failures"], [])

    def test_stage2_cannot_change_extraction_fields(self):
        original = app.stage2_tag_score

        def lose_marks(*args, **kwargs):
            result = original(*args, **kwargs)
            result["questions"][0]["marks"] = 99
            return result

        with patch.object(app, "stage2_tag_score", side_effect=lose_marks):
            report = synthetic_capture(self.case)
        self.assertEqual(report["runs"]["stage1"]["status"], "passed")
        self.assertIn("Stage 2 changed", report["runs"]["stage2"]["error"])
        self.assertEqual(report["status"], "failed")

    def test_candidate_keeps_new_topic_proposals_and_uncertainty(self):
        self.case["taxonomy"]["topics"] = {}
        self.case["expectations"]["new_topic_names"] = [["Linear equations"]]
        extraction, tags, scores = synthetic_responses(self.case)
        tags["new_topic_names"] = ["Linear equations"]
        tags["tags"]["Q1"]["uncertainties"] = ["Course taxonomy has no existing labels."]
        report = synthetic_capture(self.case, (extraction, tags, scores))
        self.assertPassed(report)
        candidate = report["runs"]["stage2"]["result"]
        self.assertEqual(candidate["candidate_status"], "needs-review")
        self.assertEqual(candidate["new_topic_names"], ["Linear equations"])
        self.assertEqual(candidate["questions"][0]["topic_tagging"]["uncertainties"],
                         ["Course taxonomy has no existing labels."])

    def test_exchange_exports_and_resumes_exact_requests(self):
        answers = {}
        extraction, tags, scores = synthetic_responses(self.case)
        for _ in range(4):
            report = evaluation.evaluate_case(
                self.case, model="gpt-subagent-test",
                client_factory=lambda name, stage: evaluation.ExchangeClient(name, answers))
            for name, record in report["runs"].items():
                if record["status"] != "pending":
                    continue
                call = record["calls"][-1]
                response = extraction if evaluation.RUNS[name] == 1 else tags if len(record["calls"]) == 1 else scores
                answers[call["request_id"]] = json.dumps(response)
        self.assertPassed(report)
        self.assertEqual(len(answers), 6)

    def test_reference_requires_human_approval_and_any_edit_invalidates_it(self):
        report = synthetic_capture(self.case)
        with self.assertRaisesRegex(ValueError, "person must approve"):
            evaluation.replay(report)
        # A simulated reviewer tests the boundary; this is not fixture approval.
        report["human_review"] = {"status": "approved", "reviewer": "test-only-person",
            "reviewed_at": "2026-09-15", "notes": "Test of approval gate only.",
            "content_sha256": evaluation.review_digest(report)}
        self.assertPassed(evaluation.replay(report))
        for path in ("case", "response", "result"):
            altered = deepcopy(report)
            if path == "case":
                altered["case"]["source_text"] += "changed"
            elif path == "response":
                altered["runs"]["stage1"]["calls"][0]["response"] += " "
            else:
                altered["runs"]["stage2"]["result"]["total_marks"] = 11
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "person must approve"):
                evaluation.replay(altered)

    def test_cli_records_content_bound_approval_only_after_passing_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            capture = Path(directory) / "capture.json"
            approved = Path(directory) / "approved.json"
            report = synthetic_capture(self.case)
            evaluation.write_new_json(capture, report)
            arguments = ["approve", str(capture), "--reviewer", "test-only-person",
                         "--notes", "Simulated approval boundary test, not actual fixture approval.",
                         "--output", str(approved), "--content-sha256"]
            self.assertEqual(evaluation.main(arguments + ["wrong-hash"]), 2)
            self.assertFalse(approved.exists())
            self.assertEqual(evaluation.main(arguments + [evaluation.review_digest(report)]), 0)
            self.assertPassed(evaluation.replay(evaluation.read_json(approved)))

    def test_complete_failing_evidence_replays_with_same_failure_and_no_truth_adoption(self):
        extraction, tags, scores = synthetic_responses(self.case)
        extraction["questions"][0]["text"] = "Q1. Define a linear equation. [4 marks]"
        report = synthetic_capture(self.case, (extraction, tags, scores))
        self.assertEqual(report["status"], "failed")
        replayed = evaluation.replay(report, require_reference=False)
        self.assertEqual(replayed["status"], "failed")
        for name in evaluation.RUNS:
            self.assertNotIn("replay_error", replayed["runs"][name])
            self.assertEqual(replayed["runs"][name].get("exact_failures"),
                             report["runs"][name].get("exact_failures"))
        with self.assertRaisesRegex(ValueError, "person must approve"):
            evaluation.replay(report)

    def test_saved_gpt_evidence_reproduces_the_observed_stage_findings_offline(self):
        captured = evaluation.read_json(FIXTURES / "astra-evidence.json")
        self.assertEqual(captured["model"], "gpt-6-astra")
        self.assertEqual(captured["human_review"]["status"], "pending")
        self.assertEqual(sum(len(r["calls"]) for r in captured["runs"].values()), 6)
        with patch.dict(os.environ, {}, clear=True), \
             patch("socket.socket", side_effect=AssertionError("Network forbidden")), \
             patch.object(app, "configure_model_clients", side_effect=AssertionError("Provider forbidden")):
            replayed = evaluation.replay(captured, require_reference=False)
        self.assertEqual(replayed["status"], "failed")
        self.assertEqual(replayed["runs"]["stage2"]["status"], "passed")
        for name in evaluation.RUNS:
            self.assertNotIn("replay_error", replayed["runs"][name])
            self.assertEqual(replayed["runs"][name]["result"], captured["runs"][name]["result"])
            self.assertEqual(replayed["runs"][name]["exact_failures"],
                             captured["runs"][name]["exact_failures"])
        with self.assertRaisesRegex(ValueError, "person must approve"):
            evaluation.replay(captured)

    def test_prompt_contract_and_result_drift_are_visible(self):
        report = synthetic_capture(self.case)
        with patch.object(app, "_S1_SYSTEM", app._S1_SYSTEM + " changed"):
            changed = evaluation.replay(report, require_reference=False)
        self.assertEqual(changed["runs"]["stage1"]["status"], "failed")
        self.assertEqual(changed["runs"]["stage2"]["status"], "passed")
        modified = deepcopy(report)
        modified["evaluation_contract_version"] = "old"
        with self.assertRaisesRegex(ValueError, "contract changed"):
            evaluation.replay(modified, require_reference=False)
        modified = deepcopy(report)
        modified["runs"]["stage2"]["result"]["per_topic"]["Linear equations"]["marks_total"] = 999
        self.assertEqual(evaluation.replay(modified, require_reference=False)["status"], "failed")

    def test_cli_live_is_explicit_and_outputs_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "capture.json"
            with self.assertRaises(SystemExit) as error:
                evaluation.main(["live", str(CASE_PATH), "--model", "gpt-test", "--output", str(target)])
            self.assertEqual(error.exception.code, 2)
            with patch.object(app, "configure_model_clients", side_effect=AssertionError("Provider forbidden")):
                self.assertEqual(evaluation.main(["exchange", str(CASE_PATH), "--model", "gpt-test",
                                                  "--output", str(target)]), 3)
            before = target.read_bytes()
            self.assertEqual(evaluation.main(["exchange", str(CASE_PATH), "--model", "gpt-test",
                                              "--output", str(target)]), 2)
            self.assertEqual(target.read_bytes(), before)

    def test_cli_help_imports_without_credentials(self):
        result = subprocess.run([sys.executable, str(Path(evaluation.__file__)), "--help"],
                                env={k: v for k, v in os.environ.items() if "KEY" not in k},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("exchange", result.stdout)


if __name__ == "__main__":
    unittest.main()
