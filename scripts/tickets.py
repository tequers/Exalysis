#!/usr/bin/env python3
"""Validate, inspect, and update the repository ticket backlog.

The Markdown ticket is the authoritative record.  This module deliberately uses
only the Python standard library so it can run in a clean checkout and in CI.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

try:
    from .ticket_history import HistoryError, select_impact, snapshot_at_commit
except ImportError:  # Direct execution: scripts/ is the import root.
    from ticket_history import HistoryError, select_impact, snapshot_at_commit


DEFAULT_BACKLOG = ".scratch/reliable-exam-analysis"
STATES = ("OPEN", "BLOCKED", "IN_PROGRESS", "TO_REVIEW", "DONE")
PRIORITIES = ("P1", "P2", "P3")
CLOSURE_REASONS = (
    "implemented",
    "already_resolved",
    "duplicate",
    "superseded",
    "cancelled",
)
VERIFICATION_RESULTS = ("still_valid", "partially_resolved", "already_resolved")
META_KEYS = {
    "schema_version",
    "id",
    "priority",
    "queue_order",
    "areas",
    "depends_on",
    "related_to",
    "references",
    "verification",
    "closure",
}
VERIFICATION_KEYS = {
    "commit",
    "checked_at",
    "criteria_digest",
    "checker",
    "result",
    "evidence",
    "provisional",
}
CLOSURE_KEYS = {"reason", "commit", "replacement", "reviewed_by", "evidence"}
META_RE = re.compile(
    r"\A(?P<title>\ufeff?\s*#\s+[^\r\n]+\r?\n)(?P<gap>\s*)"
    r"```json\s*\r?\n(?P<json>.*?)\r?\n```(?P<rest>.*)\Z",
    re.DOTALL | re.IGNORECASE,
)
CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s*(.*?)\s*$")
ID_FILENAME_RE = re.compile(r"^(?P<id>\d+)-.+\.md$", re.IGNORECASE)


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    message: str
    ticket_id: Optional[str] = None
    hint: Optional[str] = None

    def format(self) -> str:
        owner = f" ticket {self.ticket_id}" if self.ticket_id else ""
        text = f"{self.severity}{owner} [{self.code}]: {self.message}"
        return f"{text} Repair: {self.hint}" if self.hint else text


@dataclass
class Ticket:
    path: Path
    relative_path: str
    state: str
    title: str
    body: str
    metadata: Dict[str, Any]
    parse_error: Optional[str] = None

    @property
    def id(self) -> str:
        value = self.metadata.get("id")
        return value if isinstance(value, str) else "?"


@dataclass
class Backlog:
    root: Path
    path: Path
    issues_path: Path
    areas_path: Path
    index_path: Path
    tickets: List[Ticket]
    areas: Dict[str, List[str]]
    load_diagnostics: List[Diagnostic] = field(default_factory=list)

    @property
    def by_id(self) -> Dict[str, Ticket]:
        result: Dict[str, Ticket] = {}
        for ticket in self.tickets:
            if ticket.id != "?" and ticket.id not in result:
                result[ticket.id] = ticket
        return result


class TicketError(Exception):
    """An actionable user error."""


def _repo_relative_path(value: Any) -> bool:
    if (not isinstance(value, str) or not value.strip() or "\\" in value
            or ":" in value or "\x00" in value):
        return False
    path = PurePosixPath(value)
    return (not path.is_absolute() and not PureWindowsPath(value).drive
            and ".." not in path.parts and path.parts != ())


def _unique_json_object(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _require_regular_path(path: Path, parent: Path) -> None:
    """Reject redirected paths before reading or replacing authoritative files."""
    if not _inside(path, parent) or path.resolve() != path.absolute() or path.is_symlink():
        raise TicketError(f"redirected or external backlog path: {path}")
    if path.is_file() and path.stat().st_nlink > 1:
        raise TicketError(f"hard-linked backlog file is not supported: {path}")


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _run_git(root: Path, args: Sequence[str], check: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise TicketError("git is required for this command but was not found") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "git command failed"
        raise TicketError(detail) from exc


def discover_root(start: Optional[Path] = None) -> Path:
    candidate = (start or Path.cwd()).resolve()
    result = _run_git(candidate, ["rev-parse", "--show-toplevel"], check=False)
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return candidate


def resolve_backlog(root: Path, backlog_rel: str = DEFAULT_BACKLOG) -> Path:
    if not _repo_relative_path(backlog_rel):
        raise TicketError("--backlog must be a repository-relative path without '..'")
    backlog = root / PurePosixPath(backlog_rel)
    _require_regular_path(backlog, root)
    return backlog


def parse_ticket(path: Path, issues_path: Path) -> Ticket:
    _require_regular_path(path, issues_path)
    body = path.read_text(encoding="utf-8")
    relative = path.relative_to(issues_path.parent).as_posix()
    state = path.parent.name
    title_match = re.match(r"\ufeff?\s*#\s+([^\r\n]+)", body)
    title = title_match.group(1).strip() if title_match else path.stem
    match = META_RE.match(body)
    if not match:
        return Ticket(path, relative, state, title, body, {},
                      "place the first fenced JSON metadata block immediately after the H1 title")
    try:
        metadata = json.loads(match.group("json"), object_pairs_hook=_unique_json_object)
    except json.JSONDecodeError as exc:
        return Ticket(path, relative, state, title, body, {},
                      f"invalid JSON metadata at line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except ValueError as exc:
        return Ticket(path, relative, state, title, body, {}, str(exc))
    if not isinstance(metadata, dict):
        return Ticket(path, relative, state, title, body, {}, "metadata must be a JSON object")
    return Ticket(path, relative, state, title, body, metadata)


def load_backlog(root: Path, backlog_rel: str = DEFAULT_BACKLOG) -> Backlog:
    root = Path(root).resolve()
    path = resolve_backlog(root, backlog_rel)
    issues = path / "issues"
    _require_regular_path(issues, path)
    _require_regular_path(path / "TICKET_STATUS.md", path)
    diagnostics: List[Diagnostic] = []
    tickets: List[Ticket] = []
    if not issues.is_dir():
        diagnostics.append(Diagnostic("ERROR", "missing-issues", f"missing ticket directory: {issues}",
                                      hint="create the backlog issues directory and its state folders"))
    else:
        for child in sorted(issues.iterdir(), key=lambda p: p.name):
            _require_regular_path(child, issues)
            if child.is_dir() and child.name not in STATES:
                diagnostics.append(Diagnostic("ERROR", "unknown-state", f"unknown state folder {child.name}",
                                              hint=f"move tickets into one of: {', '.join(STATES)}"))
            if child.is_file() and child.suffix.lower() == ".md":
                diagnostics.append(Diagnostic("ERROR", "unfiled-ticket", f"ticket is not in a state folder: {child.name}",
                                              hint="move it into OPEN, BLOCKED, IN_PROGRESS, TO_REVIEW, or DONE"))
        for state in STATES:
            folder = issues / state
            _require_regular_path(folder, issues)
            if not folder.exists():
                continue
            for ticket_path in sorted(folder.rglob("*.md")):
                if ticket_path.parent != folder:
                    diagnostics.append(Diagnostic("ERROR", "nested-ticket", f"ticket is nested below {state}: {ticket_path}",
                                                  hint=f"move it directly under issues/{state}"))
                tickets.append(parse_ticket(ticket_path, issues))

    areas_path = path / "areas.json"
    _require_regular_path(areas_path, path)
    areas: Dict[str, List[str]] = {}
    if not areas_path.is_file():
        diagnostics.append(Diagnostic("ERROR", "missing-areas", f"missing area configuration: {areas_path}",
                                      hint="create areas.json as an object mapping area names to path globs"))
    else:
        try:
            loaded = json.loads(areas_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_json_object)
            if not isinstance(loaded, dict):
                raise ValueError("top level must be an object")
            for name, patterns in loaded.items():
                if not isinstance(name, str) or not name or not isinstance(patterns, list):
                    raise ValueError("each area must have a nonempty string name and a list of globs")
                if not all(_repo_relative_path(item) for item in patterns):
                    raise ValueError(f"area {name!r} contains an invalid repository-relative glob")
                areas[name] = list(patterns)
        except (json.JSONDecodeError, ValueError) as exc:
            diagnostics.append(Diagnostic("ERROR", "invalid-areas", f"invalid areas.json: {exc}",
                                          hint="use an object whose values are lists of repository-relative path globs"))

    return Backlog(root, path, issues, areas_path, path / "TICKET_STATUS.md", tickets, areas, diagnostics)


def criteria_digest(body: str) -> str:
    criteria: List[str] = []
    for line in body.splitlines():
        match = CHECKBOX_RE.match(line)
        if match:
            criteria.append(" ".join(match.group(1).split()))
    # New tickets use checkboxes.  The fallback keeps migrated tickets safe
    # while their remaining criteria are still written as ordinary bullets.
    if not criteria:
        lines = body.splitlines()
        start: Optional[int] = None
        level = 7
        for index, line in enumerate(lines):
            heading = re.match(r"^\s*(#{1,6})\s+remaining acceptance criteria\s*$", line, re.IGNORECASE)
            if heading:
                start = index + 1
                level = len(heading.group(1))
                break
        selected: List[str]
        if start is None:
            selected = lines
        else:
            selected = []
            for line in lines[start:]:
                heading = re.match(r"^\s*(#{1,6})\s+", line)
                if heading and len(heading.group(1)) <= level:
                    break
                selected.append(line)
        criteria = [" ".join(line.strip().split()) for line in selected if line.strip()]
    canonical = "\n".join(criteria).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _type_is(value: Any, expected: type) -> bool:
    return isinstance(value, expected) and not (expected is int and isinstance(value, bool))


def _list_of_strings(value: Any) -> bool:
    return (isinstance(value, list) and bool(value)
            and all(isinstance(item, str) and bool(item.strip()) for item in value))


def _reviewed_completion(ticket: Ticket, by_id: Mapping[str, Ticket], seen: Optional[Set[str]] = None) -> bool:
    return _effective_blocker(ticket.id, by_id, seen) is None


def _effective_blocker(ticket_id: str, by_id: Mapping[str, Ticket], seen: Optional[Set[str]] = None) -> Optional[str]:
    seen = set() if seen is None else set(seen)
    while ticket_id not in seen and ticket_id in by_id:
        seen.add(ticket_id)
        target = by_id[ticket_id]
        closure = target.metadata.get("closure")
        if target.state != "DONE" or not isinstance(closure, dict):
            return ticket_id
        reason = closure.get("reason")
        if reason in ("implemented", "already_resolved"):
            reviewer = closure.get("reviewed_by")
            reviewed = isinstance(reviewer, str) and bool(reviewer.strip())
            return None if reviewed and _list_of_strings(closure.get("evidence")) else ticket_id
        if reason not in ("duplicate", "superseded"):
            return ticket_id
        reviewer = closure.get("reviewed_by")
        if not (isinstance(reviewer, str) and reviewer.strip()
                and _list_of_strings(closure.get("evidence"))):
            return ticket_id
        replacement = closure.get("replacement")
        if not isinstance(replacement, str):
            return ticket_id
        ticket_id = replacement
    return ticket_id


def compute_blockers(ticket: Ticket, by_id: Mapping[str, Ticket]) -> List[str]:
    blockers: List[str] = []
    depends = ticket.metadata.get("depends_on")
    if not isinstance(depends, list):
        return blockers
    for dependency in depends:
        if not isinstance(dependency, str):
            continue
        blocker = _effective_blocker(dependency, by_id)
        if blocker is not None and blocker not in blockers:
            blockers.append(blocker)
    return blockers


def _find_cycles(edges: Mapping[str, Iterable[str]]) -> List[List[str]]:
    cycles: List[List[str]] = []
    done: Set[str] = set()
    for start in edges:
        if start in done:
            continue
        path = [start]
        positions = {start: 0}
        stack = [(start, iter(edges.get(start, ())))]
        while stack:
            node, targets = stack[-1]
            target = next(targets, None)
            if target is None:
                stack.pop()
                path.pop()
                positions.pop(node)
                done.add(node)
            elif target in positions:
                cycles.append(path[positions[target]:] + [target])
            elif target in edges and target not in done:
                positions[target] = len(path)
                path.append(target)
                stack.append((target, iter(edges.get(target, ()))))
    return cycles


def _validate_verification(ticket: Ticket, diagnostics: List[Diagnostic]) -> None:
    value = ticket.metadata.get("verification")
    if value is None:
        return
    if not isinstance(value, dict):
        diagnostics.append(Diagnostic("ERROR", "verification-type", "verification must be null or an object",
                                      ticket.id, "set verification to null or provide every verification field"))
        return
    missing = VERIFICATION_KEYS - set(value)
    extra = set(value) - VERIFICATION_KEYS
    if missing or extra:
        diagnostics.append(Diagnostic("ERROR", "verification-fields",
                                      f"verification fields differ: missing={sorted(missing)}, extra={sorted(extra)}",
                                      ticket.id, "use the documented verification fields exactly"))
    for name in ("commit", "checked_at", "criteria_digest", "checker", "result"):
        if not isinstance(value.get(name), str) or not value.get(name, "").strip():
            diagnostics.append(Diagnostic("ERROR", "verification-field", f"verification.{name} must be a nonempty string",
                                          ticket.id, f"record a meaningful {name}"))
    if value.get("result") not in VERIFICATION_RESULTS:
        diagnostics.append(Diagnostic("ERROR", "verification-result", f"unknown verification result {value.get('result')!r}",
                                      ticket.id, f"use one of: {', '.join(VERIFICATION_RESULTS)}"))
    if not _list_of_strings(value.get("evidence")):
        diagnostics.append(Diagnostic("ERROR", "verification-evidence", "verification evidence must contain at least one item",
                                      ticket.id, "record what was inspected or reproduced"))
    if not isinstance(value.get("provisional"), bool):
        diagnostics.append(Diagnostic("ERROR", "verification-provisional", "verification.provisional must be a boolean",
                                      ticket.id, "set provisional to true or false"))
    digest = value.get("criteria_digest")
    if isinstance(digest, str) and digest != criteria_digest(ticket.body):
        diagnostics.append(Diagnostic("WARNING", "criteria-changed", "acceptance criteria changed after verification",
                                      ticket.id, "run preflight and record new verification evidence"))
    checked_at = value.get("checked_at")
    if isinstance(checked_at, str):
        try:
            dt.datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
        except ValueError:
            diagnostics.append(Diagnostic("ERROR", "verification-date", "verification.checked_at is not an ISO-8601 date/time",
                                          ticket.id, "record an ISO-8601 value such as 2026-09-15T10:30:00+00:00"))


def _validate_closure(ticket: Ticket, diagnostics: List[Diagnostic]) -> None:
    value = ticket.metadata.get("closure")
    if ticket.state != "DONE":
        if value is not None:
            diagnostics.append(Diagnostic("ERROR", "active-closure", f"{ticket.state} ticket has closure metadata",
                                          ticket.id, "set closure to null until the ticket moves to DONE"))
        return
    if not isinstance(value, dict):
        diagnostics.append(Diagnostic("ERROR", "missing-closure", "DONE ticket has no closure record",
                                      ticket.id, "record the closure reason and evidence"))
        return
    missing = CLOSURE_KEYS - set(value)
    extra = set(value) - CLOSURE_KEYS
    if missing or extra:
        diagnostics.append(Diagnostic("ERROR", "closure-fields",
                                      f"closure fields differ: missing={sorted(missing)}, extra={sorted(extra)}",
                                      ticket.id, "use the documented closure fields exactly"))
    reason = value.get("reason")
    if reason not in CLOSURE_REASONS:
        diagnostics.append(Diagnostic("ERROR", "closure-reason", f"unknown closure reason {reason!r}",
                                      ticket.id, f"use one of: {', '.join(CLOSURE_REASONS)}"))
    for nullable in ("commit", "replacement", "reviewed_by"):
        if value.get(nullable) is not None and (not isinstance(value.get(nullable), str) or not value[nullable].strip()):
            diagnostics.append(Diagnostic("ERROR", "closure-field", f"closure.{nullable} must be null or a nonempty string",
                                          ticket.id, f"set {nullable} to null when unavailable"))
    if not _list_of_strings(value.get("evidence")):
        diagnostics.append(Diagnostic("ERROR", "closure-evidence", "closure evidence must contain at least one item",
                                      ticket.id, "record the implementation, review, or disposition evidence"))
    if reason in ("duplicate", "superseded") and not value.get("replacement"):
        diagnostics.append(Diagnostic("ERROR", "missing-replacement", f"{reason} closure has no replacement",
                                      ticket.id, "set closure.replacement to the canonical ticket ID"))
    if reason not in ("duplicate", "superseded") and value.get("replacement") is not None:
        diagnostics.append(Diagnostic("ERROR", "unexpected-replacement", f"{reason} closure has a replacement",
                                      ticket.id, "set closure.replacement to null"))
    if reason in ("implemented", "already_resolved", "duplicate", "superseded") and not value.get("reviewed_by"):
        diagnostics.append(Diagnostic("WARNING", "unreviewed-closure",
                                      "historical completion has no recorded reviewer and does not satisfy dependencies",
                                      ticket.id, "record review evidence before treating this ticket as a completed prerequisite"))


def validate(backlog: Backlog, include_index: bool = False) -> List[Diagnostic]:
    diagnostics = list(backlog.load_diagnostics)
    seen: Dict[str, Ticket] = {}
    known_areas = set(backlog.areas) - {"*"}
    for ticket in backlog.tickets:
        if ticket.parse_error:
            diagnostics.append(Diagnostic("ERROR", "metadata", ticket.parse_error, None,
                                          "add valid schema_version 1 JSON immediately after the title"))
            continue
        metadata = ticket.metadata
        unknown = set(metadata) - META_KEYS
        missing = META_KEYS - set(metadata)
        if unknown or missing:
            diagnostics.append(Diagnostic("ERROR", "metadata-fields",
                                          f"metadata fields differ: missing={sorted(missing)}, extra={sorted(unknown)}",
                                          ticket.id, "use the documented schema_version 1 fields exactly"))
        if metadata.get("schema_version") != 1 or not _type_is(metadata.get("schema_version"), int):
            diagnostics.append(Diagnostic("ERROR", "schema-version", "schema_version must be integer 1", ticket.id,
                                          "migrate the ticket to schema version 1"))
        ticket_id = metadata.get("id")
        if not isinstance(ticket_id, str) or not ticket_id.isdigit():
            diagnostics.append(Diagnostic("ERROR", "invalid-id", "id must be a string containing digits", ticket.id,
                                          "use the stable numeric ID as a quoted JSON string"))
        elif ticket_id in seen:
            diagnostics.append(Diagnostic("ERROR", "duplicate-id", f"ID also used by {seen[ticket_id].relative_path}", ticket_id,
                                          "assign a new never-before-used ID to one ticket"))
        else:
            seen[ticket_id] = ticket
        filename_match = ID_FILENAME_RE.match(ticket.path.name)
        filename_id = filename_match.group("id") if filename_match else None
        if not filename_match or filename_id != ticket_id:
            diagnostics.append(Diagnostic("ERROR", "filename-id", f"filename {ticket.path.name!r} does not begin with ID {ticket_id!r}",
                                          ticket.id, "rename the file so its prefix exactly matches metadata.id"))
        if metadata.get("priority") not in PRIORITIES:
            diagnostics.append(Diagnostic("ERROR", "priority", f"priority must be one of {', '.join(PRIORITIES)}", ticket.id,
                                          "set a supported priority"))
        if not _type_is(metadata.get("queue_order"), int):
            diagnostics.append(Diagnostic("ERROR", "queue-order", "queue_order must be an integer", ticket.id,
                                          "set an explicit integer queue order"))
        for field_name in ("areas", "depends_on", "related_to", "references"):
            if not _list_of_strings(metadata.get(field_name)) and metadata.get(field_name) != []:
                diagnostics.append(Diagnostic("ERROR", "list-field", f"{field_name} must be a list of nonempty strings", ticket.id,
                                              f"repair metadata.{field_name}"))
            elif isinstance(metadata.get(field_name), list) and len(metadata[field_name]) != len(set(metadata[field_name])):
                diagnostics.append(Diagnostic("ERROR", "duplicate-list-item", f"{field_name} contains duplicate values", ticket.id,
                                              f"remove duplicates from metadata.{field_name}"))
        for area in metadata.get("areas", []) if isinstance(metadata.get("areas"), list) else []:
            if not isinstance(area, str) or area not in known_areas:
                diagnostics.append(Diagnostic("ERROR", "unknown-area", f"unknown area {area!r}", ticket.id,
                                              "add the area to areas.json or choose an existing area"))
        for reference in metadata.get("references", []) if isinstance(metadata.get("references"), list) else []:
            if not _repo_relative_path(reference):
                diagnostics.append(Diagnostic("ERROR", "unsafe-reference", f"invalid repository-relative reference {reference!r}",
                                              ticket.id, "use a forward-slash path inside the repository"))
            elif not _inside(backlog.root / PurePosixPath(reference), backlog.root):
                diagnostics.append(Diagnostic("ERROR", "unsafe-reference", f"reference resolves outside repository: {reference}",
                                              ticket.id, "use a path inside the repository"))
            elif not (backlog.root / PurePosixPath(reference)).exists():
                diagnostics.append(Diagnostic("ERROR", "missing-reference", f"reference does not exist: {reference}", ticket.id,
                                              "repair the path or remove the obsolete reference"))
        _validate_verification(ticket, diagnostics)
        _validate_closure(ticket, diagnostics)

    by_id = backlog.by_id
    for ticket in backlog.tickets:
        if ticket.parse_error:
            continue
        for relation in ("depends_on", "related_to"):
            values = ticket.metadata.get(relation)
            if not isinstance(values, list):
                continue
            for target in values:
                if isinstance(target, str) and target not in by_id:
                    diagnostics.append(Diagnostic("ERROR", "missing-target", f"{relation} references missing ticket {target}",
                                                  ticket.id, f"create ticket {target} or remove the stale relationship"))
                if target == ticket.id:
                    diagnostics.append(Diagnostic("ERROR", "self-reference", f"{relation} references the same ticket", ticket.id,
                                                  "remove the self-reference"))
        closure = ticket.metadata.get("closure")
        if isinstance(closure, dict) and isinstance(closure.get("replacement"), str):
            replacement = closure["replacement"]
            if replacement not in by_id:
                diagnostics.append(Diagnostic("ERROR", "missing-replacement", f"replacement ticket {replacement} does not exist",
                                              ticket.id, "set replacement to an existing canonical ticket"))
            elif replacement == ticket.id:
                diagnostics.append(Diagnostic("ERROR", "self-replacement", "ticket replaces itself", ticket.id,
                                              "choose a different canonical ticket"))
        blockers = compute_blockers(ticket, by_id)
        if ticket.state == "OPEN" and blockers:
            diagnostics.append(Diagnostic("ERROR", "wrong-folder", f"OPEN ticket has unresolved blockers: {', '.join(blockers)}",
                                          ticket.id, "move the ticket to BLOCKED"))
        if ticket.state == "BLOCKED" and not blockers:
            diagnostics.append(Diagnostic("ERROR", "wrong-folder", "BLOCKED ticket has no unresolved prerequisite", ticket.id,
                                          "move the ticket to OPEN"))

    dependency_edges = {
        ticket.id: [item for item in ticket.metadata.get("depends_on", []) if isinstance(item, str)]
        for ticket in backlog.tickets if ticket.id != "?" and isinstance(ticket.metadata.get("depends_on"), list)
    }
    replacement_edges = {
        ticket.id: [ticket.metadata["closure"]["replacement"]]
        for ticket in backlog.tickets
        if ticket.id != "?" and isinstance(ticket.metadata.get("closure"), dict)
        and isinstance(ticket.metadata["closure"].get("replacement"), str)
    }
    for cycle in _find_cycles(dependency_edges):
        diagnostics.append(Diagnostic("ERROR", "dependency-cycle", " -> ".join(cycle), cycle[0],
                                      "remove or redirect one dependency edge"))
    for cycle in _find_cycles(replacement_edges):
        diagnostics.append(Diagnostic("ERROR", "replacement-cycle", " -> ".join(cycle), cycle[0],
                                      "point each duplicate or superseded ticket toward one canonical result"))

    combined_edges = {ticket_id: list(dependency_edges.get(ticket_id, ()))
                      + list(replacement_edges.get(ticket_id, ())) for ticket_id in by_id}
    for cycle in _find_cycles(combined_edges):
        has_dependency = any(target in dependency_edges.get(source, ())
                             for source, target in zip(cycle, cycle[1:]))
        has_replacement = any(target in replacement_edges.get(source, ())
                              for source, target in zip(cycle, cycle[1:]))
        if has_dependency and has_replacement:
            diagnostics.append(Diagnostic("ERROR", "dependency-replacement-cycle", " -> ".join(cycle), cycle[0],
                                          "a replacement must not depend on the ticket it replaces"))

    if include_index and not any(item.severity == "ERROR" for item in diagnostics):
        expected = render_index(backlog)
        actual = backlog.index_path.read_text(encoding="utf-8") if backlog.index_path.is_file() else None
        if actual != expected:
            diagnostics.append(Diagnostic("ERROR", "stale-index", "TICKET_STATUS.md is missing or stale",
                                          hint="run: python scripts/tickets.py index --write"))
    return diagnostics


def _static_verification_label(ticket: Ticket) -> str:
    verification = ticket.metadata.get("verification")
    if not isinstance(verification, dict):
        return "not recorded"
    if verification.get("criteria_digest") != criteria_digest(ticket.body):
        return "criteria changed"
    result = str(verification.get("result", "recorded")).replace("_", " ")
    return f"provisional {result}" if verification.get("provisional") else result


def _table_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_index(backlog: Backlog) -> str:
    lines = [
        "# Ticket status",
        "",
        "<!-- Generated by scripts/tickets.py index --write. Edit ticket records, then regenerate. -->",
        "",
        "| Queue | ID | Title | Priority | State | Blockers | Verification | Closure |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    by_id = backlog.by_id
    priority_order = {value: index for index, value in enumerate(PRIORITIES)}
    tickets = sorted(
        (ticket for ticket in backlog.tickets if ticket.id != "?"),
        key=lambda ticket: (
            ticket.metadata.get("queue_order") if _type_is(ticket.metadata.get("queue_order"), int) else 10**12,
            priority_order.get(ticket.metadata.get("priority"), len(PRIORITIES)),
            ticket.id,
        ),
    )
    for ticket in tickets:
        blockers = ", ".join(compute_blockers(ticket, by_id)) or "None"
        closure = ticket.metadata.get("closure")
        reason = closure.get("reason") if isinstance(closure, dict) else "None"
        if (isinstance(closure, dict) and reason in ("implemented", "already_resolved")
                and not closure.get("reviewed_by")):
            reason += "; review unknown"
        title = re.sub(r"^\d+\s*:\s*", "", ticket.title)
        link = f"[{ticket.id}]({ticket.relative_path})"
        lines.append(
            "| {queue} | {ticket_id} | {title} | {priority} | {state} | {blockers} | {verification} | {closure} |".format(
                queue=_table_cell(ticket.metadata.get("queue_order", "?")),
                ticket_id=link,
                title=_table_cell(title),
                priority=_table_cell(ticket.metadata.get("priority", "?")),
                state=ticket.state,
                blockers=_table_cell(blockers),
                verification=_table_cell(_static_verification_label(ticket)),
                closure=_table_cell(reason),
            )
        )
    return "\n".join(lines) + "\n"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def _metadata_text(ticket: Ticket, metadata: Mapping[str, Any]) -> str:
    match = META_RE.match(ticket.body)
    if not match:
        raise TicketError(f"ticket {ticket.id} has malformed metadata and cannot be updated safely")
    encoded = json.dumps(metadata, indent=2, ensure_ascii=False)
    return f"{match.group('title')}{match.group('gap')}```json\n{encoded}\n```{match.group('rest')}"


def _git_head(root: Path) -> str:
    return _run_git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).stdout.strip()


def _resolve_commit(root: Path, revision: str) -> Optional[str]:
    result = _run_git(root, ["rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}"], check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def changed_paths(root: Path, base: str, head: str) -> List[str]:
    base_commit = _resolve_commit(root, base)
    head_commit = _resolve_commit(root, head)
    if not base_commit:
        raise TicketError(f"base revision does not resolve to a commit: {base}")
    if not head_commit:
        raise TicketError(f"head revision does not resolve to a commit: {head}")
    output = _run_git(root, ["diff", "--name-status", "-z", "-M", base_commit, head_commit, "--"]).stdout
    fields = iter(output.rstrip("\x00").split("\x00")) if output else iter(())
    paths: Set[str] = set()
    for status in fields:
        for _ in range(2 if status.startswith(("R", "C")) else 1):
            candidate = next(fields, None)
            if candidate is None:
                raise TicketError("git returned an incomplete changed-path record")
            paths.add(PurePosixPath(candidate).as_posix())
    return sorted(paths)


def dirty_paths(root: Path) -> List[str]:
    paths: Set[str] = set()
    for args in (["diff", "--name-only", "--no-renames", "-z", "--"],
                 ["diff", "--cached", "--name-only", "--no-renames", "-z", "--"],
                 ["ls-files", "--others", "--exclude-standard", "-z"]):
        result = _run_git(root, args, check=False)
        if result.returncode == 0:
            paths.update(PurePosixPath(name).as_posix() for name in result.stdout.split("\x00") if name)
    return sorted(paths)


def _has_git_history(root: Path) -> bool:
    result = _run_git(root, ["rev-parse", "--is-inside-work-tree"], check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"


def _ticket_metadata_at_commit(backlog: Backlog, ticket: Ticket, commit: str) -> Optional[Dict[str, Any]]:
    """Read the ticket's metadata at a commit without assuming its old folder."""
    backlog_rel = backlog.path.relative_to(backlog.root).as_posix()
    listing = _run_git(
        backlog.root,
        ["ls-tree", "-r", "--name-only", commit, "--", f"{backlog_rel}/issues"],
        check=False,
    )
    if listing.returncode != 0:
        return None
    prefix = f"{ticket.id}-"
    matches = [line for line in listing.stdout.splitlines() if PurePosixPath(line).name.startswith(prefix)
               and line.lower().endswith(".md")]
    if len(matches) != 1:
        return None
    shown = _run_git(backlog.root, ["show", f"{commit}:{matches[0]}"], check=False)
    if shown.returncode != 0:
        return None
    match = META_RE.match(shown.stdout)
    if not match:
        return None
    try:
        value = json.loads(match.group("json"))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _ticket_body_at_commit(backlog: Backlog, ticket: Ticket, commit: str) -> Optional[str]:
    """Read the historical ticket body, resolving its state folder by ID."""
    backlog_rel = backlog.path.relative_to(backlog.root).as_posix()
    listing = _run_git(
        backlog.root,
        ["ls-tree", "-r", "--name-only", commit, "--", f"{backlog_rel}/issues"],
        check=False,
    )
    if listing.returncode != 0:
        return None
    prefix = f"{ticket.id}-"
    matches = [line for line in listing.stdout.splitlines() if PurePosixPath(line).name.startswith(prefix)
               and line.lower().endswith(".md")]
    if len(matches) != 1:
        return None
    shown = _run_git(backlog.root, ["show", f"{commit}:{matches[0]}"], check=False)
    return shown.stdout if shown.returncode == 0 else None


