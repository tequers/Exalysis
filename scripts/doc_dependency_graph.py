"""Parse documentation declarations and compute review associations offline."""

from collections import defaultdict, deque
from dataclasses import dataclass, field
import hashlib
import json
import posixpath
import re
from urllib.parse import unquote, urlsplit

START = "<!-- doc-dependencies:start -->"
END = "<!-- doc-dependencies:end -->"


def owner_path(path):
    return path == "README.md" or (
        path.startswith("docs/") and path.endswith(".md")
        and not path.startswith("docs/adr/SUPPRESSED/")
    )


def safe_path(path):
    return bool(path) and not (
        path.startswith("/") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", path)
        or any(c in path for c in "\\`|#?*[]")
        or any(ord(c) < 32 or ord(c) == 127 for c in path)
        or any(part in ("", ".", "..") for part in path.split("/"))
    )


def diagnostic(code, message, snapshot="after", path=None, line=None,
               severity="error", review_required=True):
    return dict(code=code, severity=severity, snapshot=snapshot, path=path,
                line=line, message=message, review_required=review_required)


def prose_lines(text):
    """Yield original line numbers outside CommonMark backtick/tilde fences."""
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if (match and match[1][0] == fence[0] and len(match[1]) >= fence[1]
                    and not match[2].strip()):
                fence = None
            continue
        if match and (match[1][0] == "~" or "`" not in match[2]):
            fence = (match[1][0], len(match[1]))
            continue
        yield number, line


def table_cells(line):
    cells, cell, escaped = [], [], False
    for char in line.strip():
        if escaped:
            if char not in "\\|":
                raise ValueError("Only escaped pipes and backslashes are allowed")
            cell.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(cell).strip())
            cell = []
        else:
            cell.append(char)
    if escaped:
        raise ValueError("Unfinished backslash escape")
    cells.append("".join(cell).strip())
    if cells and not cells[0]:
        cells.pop(0)
    if cells and not cells[-1]:
        cells.pop()
    if len(cells) != 3:
        raise ValueError("Expected exactly three table cells")
    return cells


@dataclass
class Snapshot:
    label: str
    inventory: dict
    raw: dict
    historical: bool = False
    owners: list = field(default_factory=list)
    texts: dict = field(default_factory=dict)
    edges: dict = field(default_factory=dict)
    diagnostics: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    declared: int = 0
    digest: str = ""

    def __post_init__(self):
        self.owners = sorted(p for p in self.inventory if owner_path(p))
        declarations = defaultdict(list)
        for path in self.owners:
            if self.inventory[path] != "regular" or not safe_path(path):
                self.error("invalid_owner", "Owner must be a safe regular file", path)
                continue
            content = self.raw[path]
            try:
                text = content.decode("utf-8-sig")
            except UnicodeDecodeError:
                self.error("invalid_encoding", "Owner is not valid UTF-8", path)
                continue
            self.texts[path] = text
            rows = self.parse(path, text)
            for row in rows:
                declarations[tuple(sorted((path, row["target"])))].append(row)
        for pair, rows in declarations.items():
            if len(rows) > 1:
                locations = ", ".join(f"{r['owner']}:{r['line']}" for r in rows)
                for row in rows:
                    self.error("duplicate_pair", f"Duplicate relationship at {locations}",
                               row["owner"], row["line"])
            else:
                self.edges[pair] = rows[0]
        payload = dict(scope_version=1, schema_version=1,
                       inventory=[dict(path=p, type=t) for p, t in sorted(self.inventory.items())],
                       owners=[dict(path=p, sha256=hashlib.sha256(b).hexdigest())
                               for p, b in sorted(self.raw.items())])
        self.digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
            ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()

    def error(self, code, message, path, line=None):
        self.diagnostics.append(diagnostic(code, message, self.label, path, line))

    @property
    def coverage(self):
        return dict(required=len(self.owners), declared=self.declared, missing=self.missing)

    def parse(self, path, text):
        lines = list(prose_lines(text))
        starts = [i for i, (_, line) in enumerate(lines) if line.rstrip() == START]
        ends = [i for i, (_, line) in enumerate(lines) if line.rstrip() == END]
        malformed = [(n, line) for n, line in lines
                     if (START in line or END in line) and line.rstrip() not in (START, END)]
        if malformed:
            self.error("invalid_table", "Markers must occupy their own column-one lines",
                       path, malformed[0][0])
            return []
        if not starts and not ends:
            self.missing.append(path)
            self.diagnostics.append(diagnostic(
                "historical_coverage_gap" if self.historical else "missing_block",
                "No dependency block; relationships are unknown", self.label, path,
                severity="warning" if self.historical else "error"))
            return []
        if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
            at = min(starts + ends) if starts or ends else 0
            self.error("invalid_table", "Expected one ordered start/end marker pair",
                       path, lines[at][0])
            return []
        self.declared += 1
        # Fence content is ignored for examples outside blocks, never inside a real block.
        begin, finish = lines[starts[0]][0], lines[ends[0]][0]
        body = [(n, line) for n, line in enumerate(text.splitlines(), 1)
                if begin < n < finish and line.strip()]
        try:
            if len(body) < 2 or table_cells(body[0][1]) != ["File", "Reason", "Review when"]:
                raise ValueError("Expected File | Reason | Review when header")
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in table_cells(body[1][1])):
                raise ValueError("Invalid table separator")
        except ValueError as exc:
            self.error("invalid_table", str(exc), path, body[0][0] if body else begin)
            return []
        rows = []
        for line_number, line in body[2:]:
            try:
                target, reason, review = table_cells(line)
                if not re.fullmatch(r"`[^`]+`", target):
                    raise ValueError("File must be a single backtick-wrapped repository path")
                target = target[1:-1]
                if not reason or not review or re.search(r"<(?:br|table)\b", reason + review, re.I):
                    raise ValueError("Reason and Review when must be nonempty single-line plain text")
            except ValueError as exc:
                self.error("invalid_table", str(exc), path, line_number)
                continue
            if not safe_path(target) or target.startswith("tickets/"):
                self.error("invalid_target", "Unsupported or unsafe target path", path, line_number)
            elif target == path:
                self.error("self_relation", "A document cannot depend on itself", path, line_number)
            elif target not in self.inventory:
                self.error("missing_target", f"Target does not exist with exact case: {target}", path, line_number)
            elif self.inventory[target] != "regular":
                self.error("invalid_target", f"Target is not a regular file: {target}", path, line_number)
            else:
                rows.append(dict(snapshot=self.label, owner=path, target=target,
                                 reason=reason, review_when=review, line=line_number,
                                 owner_sha256=hashlib.sha256(self.raw[path]).hexdigest()))
        return rows


