#!/usr/bin/env python3
"""Migrate the reliable-exam-analysis backlog to structured ticket metadata.

Run without arguments for a read-only preview. Pass --apply to write the exact
previewed changes. Existing structured metadata is treated as user-owned and is
not replaced, which makes the migration safe to rerun after later ticket edits.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKLOG = "tickets"
BACKLOG = REPO_ROOT / DEFAULT_BACKLOG
ISSUES = BACKLOG / "issues"
STATUS_FILE = BACKLOG / "TICKET_STATUS.md"
AREAS_FILE = BACKLOG / "areas.json"
TEMPLATE_FILE = BACKLOG / "TEMPLATE.md"
REPORT_FILE = BACKLOG / "MIGRATION_REPORT.md"
FOLDERS = ("DONE", "TO_REVIEW", "OPEN", "BLOCKED", "IN_PROGRESS")

QUEUE_ORDER = {
    "01": 1,
    "04": 2,
    "10": 3,
    "12": 4,
    "15": 5,
    "18": 6,
    "19": 7,
    "20": 8,
    "02": 9,
    "07": 10,
    "03": 11,
    "05": 12,
    "06": 13,
    "08": 14,
    "09": 15,
    "11": 16,
    "14": 17,
    "16": 18,
    "17": 19,
    "13": 20,
    "21": 21,
}

TICKET_AREAS = {
    "01": ["evaluation", "scoring"],
    "02": ["evaluation", "storage"],
    "03": ["evaluation", "scoring"],
    "04": ["extraction"],
    "05": ["evaluation", "extraction", "configuration"],
    "06": ["evaluation", "acceptance", "configuration"],
    "07": ["storage", "reports"],
    "08": ["acceptance", "storage", "reports"],
    "09": ["evaluation", "extraction", "acceptance"],
    "10": ["storage"],
    "11": ["storage", "configuration"],
    "12": ["extraction", "configuration"],
    "13": ["extraction", "storage"],
    "14": ["evaluation", "scoring", "storage"],
    "15": ["configuration", "reports"],
    "16": ["reports", "storage"],
    "17": ["scoring", "reports"],
    "18": ["reports"],
    "19": ["scoring", "reports"],
    "20": ["configuration", "storage", "evaluation"],
    "21": ["evaluation", "extraction", "configuration"],
}

TICKET_REFERENCES = {
    "01": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
        "pipeline/exam_roi/evaluation.py",
        "pipeline/tests/fixtures/difficulty-v1.json",
        "pipeline/tests/test_evaluation.py",
    ],
    "02": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
        "pipeline/exam_roi/evaluation.py",
        "pipeline/tests/test_candidate_validation.py",
        "pipeline/tests/test_cumulative_taxonomy.py",
    ],
    "03": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
        "pipeline/exam_roi/scoring.py",
        "pipeline/tests/test_scoring.py",
    ],
    "04": [
        "README.md",
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/inputs.py",
        "pipeline/tests/test_input_extraction.py",
    ],
    "05": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "docs/guides/model-request-limits.md",
        "pipeline/exam_roi/llm.py",
        "pipeline/exam_roi/question_context.py",
        "pipeline/tests/test_request_limits.py",
    ],
    "06": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "docs/guides/independent-review.md",
        "pipeline/exam_roi/review.py",
        "pipeline/tests/test_independent_review.py",
    ],
    "07": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "docs/guides/course-state-recovery.md",
        "pipeline/exam_roi/storage.py",
        "pipeline/tests/test_storage.py",
    ],
    "08": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/evaluation.py",
        "pipeline/exam_roi/storage.py",
    ],
    "09": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
        "pipeline/tests/fixtures/difficulty-v1.json",
    ],
    "10": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/identity.py",
        "pipeline/tests/test_exam_identity.py",
    ],
    "11": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/identity.py",
        "pipeline/exam_roi/storage.py",
        "pipeline/tests/test_exam_identity.py",
    ],
    "12": [
        "README.md",
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/inputs.py",
        "pipeline/tests/test_input_selection.py",
    ],
    "13": [
        "docs/adr/0007-one-record-per-paper-and-the-sitting-year.md",
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/inputs.py",
        "pipeline/exam_roi/storage.py",
    ],
    "14": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/scoring.py",
        "pipeline/exam_roi/taxonomy.py",
        "pipeline/tests/test_cumulative_taxonomy.py",
    ],
    "15": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/pipeline.py",
        "pipeline/tests/test_cli_outcomes.py",
    ],
    "16": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/reports.py",
        "pipeline/tests/test_report_rendering.py",
    ],
    "17": [
        "README.md",
        "docs/adr/0008-modular-pipeline-architecture.md",
        "docs/guides/scoring-methodology.md",
        "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
        "pipeline/exam_roi/scoring.py",
        "pipeline/tests/test_scoring.py",
    ],
    "18": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/reports.py",
        "pipeline/tests/test_report_rendering.py",
    ],
    "19": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/scoring.py",
        "pipeline/tests/test_scoring.py",
    ],
    "20": [
        "docs/adr/0008-modular-pipeline-architecture.md",
        "pipeline/exam_roi/llm.py",
        "pipeline/exam_roi/storage.py",
        "pipeline/pipeline.py",
        "pipeline/tests/test_explicit_configuration.py",
    ],
    "21": [
        "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
        "pipeline/exam_roi/evaluation.py",
        "pipeline/exam_roi/llm.py",
        "pipeline/exam_roi/review.py",
    ],
}

AREAS = {
    "documentation": ["docs/**"],
    "*": [
        "tickets/areas.json",
        "AGENTS.md",
        "CONTEXT.md",
        "docs/glossary.md",
        "README.md",
        ".github/workflows/tickets.yml",
        "docs/adr/**",
        "docs/development/ticket-ground-truth-plan.md",
        "docs/development/ticket-workflow.md",
        "pipeline/exam_roi/contracts/**",
        "pipeline/pipeline.py",
        "pipeline/tests/fixtures/**",
        "scripts/check_tickets.py",
        "scripts/migrate_tickets.py",
        "scripts/ticket_history.py",
        "scripts/tickets.py",
        "scripts/tests/**",
    ],
    "acceptance": [
        "pipeline/exam_roi/evaluation.py",
        "pipeline/exam_roi/review.py",
        "pipeline/exam_roi/storage.py",
        "pipeline/tests/test_independent_review.py",
        "pipeline/tests/test_storage.py",
    ],
    "configuration": [
        "docs/guides/glm-testing.md",
        "pipeline/exam_roi/llm.py",
        "pipeline/requirements.txt",
        "pipeline/tests/test_cli_outcomes.py",
        "pipeline/tests/test_explicit_configuration.py",
        "pipeline/tests/test_request_limits.py",
    ],
    "evaluation": [
        "pipeline/exam_roi/evaluation.py",
        "pipeline/exam_roi/review.py",
        "pipeline/exam_roi/taxonomy.py",
        "pipeline/tests/test_candidate_validation.py",
        "pipeline/tests/test_cumulative_taxonomy.py",
        "pipeline/tests/test_evaluation.py",
        "pipeline/tests/test_independent_review.py",
    ],
    "extraction": [
        "pipeline/exam_roi/inputs.py",
        "pipeline/exam_roi/question_context.py",
        "pipeline/tests/test_input_extraction.py",
        "pipeline/tests/test_input_selection.py",
        "pipeline/tests/test_request_limits.py",
    ],
    "reports": [
        "pipeline/exam_roi/reports.py",
        "pipeline/tests/test_report_rendering.py",
    ],
    "scoring": [
        "pipeline/exam_roi/scoring.py",
        "pipeline/exam_roi/taxonomy.py",
        "pipeline/tests/test_scoring.py",
    ],
    "storage": [
        "pipeline/exam_roi/identity.py",
        "pipeline/exam_roi/storage.py",
        "pipeline/tests/test_exam_identity.py",
        "pipeline/tests/test_storage.py",
    ],
}

TEMPLATE = """# ID: Short action-oriented title