def areas_for_paths(backlog: Backlog, paths: Iterable[str]) -> Tuple[Set[str], List[str]]:
    area_names = set(backlog.areas) - {"*"}
    affected: Set[str] = set()
    unknown: List[str] = []
    for raw_path in paths:
        path = PurePosixPath(raw_path).as_posix()
        matched = False
        for area, patterns in backlog.areas.items():
            if any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns):
                matched = True
                if area == "*":
                    affected.update(area_names)
                else:
                    affected.add(area)
        if not matched and not path.startswith(f"{backlog.path.relative_to(backlog.root).as_posix()}/"):
            unknown.append(path)
    return affected, unknown


def impacted_tickets(
    backlog: Backlog,
    paths: Iterable[str],
    extra_areas: Iterable[str] = (),
) -> Dict[str, List[str]]:
    path_list = [PurePosixPath(path).as_posix() for path in paths]
    areas, _ = areas_for_paths(backlog, path_list)
    areas.update(extra_areas)
    by_id = backlog.by_id
    reasons: Dict[str, List[str]] = {}

    def add(ticket_id: str, reason: str) -> None:
        if ticket_id in by_id and reason not in reasons.setdefault(ticket_id, []):
            reasons[ticket_id].append(reason)

    backlog_prefix = backlog.path.relative_to(backlog.root).as_posix() + "/issues/"
    changed_ticket_ids: Set[str] = set()
    for path in path_list:
        if path.startswith(backlog_prefix):
            match = ID_FILENAME_RE.match(PurePosixPath(path).name)
            if match:
                changed_ticket_ids.add(match.group("id"))
        for ticket in backlog.tickets:
            if path in ticket.metadata.get("references", []):
                add(ticket.id, f"references changed path {path}")

    for ticket in backlog.tickets:
        overlap = sorted(set(ticket.metadata.get("areas", [])) & areas)
        if overlap:
            add(ticket.id, f"affected area: {', '.join(overlap)}")
    for ticket_id in changed_ticket_ids:
        add(ticket_id, "ticket record changed")

    # Relationships make impact transitive.  This is intentionally conservative.
    queue = list(reasons)
    visited = set(queue)
    while queue:
        current = queue.pop(0)
        current_ticket = by_id[current]
        direct = set(current_ticket.metadata.get("depends_on", [])) | set(current_ticket.metadata.get("related_to", []))
        closure = current_ticket.metadata.get("closure")
        if isinstance(closure, dict) and isinstance(closure.get("replacement"), str):
            direct.add(closure["replacement"])
        for target in direct:
            if target in by_id:
                add(target, f"related to affected ticket {current}")
                if target not in visited:
                    visited.add(target)
                    queue.append(target)
        for other in backlog.tickets:
            other_links = set(other.metadata.get("depends_on", [])) | set(other.metadata.get("related_to", []))
            other_closure = other.metadata.get("closure")
            if isinstance(other_closure, dict) and isinstance(other_closure.get("replacement"), str):
                other_links.add(other_closure["replacement"])
            if current in other_links:
                add(other.id, f"depends on or relates to affected ticket {current}")
                if other.id not in visited:
                    visited.add(other.id)
                    queue.append(other.id)
    return {ticket_id: reasons[ticket_id] for ticket_id in sorted(reasons, key=lambda value: (len(value), value))}


