"""Versioned qualitative rules; no providers, course paths, or CLI side effects."""

from copy import deepcopy
import hashlib
import math
from pathlib import Path

CONTRACT_VERSION = "1.2.0"
LEGACY_VERSION = "legacy-unversioned"
CONTRACT_PATH = Path(__file__).with_name("contracts") / "evaluation-v1.2.0.md"
CONTRACT_TEXT = CONTRACT_PATH.read_text(encoding="utf-8")
CONTRACT_SHA256 = hashlib.sha256(CONTRACT_TEXT.encode("utf-8")).hexdigest()
ALLOWED_QUESTION_FORMATS = frozenset({
    "mcq", "short_answer", "explain_derive", "write_code_or_proof",
})
QUESTION_FIELDS = ("q_id", "text", "marks", "format")
TAG_EVIDENCE_FIELDS = ("quote", "rationale", "uncertainties")


class CandidateValidationError(ValueError):
    """A model-produced candidate cannot safely cross an evaluation boundary."""

    def __init__(self, stage, reason, disposition="correction_required"):
        self.stage = stage
        self.reason = reason
        self.disposition = disposition
        action = disposition.replace("_", " ")
        super().__init__(f"{stage} candidate rejected; {action}: {reason}")


def _reject(stage, reason, disposition="correction_required"):
    raise CandidateValidationError(stage, reason, disposition)


def contract_metadata():
    return {"evaluation_contract_version": CONTRACT_VERSION,
            "evaluation_contract_sha256": CONTRACT_SHA256}


def difficulty_version(record):
    override = record.get("human_overrides", {}).get("Diff", {})
    return override.get("evaluation_contract_version") or record.get("difficulty_contract_version") or record.get(
        "evaluation_contract_version", LEGACY_VERSION)


def validate_extraction(data, earliest_year, latest_year):
    """Validate and copy the complete Stage 1 response.

    Mark reconciliation and optional-question policy belong to ticket 3. This
    boundary still rejects non-finite mark values so they cannot poison later
    arithmetic.
    """
    stage = "question extraction"
    if not isinstance(data, dict) or set(data) != {"exam_year", "questions"}:
        _reject(stage, "response must contain exactly exam_year and questions")

    year = data["exam_year"]
    if year is not None and (type(year) is not int or not earliest_year <= year <= latest_year):
        _reject(stage, f"exam_year must be null or an integer from {earliest_year} to {latest_year}")

    questions = data["questions"]
    if not isinstance(questions, list) or not questions:
        _reject(stage, "questions must be a nonempty list")

    clean, seen = [], set()
    required = {"q_id", "text", "marks", "format"}
    for index, question in enumerate(questions, 1):
        label = f"question {index}"
        if (not isinstance(question, dict) or not required <= set(question)
                or set(question) - required - {"source_context"}):
            _reject(stage, f"{label} must contain exactly q_id, text, marks, and format")
        q_id = question["q_id"]
        if not isinstance(q_id, str) or not q_id.strip():
            _reject(stage, f"{label} q_id must be a nonempty string")
        if q_id in seen:
            _reject(stage, f"duplicate question ID: {q_id}")
        seen.add(q_id)
        if not isinstance(question["text"], str) or not question["text"].strip():
            _reject(stage, f"{q_id} text must be a nonempty string")
        marks = question["marks"]
        if marks is not None and (isinstance(marks, bool) or not isinstance(marks, (int, float))
                                  or not math.isfinite(marks)):
            _reject(stage, f"{q_id} marks must be null or a finite number")
        if (not isinstance(question["format"], str)
                or question["format"] not in ALLOWED_QUESTION_FORMATS):
            _reject(stage, f"{q_id} has unsupported format {question['format']!r}")
        entry = {key: question[key] for key in QUESTION_FIELDS}
        if "source_context" in question:
            if not isinstance(question["source_context"], str) or not question["source_context"].strip():
                _reject(stage, f"{q_id} source_context must be nonempty text")
            entry["source_context"] = question["source_context"]
        clean.append(entry)
    return clean, year