def graph(before, after, seeds=(), renames=None):
    renames = renames or {}
    reverse = {new: old for old, new in renames.items()}
    paths, pairs, owners = set(seeds), defaultdict(list), set()
    for snap in (before, after):
        if snap is None:
            continue
        paths.update(snap.owners)
        owners.update(snap.owners)
        for pair, declaration in snap.edges.items():
            paths.update(pair)
            pairs[pair].append(declaration)
    nodes = [dict(path=p, kind="document" if p in owners else "file",
                  present_in=[s.label for s in (before, after) if s and p in s.inventory],
                  renamed_from=reverse.get(p), renamed_to=renames.get(p))
             for p in sorted(paths)]
    edges = [dict(pair=list(pair), declarations=sorted(rows, key=lambda r: (r["snapshot"], r["owner"])))
             for pair, rows in sorted(pairs.items())]
    return dict(nodes=nodes, edges=edges)


def relationship_changes(before, after, renames):
    if before is None:
        return []
    changes, used = [], set()
    for pair, old in sorted(before.edges.items()):
        mapped = tuple(sorted(renames.get(p, p) for p in pair))
        new = after.edges.get(mapped)
        if new is None:
            changes.append(dict(pair_before=list(pair), pair_after=None, kinds=["removed"]))
            continue
        used.add(mapped)
        kinds = []
        if pair != mapped:
            kinds.append("renamed")
        if renames.get(old["owner"], old["owner"]) != new["owner"]:
            kinds.append("owner_changed")
        for key in ("reason", "review_when"):
            if old[key] != new[key]:
                kinds.append(key + "_changed")
        if kinds:
            changes.append(dict(pair_before=list(pair), pair_after=list(mapped), kinds=sorted(kinds)))
    for pair in sorted(after.edges.keys() - used):
        changes.append(dict(pair_before=None, pair_after=list(pair), kinds=["added"]))
    return sorted(changes, key=lambda r: (r["pair_before"] or [], r["pair_after"] or []))