def verification_state(backlog: Backlog, ticket: Ticket) -> Tuple[str, List[str]]:
    if not _has_git_history(backlog.root):
        return "needs verification", ["git history is unavailable, so the recorded revision cannot be checked"]
    record = ticket.metadata.get("verification")
    reasons: List[str] = []
    if not isinstance(record, dict):
        return "needs verification", ["no verification record"]
    commit = record.get("commit")
    resolved = _resolve_commit(backlog.root, commit) if isinstance(commit, str) else None
    if not resolved:
        reasons.append("verification commit is missing from repository history")
    if record.get("criteria_digest") != criteria_digest(ticket.body):
        reasons.append("acceptance criteria changed")
    if not _list_of_strings(record.get("evidence")):
        reasons.append("verification evidence is empty")
    if record.get("result") != "still_valid":
        reasons.append(f"recorded result is {record.get('result', 'unknown')}")
    if record.get("provisional"):
        reasons.append("verification is marked provisional")

    committed_paths: List[str] = []
    if resolved:
        head = _git_head(backlog.root)
        committed_paths.extend(changed_paths(backlog.root, resolved, head))
        historical = _ticket_metadata_at_commit(backlog, ticket, resolved)
        historical_body = _ticket_body_at_commit(backlog, ticket, resolved)
        relationship_fields = ("areas", "depends_on", "related_to", "references")
        if historical is None:
            reasons.append("ticket metadata was unavailable at the verification commit")
        elif any(historical.get(field_name) != ticket.metadata.get(field_name) for field_name in relationship_fields):
            reasons.append("ticket areas, relationships, or references changed after verification")
        if historical_body is None:
            reasons.append("ticket criteria were unavailable at the verification commit")
        elif criteria_digest(historical_body) != criteria_digest(ticket.body):
            reasons.append("acceptance criteria differ from the verification commit")
    dirty = dirty_paths(backlog.root)
    backlog_prefix = backlog.path.relative_to(backlog.root).as_posix() + "/"
    committed_relevant = [path for path in committed_paths if not path.startswith(backlog_prefix)]
    dirty_relevant = [path for path in dirty if not path.startswith(backlog_prefix)]
    affected_areas, unknown_committed = areas_for_paths(backlog, committed_relevant)
    dirty_areas, unknown_dirty = areas_for_paths(backlog, dirty_relevant)
    ticket_areas = set(ticket.metadata.get("areas", []))
    changed_refs = set(ticket.metadata.get("references", [])) & set(committed_relevant)
    dirty_refs = set(ticket.metadata.get("references", [])) & set(dirty_relevant)
    if ticket_areas & affected_areas:
        reasons.append("relevant code, tests, contracts, or configuration changed after verification")
    if ticket_areas & dirty_areas or dirty_refs:
        reasons.append("relevant dirty files make verification provisional")
    if changed_refs:
        reasons.append("referenced requirement or implementation changed after verification")
    if unknown_committed:
        reasons.append("unmapped repository changes may affect the ticket")
    if unknown_dirty:
        reasons.append("unmapped dirty files may affect the ticket")
    if reasons:
        return "needs verification", list(dict.fromkeys(reasons))
    return "ready", ["current still-valid evidence matches the criteria and relevant checkout state"]