def project_extraction_questions(questions):
    """Return the Stage 1 fields from raw or already-tagged question records."""
    return [
        {**{key: question.get(key) for key in QUESTION_FIELDS},
         **({"source_context": question["source_context"]} if "source_context" in question else {})}
        if isinstance(question, dict) else question
        for question in questions
    ]


def quote_in_question(quote, question):
    return quote in question["text"] or quote in question.get("source_context", "")


def tag_evidence(judgment):
    """Copy the evidence fields stored beside a question's topic labels."""
    return {key: judgment[key] for key in TAG_EVIDENCE_FIELDS}


def validate_tags(data, questions, known_topics):
    """Require exactly one complete, canonical 1–2-label assignment per question."""
    stage = "topic tagging"
    if not isinstance(data, dict) or set(data) != {"tags", "new_topic_names"}:
        _reject(stage, "response must contain exactly tags and new_topic_names")
    tags, new_names = data["tags"], data["new_topic_names"]
    if not isinstance(tags, dict):
        _reject(stage, "tags must be an object keyed by question ID")
    if not isinstance(new_names, list):
        _reject(stage, "new_topic_names must be a list")
    try:
        _strings(new_names, "new_topic_names")
    except ValueError as exc:
        _reject(stage, str(exc))
    if any(name in known_topics for name in new_names):
        _reject(stage, "new_topic_names must not repeat an existing canonical label")

    by_id = {question["q_id"]: question for question in questions}
    question_ids = list(by_id)
    expected, actual = set(question_ids), set(tags)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        details = []
        if missing:
            details.append("missing IDs: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected IDs: " + ", ".join(unexpected))
        _reject(stage, "; ".join(details))

    allowed = set(known_topics) | set(new_names)
    clean = {}
    for q_id in question_ids:
        judgment = tags[q_id]
        if not isinstance(judgment, dict) or set(judgment) != {
                "topics", "quote", "rationale", "uncertainties"}:
            _reject(stage, f"{q_id} tag judgment has an incomplete or unsupported structure")
        labels = judgment["topics"]
        if (not isinstance(labels, list) or not 1 <= len(labels) <= 2
                or any(not isinstance(label, str) or not label.strip() for label in labels)):
            _reject(stage, f"{q_id} must have one or two nonempty topic labels")
        if len(set(labels)) != len(labels):
            _reject(stage, f"{q_id} topic labels must be distinct")
        unknown = [label for label in labels if label not in allowed]
        if unknown:
            _reject(stage, f"{q_id} uses undeclared topic labels: {', '.join(unknown)}")
        try:
            _text(judgment["quote"], "tag quote")
            _text(judgment["rationale"], "tag rationale")
            _strings(judgment["uncertainties"], "tag uncertainties")
        except ValueError as exc:
            _reject(stage, f"{q_id}: {exc}")
        if not quote_in_question(judgment["quote"], by_id[q_id]):
            _reject(stage, f"{q_id} tag quote is absent from its source question")
        clean[q_id] = {
            "topics": list(labels),
            "quote": judgment["quote"],
            "rationale": judgment["rationale"],
            "uncertainties": list(judgment["uncertainties"]),
        }
    unused = [name for name in new_names
              if all(name not in judgment["topics"] for judgment in clean.values())]
    if unused:
        _reject(stage, "new topic proposals are not used by any question: " + ", ".join(unused))
    return clean, list(new_names)


