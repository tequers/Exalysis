"""Inspect declared documentation relationships. See docs/specs/doc-dependencies.md."""

import argparse
import copy
import html
import json
import os
import re
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

from doc_dependency_graph import (
    Snapshot, diagnostic, discover, graph, owner_path, relationship_changes,
    safe_path, select_impact,
)

MARKER = "<!-- doc-dependencies:graph:v1 -->"


class OperationalError(Exception):
    """An input or I/O failure prevents a trustworthy result."""


class Repository:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def git(self, *args, allow_failure=False):
        environment = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
        result = subprocess.run(["git", "-C", str(self.root), *args],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=environment, check=False)
        if result.returncode and not allow_failure:
            raise OperationalError(result.stderr.decode("utf-8", "replace").strip()
                                   or f"Git failed: {args[0]}")
        return result

    def resolve(self, ref):
        return self.git("rev-parse", "--verify", "--end-of-options",
                        ref + "^{commit}").stdout.decode().strip()

    def head(self):
        result = self.git("rev-parse", "--verify", "HEAD", allow_failure=True)
        return result.stdout.decode().strip() if result.returncode == 0 else None

    def inventory(self, revision=None):
        args = ("ls-tree", "-r", "-z", "--full-tree", revision) if revision else ("ls-files", "--stage", "-z")
        records = {}
        for record in self.git(*args).stdout.split(b"\0"):
            if not record:
                continue
            info, raw_path = record.split(b"\t", 1)
            fields = info.decode("ascii").split()
            mode = fields[0]
            if revision:
                oid = fields[2]
            else:
                oid = fields[1]
                if fields[2] != "0":
                    raise OperationalError("Unmerged index entries must be resolved first")
            path = raw_path.decode("utf-8")
            kind = "symlink" if mode == "120000" else "submodule" if mode == "160000" else "regular"
            records[path] = (kind, oid)
        return records

    def disk_kind(self, relative):
        """Check every component before opening a tracked path; do not follow links."""
        path = self.root
        for part in relative.split("/"):
            path = path / part
            try:
                info = path.lstat()
            except FileNotFoundError:
                return None
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                return "symlink"
        return "regular" if stat.S_ISREG(info.st_mode) else "directory"

    def snapshot(self, mode, label="after", revision=None, historical=False):
        records = self.inventory(revision if mode == "commit" else None)
        inventory, raw = {}, {}
        for path, (kind, oid) in records.items():
            if mode == "worktree" and kind != "submodule":
                kind = self.disk_kind(path)
                if kind is None:
                    continue
                # A tracked file replaced by a directory is an unsupported input.
                if kind == "directory":
                    raise OperationalError(f"Tracked path is now a directory: {path}")
            inventory[path] = kind
            if owner_path(path) and kind == "regular" and safe_path(path):
                raw[path] = ((self.root / path).read_bytes() if mode == "worktree"
                             else self.git("cat-file", "blob", oid).stdout)
        return Snapshot(label, inventory, raw, historical)

    def changes(self, mode, base=None, head=None):
        args = ["diff", "--no-ext-diff", "--no-textconv", "--name-status", "-z",
                "--no-renames", "--find-renames=50%", "--ignore-submodules=none"]
        if mode == "staged":
            args += ["--cached", base]
        elif mode != "unstaged":
            args += [base, head]
        args += ["--"]
        fields = self.git(*args).stdout.decode("utf-8").split("\0")
        result, i = [], 0
        while i < len(fields) and fields[i]:
            status, path = fields[i], fields[i + 1]
            i += 2
            code = status[0]
            if code == "R":
                old, new = path, fields[i]
                i += 1
            elif code in ("A", "D", "M", "T"):
                old, new = (None if code == "A" else path), (None if code == "D" else path)
            else:
                raise OperationalError(f"Unsupported Git change status: {status}")
            result.append(dict(status=code, before_path=old, after_path=new))
        return sorted(result, key=lambda r: (r["before_path"] or "", r["after_path"] or "", r["status"]))


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Value must be a positive integer")
    return number


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("check", "build", "impact", "discover"):
        command = commands.add_parser(name)
        command.add_argument("--format", choices=("text", "json"), default="text")
        if name in ("check", "build"):
            snapshots = command.add_mutually_exclusive_group()
            snapshots.add_argument("--ref")
            snapshots.add_argument("--index", action="store_true")
        if name == "check":
            command.add_argument("--against-artifacts")
        if name == "build":
            command.add_argument("--output-dir", default=".scratch/doc-dependencies")
        if name in ("impact", "discover"):
            command.add_argument("--file", action="append", dest="files")
        if name == "impact":
            command.add_argument("--base")
            command.add_argument("--head")
            command.add_argument("--merge-base", action="store_true")
            command.add_argument("--staged", action="store_true")
            command.add_argument("--unstaged", action="store_true")
            command.add_argument("--depth", type=positive, default=1)
            command.add_argument("--limit", type=positive)
    return result