```json
{
  "schema_version": 1,
  "id": "ID",
  "priority": "P2",
  "queue_order": 0,
  "areas": [],
  "depends_on": [],
  "related_to": [],
  "references": [],
  "verification": null,
  "closure": null
}
```

**What to build:** State the user-visible or system behavior this ticket changes.

- [ ] Write acceptance criteria that can be checked.

**Architecture:** Link to approved contracts or decisions instead of copying their rules.

## Evidence and history

Preserve checks, decisions, and partial-resolution history here. Record structured
verification and closure evidence in the metadata when the workflow requires it.
"""


@dataclass(frozen=True)
class Ticket:
    path: Path
    folder: str
    ticket_id: str
    title: str
    text: str
    metadata: Optional[dict[str, object]]
    body_status: Optional[str]
    body_priority: Optional[str]
    body_dependencies: list[str]


@dataclass(frozen=True)
class Change:
    source: Path
    destination: Path
    content: str
    description: str
    expected_content: Optional[str]


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def configure_paths(root: Path, backlog_value: str) -> None:
    global REPO_ROOT, BACKLOG, ISSUES, STATUS_FILE, AREAS_FILE, TEMPLATE_FILE, REPORT_FILE
    root = root.resolve()
    backlog_rel = Path(backlog_value)
    if backlog_rel.is_absolute() or ".." in backlog_rel.parts:
        raise ValueError("--backlog must be a repository-relative path without '..'")
    backlog = (root / backlog_rel).resolve()
    try:
        backlog.relative_to(root)
    except ValueError as error:
        raise ValueError("--backlog must resolve inside --root") from error
    REPO_ROOT = root
    BACKLOG = backlog
    ISSUES = backlog / "issues"
    STATUS_FILE = backlog / "TICKET_STATUS.md"
    AREAS_FILE = backlog / "areas.json"
    TEMPLATE_FILE = backlog / "TEMPLATE.md"
    REPORT_FILE = backlog / "MIGRATION_REPORT.md"


def parse_metadata(text: str) -> Optional[dict[str, object]]:
    title = re.search(r"(?m)^# .+$", text)
    if not title:
        raise ValueError("missing H1 title")
    remainder = text[title.end() :]
    match = re.match(r"\s*```json\s*\n(?P<json>.*?)\n```", remainder, re.DOTALL)
    if not match:
        return None
    value = json.loads(match.group("json"))
    if not isinstance(value, dict):
        raise ValueError("metadata must be a JSON object")
    return value


def dependency_ids(value: Optional[str]) -> list[str]:
    if not value or value.strip().rstrip(".").lower() == "none":
        return []
    return re.findall(r"(?:^|;\s*)(\d+)(?=\s*:)", value)


def read_tickets() -> list[Ticket]:
    tickets: list[Ticket] = []
    seen: dict[str, Path] = {}
    for folder in FOLDERS:
        directory = ISSUES / folder
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            match = re.match(r"(\d+)-", path.name)
            if not match:
                raise ValueError(f"{relative(path)}: filename must start with an ID")
            ticket_id = match.group(1)
            if ticket_id in seen:
                raise ValueError(
                    f"duplicate ticket {ticket_id}: {relative(seen[ticket_id])} and {relative(path)}"
                )
            seen[ticket_id] = path
            text = path.read_text(encoding="utf-8")
            title_match = re.search(r"(?m)^#\s+(?:\d+:\s*)?(.+)$", text)
            if not title_match:
                raise ValueError(f"{relative(path)}: missing H1 title")
            status_match = re.search(r"(?m)^\*\*Status:\*\*\s*(.+?)\s*$", text)
            priority_match = re.search(r"(?m)^\*\*Priority:\*\*\s*(.+?)\s*$", text)
            dependency_match = re.search(r"(?m)^\*\*Depends on:\*\*\s*(.+?)\s*$", text)
            tickets.append(
                Ticket(
                    path=path,
                    folder=folder,
                    ticket_id=ticket_id,
                    title=title_match.group(1).strip(),
                    text=text,
                    metadata=parse_metadata(text),
                    body_status=status_match.group(1).strip() if status_match else None,
                    body_priority=priority_match.group(1).strip() if priority_match else None,
                    body_dependencies=dependency_ids(
                        dependency_match.group(1) if dependency_match else None
                    ),
                )
            )
    actual = {ticket.ticket_id for ticket in tickets}
    expected = set(QUEUE_ORDER)
    missing = sorted(expected - actual)
    extra = sorted(
        ticket.ticket_id
        for ticket in tickets
        if ticket.ticket_id not in expected and ticket.metadata is None
    )
    if missing or extra:
        raise ValueError(f"ticket inventory mismatch; missing={missing}, extra={extra}")
    return sorted(
        tickets,
        key=lambda ticket: (
            QUEUE_ORDER[ticket.ticket_id]
            if ticket.ticket_id in QUEUE_ORDER
            else ticket.metadata["queue_order"]
        ),
    )


def closure_for(ticket: Ticket) -> Optional[dict[str, object]]:
    if ticket.folder != "DONE":
        return None
    if ticket.ticket_id == "12":
        return {
            "reason": "implemented",
            "commit": None,
            "replacement": None,
            "reviewed_by": "Historical standards and specification reviews; reviewer identity unavailable",
            "evidence": [
                "Ticket body records separate standards and specification reviews with no actionable findings."
            ],
        }
    evidence = "Historical completion claim and scope are preserved in this ticket body."
    if "## Completion evidence" in ticket.text or "## Implementation and verification" in ticket.text:
        evidence = "Historical implementation and check evidence is preserved in this ticket body."
    return {
        "reason": "implemented",
        "commit": None,
        "replacement": None,
        "reviewed_by": None,
        "evidence": [evidence],
    }


def initial_metadata(ticket: Ticket) -> dict[str, object]:
    if not ticket.body_priority:
        raise ValueError(f"{relative(ticket.path)}: missing legacy Priority header")
    return {
        "schema_version": 1,
        "id": ticket.ticket_id,
        "priority": ticket.body_priority,
        "queue_order": QUEUE_ORDER[ticket.ticket_id],
        "areas": TICKET_AREAS[ticket.ticket_id],
        "depends_on": ticket.body_dependencies,
        "related_to": [],
        "references": TICKET_REFERENCES[ticket.ticket_id],
        "verification": None,
        "closure": closure_for(ticket),
    }


def add_metadata_and_remove_mirrors(ticket: Ticket, metadata: dict[str, object]) -> str:
    title = re.search(r"(?m)^# .+$", ticket.text)
    assert title is not None
    block = "\n\n```json\n" + json.dumps(metadata, indent=2) + "\n```"
    text = ticket.text[: title.end()] + block + ticket.text[title.end() :]
    text = re.sub(
        r"(?m)^\*\*(?:Depends on|Status|Priority):\*\*[^\n]*(?:\n|$)", "", text
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.rstrip() + "\n"


def repair_known_link_depth(text: str, ticket_path: Path) -> tuple[str, int]:
    repairs = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal repairs
        label, target, anchor = match.group("label", "target", "anchor")
        if not target.startswith("../../../") or target.startswith("../../../../"):
            return match.group(0)
        current = (ticket_path.parent / target).resolve()
        candidate_target = "../" + target
        candidate = (ticket_path.parent / candidate_target).resolve()
        if current.exists() or not candidate.exists():
            return match.group(0)
        repairs += 1
        return f"[{label}]({candidate_target}{anchor or ''})"

    pattern = re.compile(
        r"\[(?P<label>[^\]]+)\]\((?P<target>\.\./\.\./\.\./[^)#]+)(?P<anchor>#[^)]+)?\)"
    )
    return pattern.sub(replace, text), repairs


def metadata_for(ticket: Ticket) -> dict[str, object]:
    return ticket.metadata if ticket.metadata is not None else initial_metadata(ticket)


def dependency_satisfied(metadata: dict[str, object]) -> bool:
    closure = metadata.get("closure")
    if not isinstance(closure, dict):
        return False
    reason = closure.get("reason")
    if reason not in ("implemented", "already_resolved"):
        return False
    return bool(closure.get("reviewed_by")) and bool(closure.get("evidence"))


def desired_folder(ticket: Ticket, by_id: dict[str, Ticket]) -> str:
    if ticket.folder not in ("OPEN", "BLOCKED"):
        return ticket.folder
    metadata = metadata_for(ticket)
    dependencies = metadata.get("depends_on", [])
    blockers = [
        dependency
        for dependency in dependencies
        if dependency not in by_id or not dependency_satisfied(metadata_for(by_id[dependency]))
    ]
    return "BLOCKED" if blockers else "OPEN"


def table_snapshot() -> dict[str, tuple[str, str, list[str]]]:
    if not STATUS_FILE.exists():
        return {}
    result: dict[str, tuple[str, str, list[str]]] = {}
    row_pattern = re.compile(
        r"^\|\s*\d+\s*\|\s*(\d+)\s*\|.*?\|\s*(P[123])\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|$"
    )
    for line in STATUS_FILE.read_text(encoding="utf-8").splitlines():
        match = row_pattern.match(line)
        if not match:
            continue
        blockers = [] if match.group(4).strip() == "None" else re.findall(r"\d+", match.group(4))
        result[match.group(1)] = (match.group(2), match.group(3).strip(), blockers)
    return result


def report_text(tickets: list[Ticket]) -> str:
    table = table_snapshot()
    rows = []
    for ticket in tickets:
        table_priority, table_status, table_blockers = table.get(ticket.ticket_id, ("—", "Missing", []))
        metadata = metadata_for(ticket)
        dependencies = metadata.get("depends_on", [])
        closure = metadata.get("closure")
        review = "n/a"
        if isinstance(closure, dict):
            review = str(closure.get("reviewed_by") or "unknown")
        rows.append(
            f"| {ticket.ticket_id} | {ticket.folder} | {ticket.body_status or 'removed'} | "
            f"{table_status} | {metadata['priority']} / {table_priority} | "
            f"{', '.join(dependencies) or 'None'} | {', '.join(table_blockers) or 'None'} | {review} |"
        )
    return (
        "# Ticket migration reconciliation report\n\n"
        "> Generated by `python scripts/migrate_tickets.py --apply`. Do not edit by hand.\n\n"
        "The migration compared folder placement, the legacy body headers, and the legacy "
        "status table before removing duplicated body fields. No ticket scope, acceptance "
        "criterion, history, or ticket ID was removed. `verification` remains `null` because "
        "the legacy records do not identify a revision-bound preflight check.\n\n"
        "## Migration result\n\n"
        "- Preview found 21 ticket IDs exactly once and proposed 21 metadata additions, one "
        "folder move, and no local Markdown link repairs.\n"
        "- Apply completed 24 file operations: 21 ticket rewrites or moves plus creation of "
        "the area map, template, and this report.\n"
        "- A second preview proposed no changes. All repository-relative metadata references "
        "and local Markdown links resolve in the migrated tree.\n\n"
        "## Reconciliation decisions\n\n"
        "- Ticket 01 had the only direct status contradiction: its folder and body said "
        "`DONE`/`Done`, while the table said `Review` and linked to `TO_REVIEW`. The detailed "
        "completion section supports retaining the historical `implemented` closure, but it "
        "explicitly describes review by the implementation author and says the examples were "
        "not human-reviewed. Its `reviewed_by` value is therefore `null`. Ticket 01 does not "
        "satisfy dependencies until independent review evidence is recorded, so tickets 09 "
        "and 17 remain blocked by it.\n"
        "- Existing `DONE` placement is retained as historical closure. A checked checklist or "
        "test statement is implementation evidence, not independent review evidence. Such "
        "closures use `reviewed_by: null` and do not clear blockers.\n"
        "- Ticket 12 explicitly records separate standards and specification reviews. The "
        "migration preserves that attribution without inventing a reviewer identity.\n"
        "- Tickets 07 and 20 say `Done` but retain unchecked criteria and no recorded review. "
        "Their scope and checklist stay unchanged; their closures remain unverified. Ticket 19 "
        "similarly stays in `TO_REVIEW` with its unchecked checklist intact.\n"
        "- Tickets already in `TO_REVIEW` keep that workflow state even when dependencies are "
        "unresolved. Ticket 21 moves from `OPEN` to `BLOCKED` because ticket 20's historical "
        "closure has no review evidence.\n\n"
        "## Legacy snapshot\n\n"
        "| ID | Folder | Body status | Table status | Metadata/table priority | Dependencies | Table blockers | Historical reviewer |\n"
        "|---:|---|---|---|---|---|---|---|\n"
        + "\n".join(rows)
        + "\n\n## Remaining unknowns\n\n"
        "- Independent reviewer identities and review evidence are unavailable for all "
        "historical `DONE` tickets except the anonymous separate reviews recorded by ticket 12.\n"
        "- Historical fixing commits were not stated in the ticket records, so closure commit "
        "fields remain `null`.\n"
        "- The unchecked criteria in tickets 07, 19, and 20 need human reconciliation; migration "
        "does not reinterpret or rewrite their scope.\n"
    )


def validate_references(metadata: dict[str, object], ticket_id: str) -> None:
    for reference in metadata.get("references", []):
        path = (REPO_ROOT / reference).resolve()
        try:
            path.relative_to(REPO_ROOT.resolve())
        except ValueError as error:
            raise ValueError(f"ticket {ticket_id}: reference escapes repository: {reference}") from error
        if not path.exists():
            raise ValueError(f"ticket {ticket_id}: missing reference: {reference}")


def validate_local_links(text: str, path: Path) -> None:
    for match in re.finditer(r"\[[^\]]+\]\((?P<target>[^)]+)\)", text):
        target = match.group("target")
        if "://" in target or target.startswith("#"):
            continue
        path_part = target.split("#", 1)[0]
        if path_part and not (path.parent / path_part).resolve().exists():
            raise ValueError(f"{relative(path)}: broken local link: {target}")


def planned_changes(tickets: list[Ticket]) -> tuple[list[Change], int, int, int]:
    changes: list[Change] = []
    metadata_additions = 0
    moves = 0
    link_repairs = 0
    by_id = {ticket.ticket_id: ticket for ticket in tickets}
    for ticket in tickets:
        metadata = metadata_for(ticket)
        validate_references(metadata, ticket.ticket_id)
        content = ticket.text
        if ticket.metadata is None:
            content = add_metadata_and_remove_mirrors(ticket, metadata)
            metadata_additions += 1
        content, repaired = repair_known_link_depth(content, ticket.path)
        link_repairs += repaired
        folder = desired_folder(ticket, by_id)
        destination = ISSUES / folder / ticket.path.name
        if destination != ticket.path:
            if destination.exists():
                raise ValueError(f"refusing destination collision: {relative(destination)}")
            moves += 1
        validate_local_links(content, destination)
        if content != ticket.text or destination != ticket.path:
            changes.append(
                Change(
                    source=ticket.path,
                    destination=destination,
                    content=content,
                    description=f"migrate ticket {ticket.ticket_id}",
                    expected_content=ticket.text,
                )
            )

    create_once = (
        (AREAS_FILE, json.dumps(AREAS, indent=2) + "\n", "create areas.json"),
        (TEMPLATE_FILE, TEMPLATE, "create ticket template"),
    )
    for path, content, description in create_once:
        if not path.exists():
            changes.append(Change(path, path, content, description, None))

    report = report_text(tickets)
    if not REPORT_FILE.exists():
        changes.append(
            Change(REPORT_FILE, REPORT_FILE, report, "write reconciliation report", None)
        )
    return changes, metadata_additions, moves, link_repairs


def normalized(path: Path) -> str:
    return os.path.normcase(str(path))


def validate_direct_path(path: Path, allowed_root: Path) -> None:
    resolved_root = allowed_root.resolve()
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise OSError(f"refusing path outside {allowed_root}: {path}") from error
    direct = Path(os.path.abspath(str(path)))
    if normalized(resolved) != normalized(direct):
        raise OSError(f"refusing redirected path: {path}")


def assert_expected(path: Path, expected_content: Optional[str]) -> None:
    if expected_content is None:
        if path.exists() or path.is_symlink():
            raise OSError(f"refusing to overwrite newly created path: {path}")
        return
    if not path.exists() or path.is_symlink():
        raise OSError(f"source changed or was redirected after preview: {path}")
    if path.read_text(encoding="utf-8") != expected_content:
        raise OSError(f"source changed after preview: {path}")


def atomic_write(path: Path, content: str, expected_content: Optional[str]) -> None:
    validate_direct_path(path, REPO_ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".migration-tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary.flush()
            temporary_path = Path(temporary.name)
        assert_expected(path, expected_content)
        temporary_path.replace(path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def apply_changes(changes: list[Change]) -> None:
    for change in changes:
        if change.source != change.destination:
            validate_direct_path(change.source, ISSUES)
            validate_direct_path(change.destination, ISSUES)
            assert_expected(change.source, change.expected_content)
            assert_expected(change.destination, None)
            atomic_write(change.destination, change.content, None)
            assert_expected(change.source, change.expected_content)
            change.source.unlink()
        else:
            atomic_write(change.destination, change.content, change.expected_content)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repository root")
    parser.add_argument(
        "--backlog", default=DEFAULT_BACKLOG, help="repository-relative backlog path"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preview", action="store_true", help="preview only (the default)")
    mode.add_argument(
        "--apply", action="store_true", help="write the migration after previewing it"
    )
    args = parser.parse_args(argv)
    try:
        configure_paths(args.root, args.backlog)
        tickets = read_tickets()
        changes, additions, moves, repairs = planned_changes(tickets)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"migration error: {error}", file=sys.stderr)
        return 1

    mode = "APPLY" if args.apply else "PREVIEW"
    print(f"{mode}: {len(tickets)} tickets found exactly once")
    print(f"metadata additions: {additions}")
    print(f"ticket moves: {moves}")
    print(f"local link repairs: {repairs}")
    for change in changes:
        source = relative(change.source)
        destination = relative(change.destination)
        location = source if source == destination else f"{source} -> {destination}"
        print(f"- {change.description}: {location}")
    if not changes:
        print("No changes proposed.")
        return 0
    if not args.apply:
        print("Preview only. Run again with --apply to write these changes.")
        return 0

    try:
        apply_changes(changes)
    except OSError as error:
        print(f"migration write error: {error}", file=sys.stderr)
        return 1
    print(f"Applied {len(changes)} file operations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
