"""Keep source questions whole when a paper needs several extraction requests."""

from dataclasses import dataclass
import re

from .evaluation import CandidateValidationError


@dataclass(frozen=True)
class SourceQuestion:
    q_id: str
    text: str


def source_questions(text):
    """Recognize explicit top-level headings, never page breaks or character cuts.

    Bare numbered lists are ambiguous with answer choices. Without explicit
    headings the whole source remains one unit. Repeated headings also remain
    one unit so section-local numbering cannot accidentally merge questions.
    """
    matches = list(re.finditer(
        r"(?im)^[ \t]*(?:Q(?:uestion)?\s*|Pregunta\s+|Ejercicio\s+)(\d+)"
        r"(?=[ \t.:)\-]|$)", text))
    ids = [f"Q{int(match[1])}" for match in matches]
    if not matches or len(ids) != len(set(ids)):
        return "", [SourceQuestion("", text)]
    prefix = text[:matches[0].start()]
    return prefix, [SourceQuestion(q_id, text[match.start():
                        matches[i + 1].start() if i + 1 < len(matches) else len(text)])
                    for i, (q_id, match) in enumerate(zip(ids, matches))]


def related_source_units(batch, all_units):
    """Include explicitly referenced questions, including chains of references."""
    by_id = {unit.q_id: unit for unit in all_units}
    wanted = {unit.q_id for unit in batch}
    pending = list(batch)
    while pending:
        unit = pending.pop()
        for number in re.findall(r"\b(?:Q(?:uestion)?\s*|Pregunta\s+|Ejercicio\s+)(\d+)\b",
                                 unit.text, re.IGNORECASE):
            q_id = f"Q{int(number)}"
            if q_id in by_id and q_id not in wanted:
                wanted.add(q_id)
                pending.append(by_id[q_id])
    return [unit for unit in all_units if unit.q_id in wanted]


def retain_source_context(questions, units, prefix, all_units=None):
    """Check heading coverage and retain exact source even if extraction shortened it."""
    by_id = {unit.q_id: unit for unit in units}
    covered = set()
    for question in questions:
        if "" in by_id:
            source_id = ""
        else:
            match = re.fullmatch(r"(Q\d+)(?:[a-z]|\([a-z]\)|[.][a-z0-9]+)*", question["q_id"])
            source_id = match[1] if match else None
        if source_id not in by_id:
            raise CandidateValidationError("question extraction",
                f"Unexpected or unstable question ID {question['q_id']}; use printed Q numbers and subpart suffixes")
        related = related_source_units([by_id[source_id]], all_units or units)
        question["source_context"] = prefix + "".join(unit.text for unit in related)
        covered.add(source_id)
    if covered != set(by_id):
        raise CandidateValidationError("question extraction",
            "Missing source questions: " + ", ".join(sorted(set(by_id) - covered)))


def question_evidence(questions):
    """Keep task text and its source context, excluding mark/format scoring cues."""
    return [{key: q[key] for key in ("q_id", "text", "source_context", "topics") if key in q}
            for q in questions]
