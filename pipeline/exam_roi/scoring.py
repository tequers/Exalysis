"""Pure mark aggregation and ROI ranking rules.

The functions in this module take all source data as arguments and return new
data. They do not read files or environment variables, call models, write to a
console, or mutate their inputs. Command code remains responsible for loading
accepted papers, rebuilding taxonomy, and exporting the returned report.

Legacy compatibility remains here until the tickets that own those behavior
changes are implemented. ``aggregate_paper_scores`` uses 1.0 as the denominator
when ``total_marks`` is falsey; ticket 03 will replace that fallback with mark
validation. ``build_ranked_report`` uses Conn=1, Diff=3, and Fmt=2 when old data
has no usable value, and labels missing contract versions as
``legacy-unversioned``. Ticket 17 owns the final missing-score and ranking
contract. Unknown question formats also retain the old Fmt=2 weight.
"""

from copy import deepcopy
from dataclasses import dataclass

from .evaluation import (
    CONTRACT_VERSION,
    LEGACY_VERSION,
    difficulty_version,
    tag_evidence,
)


# Format to integer score on the existing MVP scale.
FMT_SCORE = {
    "mcq": 1,
    "short_answer": 2,
    "explain_derive": 2,
    "write_code_or_proof": 3,
}


@dataclass(frozen=True)
class RankedReport:
    """The complete deterministic input needed by the report writers."""

    rows: list
    exam_list: list
    tier1_count: int


def aggregate_paper_scores(*, questions, assignments, topic_scores, total_marks,
                           known_topic_names, proposed_new_topic_names=()):
    """Combine explicit question, topic-assignment, and judgment inputs.

    Marks from a question are split equally across its assigned topics. The same
    shares determine the topic's format distribution. Qualitative scores pass
    through unchanged beside the calculated fields.
    """
    known_topics = set(known_topic_names)
    tagged_questions = []
    for question in questions:
        tagged = deepcopy(question)
        assignment = assignments[tagged["q_id"]]
        tagged["topics"] = deepcopy(assignment["topics"])
        tagged["topic_tagging"] = deepcopy(tag_evidence(assignment))
        tagged_questions.append(tagged)

    seen_topics = {topic for question in tagged_questions for topic in question["topics"]}
    new_topic_names = [
        topic for topic in proposed_new_topic_names
        if topic in seen_topics and topic not in known_topics
    ]
    new_topic_names += [
        topic for topic in sorted(seen_topics)
        if topic not in known_topics and topic not in new_topic_names
    ]

    denominator = float(total_marks) or 1.0
    totals = {}
    for question in tagged_questions:
        topics = question["topics"]
        if not topics:
            continue
        marks = question.get("marks")
        marks = float(marks) if isinstance(marks, (int, float)) else 0.0
        share = marks / len(topics)
        question_format = question.get("format") or "short_answer"
        for topic in topics:
            aggregate = totals.setdefault(topic, {"marks": 0.0, "by_fmt": {}})
            aggregate["marks"] += share
            aggregate["by_fmt"][question_format] = (
                aggregate["by_fmt"].get(question_format, 0.0) + share
            )

    scores = deepcopy(topic_scores)
    per_topic = {}
    for topic, aggregate in totals.items():
        judgment = scores[topic]
        marks_total = aggregate["marks"]
        if marks_total:
            distribution = {
                question_format: round(marks / marks_total, 3)
                for question_format, marks in aggregate["by_fmt"].items()
            }
        else:
            distribution = {
                question_format: round(1 / len(aggregate["by_fmt"]), 3)
                for question_format in aggregate["by_fmt"]
            }
        summary = {
            "marks_total": round(marks_total, 2),
            "mark_fraction": round(marks_total / denominator, 4),
            "format_distribution": distribution,
            "dominant_format": (
                max(distribution, key=distribution.get) if distribution else "short_answer"
            ),
            "Diff": judgment.get("Diff"),
            "Conn": judgment.get("Conn"),
            "prerequisites": judgment.get("prerequisites", []),
            "evaluation_contract_version": judgment.get(
                "evaluation_contract_version", LEGACY_VERSION
            ),
            "difficulty_contract_version": difficulty_version(judgment),
            "is_new_topic": topic in new_topic_names,
        }
        summary.update(deepcopy(judgment))
        per_topic[topic] = summary

    return {
        "questions": tagged_questions,
        "new_topic_names": new_topic_names,
        "per_topic": per_topic,
        "topic_judgments": scores,
    }