def _ticket_or_error(backlog: Backlog, ticket_id: str) -> Ticket:
    ticket = backlog.by_id.get(ticket_id)
    if ticket is None:
        raise TicketError(f"ticket {ticket_id} was not found in any state folder")
    return ticket


def _print_diagnostics(diagnostics: Iterable[Diagnostic]) -> None:
    for diagnostic in diagnostics:
        print(diagnostic.format())


def command_check(backlog: Backlog, _args: argparse.Namespace) -> int:
    diagnostics = validate(backlog, include_index=True)
    _print_diagnostics(diagnostics)
    errors = sum(item.severity == "ERROR" for item in diagnostics)
    warnings = sum(item.severity == "WARNING" for item in diagnostics)
    print(f"check: {len(backlog.tickets)} tickets, {errors} errors, {warnings} warnings")
    return 1 if errors else 0


def command_index(backlog: Backlog, args: argparse.Namespace) -> int:
    diagnostics = validate(backlog, include_index=False)
    errors = [item for item in diagnostics if item.severity == "ERROR"]
    if errors:
        _print_diagnostics(errors)
        print("index not written because authoritative records are invalid")
        return 1
    rendered = render_index(backlog)
    if args.write:
        _atomic_write(backlog.index_path, rendered)
        print(f"wrote {backlog.index_path}")
    else:
        sys.stdout.write(rendered)
    return 0