def select_impact(full_graph, seeds, depth, limit=None):
    adjacency = defaultdict(list)
    for edge in full_graph["edges"]:
        a, b = edge["pair"]
        adjacency[a].append((b, 1))
        adjacency[b].append((a, 1))
    for node in full_graph["nodes"]:
        for key in ("renamed_from", "renamed_to"):
            if node[key]:
                adjacency[node["path"]].append((node[key], 0))
    distance = {p: 0 for p in seeds}
    queue = deque(sorted(seeds))
    while queue:
        path = queue.popleft()
        for target, weight in adjacency[path]:
            candidate = distance[path] + weight
            if candidate < distance.get(target, float("inf")):
                distance[target] = candidate
                (queue.appendleft if weight == 0 else queue.append)(target)
    eligible = sorted((p for p, d in distance.items() if d <= depth), key=lambda p: (distance[p], p))
    selected = set(eligible if limit is None else eligible[:limit])
    edges = [e for e in full_graph["edges"] if set(e["pair"]) <= selected]
    eligible_edges = [e for e in full_graph["edges"] if set(e["pair"]) <= set(eligible)]
    return dict(nodes=[n for n in full_graph["nodes"] if n["path"] in selected], edges=edges,
                seeds=sorted(set(seeds)), depth=depth,
                outside_depth=any(d > depth for d in distance.values()),
                eligible_count=len(eligible), returned_count=len(selected),
                omitted_count=len(eligible) - len(selected),
                omitted_edge_count=len(eligible_edges) - len(edges))


def discover(snapshot, selected):
    candidates, diagnostics = defaultdict(list), []
    for owner in selected:
        lines, inside = [], False
        for number, line in prose_lines(snapshot.texts.get(owner, "")):
            if line.rstrip() == START:
                inside = True
            elif line.rstrip() == END:
                inside = False
            elif not inside:
                lines.append((number, line))
        definitions = defaultdict(set)
        definition_lines = set()
        for number, line in lines:
            match = re.match(r" {0,3}\[([^\]]+)\]:\s*(<[^>]*>|\S+)", line)
            if match:
                definitions[" ".join(match[1].casefold().split())].add(match[2].strip("<>"))
                definition_lines.add(number)

        def observe(target, number, kind, literal):
            if kind == "path_mention":
                path = target
            else:
                try:
                    url = urlsplit(target)
                except ValueError:
                    url = None
                if url and (url.scheme or url.netloc):
                    return
                if not target or target.startswith("#"):
                    return
                raw_path = unquote(target.split("#", 1)[0])
                path = posixpath.normpath(posixpath.join(posixpath.dirname(owner), raw_path))
            if path in (owner, ".") or path.startswith("tickets/"):
                return
            if not safe_path(path):
                code = "discovery_ambiguous_reference"
            elif path not in snapshot.inventory:
                if any(p.startswith(path.rstrip("/") + "/") for p in snapshot.inventory):
                    return
                code = "discovery_missing_target"
            elif snapshot.inventory[path] != "regular":
                code = "discovery_ambiguous_reference"
            else:
                if tuple(sorted((owner, path))) not in snapshot.edges:
                    evidence = dict(line=number, kind=kind, text=literal)
                    if evidence not in candidates[(owner, path)]:
                        candidates[(owner, path)].append(evidence)
                return
            diagnostics.append(diagnostic(code, f"Unresolved reference: {literal}", "after",
                                          owner, number, "warning"))

        for number, line in lines:
            if number in definition_lines:
                continue
            for match in re.finditer(r"(`+)(.+?)\1(?!`)", line):
                value = match[2]
                if value in snapshot.inventory or (safe_path(value) and ("/" in value or re.search(r"\.\w+$", value))):
                    observe(value, number, "path_mention", match[0])
            masked = re.sub(r"(`+)(.+?)\1(?!`)", lambda m: " " * len(m[0]), line)
            inline = re.compile(r"!?\[([^\]\n]*)\]\((<[^>\n]*>|(?:\\.|[^()\n]|\([^()\n]*\))*)\)")
            spans = []
            for match in inline.finditer(masked):
                destination = match[2].strip()
                if destination.startswith("<"):
                    destination = destination[1:destination.find(">")]
                else:
                    destination = re.split(r'\s+[\"\']', destination, maxsplit=1)[0]
                observe(destination, number, "inline_link", line[match.start():match.end()])
                spans.append((match.start(), match.end()))
            for match in re.finditer(r"!?\[([^\]\n]+)\](?:\[([^\]\n]*)\])?", masked):
                if any(a <= match.start() < b for a, b in spans):
                    continue
                label = match[2] if match[2] else match[1]
                targets = definitions.get(" ".join(label.casefold().split()), set())
                if len(targets) == 1:
                    observe(next(iter(targets)), number, "reference_link", line[match.start():match.end()])
                elif len(targets) > 1 or match[2] is not None:
                    diagnostics.append(diagnostic("discovery_ambiguous_reference",
                        f"Unresolved reference: {match[0]}", "after", owner, number, "warning"))
    return [dict(owner=o, target=t, evidence=sorted(e, key=lambda x: (x["line"], x["kind"], x["text"])))
            for (o, t), e in sorted(candidates.items())], diagnostics
