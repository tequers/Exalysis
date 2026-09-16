"""Read ticket metadata at Git commits and select affected tickets.

This module has no dependency on the ticket command module. It reads committed
blobs in one batch and compares the relationship graphs at both ends of an
impact range, so removed tickets and removed relationships remain visible.
"""

from __future__ import annotations

import fnmatch
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


STATES = {"OPEN", "BLOCKED", "IN_PROGRESS", "TO_REVIEW", "DONE"}
KNOWN_BACKLOG_SUPPORT = {
    "MIGRATION_REPORT.md",
    "README.md",
    "TEMPLATE.md",
    "TICKET_STATUS.md",
    "areas.json",
}
ID_FILENAME_RE = re.compile(r"^(?P<id>\d+)-.+\.md$", re.IGNORECASE)
META_RE = re.compile(
    r"\A\ufeff?\s*#\s+[^\r\n]+\r?\n\s*```json\s*\r?\n(?P<json>.*?)\r?\n```",
    re.DOTALL | re.IGNORECASE,
)


class HistoryError(Exception):
    """A commit snapshot could not be read safely."""


@dataclass(frozen=True)
class HistoricalTicket:
    id: str
    path: str
    areas: Tuple[str, ...]
    depends_on: Tuple[str, ...]
    related_to: Tuple[str, ...]
    references: Tuple[str, ...]
    replacement: Optional[str]

    @property
    def links(self) -> Set[str]:
        result = set(self.depends_on) | set(self.related_to)
        if self.replacement:
            result.add(self.replacement)
        return result


@dataclass(frozen=True)
class HistorySnapshot:
    revision: str
    backlog_path: str
    areas: Mapping[str, Tuple[str, ...]]
    tickets: Mapping[str, HistoricalTicket]
    unknown_issue_paths: Tuple[str, ...] = ()


@dataclass
class ImpactSelection:
    reasons: Dict[str, List[str]] = field(default_factory=dict)
    areas: Set[str] = field(default_factory=set)
    unknown_paths: List[str] = field(default_factory=list)


def _git_bytes(root: Path, args: Sequence[str], input_bytes: Optional[bytes] = None) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise HistoryError(message or f"git {' '.join(args)} failed with code {result.returncode}")
    return result.stdout


def _committed_blobs(root: Path, revision: str, paths: Sequence[str]) -> Dict[str, str]:
    listing = _git_bytes(root, ["ls-tree", "-r", "-z", revision, "--", *paths])
    entries: List[Tuple[bytes, str]] = []
    for raw_entry in listing.split(b"\0"):
        if not raw_entry:
            continue
        try:
            descriptor, raw_path = raw_entry.split(b"\t", 1)
            _mode, object_type, object_id = descriptor.split(b" ", 2)
        except ValueError as error:
            raise HistoryError("git returned a malformed tree entry") from error
        if object_type != b"blob":
            continue
        entries.append((object_id, os.fsdecode(raw_path)))
    if not entries:
        return {}

    output = _git_bytes(root, ["cat-file", "--batch"], b"".join(oid + b"\n" for oid, _ in entries))
    by_id: Dict[bytes, bytes] = {}
    position = 0
    for expected_id, _path in entries:
        line_end = output.find(b"\n", position)
        if line_end < 0:
            raise HistoryError("git returned an incomplete cat-file header")
        header = output[position:line_end].split()
        position = line_end + 1
        if len(header) != 3 or header[1] != b"blob":
            raise HistoryError("git returned a non-blob ticket object")
        try:
            size = int(header[2])
        except ValueError as error:
            raise HistoryError("git returned an invalid blob size") from error
        content = output[position : position + size]
        if len(content) != size or output[position + size : position + size + 1] != b"\n":
            raise HistoryError("git returned incomplete blob content")
        position += size + 1
        by_id[expected_id] = content

    decoded: Dict[str, str] = {}
    for object_id, path in entries:
        try:
            decoded[PurePosixPath(path).as_posix()] = by_id[object_id].decode("utf-8")
        except UnicodeDecodeError as error:
            raise HistoryError(f"committed ticket data is not UTF-8: {path}") from error
    return decoded


def _strings(value: object) -> Tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _unique_object(pairs: Iterable[Tuple[str, object]]) -> Dict[str, object]:
    result: Dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _valid_string_list(value: object) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and bool(item) for item in value
    )