def _require_valid_records(backlog: Backlog) -> None:
    analyzable = {"wrong-folder", "missing-reference", "missing-target"}
    errors = [item for item in validate(backlog, include_index=False)
              if item.severity == "ERROR" and item.code not in analyzable]
    if errors:
        _print_diagnostics(errors)
        raise TicketError("authoritative records are invalid; repair them before using this command")


def command_show(backlog: Backlog, args: argparse.Namespace) -> int:
    _require_valid_records(backlog)
    ticket = _ticket_or_error(backlog, args.id)
    blockers = compute_blockers(ticket, backlog.by_id)
    status, reasons = verification_state(backlog, ticket)
    print(f"Ticket {ticket.id}: {ticket.title}")
    print(f"Path: {ticket.relative_path}")
    print(f"State: {ticket.state}")
    print(f"Blockers: {', '.join(blockers) if blockers else 'none'}")
    print(f"Verification: {status} ({'; '.join(reasons)})")
    verification = ticket.metadata.get("verification")
    closure = ticket.metadata.get("closure")
    if isinstance(verification, dict):
        print("Verification evidence:")
        for item in verification.get("evidence", []):
            print(f"  - {item}")
    if isinstance(closure, dict):
        print(f"Closure: {closure.get('reason')}")
        print("Closure evidence:")
        for item in closure.get("evidence", []):
            print(f"  - {item}")
    print("\n" + ticket.body.rstrip())
    return 0