def validate_modes(args, cli):
    if args.command != "impact":
        return
    if bool(args.base) != bool(args.head):
        cli.error("--base and --head must be supplied together")
    modes = [bool(args.files), bool(args.base), args.staged, args.unstaged]
    if sum(modes) != 1 or (args.merge_base and not args.base):
        cli.error("Choose exactly one impact input mode; --merge-base needs --base and --head")


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def load_selection(repo, args):
    metadata = dict(mode=None, requested_base=None, requested_head=None, base_commit=None,
                    head_commit=None, effective_base=None, before_digest=None,
                    after_digest=None, untracked_excluded=False)
    before, changes, seeds = None, [], []
    if args.command == "impact" and not args.files:
        if args.staged:
            mode, base, head = "staged", repo.resolve("HEAD"), None
            before = repo.snapshot("commit", "before", base, historical=True)
            after = repo.snapshot("index")
        elif args.unstaged:
            mode, base, head = "unstaged", None, None
            before = repo.snapshot("index", "before", historical=True)
            after = repo.snapshot("worktree")
        else:
            mode = "merge_base" if args.merge_base else "endpoints"
            base, head = repo.resolve(args.base), repo.resolve(args.head)
            metadata.update(requested_base=args.base, requested_head=args.head)
            effective = base
            if args.merge_base:
                bases = repo.git("merge-base", "--all", base, head).stdout.decode().splitlines()
                if len(bases) != 1:
                    raise OperationalError("The selected refs must have exactly one merge base")
                effective = bases[0]
            before = repo.snapshot("commit", "before", effective, historical=True)
            after = repo.snapshot("commit", revision=head)
            metadata["effective_base"] = effective
        metadata.update(mode=mode, base_commit=base, head_commit=head,
                        untracked_excluded=mode == "unstaged")
        if mode == "staged":
            metadata["effective_base"] = base
        changes = repo.changes(mode, metadata["effective_base"], head)
        seeds = sorted({p for c in changes for p in (c["before_path"], c["after_path"]) if p})
    else:
        ref = getattr(args, "ref", None)
        mode = "commit" if ref else "index" if getattr(args, "index", False) else "worktree"
        head = repo.resolve(ref) if ref else repo.head()
        after = repo.snapshot(mode, revision=head if ref else None)
        metadata.update(mode="files" if args.command == "impact" else mode,
                        requested_head=ref, head_commit=head, untracked_excluded=mode == "worktree")
        if args.command in ("impact", "discover"):
            seeds = sorted(set(args.files or []))
            for path in seeds:
                if not safe_path(path) or after.inventory.get(path) != "regular":
                    raise OperationalError(f"Unknown or unsupported current file: {path}. Use a comparison mode for deletions.")
                if args.command == "discover" and not owner_path(path):
                    raise OperationalError(f"Discovery file is outside owner coverage: {path}")
    metadata.update(before_digest=before.digest if before else None, after_digest=after.digest)
    return before, after, metadata, changes, seeds


def output_directory(repo, supplied):
    path = Path(supplied)
    if path.is_absolute() or not supplied or any(part in ("..", ".git") for part in path.parts):
        raise OperationalError("Artifact directory must be an ignored directory inside the repository")
    relative = path.as_posix().rstrip("/")
    if relative in ("", "."):
        raise OperationalError("Artifact directory cannot be the repository root")
    folder = repo.root / path
    resolved = folder.resolve()
    if not resolved.is_relative_to(repo.root):
        raise OperationalError("Artifact directory escapes the repository")
    current = repo.root
    for part in path.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise OperationalError("Artifact directory cannot contain symlinks or junctions")
            if not stat.S_ISDIR(info.st_mode):
                raise OperationalError("Artifact parent is not a directory")
    tracked = repo.inventory()
    if any(p == relative or p.startswith(relative + "/") for p in tracked):
        raise OperationalError("Artifact directory contains tracked files")
    if repo.git("check-ignore", "--quiet", "--no-index", relative + "/", allow_failure=True).returncode != 0:
        raise OperationalError("Artifact directory must be ignored by Git")
    for name in ("graph.json", "graph.md"):
        item = folder / name
        if item.exists() or item.is_symlink():
            info = item.lstat()
            if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise OperationalError("Artifacts must be regular files")
    return folder