def summarize_difficulty(papers):
    """Lower median per paper, then across papers; inputs share version/baseline.

    Keep paper IDs explicit to avoid treating subdivisions as independent papers.
    Abstention is an error at this boundary, never a fabricated default level.
    """
    if not papers:
        raise ValueError("Difficulty requires question evidence")
    medians, all_levels = [], []
    for levels in papers.values():
        if not levels or any(type(n) is not int or not 1 <= n <= 6 for n in levels):
            raise ValueError("Difficulty requires resolved integer levels 1–6")
        ordered = sorted(levels)
        medians.append(ordered[(len(ordered) - 1) // 2])
        all_levels.extend(ordered)
    medians.sort()
    low, high = min(all_levels), max(all_levels)
    return {"Diff": medians[(len(medians) - 1) // 2],
            "difficulty_range": [low, high],
            "difficulty_review_required": high - low >= 2,
            "difficulty_provisional": len(papers) == 1}


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} requires a nonempty string")


def _strings(value, field):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError(f"{field} requires a list of strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{field} must not contain duplicates")


def _require_fields(value, required, label, allowed_extra=()):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    missing = set(required) - set(value)
    unsupported = set(value) - set(required) - set(allowed_extra)
    if missing or unsupported:
        details = []
        if missing:
            details.append("missing: " + ", ".join(sorted(missing)))
        if unsupported:
            details.append("unsupported: " + ", ".join(sorted(unsupported)))
        raise ValueError(f"{label} has invalid fields ({'; '.join(details)})")


def _validate_connection_edge(edge, by_id, allowed_topics, topic_name=None):
    _require_fields(edge, {"prerequisite", "dependent", "q_id", "quote", "rationale"},
                    "connection edge")
    source, target = edge["prerequisite"], edge["dependent"]
    if source not in allowed_topics or target not in allowed_topics or source == target:
        raise ValueError("Invalid connection endpoints")
    if topic_name is not None and topic_name not in (source, target):
        raise ValueError(f"{topic_name}: edge must involve the scored topic")
    question = by_id.get(edge["q_id"])
    if not question or not ({source, target} & set(question["topics"])):
        raise ValueError("Connection evidence must cite a task testing an endpoint")
    for field in ("quote", "rationale"):
        _text(edge[field], field)
    if not quote_in_question(edge["quote"], question):
        raise ValueError("Connection quote is absent from the source question")
    return {key: edge[key]
            for key in ("prerequisite", "dependent", "q_id", "quote", "rationale")}


def validate_topic_scores(scores, names, questions, allowed_topics, already_validated=False):
    """Validate the new qualitative representation before persisting it.

    Extraction and tag coverage are validated at their own boundaries. Only
    explicit fields cross this boundary, so unsolicited duration fields cannot
    leak into new records. Quotes are checked against stored question text.
    """
    if not isinstance(scores, dict) or set(scores) != set(names):
        raise ValueError("Paper scores must cover exactly the requested topics")
    by_id = {q["q_id"]: q for q in questions}

    def evidence(item):
        if not isinstance(item, dict) or item.get("q_id") not in by_id:
            raise ValueError("Evidence requires a known question ID")
        _text(item.get("quote"), "quote")
        if not quote_in_question(item["quote"], by_id[item["q_id"]]):
            raise ValueError("Evidence quote is absent from its source question")

    result = {}
    score_fields = {
        "question_difficulty", "difficulty_rationale", "assumed_prerequisites",
        "prerequisite_evidence", "Conn", "connection_rationale", "connection_evidence",
        "connection_edges", "unlocks", "prerequisites", "uncertainties",
    }
    derived_fields = {
        "Diff", "difficulty_range", "difficulty_review_required", "difficulty_provisional",
        "evaluation_contract_version", "evaluation_contract_sha256",
    }
    for name in names:
        score = scores[name]
        _require_fields(score, score_fields, f"{name} topic judgment",
                        allowed_extra=derived_fields if already_validated else set())
        for field in ("difficulty_rationale", "connection_rationale"):
            _text(score.get(field), field)
        for field in ("prerequisites", "unlocks", "assumed_prerequisites", "uncertainties"):
            _strings(score.get(field), field)
        assumptions = score.get("prerequisite_evidence")
        if not isinstance(assumptions, list):
            raise ValueError(f"{name}: prerequisite evidence must be a list")
        covered = set()
        for item in assumptions:
            _require_fields(item, {"prerequisite", "q_id", "quote", "rationale"},
                            f"{name} prerequisite evidence")
            evidence(item)
            _text(item.get("rationale"), "prerequisite rationale")
            _text(item.get("prerequisite"), "prerequisite")
            if item["prerequisite"] not in score["assumed_prerequisites"]:
                raise ValueError(f"{name}: evidence names an unlisted prerequisite")
            covered.add(item["prerequisite"])
        if covered != set(score["assumed_prerequisites"]):
            raise ValueError(f"{name}: every inferred prerequisite needs exam evidence")
        for field in ("prerequisites", "unlocks"):
            if any(t == name or t not in allowed_topics for t in score[field]):
                raise ValueError(f"{name}: invalid {field} reference")
        conn = score.get("Conn")
        expected_conn = 1 if not score["unlocks"] else 2 if len(score["unlocks"]) <= 2 else 3
        if type(conn) is not int or not 1 <= conn <= 3 or conn != expected_conn:
            raise ValueError(f"{name}: Conn must match supported downstream labels")
        connections = score.get("connection_evidence")
        if not isinstance(connections, list) or not connections:
            raise ValueError(f"{name}: connection evidence is required")
        for item in connections:
            _require_fields(item, {"q_id", "quote"}, f"{name} connection evidence")
            evidence(item)
        edges = score.get("connection_edges")
        if not isinstance(edges, list):
            raise ValueError(f"{name}: connection_edges must be a list")
        clean_edges = [
            _validate_connection_edge(edge, by_id, allowed_topics, topic_name=name)
            for edge in edges
        ]
        if {e["dependent"] for e in edges if e["prerequisite"] == name} != set(score["unlocks"]):
            raise ValueError(f"{name}: every unlock requires matching edge evidence")
        if {e["prerequisite"] for e in edges if e["dependent"] == name} != set(score["prerequisites"]):
            raise ValueError(f"{name}: every prerequisite requires matching edge evidence")
        judgments = score.get("question_difficulty")
        if not isinstance(judgments, list) or not judgments:
            raise ValueError(f"{name}: question difficulty evidence is required")
        expected_ids = {q["q_id"] for q in questions if name in q["topics"]}
        ids, clean = [], []
        for item in judgments:
            _require_fields(item, {"q_id", "level", "quote", "rationale", "uncertainties"},
                            f"{name} question difficulty")
            evidence(item)
            _text(item.get("rationale"), "question rationale")
            _strings(item.get("uncertainties"), "question uncertainties")
            ids.append(item["q_id"])
            clean.append({k: item.get(k) for k in
                          ("q_id", "level", "quote", "rationale", "uncertainties")})
        if len(ids) != len(set(ids)) or set(ids) != expected_ids:
            raise ValueError(f"{name}: difficulty must cover each tagged question once")
        levels = [item["level"] for item in clean]
        if any(type(level) is not int or not 1 <= level <= 6 for level in levels):
            disposition = "needs_review" if any(level is None for level in levels) else "correction_required"
            _reject("topic scoring", "Difficulty requires resolved integer levels 1–6", disposition)
        summary = summarize_difficulty({"current-paper": levels})
        result[name] = {
            **summary, **contract_metadata(), "question_difficulty": clean,
            **{k: score[k] for k in ("Conn", "difficulty_rationale", "connection_rationale",
                "assumed_prerequisites", "prerequisites", "unlocks", "uncertainties")},
            "connection_edges": clean_edges,
            "prerequisite_evidence": [
                {k: i[k] for k in ("prerequisite", "q_id", "quote", "rationale")}
                for i in assumptions],
            "connection_evidence": [{"q_id": i["q_id"], "quote": i["quote"]}
                                    for i in connections],
        }
    return result


def _validate_topic_summaries(per_topic, topic_names, judgments):
    stage = "candidate analysis"
    if not isinstance(per_topic, dict) or set(per_topic) != set(topic_names):
        _reject(stage, "per_topic must cover every and only tagged topics")
    clean = {}
    for name in topic_names:
        summary = per_topic[name]
        if not isinstance(summary, dict):
            _reject(stage, f"{name}: per_topic entry must be an object")
        for field in ("marks_total", "mark_fraction"):
            value = summary.get(field)
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value)):
                _reject(stage, f"{name}: {field} must be a finite number")
        distribution = summary.get("format_distribution")
        if (not isinstance(distribution, dict) or not distribution
                or any(fmt not in ALLOWED_QUESTION_FORMATS for fmt in distribution)
                or any(isinstance(value, bool) or not isinstance(value, (int, float))
                       or not math.isfinite(value) for value in distribution.values())):
            _reject(stage, f"{name}: format_distribution is invalid")
        if summary.get("dominant_format") not in ALLOWED_QUESTION_FORMATS:
            _reject(stage, f"{name}: dominant_format is invalid")
        if summary.get("Diff") != judgments[name]["Diff"] or summary.get("Conn") != judgments[name]["Conn"]:
            _reject(stage, f"{name}: summary scores disagree with validated judgments")
        clean[name] = deepcopy(summary)
    return clean