def command_next(backlog: Backlog, _args: argparse.Namespace) -> int:
    _require_valid_records(backlog)
    by_id = backlog.by_id
    eligible = [ticket for ticket in backlog.tickets if ticket.state == "OPEN" and not compute_blockers(ticket, by_id)]
    eligible.sort(key=lambda ticket: (ticket.metadata.get("queue_order", 10**12),
                                      PRIORITIES.index(ticket.metadata.get("priority"))
                                      if ticket.metadata.get("priority") in PRIORITIES else 99,
                                      ticket.id))
    if not eligible:
        print("No unblocked OPEN ticket is available.")
        return 0
    for ticket in eligible:
        status, reasons = verification_state(backlog, ticket)
        display_title = re.sub(r"^\d+\s*:\s*", "", ticket.title)
        print(f"{ticket.id} [{ticket.metadata.get('priority', '?')}] queue {ticket.metadata.get('queue_order', '?')}: "
              f"{status}: {display_title}")
        if status != "ready":
            print(f"  Needed: {'; '.join(reasons)}")
    return 0


def command_preflight(backlog: Backlog, args: argparse.Namespace) -> int:
    _require_valid_records(backlog)
    ticket = _ticket_or_error(backlog, args.id)
    if ticket.state == "DONE":
        print(f"Ticket {ticket.id} is closed in DONE and is not ready to start. Reopen it explicitly before implementation.")
        return 1
    if ticket.state == "TO_REVIEW":
        print(f"Ticket {ticket.id} is awaiting review in TO_REVIEW, not ready to start.")
        return 1
    already_in_progress = ticket.state == "IN_PROGRESS"
    if already_in_progress:
        print(f"Ticket {ticket.id} is already IN_PROGRESS; preflight does not start it again.")
    blockers = compute_blockers(ticket, backlog.by_id)
    if blockers:
        print(f"Ticket {ticket.id} cannot start; unresolved blockers: {', '.join(blockers)}")
        return 1
    status, reasons = verification_state(backlog, ticket)
    print(f"Ticket {ticket.id}: {status}")
    for reason in reasons:
        print(f"- {reason}")
    if status != "ready":
        print("Reproduce or inspect the remaining behavior, then record evidence with the verify command.")
        return 1
    if already_in_progress:
        print("Preflight evidence is current for this in-progress ticket.")
    else:
        print("Preflight evidence is current. Review it before moving the ticket to IN_PROGRESS.")
    return 0


def command_impact(backlog: Backlog, args: argparse.Namespace) -> int:
    base_commit = _resolve_commit(backlog.root, args.base)
    head_commit = _resolve_commit(backlog.root, args.head)
    if not base_commit:
        raise TicketError(f"base revision does not resolve to a commit: {args.base}")
    if not head_commit:
        raise TicketError(f"head revision does not resolve to a commit: {args.head}")
    backlog_rel = backlog.path.relative_to(backlog.root).as_posix()
    try:
        base_snapshot = snapshot_at_commit(backlog.root, backlog_rel, base_commit)
        head_snapshot = snapshot_at_commit(backlog.root, backlog_rel, head_commit)
    except HistoryError as exc:
        raise TicketError(f"cannot read ticket history: {exc}") from exc
    known_areas = (set(base_snapshot.areas) | set(head_snapshot.areas)) - {"*"}
    invalid_areas = sorted(set(args.area) - known_areas)
    if invalid_areas:
        raise TicketError(f"unknown extra area(s): {', '.join(invalid_areas)}")
    paths = changed_paths(backlog.root, base_commit, head_commit)
    selected = select_impact(paths, base_snapshot, head_snapshot, args.area)
    print(f"Changed paths: {len(paths)}")
    print(f"Affected areas: {', '.join(sorted(selected.areas)) if selected.areas else 'none'}")
    for path in selected.unknown_paths:
        print(f"WARNING [unmapped-path]: {path} is not covered by areas.json or recognized ticket records; "
              "review impact manually")
    if not selected.reasons:
        print("No candidate tickets found. Unmapped paths still require manual review.")
        return 1 if selected.unknown_paths else 0
    print("Candidate tickets:")
    for ticket_id, reasons in selected.reasons.items():
        print(f"- {ticket_id}: {'; '.join(reasons)}")
    return 1 if selected.unknown_paths else 0