def markdown_bytes(artifact):
    nodes, edges = artifact["data"]["nodes"], artifact["data"]["edges"]
    ids = {n["path"]: f"n{i:04d}" for i, n in enumerate(nodes, 1)}
    def label(value):
        return "".join(f"#{ord(c)};" if c in '\\"[]<>`&#' or ord(c) < 32 else c for c in value)
    def cell(value):
        text = html.escape(str(value).replace("\n", " "), quote=False)
        return re.sub(r"([\\`*_{}\[\]()#+.!|~-])", r"\\\1", text)
    lines = [MARKER, "# Documentation relationships", "", "Generated from declarations. Review associations are undirected; they do not certify semantic consistency.",
             "", "Snapshot:", "", "```json", json_bytes(artifact["snapshot"]).decode().rstrip(), "```", "",
             "```mermaid", "flowchart LR"]
    lines += [f'    {ids[n["path"]]}["{label(n["path"])}"]' for n in nodes]
    lines += [f'    {ids[e["pair"][0]]} --- {ids[e["pair"][1]]}' for e in edges]
    lines += ["```", "", "Legend: nodes are files; lines mean that a change may require reviewing the other file.", "",
              "| Owner | Target | Reason | Review when | Source |", "|---|---|---|---|---|"]
    for edge in edges:
        for row in edge["declarations"]:
            values = [row["owner"], row["target"], row["reason"], row["review_when"], f'{row["owner"]}:{row["line"]}']
            lines.append("| " + " | ".join(cell(v) for v in values) + " |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def expected_artifacts(result, full_graph):
    artifact = copy.deepcopy(result)
    artifact.update(command="build", kind="graph_artifact", data=full_graph)
    return {"graph.json": json_bytes(artifact), "graph.md": markdown_bytes(artifact)}


def validate_artifact_ownership(folder):
    for name in ("graph.json", "graph.md"):
        target = folder / name
        if target.exists():
            try:
                data = target.read_bytes()
                owned = (json.loads(data).get("kind") == "graph_artifact" if name.endswith(".json")
                         else data.startswith(MARKER.encode()))
            except (ValueError, AttributeError):
                owned = False
            if not owned:
                raise OperationalError(f"Refusing to overwrite unrelated file: {target.name}")
def write_artifacts(folder, contents):
    validate_artifact_ownership(folder)
    folder.mkdir(parents=True, exist_ok=True)
    temporary = []
    try:
        for name, content in contents.items():
            with tempfile.NamedTemporaryFile(dir=folder, prefix=".doc-dependencies-", delete=False) as file:
                temporary.append((Path(file.name), folder / name))
                file.write(content)
        for source, target in temporary:
            os.replace(source, target)
    finally:
        for source, _ in temporary:
            if source.exists():
                source.unlink()


def run(repo, args):
    # Invalid destinations are operational errors even when declarations are invalid.
    folder = None
    if args.command == "build":
        folder = output_directory(repo, args.output_dir)
        validate_artifact_ownership(folder)
    elif args.command == "check" and args.against_artifacts:
        folder = output_directory(repo, args.against_artifacts)
    before, after, metadata, changes, seeds = load_selection(repo, args)
    renames = {c["before_path"]: c["after_path"] for c in changes if c["status"] == "R"}
    full_graph = graph(before, after, seeds, renames)
    diagnostics = [d for s in (before, after) if s for d in s.diagnostics]
    data = dict(counts=dict(nodes=len(full_graph["nodes"]), edges=len(full_graph["edges"]), owners=len(after.owners)))
    result = dict(schema_version=1, command=args.command, kind="result", valid=True, complete=True,
                  snapshot=metadata, coverage=dict(before=before.coverage if before else None,
                  after=after.coverage), diagnostics=diagnostics, data=data)
    if args.command == "impact":
        data = select_impact(full_graph, seeds, args.depth, args.limit)
        data.update(changes=changes, relationship_changes=relationship_changes(before, after, renames))
        result["data"] = data
        if data["omitted_count"]:
            diagnostics.append(diagnostic("output_limited", "Requested limit omitted selected nodes",
                                          snapshot=None, severity="warning"))
    elif args.command == "discover":
        candidates, findings = discover(after, seeds or after.owners)
        result["data"] = dict(candidates=candidates)
        diagnostics.extend(findings)
    elif args.command == "check":
        data["artifacts_checked"] = args.against_artifacts
    else:
        data["paths"] = dict(json=(Path(args.output_dir) / "graph.json").as_posix(),
                             markdown=(Path(args.output_dir) / "graph.md").as_posix())
    invalid = any(d["severity"] == "error" for d in diagnostics)
    incomplete = any(d["code"] in ("historical_coverage_gap", "output_limited") for d in diagnostics)
    result.update(valid=not invalid, complete=not (invalid or incomplete))
    if args.command == "check" and args.against_artifacts and result["complete"]:
        expected = expected_artifacts(result, full_graph)
        stale = any(not (folder / name).exists() or (folder / name).read_bytes() != content
                    for name, content in expected.items())
        message = "Saved map files are missing, stale, malformed, or edited"
        if stale:
            diagnostics.append(diagnostic("stale_artifact", message, snapshot="after"))
            result.update(valid=False, complete=False)
    diagnostics.sort(key=lambda d: (d["snapshot"] or "", d["path"] or "", d["line"] or 0, d["code"], d["message"]))
    code = 1 if not result["valid"] else 3 if not result["complete"] else 0
    if args.command == "build" and code == 0:
        write_artifacts(folder, expected_artifacts(result, full_graph))
    return result, code


def text_result(result):
    data = result["data"]
    lines = [f'{result["command"]}: valid={str(result["valid"]).lower()}, complete={str(result["complete"]).lower()}']
    for when, coverage in result["coverage"].items():
        if coverage is not None:
            lines.append(f'{when}: {coverage["declared"]}/{coverage["required"]} owners declare relationships')
    if result["snapshot"]["untracked_excluded"]:
        lines.append("Untracked files were excluded. Stage intended new documents before checking them.")
    if "counts" in data:
        lines.append(f'{data["counts"]["nodes"]} nodes; {data["counts"]["edges"]} relationships')
    if "paths" in data:
        lines += [f"{kind}: {path}" for kind, path in data["paths"].items()]
        lines.append(f'Digest: {result["snapshot"]["after_digest"]}')
    if "seeds" in data:
        lines += [f'Seeds: {", ".join(data["seeds"]) or "none"}',
                  f'Depth {data["depth"]}; {data["returned_count"]}/{data["eligible_count"]} selected nodes; '
                  f'{data["omitted_count"]} nodes and {data["omitted_edge_count"]} edges omitted; outside depth={data["outside_depth"]}']
        lines += [f'- {n["path"]}' for n in data["nodes"]]
        for edge in data["edges"]:
            for row in edge["declarations"]:
                lines.append(f'{row["snapshot"]} {row["owner"]}:{row["line"]} -> {row["target"]}: '
                             f'{row["reason"]} Review when: {row["review_when"]}')
        for change in data["relationship_changes"]:
            lines.append(f'Relationship {", ".join(change["kinds"])}: {change["pair_before"]} -> {change["pair_after"]}')
    for candidate in data.get("candidates", []):
        lines.append(f'Suggestion: {candidate["owner"]} -> {candidate["target"]}')
        lines += [f'  line {e["line"]} ({e["kind"]}): {e["text"]}' for e in candidate["evidence"]]
    lines += [f'{d["severity"].upper()} {d["code"]} {d["snapshot"] or ""} '
              f'{d["path"] or ""}:{d["line"] or ""}: {d["message"]}' for d in result["diagnostics"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    cli = parser()
    args = cli.parse_args(argv)
    validate_modes(args, cli)
    try:
        location = Repository(Path.cwd()).git("rev-parse", "--show-toplevel").stdout.decode("utf-8").strip()
        result, code = run(Repository(location), args)
        output = json_bytes(result).decode("utf-8") if args.format == "json" else text_result(result)
        sys.stdout.write(output)
        return code
    except (OperationalError, OSError, UnicodeError) as exc:
        print(f"doc_dependencies: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