def _validate_extraction_provenance(extraction):
    """Every candidate must say how its text was read and where each part came from.

    Without these references a later evidence check has no way back from a quote
    to the page it was taken from. The record is produced by the input reader, not
    by a model, so this is a shape check rather than a judgment.
    """
    stage = "candidate analysis"
    if not isinstance(extraction, dict):
        _reject(stage, "source extraction record must be an object")
    try:
        _text(extraction.get("extraction_kind"), "extraction kind")
    except ValueError as exc:
        _reject(stage, str(exc))
    segments = extraction.get("segments")
    if not isinstance(segments, list) or not segments:
        _reject(stage, "source extraction requires a nonempty segments list")
    for index, segment in enumerate(segments, 1):
        if not isinstance(segment, dict) or not {
                "char_start", "char_end", "line_start"} <= set(segment):
            _reject(stage, f"extraction segment {index} needs char_start, char_end, "
                           "and line_start")


def _validate_provenance(source, model):
    stage = "candidate analysis"
    if not isinstance(source, dict) or set(source) != {
            "file_name", "resolved_path", "sha256", "extraction"}:
        _reject(stage, "source provenance requires file_name, resolved_path, "
                       "sha256, and extraction")
    _validate_extraction_provenance(source["extraction"])
    try:
        _text(source["file_name"], "source file_name")
        _text(source["resolved_path"], "source resolved_path")
    except ValueError as exc:
        _reject(stage, str(exc))
    digest = source["sha256"]
    if (not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)):
        _reject(stage, "source sha256 must be a lowercase SHA-256 digest")
    required_model = {"provider", "extraction_model", "analysis_model"}
    split_providers = {"extraction_provider", "analysis_provider"}
    if not isinstance(model, dict) or set(model) not in (required_model, required_model | split_providers):
        _reject(stage, "model provenance requires provider, extraction_model, and analysis_model; "
                       "separate providers must name both stages")
    try:
        for field, value in model.items():
            _text(value, f"model {field}")
    except ValueError as exc:
        _reject(stage, str(exc))


