"""Pure contracts for documentation declarations, review graphs, and discovery."""

import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from doc_dependency_graph import Snapshot, discover, graph, owner_path, relationship_changes, select_impact

HEADER = "<!-- doc-dependencies:start -->\n| File | Reason | Review when |\n|---|---|---|\n"
END = "<!-- doc-dependencies:end -->\n"


def block(*rows):
    return HEADER + "".join(f"| `{p}` | {r} | {w} |\n" for p, r, w in rows) + END


def snapshot(files, historical=False, types=None, label="after"):
    inventory = {p: "regular" for p in files}
    inventory.update(types or {})
    raw = {p: text.encode("utf-8") if isinstance(text, str) else text
           for p, text in files.items() if owner_path(p) and inventory[p] == "regular"}
    return Snapshot(label, inventory, raw, historical)


class ParserTests(unittest.TestCase):
    def test_reverse_lookup_cycles_and_isolated_seed(self):
        s = snapshot({"README.md": block(("docs/a.md", "Shares a rule", "Rule changes")),
                      "docs/a.md": block(("docs/b.md", "Uses contract", "Contract changes")),
                      "docs/b.md": block(("README.md", "Checks summary", "Summary changes")),
                      "code.py": ""})
        self.assertEqual([], s.diagnostics)
        result = select_impact(graph(None, s, ["docs/a.md"]), ["docs/a.md"], 1)
        self.assertEqual(["README.md", "docs/a.md", "docs/b.md"], [n["path"] for n in result["nodes"]])
        isolated = select_impact(graph(None, s, ["code.py"]), ["code.py"], 2)
        self.assertEqual(["code.py"], [n["path"] for n in isolated["nodes"]])

    def test_empty_missing_and_historical_blocks(self):
        s = snapshot({"README.md": block(), "docs/a.md": "# No block", "AGENTS.md": "no block",
                      "docs/adr/SUPPRESSED/a.md": "no block", "tickets/x.md": "no block"})
        self.assertEqual(dict(required=2, declared=1, missing=["docs/a.md"]), s.coverage)
        old = snapshot({"README.md": "legacy"}, historical=True, label="before")
        self.assertEqual("historical_coverage_gap", old.diagnostics[0]["code"])
        self.assertEqual("warning", old.diagnostics[0]["severity"])

    def test_fenced_examples_are_not_declarations(self):
        for fence in ("```markdown", "~~~~markdown", "   ```markdown"):
            with self.subTest(fence=fence):
                closing = fence.strip().replace("markdown", "")
                text = fence + "\n" + block() + closing + "\n" + block()
                self.assertEqual([], snapshot({"README.md": text}).diagnostics)
        self.assertEqual("missing_block", snapshot({"README.md": "```\n" + block() + "```"}).diagnostics[0]["code"])

    def test_escaped_cells_unicode_bom_and_locations(self):
        text = "# Guide\n\n" + block(("code café.py", r"Uses x\|y and a\\b", "Behavior changes"))
        s = snapshot({"README.md": b"\xef\xbb\xbf" + text.encode(), "code café.py": ""})
        self.assertEqual([], s.diagnostics)
        row = next(iter(s.edges.values()))
        self.assertEqual("Uses x|y and a\\b", row["reason"])
        self.assertEqual(6, row["line"])
        self.assertEqual(hashlib.sha256(s.raw["README.md"]).hexdigest(), row["owner_sha256"])

    def test_bad_grammar_and_encoding(self):
        malformed = [block() + block(), END + HEADER, HEADER, END,
                     block().replace("<!-- doc-dependencies:start -->", " <!-- doc-dependencies:start -->"),
                     block().replace("Reason", "Why"), block().replace("---", "--"),
                     block(("code.py", "", "change")), block(("code.py", r"Bad\n", "change")),
                     block(("code.py", "<br>break", "change")), HEADER + "```\n```\n" + END]
        for text in malformed:
            with self.subTest(text=text):
                self.assertTrue(snapshot({"README.md": text, "code.py": ""}).diagnostics)
        self.assertEqual("invalid_encoding", snapshot({"README.md": b"\xff"}).diagnostics[0]["code"])

    def test_unsafe_missing_and_special_targets(self):
        for target in ("../x.py", "./x.py", "/x.py", "C:/x.py", "a//x.py", "a\\x.py",
                       "x.py#part", "x.py?query", "*.py", "Code.py", "missing.py", "tickets/x.md", "folder", "README.md"):
            with self.subTest(target=target):
                s = snapshot({"README.md": block((target, "reason", "trigger")), "code.py": "", "folder/a.py": ""})
                self.assertTrue(s.diagnostics)
                self.assertFalse(s.edges)
        for kind in ("symlink", "submodule"):
            s = snapshot({"README.md": block(("target", "reason", "trigger"))}, types={"target": kind})
            self.assertEqual("invalid_target", s.diagnostics[0]["code"])

    def test_duplicate_pairs_report_both_owners_without_choosing_one(self):
        s = snapshot({"README.md": block(("docs/a.md", "one", "change")),
                      "docs/a.md": block(("README.md", "two", "change"))})
        self.assertEqual(2, len(s.diagnostics))
        self.assertTrue(all(d["code"] == "duplicate_pair" for d in s.diagnostics))
        self.assertEqual({}, s.edges)

    def test_limits_and_depth_do_not_hide_coverage_diagnostics(self):
        s = snapshot({"README.md": block(("docs/a.md", "one", "change")),
                      "docs/a.md": block(("docs/b.md", "two", "change")), "docs/b.md": block()})
        full = graph(None, s, ["README.md"])
        shallow = select_impact(full, ["README.md"], 1)
        self.assertTrue(shallow["outside_depth"])
        self.assertEqual(0, shallow["omitted_count"])
        limited = select_impact(full, ["README.md"], 2, 1)
        self.assertEqual(2, limited["omitted_count"])
        self.assertEqual(2, limited["omitted_edge_count"])

    def test_discovery_observation_sources_and_evidence(self):
        a = block() + '[Code](../code.py) and `code.py`.\n[again][c]\n[c]: ../code.py\n[other](b.md)\n'
        b = block() + '[reverse](a.md)\n[missing](../missing.py)\n[bad][unknown]\n'
        s = snapshot({"README.md": block(), "docs/a.md": a, "docs/b.md": b, "code.py": ""})
        candidates, diagnostics = discover(s, ["docs/a.md", "docs/b.md"])
        by_pair = {(c["owner"], c["target"]): c for c in candidates}
        self.assertEqual(3, len(by_pair[("docs/a.md", "code.py")]["evidence"]))
        self.assertIn(("docs/a.md", "docs/b.md"), by_pair)
        self.assertIn(("docs/b.md", "docs/a.md"), by_pair)
        self.assertEqual({"discovery_missing_target", "discovery_ambiguous_reference"}, {d["code"] for d in diagnostics})

    def test_rename_alias_has_zero_hop_cost(self):
        old = snapshot({"docs/a.md": block(("old.py", "reason", "trigger")),
                        "old.py": ""}, label="before")
        new = snapshot({"docs/a.md": block(("new.py", "reason", "trigger")),
                        "new.py": ""})
        full = graph(old, new, ["old.py", "new.py"], {"old.py": "new.py"})
        result = select_impact(full, ["old.py"], 1)
        self.assertEqual({"old.py", "new.py", "docs/a.md"}, {n["path"] for n in result["nodes"]})
        self.assertFalse(result["outside_depth"])

    def test_deleted_edge_and_changed_reason_keep_before_after(self):
        old = snapshot({"README.md": block(("code.py", "old reason", "old trigger")), "code.py": ""}, label="before")
        new = snapshot({"README.md": block(("code.py", "new reason", "new trigger")), "code.py": ""})
        delta = relationship_changes(old, new, {})
        self.assertEqual(["reason_changed", "review_when_changed"], delta[0]["kinds"])
        self.assertEqual({"old reason", "new reason"}, {d["reason"] for d in graph(old, new)["edges"][0]["declarations"]})
        empty = snapshot({"README.md": block(), "code.py": ""})
        self.assertEqual(["removed"], relationship_changes(old, empty, {})[0]["kinds"])

    def test_digest_uses_literal_unicode_and_raw_owner_bytes(self):
        raw = block().encode("utf-8")
        snap = snapshot({"README.md": raw, "café.py": "code"})
        payload = dict(scope_version=1, schema_version=1,
                       inventory=[dict(path="README.md", type="regular"), dict(path="café.py", type="regular")],
                       owners=[dict(path="README.md", sha256=hashlib.sha256(raw).hexdigest())])
        expected = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(expected, snap.digest)
        self.assertEqual(snap.digest, snapshot({"README.md": raw, "café.py": "different code"}).digest)
        self.assertNotEqual(snap.digest, snapshot({"README.md": raw + b"\n", "café.py": "code"}).digest)

    def test_discovery_excludes_declared_external_ticket_fence_and_self(self):
        text = block(("code.py", "reason", "trigger")) + '\n'.join([
            '[code](code.py)', '[ticket](tickets/x.md)', '[web](https://example.invalid/a)',
            '[self](#here)', '[root](./)', '```', '[hidden](hidden.py)', '```', '[dir](docs/)',
        ])
        s = snapshot({"README.md": text, "code.py": "", "docs/a.md": block()})
        self.assertEqual(([], []), discover(s, ["README.md"]))



if __name__ == "__main__":
    unittest.main()
