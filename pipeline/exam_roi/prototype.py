"""Unreviewed reports from candidates, with no acceptance or provider calls."""

from copy import deepcopy
import math
import os
from pathlib import Path
import shutil
import tempfile
from uuid import uuid4

from .evaluation import CandidateValidationError, CONTRACT_VERSION
from .reports import exam_labels, write_json, write_xlsx
from .scoring import aggregate_paper_scores, build_ranked_report
from .taxonomy import aggregate_taxonomy


def validate_total(total_marks):
    if (type(total_marks) not in (int, float) or not math.isfinite(total_marks)
            or total_marks <= 0):
        raise ValueError("Prototype mode requires --total-marks with a finite positive total "
                         "for a paper where all questions are compulsory.")


def validate_marks(questions, total_marks):
    """Check the supported compulsory-paper case without inventing mark shares."""
    validate_total(total_marks)
    for question in questions:
        marks = question.get("marks")
        if type(marks) not in (int, float) or not math.isfinite(marks) or marks < 0:
            raise CandidateValidationError(
                "prototype marks", f"{question.get('q_id')}: every question needs finite "
                "nonnegative printed marks; do not invent allocations for shared totals")
    found = sum(question["marks"] for question in questions)
    if not questions or not math.isclose(found, total_marks, rel_tol=0, abs_tol=0.000001):
        raise CandidateValidationError(
            "prototype marks", f"Extracted marks sum to {found:g}, expected {total_marks:g}. "
            "Check question coverage and shared mark allocations before retrying.")


def candidate_taxonomy(snapshot, *, exclude_id=None):
    """Use only candidates as evidence; carry canonical names and overrides."""
    papers = {eid: paper for eid, paper in snapshot.candidates.items() if eid != exclude_id}
    for eid, paper in papers.items():
        if (paper.get("record_kind") != "candidate-analysis"
                or paper.get("evaluation_contract_version") != CONTRACT_VERSION):
            raise ValueError(f"Candidate {eid} is incompatible with prototype export; "
                             "reprocess that paper with add-exam --prototype --force.")
        validate_marks(paper.get("questions", []), paper.get("total_marks"))
        expected = aggregate_paper_scores(
            questions=paper["questions"],
            assignments={q["q_id"]: {"topics": q["topics"], **q["topic_tagging"]}
                         for q in paper["questions"]},
            topic_scores=paper["topic_judgments"], total_marks=paper["total_marks"],
            known_topic_names=list(paper["topic_judgments"]))["per_topic"]
        fields = ("marks_total", "mark_fraction", "format_distribution", "dominant_format")
        if (set(expected) != set(paper["per_topic"]) or any(
                expected[name][field] != paper["per_topic"][name].get(field)
                for name in expected for field in fields)):
            raise ValueError(f"Candidate {eid} has inconsistent saved topic totals or formats. "
                             "Restore the saved candidate or reprocess that paper; "
                             "reports were not refreshed.")
    return aggregate_taxonomy(snapshot.taxonomy, papers)


def _safe_destination(path):
    if path.resolve() != path or path.is_symlink():
        raise ValueError(f"Prototype destination is redirected: {path}")
    if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
        raise ValueError(f"Prototype destination must be a regular file: {path}")


def export_prototype(snapshot, course_folder):
    """Render both files before replacement; roll back ordinary write failures.

    The caller owns the course lock. Two replacements are not crash-atomic:
    consumers can compare generation IDs after an interruption and rebuild.
    """
    if not snapshot.candidates:
        raise ValueError("No candidates to export. Run add-exam --prototype first.")
    taxonomy = candidate_taxonomy(snapshot)
    report = build_ranked_report(snapshot.candidates, taxonomy,
                                 exam_labels_by_id=exam_labels(list(snapshot.candidates.values())))
    if not report.rows:
        raise ValueError("Candidates have no ranked topics to export.")
    generation = uuid4().hex
    rows = deepcopy(report.rows)
    for row in rows:
        row.update(report_status="unreviewed-prototype", generation_id=generation)
        row["review_notes"] = "; ".join(filter(None, (
            "Unreviewed prototype; topic marks use equal shares", row.get("review_notes"))))
    folder = Path(course_folder) / "prototype"
    if folder.resolve() != folder or folder.is_symlink():
        raise ValueError(f"Prototype folder is redirected: {folder}")
    folder.mkdir(exist_ok=True)
    names = ("Exam_ROI_Pipeline.xlsx", "Exam_ROI_Pipeline.json")
    destinations = [folder / name for name in names]
    for path in destinations:
        _safe_destination(path)
    with tempfile.TemporaryDirectory(prefix=".export-", dir=folder) as temp:
        staging = Path(temp)
        write_xlsx(rows, report.exam_list, taxonomy, staging / names[0],
                   report_note=f"UNREVIEWED PROTOTYPE | Generation {generation}")
        write_json(rows, staging / names[1])
        backups = {}
        for path in destinations:
            if path.exists():
                backup = staging / (path.name + ".previous")
                shutil.copyfile(path, backup)
                backups[path] = backup
        replaced = []
        try:
            for path in destinations:
                _safe_destination(path)
                os.replace(staging / path.name, path)
                replaced.append(path)
        except Exception as exc:
            rollback_errors = []
            for path in reversed(replaced):
                try:
                    if path in backups:
                        os.replace(backups[path], path)
                    else:
                        path.unlink()
                except OSError as rollback_error:
                    rollback_errors.append(str(rollback_error))
            if rollback_errors:
                raise OSError("Export replacement and rollback failed. Do not use the "
                              "report pair until rebuild --prototype succeeds. "
                              + "; ".join(rollback_errors)) from exc
            raise
    return destinations