def snapshot_at_commit(root: Path, backlog_path: str, revision: str) -> HistorySnapshot:
    normalized_backlog = PurePosixPath(backlog_path).as_posix().rstrip("/")
    areas_path = f"{normalized_backlog}/areas.json"
    issues_path = f"{normalized_backlog}/issues"
    blobs = _committed_blobs(root, revision, [areas_path, issues_path])
    raw_areas = blobs.get(areas_path)
    if raw_areas is None:
        raise HistoryError(f"{areas_path} is missing at {revision}")
    try:
        area_value = json.loads(raw_areas, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, ValueError) as error:
        detail = error.msg if isinstance(error, json.JSONDecodeError) else str(error)
        raise HistoryError(f"{areas_path} has invalid JSON at {revision}: {detail}") from error
    if not isinstance(area_value, dict):
        raise HistoryError(f"{areas_path} is not an object at {revision}")
    areas: Dict[str, Tuple[str, ...]] = {}
    for name, patterns in area_value.items():
        if not isinstance(name, str) or not isinstance(patterns, list) or not all(
            isinstance(pattern, str) and pattern for pattern in patterns
        ):
            raise HistoryError(f"{areas_path} has an invalid area entry at {revision}")
        areas[name] = tuple(patterns)

    tickets: Dict[str, HistoricalTicket] = {}
    unknown: List[str] = []
    prefix = issues_path + "/"
    for path, body in blobs.items():
        if not path.startswith(prefix):
            continue
        relative_parts = PurePosixPath(path[len(prefix) :]).parts
        filename = relative_parts[-1] if relative_parts else ""
        if len(relative_parts) == 2 and relative_parts[0] in STATES and filename == ".gitkeep":
            continue
        filename_match = ID_FILENAME_RE.match(filename)
        if len(relative_parts) != 2 or relative_parts[0] not in STATES or not filename_match:
            unknown.append(path)
            continue
        metadata_match = META_RE.match(body)
        if not metadata_match:
            unknown.append(path)
            continue
        try:
            metadata = json.loads(
                metadata_match.group("json"), object_pairs_hook=_unique_object
            )
        except (json.JSONDecodeError, ValueError):
            unknown.append(path)
            continue
        ticket_id = metadata.get("id") if isinstance(metadata, dict) else None
        list_fields = ("areas", "depends_on", "related_to", "references")
        closure = metadata.get("closure") if isinstance(metadata, dict) else None
        invalid_closure = closure is not None and (
            not isinstance(closure, dict)
            or (
                closure.get("replacement") is not None
                and not (
                    isinstance(closure.get("replacement"), str)
                    and bool(closure.get("replacement"))
                )
            )
        )
        if (
            not isinstance(metadata, dict)
            or metadata.get("schema_version") != 1
            or not isinstance(ticket_id, str)
            or ticket_id != filename_match.group("id")
            or ticket_id in tickets
            or any(not _valid_string_list(metadata.get(name)) for name in list_fields)
            or invalid_closure
        ):
            unknown.append(path)
            continue
        replacement = closure.get("replacement") if isinstance(closure, dict) else None
        tickets[ticket_id] = HistoricalTicket(
            id=ticket_id,
            path=path,
            areas=_strings(metadata.get("areas")),
            depends_on=_strings(metadata.get("depends_on")),
            related_to=_strings(metadata.get("related_to")),
            references=_strings(metadata.get("references")),
            replacement=replacement if isinstance(replacement, str) and replacement else None,
        )
    return HistorySnapshot(revision, normalized_backlog, areas, tickets, tuple(sorted(unknown)))


def _areas_for_path(path: str, snapshots: Iterable[HistorySnapshot]) -> Set[str]:
    affected: Set[str] = set()
    for snapshot in snapshots:
        names = set(snapshot.areas) - {"*"}
        if path == f"{snapshot.backlog_path}/areas.json":
            affected.update(names)
        for area, patterns in snapshot.areas.items():
            if any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns):
                affected.update(names if area == "*" else {area})
    return affected


def _ticket_id_from_issue_path(path: str, backlog_path: str) -> Optional[str]:
    prefix = f"{backlog_path}/issues/"
    if not path.startswith(prefix):
        return None
    match = ID_FILENAME_RE.match(PurePosixPath(path).name)
    return match.group("id") if match else None