def build_candidate_analysis(*, exam_id, year, year_label, total_marks, analysis,
                             known_topics, source_provenance, model_provenance,
                             processed_at):
    """Create a validated, traceable candidate without mutating accepted state."""
    stage = "candidate analysis"
    try:
        _text(exam_id, "exam_id")
        _text(processed_at, "processed_at")
    except ValueError as exc:
        _reject(stage, str(exc))
    if year is not None and type(year) is not int:
        _reject(stage, "year must be null or an integer")
    if year_label is not None and not isinstance(year_label, str):
        _reject(stage, "year_label must be null or a string")
    if (isinstance(total_marks, bool) or not isinstance(total_marks, (int, float))
            or not math.isfinite(total_marks)):
        _reject(stage, "total_marks must be a finite number")
    if not isinstance(analysis, dict) or set(analysis) != {
            "questions", "new_topic_names", "per_topic", "topic_judgments"}:
        _reject(stage, "analysis has an incomplete or unsupported structure")
    questions = analysis["questions"]
    if not isinstance(questions, list):
        _reject(stage, "questions must be a list")

    extraction = {"exam_year": year, "questions": project_extraction_questions(questions)}
    clean_questions, _ = validate_extraction(extraction, 1, 9999)
    tag_data = {
        "tags": {
            question["q_id"]: {
                "topics": question.get("topics"),
                **(question.get("topic_tagging") or {}),
            }
            for question in questions if isinstance(question, dict) and "q_id" in question
        },
        "new_topic_names": analysis["new_topic_names"],
    }
    clean_tags, new_names = validate_tags(
        tag_data, clean_questions, known_topics)
    tagged_questions = [
        {
            **question,
            "topics": clean_tags[question["q_id"]]["topics"],
            "topic_tagging": tag_evidence(clean_tags[question["q_id"]]),
        }
        for question in clean_questions
    ]
    topic_names = sorted({topic for judgment in clean_tags.values()
                          for topic in judgment["topics"]})
    try:
        judgments = validate_topic_scores(
            analysis["topic_judgments"], topic_names, tagged_questions,
            list(known_topics) + new_names, already_validated=True)
    except CandidateValidationError:
        raise
    except ValueError as exc:
        _reject(stage, str(exc))

    clean_per_topic = _validate_topic_summaries(analysis["per_topic"], topic_names, judgments)
    _validate_provenance(source_provenance, model_provenance)

    needs_review = any(
        question["topic_tagging"]["uncertainties"] for question in tagged_questions
    ) or any(
        judgment["uncertainties"]
        or any(item["uncertainties"] for item in judgment["question_difficulty"])
        or judgment["difficulty_review_required"]
        for judgment in judgments.values()
    )
    return {
        **contract_metadata(),
        "record_kind": "candidate-analysis",
        "candidate_status": "needs-review" if needs_review else "validated",
        "exam_id": exam_id,
        "year": year,
        "year_label": year_label,
        "total_marks": total_marks,
        # Keep these compatibility fields while the storage migration is pending.
        "source_file": source_provenance["file_name"],
        "source_path": source_provenance["resolved_path"],
        "processed_at": processed_at,
        "source_provenance": deepcopy(source_provenance),
        "model_provenance": deepcopy(model_provenance),
        "evaluation_context": {"canonical_topic_names": sorted(known_topics)},
        "questions": tagged_questions,
        "topic_judgments": judgments,
        "per_topic": clean_per_topic,
    }


