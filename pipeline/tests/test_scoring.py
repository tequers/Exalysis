"""Direct tests for the provider-independent scoring package."""

import copy
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
import unittest


PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))

from exam_roi.evaluation import CONTRACT_VERSION, LEGACY_VERSION
from exam_roi.scoring import (
    aggregate_paper_scores,
    build_ranked_report,
    tier1_count,
)


def assignment(*topics):
    return {
        "topics": list(topics),
        "quote": "Source quote.",
        "rationale": "The question tests the assigned topic.",
        "uncertainties": [],
    }


class PaperAggregationTests(unittest.TestCase):
    def test_mixed_formats_and_shared_question_match_hand_calculation(self):
        questions = [
            {"q_id": "Q1", "text": "Solve it.", "marks": 12,
             "format": "short_answer", "source_page": 1},
            {"q_id": "Q2", "text": "Choose it.", "marks": 8,
             "format": "mcq", "source_page": 2},
            {"q_id": "Q3", "text": "Prove it.", "marks": 10,
             "format": "write_code_or_proof", "source_page": 3},
        ]
        assignments = {
            "Q1": assignment("Algebra"),
            "Q2": assignment("Algebra", "Statistics"),
            "Q3": assignment("Statistics"),
        }
        topic_scores = {
            "Algebra": {"Diff": 2, "Conn": 1, "prerequisites": []},
            "Statistics": {"Diff": 4, "Conn": 2, "prerequisites": ["Algebra"]},
        }
        before = copy.deepcopy((questions, assignments, topic_scores))
        stdout = StringIO()

        with redirect_stdout(stdout):
            result = aggregate_paper_scores(
                questions=questions,
                assignments=assignments,
                topic_scores=topic_scores,
                total_marks=30,
                known_topic_names=["Algebra"],
                proposed_new_topic_names=["Statistics", "Unused proposal"],
            )

        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual((questions, assignments, topic_scores), before)
        self.assertEqual(result["new_topic_names"], ["Statistics"])
        algebra = result["per_topic"]["Algebra"]
        statistics = result["per_topic"]["Statistics"]
        self.assertEqual(algebra["marks_total"], 16.0)
        self.assertEqual(algebra["mark_fraction"], 0.5333)
        self.assertEqual(
            algebra["format_distribution"],
            {"short_answer": 0.75, "mcq": 0.25},
        )
        self.assertEqual(algebra["dominant_format"], "short_answer")
        self.assertEqual(statistics["marks_total"], 14.0)
        self.assertEqual(statistics["mark_fraction"], 0.4667)
        self.assertEqual(
            statistics["format_distribution"],
            {"mcq": 0.286, "write_code_or_proof": 0.714},
        )
        self.assertEqual(statistics["dominant_format"], "write_code_or_proof")
        self.assertEqual(result["questions"][1]["topics"], ["Algebra", "Statistics"])
        self.assertEqual(result["questions"][1]["source_page"], 2)


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.exams = {
            "morning": {
                "exam_id": "exam_2024_morning",
                "year": 2024,
                "evaluation_contract_version": CONTRACT_VERSION,
                "per_topic": {
                    "A": {
                        "marks_total": 50,
                        "mark_fraction": 0.5,
                        "format_distribution": {"mcq": 0.5, "write_code_or_proof": 0.5},
                    },
                    "B": {
                        "marks_total": 25,
                        "mark_fraction": 0.25,
                        "format_distribution": {"write_code_or_proof": 1.0},
                    },
                },
            },
            "evening": {
                "exam_id": "exam_2024_evening",
                "year": 2024,
                "evaluation_contract_version": CONTRACT_VERSION,
                "per_topic": {
                    "A": {
                        "marks_total": 20,
                        "mark_fraction": 0.25,
                        "format_distribution": {"short_answer": 1.0},
                    },
                    "C": {
                        "marks_total": 40,
                        "mark_fraction": 0.5,
                        "format_distribution": {"mcq": 1.0},
                    },
                },
            },
        }
        self.taxonomy = {
            "topics": {
                "A": {"Diff": 3, "Conn": 2, "prerequisites": [],
                      "evaluation_contract_version": CONTRACT_VERSION},
                "B": {"Diff": 1, "Conn": 1, "prerequisites": [],
                      "evaluation_contract_version": CONTRACT_VERSION},
                "C": {"Diff": 2, "Conn": 1, "prerequisites": ["A"],
                      "evaluation_contract_version": CONTRACT_VERSION},
            }
        }

    def test_multi_paper_ranking_tiers_and_presentation_match_hand_calculation(self):
        before = copy.deepcopy((self.exams, self.taxonomy))
        labels = {
            "exam_2024_evening": "2024 evening",
            "exam_2024_morning": "2024 morning",
        }
        report = build_ranked_report(
            self.exams,
            self.taxonomy,
            exam_labels_by_id=labels,
        )

        self.assertEqual((self.exams, self.taxonomy), before)
        self.assertEqual(
            [exam["exam_id"] for exam in report.exam_list],
            ["exam_2024_evening", "exam_2024_morning"],
        )
        self.assertEqual([row["topic"] for row in report.rows], ["A", "C", "B"])
        by_topic = {row["topic"]: row for row in report.rows}
        self.assertEqual(by_topic["A"]["Freq"], 1.0)
        self.assertEqual(by_topic["A"]["G_Marks"], 0.375)
        self.assertEqual(by_topic["A"]["Fmt"], 2.0)
        self.assertEqual(by_topic["A"]["priority"], 12.5)
        self.assertEqual(by_topic["C"]["priority"], 12.5)
        self.assertEqual(by_topic["B"]["priority"], 4.1667)
        self.assertEqual(by_topic["C"]["prerequisites"], "A")
        self.assertEqual(
            by_topic["A"]["per_exam"]["exam_2024_evening"]["label"],
            "2024 evening",
        )
        self.assertEqual([row["rank"] for row in report.rows], [1, 2, 3])
        self.assertEqual([row["tier"] for row in report.rows], ["★ Tier 1", "", ""])
        self.assertEqual(report.tier1_count, 1)

    def test_legacy_fallbacks_are_preserved_in_the_report(self):
        exams = {
            "old": {
                "exam_id": "old",
                "year": None,
                "per_topic": {
                    "Legacy": {
                        "marks_total": 20,
                        "mark_fraction": 0.2,
                        "format_distribution": {"unknown_old_format": 1.0},
                    }
                },
            }
        }
        row = build_ranked_report(
            exams,
            {"topics": {"Legacy": {}}},
            exam_labels_by_id={"old": "?"},
        ).rows[0]

        self.assertEqual(row["Conn"], 1)
        self.assertEqual(row["Diff"], 3)
        self.assertEqual(row["Fmt"], 2.0)
        self.assertEqual(row["priority"], 3.3333)
        self.assertEqual(row["evaluation_contract_version"], LEGACY_VERSION)
        self.assertEqual(
            row["per_exam"]["old"]["evaluation_contract_version"],
            LEGACY_VERSION,
        )
        self.assertIn("Older judgment basis", row["review_notes"])

    def test_tier_count_uses_the_existing_rounding_rule(self):
        self.assertEqual(tier1_count(3), 1)
        self.assertEqual(tier1_count(8), 2)
        self.assertEqual(tier1_count(12), 2)
        self.assertEqual(tier1_count(13), 3)


class PackageBoundaryTests(unittest.TestCase):
    def test_import_needs_no_provider_or_credentials(self):
        environment = {key: value for key, value in os.environ.items() if "API_KEY" not in key}
        script = (
            "import sys; sys.path.insert(0, %r); import exam_roi.scoring; "
            "assert 'anthropic' not in sys.modules; assert 'openai' not in sys.modules; "
            "print('import-ok')" % str(PIPELINE_DIR)
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "import-ok")


if __name__ == "__main__":
    unittest.main()