def _is_known_support_path(path: str, backlog_path: str) -> bool:
    prefix = backlog_path + "/"
    if not path.startswith(prefix):
        return False
    relative = path[len(prefix) :]
    return "/" not in relative and relative in KNOWN_BACKLOG_SUPPORT


def select_impact(
    changed_paths: Iterable[str],
    base: HistorySnapshot,
    head: HistorySnapshot,
    extra_areas: Iterable[str] = (),
) -> ImpactSelection:
    """Select candidates from the union of the base and head ticket graphs."""
    snapshots = (base, head)
    all_tickets: Dict[str, List[HistoricalTicket]] = {}
    for snapshot in snapshots:
        for ticket_id, ticket in snapshot.tickets.items():
            all_tickets.setdefault(ticket_id, []).append(ticket)

    selection = ImpactSelection(areas=set(extra_areas))
    selection.unknown_paths.extend(base.unknown_issue_paths)
    selection.unknown_paths.extend(head.unknown_issue_paths)

    def add(ticket_id: str, reason: str) -> None:
        if ticket_id in all_tickets and reason not in selection.reasons.setdefault(ticket_id, []):
            selection.reasons[ticket_id].append(reason)

    changed_ids: Set[str] = set()
    normalized_paths = sorted({PurePosixPath(path).as_posix() for path in changed_paths})
    for path in normalized_paths:
        path_areas = _areas_for_path(path, snapshots)
        selection.areas.update(path_areas)
        matched = bool(path_areas)
        for ticket_versions in all_tickets.values():
            if any(path in ticket.references for ticket in ticket_versions):
                add(ticket_versions[0].id, f"references changed path {path}")
                matched = True
        path_ids = {
            ticket_id
            for snapshot in snapshots
            for ticket_id in [_ticket_id_from_issue_path(path, snapshot.backlog_path)]
            if ticket_id is not None
        }
        for ticket_id in path_ids:
            if ticket_id in all_tickets:
                changed_ids.add(ticket_id)
                matched = True
        if any(_is_known_support_path(path, snapshot.backlog_path) for snapshot in snapshots):
            matched = True
        if not matched:
            selection.unknown_paths.append(path)

    for ticket_versions in all_tickets.values():
        ticket_areas = set().union(*(set(ticket.areas) for ticket in ticket_versions))
        overlap = sorted(ticket_areas & selection.areas)
        if overlap:
            add(ticket_versions[0].id, f"affected area: {', '.join(overlap)}")

    for changed_id in changed_ids:
        add(changed_id, "ticket record changed")
        changed_versions = all_tickets[changed_id]
        old_new_areas = set().union(*(set(ticket.areas) for ticket in changed_versions))
        old_new_references = set().union(*(set(ticket.references) for ticket in changed_versions))
        for candidate_id, candidate_versions in all_tickets.items():
            if candidate_id == changed_id:
                continue
            candidate_areas = set().union(*(set(ticket.areas) for ticket in candidate_versions))
            shared_areas = sorted(old_new_areas & candidate_areas)
            if shared_areas:
                add(candidate_id, f"shares changed ticket area: {', '.join(shared_areas)}")
            candidate_references = set().union(*(set(ticket.references) for ticket in candidate_versions))
            shared_references = sorted(old_new_references & candidate_references)
            if shared_references:
                add(candidate_id, f"shares changed ticket reference {shared_references[0]}")

    adjacency: Dict[str, Set[str]] = {ticket_id: set() for ticket_id in all_tickets}
    for ticket_id, versions in all_tickets.items():
        for ticket in versions:
            for target in ticket.links:
                if target in all_tickets:
                    adjacency[ticket_id].add(target)
                    adjacency[target].add(ticket_id)

    queue = list(selection.reasons)
    visited = set(queue)
    while queue:
        current = queue.pop(0)
        for other in sorted(adjacency.get(current, ())):
            add(other, f"depends on or relates to affected ticket {current}")
            if other not in visited:
                visited.add(other)
                queue.append(other)

    selection.reasons = {
        ticket_id: selection.reasons[ticket_id]
        for ticket_id in sorted(selection.reasons, key=lambda value: (not value.isdigit(), int(value) if value.isdigit() else value))
    }
    selection.unknown_paths = sorted(set(selection.unknown_paths))
    return selection