def command_audit(backlog: Backlog, args: argparse.Namespace) -> int:
    initial = validate(backlog, include_index=True)
    errors = [item for item in initial if item.severity == "ERROR"]
    if errors:
        _print_diagnostics(initial)
        print(f"audit: structural repair required before verification audit ({len(errors)} errors)")
        return 1
    today = dt.datetime.now(dt.timezone.utc)
    count = 0
    for ticket in sorted(backlog.tickets, key=lambda value: value.id):
        record = ticket.metadata.get("verification")
        findings: List[str] = []
        if not isinstance(record, dict):
            findings.append("never verified")
        else:
            checked = record.get("checked_at")
            try:
                instant = dt.datetime.fromisoformat(str(checked).replace("Z", "+00:00"))
                if instant.tzinfo is None:
                    instant = instant.replace(tzinfo=dt.timezone.utc)
                age = (today - instant.astimezone(dt.timezone.utc)).days
                if age > args.max_age_days:
                    findings.append(f"verification is {age} days old")
            except ValueError:
                findings.append("verification date is invalid")
            if record.get("criteria_digest") != criteria_digest(ticket.body):
                findings.append("criteria changed")
            if record.get("provisional"):
                findings.append("verification is provisional")
        closure = ticket.metadata.get("closure")
        if ticket.state == "DONE" and isinstance(closure, dict) and closure.get("reason") in ("implemented", "already_resolved") \
                and not closure.get("reviewed_by"):
            findings.append("completion has no recorded review")
        if isinstance(closure, dict) and closure.get("reason") in ("duplicate", "superseded"):
            findings.append(f"review canonical replacement {closure.get('replacement')}")
        if findings:
            count += 1
            print(f"{ticket.id} [{ticket.state}]: {'; '.join(findings)}")
    structural = initial
    for item in structural:
        print(item.format())
    print(f"audit: {count} tickets need review; {len(structural)} structural findings")
    return 1 if any(item.severity == "ERROR" for item in structural) else 0


def command_search(backlog: Backlog, args: argparse.Namespace) -> int:
    _require_valid_records(backlog)
    query = args.query.casefold()
    matches = [ticket for ticket in backlog.tickets
               if query in ticket.title.casefold() or query in ticket.body.casefold()]
    for ticket in sorted(matches, key=lambda value: (value.metadata.get("queue_order", 10**12), value.id)):
        display_title = re.sub(r"^\d+\s*:\s*", "", ticket.title)
        print(f"{ticket.id} [{ticket.state}] {display_title}: {ticket.relative_path}")
    if not matches:
        print(f"No ticket contains {args.query!r}.")
    return 0


def _validate_before_mutation(backlog: Backlog, allowed_codes: Iterable[str] = ()) -> None:
    allowed = set(allowed_codes)
    errors = [item for item in validate(backlog, include_index=False)
              if item.severity == "ERROR" and item.code not in allowed]
    if errors:
        _print_diagnostics(errors)
        raise TicketError("authoritative records are invalid; repair them before applying a mutation")


def _write_ticket_update(backlog: Backlog, ticket: Ticket, metadata: Dict[str, Any], state: Optional[str] = None) -> Path:
    target_state = state or ticket.state
    target_folder = (backlog.issues_path / target_state).resolve()
    target_path = (target_folder / ticket.path.name).resolve()
    if not _inside(target_folder, backlog.issues_path) or not _inside(target_path, backlog.issues_path):
        raise TicketError("refusing to write a ticket outside the backlog issues directory")
    content = _metadata_text(ticket, metadata)

    # Validate the proposed record and folder state entirely in memory first.
    proposed = copy.deepcopy(backlog)
    proposed_ticket = next(item for item in proposed.tickets if item.path == ticket.path)
    proposed_ticket.metadata = copy.deepcopy(metadata)
    proposed_ticket.body = content
    proposed_ticket.state = target_state
    proposed_ticket.path = target_path
    proposed_ticket.relative_path = target_path.relative_to(backlog.path).as_posix()

    proposed_by_id = proposed.by_id
    for dependent in proposed.tickets:
        blockers = compute_blockers(dependent, proposed_by_id)
        new_state = dependent.state
        if dependent.state == "OPEN" and blockers:
            new_state = "BLOCKED"
        elif dependent.state == "BLOCKED" and not blockers:
            new_state = "OPEN"
        if new_state != dependent.state:
            dependent.state = new_state
            dependent.path = (proposed.issues_path / new_state / dependent.path.name).resolve()
            dependent.relative_path = dependent.path.relative_to(proposed.path).as_posix()

    errors = [item for item in validate(proposed, include_index=False) if item.severity == "ERROR"]
    if errors:
        _print_diagnostics(errors)
        raise TicketError("proposed update is invalid; no files were changed")

    original_by_id = backlog.by_id
    source_paths = {item.path.resolve() for item in backlog.tickets}
    operations: List[Tuple[Path, Path, str, str]] = []
    for updated in proposed.tickets:
        original = original_by_id[updated.id]
        source = original.path.resolve()
        destination = updated.path.resolve()
        if destination != source or updated.body != original.body:
            if destination.exists() and destination != source and destination not in source_paths:
                raise TicketError(f"destination collision: {destination}")
            operations.append((source, destination, original.body, updated.body))

    for source, destination, original_body, _updated_body in operations:
        _require_regular_path(source, backlog.issues_path)
        if source.read_text(encoding="utf-8") != original_body:
            raise TicketError(f"ticket changed while the update was being prepared: {source}; retry the command")
        destination.parent.mkdir(parents=True, exist_ok=True)
        _require_regular_path(destination.parent, backlog.issues_path)
        if destination.exists():
            _require_regular_path(destination, backlog.issues_path)

    for _source, destination, _original_body, updated_body in operations:
        _atomic_write(destination, updated_body)
    for source, destination, _original_body, _updated_body in operations:
        if source == destination:
            continue
        try:
            source.unlink()
        except OSError as exc:
            raise TicketError(
                f"new copy was written to {destination}, but the old copy could not be removed: {exc}. "
                "Run check to expose the duplicate before continuing."
            ) from exc
    refreshed = load_backlog(backlog.root, backlog.path.relative_to(backlog.root).as_posix())
    _atomic_write(refreshed.index_path, render_index(refreshed))
    return proposed.by_id[ticket.id].path


