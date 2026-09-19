"""Offline contracts for documentation dependency parsing, history, and artifacts."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import doc_dependencies as cli
from test_doc_dependency_graph import HEADER, block

class GitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="doc-deps-")
        self.addCleanup(self.temp.cleanup)
        parent = Path(self.temp.name)
        config = parent / "empty.gitconfig"
        config.write_text("", encoding="utf-8")
        self.environment = patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": str(config), "GIT_CONFIG_NOSYSTEM": "1"})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.root = parent / "repo"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "Documentation tests")
        self.git("config", "core.autocrlf", "false")
        self.write(".gitignore", ".scratch/\n")
        self.write("README.md", block())
        self.write("docs/a.md", block(("code.py", "Explains code", "Code changes")))
        self.write("docs/b.md", block())
        self.write("code.py", "value = 1\n")
        self.commit("baseline")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.repo = cli.Repository(self.root)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.PIPE).decode("utf-8")

    def write(self, path, text):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")

    def commit(self, message):
        self.git("add", "--all")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD").strip()

    def run_tool(self, *arguments):
        args = cli.parser().parse_args(arguments)
        cli.validate_modes(args, cli.parser())
        return cli.run(self.repo, args)

    def test_check_and_reverse_query_contract(self):
        result, code = self.run_tool("check")
        self.assertEqual(0, code)
        self.assertEqual({"schema_version", "command", "kind", "valid", "complete", "snapshot", "coverage", "diagnostics", "data"}, set(result))
        self.assertTrue(result["snapshot"]["untracked_excluded"])
        result, code = self.run_tool("impact", "--file", "code.py")
        self.assertEqual(0, code)
        self.assertEqual(["code.py", "docs/a.md"], [n["path"] for n in result["data"]["nodes"]])
        self.assertEqual("Explains code", result["data"]["edges"][0]["declarations"][0]["reason"])

    def test_staged_unstaged_committed_and_untracked_are_separate(self):
        self.write("docs/a.md", block(("code.py", "Staged reason", "Code changes")))
        self.git("add", "docs/a.md")
        self.write("docs/a.md", block(("code.py", "Disk reason", "Code changes")))
        self.write("docs/untracked.md", "no declaration")
        staged, code = self.run_tool("impact", "--staged")
        self.assertEqual(0, code)
        reasons = {r["reason"] for r in staged["data"]["edges"][0]["declarations"]}
        self.assertEqual({"Explains code", "Staged reason"}, reasons)
        unstaged, code = self.run_tool("impact", "--unstaged")
        self.assertEqual({"Staged reason", "Disk reason"}, {r["reason"] for r in unstaged["data"]["edges"][0]["declarations"]})
        committed, code = self.run_tool("impact", "--base", self.base, "--head", self.base)
        self.assertEqual([], committed["data"]["seeds"])
        self.assertEqual(3, unstaged["coverage"]["after"]["required"])
        self.git("add", "docs/untracked.md")
        self.assertEqual(1, self.run_tool("check")[1])

    def test_removed_owner_and_removed_edge_keep_old_impact(self):
        (self.root / "docs/a.md").unlink()
        head = self.commit("remove owner")
        result, code = self.run_tool("impact", "--base", self.base, "--head", head)
        self.assertEqual(0, code)
        self.assertIn("code.py", result["data"]["seeds"] + [n["path"] for n in result["data"]["nodes"]])
        self.assertEqual(["removed"], result["data"]["relationship_changes"][0]["kinds"])
        self.assertEqual("before", result["data"]["edges"][0]["declarations"][0]["snapshot"])

    def test_rename_aliases_preserve_relationship(self):
        self.git("mv", "code.py", "renamed.py")
        self.write("docs/a.md", block(("renamed.py", "Explains code", "Code changes")))
        head = self.commit("rename target")
        result, code = self.run_tool("impact", "--base", self.base, "--head", head)
        self.assertEqual(0, code)
        self.assertEqual(["renamed"], result["data"]["relationship_changes"][0]["kinds"])
        by_path = {n["path"]: n for n in result["data"]["nodes"]}
        self.assertEqual("renamed.py", by_path["code.py"]["renamed_to"])
        self.assertEqual("code.py", by_path["renamed.py"]["renamed_from"])

    def test_owner_move_is_not_add_remove(self):
        self.write("README.md", block(("docs/a.md", "same", "same")))
        self.write("docs/a.md", block())
        before = self.commit("first owner")
        self.write("README.md", block())
        self.write("docs/a.md", block(("README.md", "same", "same")))
        after = self.commit("move ownership")
        result, code = self.run_tool("impact", "--base", before, "--head", after)
        self.assertEqual(["owner_changed"], result["data"]["relationship_changes"][0]["kinds"])

    def test_historical_coverage_and_malformed_history(self):
        self.write("README.md", "legacy")
        old = self.commit("no block")
        self.write("README.md", block())
        head = self.commit("add block")
        result, code = self.run_tool("impact", "--base", old, "--head", head)
        self.assertEqual(3, code)
        self.assertTrue(result["valid"])
        self.assertFalse(result["complete"])
        self.assertEqual(0, self.run_tool("check")[1])
        self.write("README.md", HEADER)
        malformed = self.commit("malformed")
        self.assertEqual(1, self.run_tool("impact", "--base", malformed, "--head", head)[1])

    def test_merge_base_is_explicit_and_uses_ancestor_graph(self):
        self.git("checkout", "-qb", "side")
        self.write("docs/a.md", block())
        side = self.commit("remove on side")
        self.git("checkout", "-qb", "other", self.base)
        self.write("code.py", "value = 2\n")
        head = self.commit("code on head")
        endpoints, _ = self.run_tool("impact", "--base", side, "--head", head)
        merged, _ = self.run_tool("impact", "--base", side, "--head", head, "--merge-base")
        self.assertEqual(["added"], endpoints["data"]["relationship_changes"][0]["kinds"])
        self.assertEqual([], merged["data"]["relationship_changes"])
        self.assertEqual(self.base, merged["snapshot"]["effective_base"])
        self.assertEqual(side, merged["snapshot"]["base_commit"])

    def test_limit_exit_and_discovery_warning_exit(self):
        result, code = self.run_tool("impact", "--file", "code.py", "--limit", "1")
        self.assertEqual(3, code)
        self.assertEqual(1, result["data"]["omitted_count"])
        self.write("README.md", block() + "[missing](missing.py)\n")
        result, code = self.run_tool("discover", "--file", "README.md")
        self.assertEqual(0, code)
        self.assertEqual([], result["data"]["candidates"])
        self.assertEqual("warning", result["diagnostics"][0]["severity"])
        self.write("docs/b.md", "missing block")
        self.assertEqual(1, self.run_tool("discover", "--file", "README.md")[1])

    def test_build_determinism_and_freshness(self):
        result, code = self.run_tool("build")
        self.assertEqual(0, code)
        folder = self.root / ".scratch/doc-dependencies"
        first = {p.name: p.read_bytes() for p in folder.iterdir()}
        self.assertEqual(0, self.run_tool("build")[1])
        self.assertEqual(first, {p.name: p.read_bytes() for p in folder.iterdir()})
        self.assertEqual(0, self.run_tool("check", "--against-artifacts", ".scratch/doc-dependencies")[1])
        self.assertEqual("graph_artifact", json.loads(first["graph.json"])["kind"])
        self.assertIn(b"flowchart LR", first["graph.md"])
        self.write("code.py", "content only\n")
        self.assertEqual(0, self.run_tool("check", "--against-artifacts", ".scratch/doc-dependencies")[1])
        self.write("README.md", block() + "New prose\n")
        self.assertEqual(1, self.run_tool("check", "--against-artifacts", ".scratch/doc-dependencies")[1])
        self.run_tool("build")
        (folder / "graph.md").write_text("edited")
        self.assertEqual(1, self.run_tool("check", "--against-artifacts", ".scratch/doc-dependencies")[1])
        with self.assertRaises(cli.OperationalError):
            self.run_tool("build")

    def test_validation_failure_does_not_overwrite_artifacts(self):
        self.run_tool("build")
        path = self.root / ".scratch/doc-dependencies/graph.json"
        previous = path.read_bytes()
        self.write("README.md", "missing")
        self.assertEqual(1, self.run_tool("build")[1])
        self.assertEqual(previous, path.read_bytes())

    def test_interrupted_pair_is_detected_and_temporary_files_cleaned(self):
        self.run_tool("build")
        self.write("README.md", block() + "Changed prose\n")
        replace = os.replace
        count = 0
        def fail_second(source, target):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("simulated interruption")
            return replace(source, target)
        with patch.object(cli.os, "replace", side_effect=fail_second):
            with self.assertRaises(OSError):
                self.run_tool("build")
        self.assertEqual(1, self.run_tool("check", "--against-artifacts", ".scratch/doc-dependencies")[1])
        folder = self.root / ".scratch/doc-dependencies"
        self.assertEqual({"graph.json", "graph.md"}, {p.name for p in folder.iterdir()})

    def test_output_paths_reject_escape_tracked_and_unignored_directories(self):
        for directory in ("../outside", "docs", ".git/objects", "new-output", str(self.root.parent)):
            with self.subTest(directory=directory):
                with self.assertRaises(cli.OperationalError):
                    self.run_tool("build", "--output-dir", directory)

    def test_symlink_owner_is_not_read(self):
        raw = self.repo.disk_kind
        with patch.object(self.repo, "disk_kind", side_effect=lambda p: "symlink" if p == "README.md" else raw(p)):
            result, code = self.run_tool("check")
        self.assertEqual(1, code)
        self.assertIn("invalid_owner", [d["code"] for d in result["diagnostics"]])

    def test_real_symlink_output_is_rejected(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        link = self.root / ".scratch"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symlink creation unavailable: {exc}")
        with self.assertRaises(cli.OperationalError):
            self.run_tool("build")
        self.assertEqual([], list(outside.iterdir()))

    def test_missing_paths_unknown_refs_and_unmerged_index_fail(self):
        (self.root / "code.py").unlink()
        with self.assertRaises(cli.OperationalError):
            self.run_tool("impact", "--file", "code.py")
        with self.assertRaises(cli.OperationalError):
            self.run_tool("check", "--ref", "missing-reference")
        oid = self.git("rev-parse", "HEAD:README.md").strip()
        data = f"0 {'0' * len(oid)}\tREADME.md\n100644 {oid} 1\tREADME.md\n100644 {oid} 2\tREADME.md\n"
        subprocess.run(["git", "-C", str(self.root), "update-index", "--index-info"], input=data.encode(), check=True)
        with self.assertRaises(cli.OperationalError):
            self.run_tool("check")
        # An explicit committed snapshot does not inspect pending index conflicts.
        self.assertEqual(0, self.run_tool("check", "--ref", self.base)[1])

    def test_limited_result_keeps_errors_and_old_schema_is_stale(self):
        self.write("docs/b.md", "no block")
        result, code = self.run_tool("impact", "--file", "code.py", "--limit", "1")
        self.assertEqual(1, code)
        self.assertEqual(["docs/b.md"], result["coverage"]["after"]["missing"])
        self.assertEqual({"missing_block", "output_limited"}, {d["code"] for d in result["diagnostics"]})
        self.write("docs/b.md", block())
        self.run_tool("build")
        target = self.root / ".scratch/doc-dependencies/graph.json"
        data = json.loads(target.read_bytes())
        data["schema_version"] = 0
        target.write_bytes(cli.json_bytes(data))
        self.assertEqual(1, self.run_tool("check", "--against-artifacts", ".scratch/doc-dependencies")[1])

    def test_invalid_artifact_argument_outranks_invalid_graph(self):
        self.write("README.md", "missing block")
        for command, option in (("check", "--against-artifacts"), ("build", "--output-dir")):
            with self.subTest(command=command):
                with self.assertRaises(cli.OperationalError):
                    self.run_tool(command, option, "../outside")

    def test_unrelated_map_file_is_rejected_before_invalid_declarations(self):
        self.write("README.md", "missing block")
        self.write(".scratch/doc-dependencies/graph.md", "unrelated document")
        with self.assertRaises(cli.OperationalError):
            self.run_tool("build")

    def test_generated_markdown_displays_declaration_text_literally(self):
        self.write("docs/a.md", block(("code.py", "[label](https://example.invalid) *word* <img src=x>", "A & B")))
        result, code = self.run_tool("build")
        self.assertEqual(0, code)
        folder = self.root / ".scratch/doc-dependencies"
        markdown = (folder / "graph.md").read_text(encoding="utf-8")
        self.assertIn(r"\[label\]\(https://example\.invalid\)", markdown)
        self.assertIn("&lt;img src=x&gt;", markdown)
        self.assertIn("A &amp; B", markdown)
        self.assertNotIn("<img", markdown)
        data = json.loads((folder / "graph.json").read_bytes())
        self.assertIn("[label](https://example.invalid)", data["data"]["edges"][0]["declarations"][0]["reason"])
        unusual = json.loads(json.dumps(data).replace("code.py", "code<&>.py"))
        rendered = cli.markdown_bytes(unusual).decode("utf-8")
        self.assertIn("code&lt;&amp;&gt;", rendered)
        self.assertNotIn("code<&>", rendered)

    def test_unreadable_owner_is_operational_not_missing_coverage(self):
        original = Path.read_bytes
        def unreadable(path):
            if path == self.root / "README.md":
                raise PermissionError("simulated unreadable owner")
            return original(path)
        with patch.object(Path, "read_bytes", unreadable):
            with self.assertRaises(PermissionError):
                self.run_tool("check")

    def test_inventory_changes_and_missing_map_invalidate_artifacts(self):
        self.run_tool("build")
        self.write("added.py", "")
        self.git("add", "added.py")
        self.assertEqual(1, self.run_tool("check", "--against-artifacts", ".scratch/doc-dependencies")[1])
        self.run_tool("build")
        path = self.root / ".scratch/doc-dependencies/graph.md"
        path.unlink()
        self.assertEqual(1, self.run_tool("check", "--against-artifacts", ".scratch/doc-dependencies")[1])

    def test_deleted_and_unrelated_added_file_is_not_a_rename(self):
        (self.root / "code.py").unlink()
        self.write("other.py", "completely unrelated content\n" * 50)
        self.write("docs/a.md", block(("other.py", "new", "new")))
        after = self.commit("delete and add")
        result, code = self.run_tool("impact", "--base", self.base, "--head", after)
        self.assertEqual(0, code)
        self.assertNotIn("R", {c["status"] for c in result["data"]["changes"]})
        self.assertEqual({"added", "removed"}, {c["kinds"][0] for c in result["data"]["relationship_changes"]})

    def test_owner_rename_and_multiple_merge_bases(self):
        self.git("mv", "docs/a.md", "docs/renamed.md")
        after = self.commit("rename owner")
        result, code = self.run_tool("impact", "--base", self.base, "--head", after)
        self.assertEqual(0, code)
        self.assertEqual(["renamed"], result["data"]["relationship_changes"][0]["kinds"])
        original = self.repo.git
        def git(*args, **kwargs):
            if args[:2] == ("merge-base", "--all"):
                return subprocess.CompletedProcess(args, 0, f"{self.base}\n{after}\n".encode(), b"")
            return original(*args, **kwargs)
        with patch.object(self.repo, "git", side_effect=git):
            with self.assertRaises(cli.OperationalError):
                self.run_tool("impact", "--base", self.base, "--head", after, "--merge-base")

    def test_cli_json_from_subdirectory_and_usage_errors(self):
        script = Path(cli.__file__).resolve()
        result = subprocess.run([sys.executable, str(script), "impact", "--file", "code.py", "--format", "json"],
                                cwd=self.root / "docs", capture_output=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("impact", json.loads(result.stdout)["command"])
        self.assertTrue(result.stdout.endswith(b"\n"))
        for args in (("impact",), ("impact", "--base", "HEAD"),
                     ("impact", "--file", "code.py", "--staged"),
                     ("impact", "--file", "code.py", "--depth", "0")):
            result = subprocess.run([sys.executable, str(script), *args], cwd=self.root, capture_output=True)
            self.assertEqual(2, result.returncode)
            self.assertEqual(b"", result.stdout)


if __name__ == "__main__":
    unittest.main()