def weighted_fmt(format_distribution):
    """Return the mark-weighted format score for one paper and topic."""
    total = 0.0
    weighted = 0.0
    for question_format, fraction in format_distribution.items():
        weighted += FMT_SCORE.get(question_format, 2) * fraction
        total += fraction
    return round(weighted / total, 3) if total else 2.0


def tier1_count(topic_count):
    """Apply the existing Python round-to-even Tier 1 rule."""
    return max(1, round(topic_count * 0.2))


def build_ranked_report(exams, taxonomy, *, exam_labels_by_id):
    """Build ranked topic rows from accepted papers, taxonomy, and display labels."""
    exam_list = sorted(
        (deepcopy(exam) for exam in exams.values()),
        key=lambda exam: (exam.get("year") or 0, exam["exam_id"]),
    )
    exam_count = len(exam_list)
    all_topics = set()
    for exam in exam_list:
        all_topics.update(exam["per_topic"])

    rows = []
    for topic in sorted(all_topics):
        taxonomy_topic = taxonomy["topics"].get(topic, {})
        per_exam = {}
        for exam in exam_list:
            exam_id = exam["exam_id"]
            topic_data = exam["per_topic"].get(topic)
            common = {
                "year": exam.get("year"),
                "label": exam_labels_by_id.get(exam_id, exam_id),
                "evaluation_contract_version": exam.get(
                    "evaluation_contract_version", LEGACY_VERSION
                ),
            }
            if topic_data:
                per_exam[exam_id] = {
                    **common,
                    "present": 1,
                    "mark_fraction": topic_data.get("mark_fraction", 0),
                    "marks_total": topic_data.get("marks_total", 0),
                    "fmt_score": weighted_fmt(topic_data.get("format_distribution", {})),
                }
            else:
                per_exam[exam_id] = {
                    **common,
                    "present": 0,
                    "mark_fraction": 0,
                    "marks_total": 0,
                    "fmt_score": 0,
                }

        appearances = sum(1 for details in per_exam.values() if details["present"])
        frequency = appearances / exam_count
        present_marks = [
            details["mark_fraction"] for details in per_exam.values() if details["present"]
        ]
        mean_marks = sum(present_marks) / len(present_marks) if present_marks else 0
        format_values = [
            details["fmt_score"] for details in per_exam.values() if details["present"]
        ]
        mean_format = sum(format_values) / len(format_values) if format_values else 2.0
        connection = taxonomy_topic.get("Conn") or 1
        difficulty = taxonomy_topic.get("Diff") or 3
        denominator = difficulty * mean_format
        priority = (
            100 * frequency * mean_marks * connection / denominator
            if denominator > 0 else 0
        )

        rows.append({
            "topic": topic,
            "per_exam": per_exam,
            "Freq": round(frequency, 3),
            "G_Marks": round(mean_marks, 3),
            "Conn": connection,
            "Diff": difficulty,
            "difficulty_contract_version": difficulty_version(taxonomy_topic),
            "evaluation_contract_version": taxonomy_topic.get(
                "evaluation_contract_version", LEGACY_VERSION
            ),
            "human_overrides": deepcopy(taxonomy_topic.get("human_overrides", {})),
            "model_estimate": deepcopy(taxonomy_topic.get("model_estimate", {})),
            "contributing_exam_ids": deepcopy(
                taxonomy_topic.get("contributing_exam_ids", [])
            ),
            "connection_evidence": deepcopy(taxonomy_topic.get("connection_evidence", [])),
            "review_notes": "; ".join(
                label
                for flag, label in (
                    (taxonomy_topic.get("difficulty_review_required"), "Difficulty needs review"),
                    (taxonomy_topic.get("connection_review_required"), "Conflicting dependencies"),
                    (taxonomy_topic.get("excluded_legacy_exam_ids"), "Older evidence excluded"),
                    (
                        taxonomy_topic.get("evaluation_contract_version") != CONTRACT_VERSION,
                        "Older judgment basis",
                    ),
                )
                if flag
            ),
            "Fmt": round(mean_format, 2),
            "priority": round(priority, 4),
            "appearances": appearances,
            "prerequisites": ", ".join(taxonomy_topic.get("prerequisites", [])),
        })

    rows.sort(key=lambda row: row["priority"], reverse=True)
    first_tier_count = tier1_count(len(rows))
    for index, row in enumerate(rows):
        row["rank"] = index + 1
        row["tier"] = "★ Tier 1" if index < first_tier_count else ""

    return RankedReport(
        rows=rows,
        exam_list=exam_list,
        tier1_count=first_tier_count,
    )