def command_verify(backlog: Backlog, args: argparse.Namespace) -> int:
    _validate_before_mutation(backlog)
    ticket = _ticket_or_error(backlog, args.id)
    commit = args.commit or _git_head(backlog.root)
    resolved = _resolve_commit(backlog.root, commit)
    if not resolved:
        raise TicketError(f"verification commit does not resolve: {commit}")
    backlog_prefix = backlog.path.relative_to(backlog.root).as_posix() + "/"
    relevant_dirty = [path for path in dirty_paths(backlog.root) if not path.startswith(backlog_prefix)]
    affected_areas, unknown_dirty = areas_for_paths(backlog, relevant_dirty)
    historical_body = _ticket_body_at_commit(backlog, ticket, resolved)
    historical_metadata = _ticket_metadata_at_commit(backlog, ticket, resolved)
    criteria_differ = historical_body is None or criteria_digest(historical_body) != criteria_digest(ticket.body)
    relationship_fields = ("areas", "depends_on", "related_to", "references")
    relationships_differ = historical_metadata is None or any(
        historical_metadata.get(field_name) != ticket.metadata.get(field_name)
        for field_name in relationship_fields
    )
    is_relevant_dirty = bool(set(ticket.metadata.get("areas", [])) & affected_areas
                             or set(ticket.metadata.get("references", [])) & set(relevant_dirty)
                             or unknown_dirty or criteria_differ or relationships_differ)
    provisional = bool(args.provisional or is_relevant_dirty)
    metadata = copy.deepcopy(ticket.metadata)
    metadata["verification"] = {
        "commit": resolved,
        "checked_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "criteria_digest": criteria_digest(ticket.body),
        "checker": args.checker,
        "result": args.result,
        "evidence": args.evidence,
        "provisional": provisional,
    }
    target = _write_ticket_update(backlog, ticket, metadata)
    print(f"recorded {args.result} verification for ticket {ticket.id} in {target}")
    if is_relevant_dirty:
        print("Verification is provisional because relevant files have uncommitted changes.")
    return 0


def command_move(backlog: Backlog, args: argparse.Namespace) -> int:
    ticket = _ticket_or_error(backlog, args.id)
    target_state = args.state.upper()
    if target_state not in STATES:
        raise TicketError(f"unknown state {target_state}; choose one of: {', '.join(STATES)}")
    collision_path = (backlog.issues_path / target_state / ticket.path.name).resolve()
    if collision_path != ticket.path.resolve() and collision_path.exists():
        raise TicketError(f"destination collision: {collision_path}")
    _validate_before_mutation(backlog, allowed_codes={"wrong-folder"})
    same_done_update = ticket.state == "DONE" and target_state == "DONE" and bool(args.reason)
    if ticket.state == target_state and not same_done_update:
        raise TicketError(f"ticket {ticket.id} is already in {target_state}")
    normal = {
        "OPEN": {"BLOCKED", "IN_PROGRESS", "DONE"},
        "BLOCKED": {"OPEN", "IN_PROGRESS", "DONE"},
        "IN_PROGRESS": {"BLOCKED", "OPEN", "TO_REVIEW", "DONE"},
        "TO_REVIEW": {"IN_PROGRESS", "DONE"},
        "DONE": set(),
    }
    if not same_done_update and target_state not in normal[ticket.state] and not args.force:
        raise TicketError(f"unsupported transition {ticket.state} -> {target_state}; use --force for an explicit reopen")
    metadata = copy.deepcopy(ticket.metadata)
    if target_state == "DONE":
        if not args.reason:
            raise TicketError("moving to DONE requires --reason")
        if not args.evidence:
            raise TicketError("moving to DONE requires at least one --evidence item")
        if args.reason in ("duplicate", "superseded") and not args.replacement:
            raise TicketError(f"--reason {args.reason} requires --replacement")
        if args.reason not in ("duplicate", "superseded") and args.replacement:
            raise TicketError("--replacement is valid only for duplicate or superseded closure")
        if args.reason in ("implemented", "already_resolved", "duplicate", "superseded") and not args.reviewed_by:
            raise TicketError(f"--reason {args.reason} requires --reviewed-by; unreviewed historical closure must be migrated explicitly")
        commit = args.commit
        if commit:
            commit = _resolve_commit(backlog.root, commit)
            if not commit:
                raise TicketError(f"closure commit does not resolve: {args.commit}")
        metadata["closure"] = {
            "reason": args.reason,
            "commit": commit,
            "replacement": args.replacement,
            "reviewed_by": args.reviewed_by,
            "evidence": args.evidence,
        }
    else:
        if any((args.reason, args.commit, args.replacement, args.reviewed_by, args.evidence)):
            raise TicketError("closure options may be used only when moving to DONE")
        metadata["closure"] = None
        if target_state == "IN_PROGRESS":
            status, reasons = verification_state(backlog, ticket)
            if status != "ready":
                raise TicketError(f"preflight is not ready: {'; '.join(reasons)}")
    target = _write_ticket_update(backlog, ticket, metadata, target_state)
    print(f"moved ticket {ticket.id}: {ticket.state} -> {target_state} ({target})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="repository root (default: discover from current directory)")
    parser.add_argument("--backlog", default=DEFAULT_BACKLOG,
                        help=f"repository-relative backlog path (default: {DEFAULT_BACKLOG})")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("check", help="validate records and the generated index").set_defaults(handler=command_check)
    index = commands.add_parser("index", help="print or atomically regenerate the derived status table")
    index.add_argument("--write", action="store_true", help="replace TICKET_STATUS.md atomically")
    index.set_defaults(handler=command_index)
    show = commands.add_parser("show", help="show a ticket resolved by ID")
    show.add_argument("id")
    show.set_defaults(handler=command_show)
    commands.add_parser("next", help="list unblocked OPEN tickets in priority order").set_defaults(handler=command_next)
    preflight = commands.add_parser("preflight", help="check whether a ticket has current evidence and can start")
    preflight.add_argument("id")
    preflight.set_defaults(handler=command_preflight)
    impact = commands.add_parser("impact", help="find tickets affected by changes between two commits")
    impact.add_argument("--base", required=True)
    impact.add_argument("--head", required=True)
    impact.add_argument("--area", action="append", default=[], help="add a known affected area (repeatable)")
    impact.set_defaults(handler=command_impact)
    audit = commands.add_parser("audit", help="list verification and structural review work")
    audit.add_argument("--max-age-days", type=int, default=30, help="age threshold in days (default: 30)")
    audit.set_defaults(handler=command_audit)
    search = commands.add_parser("search", help="search active and completed ticket text")
    search.add_argument("query")
    search.set_defaults(handler=command_search)
    verify = commands.add_parser("verify", help="record preflight verification evidence")
    verify.add_argument("id")
    verify.add_argument("--result", choices=VERIFICATION_RESULTS, required=True)
    verify.add_argument("--checker", required=True)
    verify.add_argument("--evidence", action="append", required=True)
    verify.add_argument("--commit")
    verify.add_argument("--provisional", action="store_true")
    verify.set_defaults(handler=command_verify)
    move = commands.add_parser("move", help="validate and move a ticket between workflow folders")
    move.add_argument("id")
    move.add_argument("state", type=str.upper, choices=STATES)
    move.add_argument("--reason", choices=CLOSURE_REASONS)
    move.add_argument("--commit")
    move.add_argument("--replacement")
    move.add_argument("--reviewed-by")
    move.add_argument("--evidence", action="append", default=[])
    move.add_argument("--force", action="store_true", help="allow an exceptional transition or explicit reopen")
    move.set_defaults(handler=command_move)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve() if args.root else discover_root()
        backlog = load_backlog(root, args.backlog)
        return int(args.handler(backlog, args))
    except TicketError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
