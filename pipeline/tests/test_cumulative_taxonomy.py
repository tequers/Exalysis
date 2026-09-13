"""Synthetic cumulative evidence checks; no network/model calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_evaluation import app, contract_metadata, score, tagging, FIXTURES
from exam_roi.taxonomy import aggregate_taxonomy


def paper(name, prerequisite=None, level=3, baseline=()):
    text = f"Use {prerequisite} to solve {name}." if prerequisite else f"Solve {name}."
    judgment = score(FIXTURES["examples"][2])["Topic"]
    judgment.update(assumed_prerequisites=list(baseline),
                    prerequisite_evidence=[dict(prerequisite=p, q_id="Q1", quote=text,
                                                rationale="Required by the task") for p in baseline],
                    question_difficulty=[dict(q_id="Q1", level=level, quote=text,
                                              rationale="Reasoning required by this task", uncertainties=[])],
                    connection_evidence=[dict(q_id="Q1", quote=text)],
                    prerequisites=[prerequisite] if prerequisite else [],
                    connection_edges=[dict(prerequisite=prerequisite, dependent=name,
                                           q_id="Q1", quote=text, rationale="Required to solve the task")]
                                     if prerequisite else [])
    return {**contract_metadata(), "questions": [dict(q_id="Q1", text=text, topics=[name],
                                                     marks=10, format="short_answer")],
            "topic_judgments": {name: judgment}}


class CumulativeTests(unittest.TestCase):
    def test_new_dependents_update_a_topic_absent_from_new_papers(self):
        exams = {"one": paper("A")}
        tax = aggregate_taxonomy({"topics": {}}, exams)
        self.assertEqual(tax["topics"]["A"]["Conn"], 1)
        for eid, dependent, expected in [("two", "B", 2), ("three", "C", 2), ("four", "D", 3)]:
            exams[eid] = paper(dependent, "A")
            tax = aggregate_taxonomy(tax, exams)
            self.assertEqual(tax["topics"]["A"]["Conn"], expected)
        self.assertEqual(tax["topics"]["A"]["unlocks"], ["B", "C", "D"])
        self.assertEqual(tax["topics"]["B"]["prerequisites"], ["A"])
        self.assertEqual(tax["topics"]["A"]["contributing_exam_ids"], ["four", "one", "three", "two"])

    def test_repeated_edges_do_not_inflate_connection_and_reparse_retracts(self):
        exams = {"a": paper("A"), "b": paper("B", "A"), "c": paper("C", "A"),
                 "d": paper("D", "A"), "repeat": paper("B", "A")}
        tax = aggregate_taxonomy({"topics": {}}, exams)
        self.assertEqual(tax["topics"]["A"]["Conn"], 3)
        self.assertEqual(len(tax["topics"]["A"]["connection_evidence"]), 4)
        exams["d"] = paper("D")
        tax = aggregate_taxonomy(tax, exams)
        self.assertEqual(tax["topics"]["A"]["Conn"], 2)
        self.assertEqual(tax["topics"]["A"]["unlocks"], ["B", "C"])
        self.assertEqual(tax, aggregate_taxonomy(tax, exams))
        exams = {"a": exams["a"]}
        tax = aggregate_taxonomy(tax, exams)
        self.assertEqual(tax["topics"]["A"]["Conn"], 1)
        self.assertEqual(tax["topics"]["A"]["connection_evidence"], [])

    def test_difficulty_uses_all_papers_instead_of_first_or_latest(self):
        exams = {"a": paper("A", level=2), "b": paper("A", level=4), "c": paper("A", level=4)}
        tax = aggregate_taxonomy({"topics": {}}, exams)
        self.assertEqual(tax["topics"]["A"]["Diff"], 4)
        self.assertEqual(tax["topics"]["A"]["difficulty_range"], [2, 4])
        self.assertTrue(tax["topics"]["A"]["difficulty_review_required"])
        exams["c"] = paper("A", level=1)
        self.assertEqual(aggregate_taxonomy(tax, exams)["topics"]["A"]["Diff"], 2)

    def test_distinct_assumptions_stay_in_separate_groups(self):
        exams = {"a": paper("A", level=2), "b": paper("A", level=5, baseline=["Algebra"]),
                 "c": paper("A", level=5, baseline=["Algebra"])}
        topic = aggregate_taxonomy({"topics": {}}, exams)["topics"]["A"]
        self.assertEqual(topic["Diff"], 5)
        self.assertEqual(len(topic["difficulty_groups"]), 2)
        self.assertTrue(topic["difficulty_review_required"])

    def test_conflicting_cycles_are_visible_and_do_not_raise_conn(self):
        exams = {"a": paper("A", "B"), "b": paper("B", "A")}
        tax = aggregate_taxonomy({"topics": {}}, exams)
        for topic in tax["topics"].values():
            self.assertEqual(topic["Conn"], 1)
            self.assertTrue(topic["connection_review_required"])
            self.assertEqual(len(topic["connection_conflicts"]), 2)

    def test_human_override_and_detected_direct_edit_survive_refresh(self):
        exams = {"a": paper("A"), "b": paper("B", "A")}
        tax = aggregate_taxonomy({"topics": {}}, exams)
        app._record_override(tax["topics"]["A"], "Conn", 3)
        tax["topics"]["A"]["Diff"] = 6
        updated = aggregate_taxonomy(tax, exams)
        self.assertEqual(updated["topics"]["A"]["Conn"], 3)
        self.assertEqual(updated["topics"]["A"]["Diff"], 6)
        self.assertEqual(updated["topics"]["A"]["model_estimate"], {"Conn": 2, "Diff": 3})
        self.assertEqual(updated["topics"]["A"]["human_overrides"]["Diff"]["source"], "taxonomy.json")

    def test_input_order_does_not_change_results_or_mutate_inputs(self):
        exams = {"a": paper("A"), "b": paper("B", "A"), "c": paper("C", "A")}
        before = copy.deepcopy(exams)
        left = aggregate_taxonomy({"topics": {}}, exams)
        right = aggregate_taxonomy({"topics": {}}, dict(reversed(list(exams.items()))))
        self.assertEqual(left, right)
        self.assertEqual(exams, before)

    def test_old_contracts_are_excluded_not_reinterpreted(self):
        old = paper("A", level=6)
        old["evaluation_contract_version"] = "1.1.0"
        topic = aggregate_taxonomy({"topics": {}}, {"new": paper("A", level=2), "old": old})["topics"]["A"]
        self.assertEqual(topic["Diff"], 2)
        self.assertEqual(topic["excluded_legacy_exam_ids"], ["old"])

    def test_missing_edge_evidence_is_rejected(self):
        broken = paper("B", "A")
        broken["topic_judgments"]["B"]["connection_edges"] = []
        with self.assertRaisesRegex(ValueError, "matching edge evidence"):
            aggregate_taxonomy({"topics": {}}, {"a": paper("A"), "b": broken})

    def test_process_keeps_candidate_separate_from_accepted_taxonomy(self):
        with tempfile.TemporaryDirectory() as folder:
            app.setup_course_folder(Path(folder))
            observed = paper("A")
            path = Path(folder) / "one.txt"
            path.write_text(observed["questions"][0]["text"], encoding="utf-8")
            with patch.object(app, "stage1_extract", return_value=(observed["questions"], 2026)), \
                 patch.object(app, "_stage2_tag", return_value=(tagging("A", observed["questions"][0]["text"]), ["A"])), \
                 patch.object(app, "call_llm", return_value=json.dumps(observed["topic_judgments"])):
                app.process_exam_file(path)
            self.assertEqual(app.load_taxonomy(), {"topics": {}})
            self.assertEqual(app.load_all_exams(), {})
            candidate = json.loads((app.CANDIDATES_DIR / "one.json").read_text(encoding="utf-8"))
            self.assertEqual(candidate["topic_judgments"]["A"]["Conn"], 1)
            self.assertIn("A", candidate["proposed_taxonomy_changes"]["topics"])

    def test_new_topic_triggers_evidence_review_of_earlier_paper(self):
        early = paper("B")
        early["questions"][0]["text"] = "Solve B. Use A to solve B."
        original_judgments = copy.deepcopy(early["topic_judgments"])
        answer = {"edges": [dict(prerequisite="A", dependent="B", q_id="Q1",
                                  quote="Use A to solve B.", rationale="B requires A in this task")]}
        with patch.object(app, "call_llm", return_value=json.dumps(answer)):
            review = app.refresh_connections(early, ["A", "B"])
        self.assertEqual(early["topic_judgments"], original_judgments)
        self.assertEqual(review["edges"][0]["prerequisite"], "A")