def finalize_candidate_analysis(candidate, proposed_taxonomy, accepted_topics):
    """Attach a separate taxonomy proposal and make the final review classification."""
    stage = "candidate analysis"
    if (not isinstance(candidate, dict)
            or candidate.get("record_kind") != "candidate-analysis"
            or candidate.get("candidate_status") not in {"validated", "needs-review"}):
        _reject(stage, "a validated candidate core is required")
    if not isinstance(proposed_taxonomy, dict) or not isinstance(proposed_taxonomy.get("topics"), dict):
        _reject(stage, "proposed taxonomy must contain a topics object")
    if not isinstance(accepted_topics, dict):
        _reject(stage, "accepted topics must be an object")

    result = deepcopy(candidate)
    changed_topics = {
        name: topic for name, topic in proposed_taxonomy["topics"].items()
        if topic != accepted_topics.get(name)
    }
    result["proposed_taxonomy_changes"] = {
        "new_topic_names": sorted(set(result["topic_judgments"]) - set(accepted_topics)),
        "topics": changed_topics,
    }
    if any(topic.get("difficulty_review_required") or topic.get("connection_review_required")
           for topic in changed_topics.values()):
        result["candidate_status"] = "needs-review"
    return result


def validate_connection_review(data, questions, allowed_topics):
    """Validate a fresh dependency review without changing original difficulty evidence."""
    if not isinstance(data, dict) or set(data) != {"edges"} or not isinstance(data["edges"], list):
        raise ValueError("Connection review requires an edges list")
    by_id = {q["q_id"]: q for q in questions}
    clean = [_validate_connection_edge(edge, by_id, allowed_topics) for edge in data["edges"]]
    return {**contract_metadata(), "context_topics": sorted(allowed_topics), "edges": clean}
