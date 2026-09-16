"""Regression checks for malformed records, portable paths, and large graphs."""

import importlib
import json
import os
from pathlib import Path
import unittest

from test_tickets import TicketToolTestCase


class RecordBoundaryTests(TicketToolTestCase):
    def test_non_utf8_record_is_an_actionable_error(self):
        path = self.add_ticket("01")
        path.write_bytes(b"# Invalid encoding\n\xff")
        result = self.command("check")
        self.assert_problem(result, "decode")
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_replacement_cannot_depend_on_the_ticket_it_replaces(self):
        self.add_ticket("01", "BLOCKED", depends_on=["02"])
        self.add_ticket("02", "DONE", closure={"reason": "duplicate", "commit": None,
                        "replacement": "01", "reviewed_by": None, "evidence": ["Same requirement"]})
        self.assert_problem(self.command("check"), "cycle")

    def test_invalid_metadata_types_report_errors_without_tracebacks(self):
        for overrides in ({"areas": [{}]}, {"depends_on": None},
                          {"related_to": [42]}, {"priority": []},
                          {"queue_order": {}}, {"references": [None]}):
            with self.subTest(overrides=overrides):
                self.add_ticket("01", **overrides)
                result = self.command("check")
                self.assert_problem(result)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_duplicate_json_keys_and_empty_review_evidence_are_rejected(self):
        path = self.add_ticket("01")
        path.write_text(path.read_text(encoding="utf-8").replace(
            '"id": "01",', '"id": "01", "id": "02",'), encoding="utf-8")
        self.assert_problem(self.command("check"), "duplicate JSON key")
        path.unlink()
        closure = self.implemented_closure()
        closure["evidence"] = []
        self.add_ticket("01", "DONE", closure=closure)
        self.assert_problem(self.command("check"), "evidence")

    def test_windows_absolute_paths_and_stream_names_are_not_repo_references(self):
        for reference in ("C:/Windows", "C:relative", "src/core.py:stream", "../outside"):
            with self.subTest(reference=reference):
                self.add_ticket("01", references=[reference])
                self.assert_problem(self.command("check"), "reference")

    def test_redirected_source_and_index_are_rejected_without_changing_targets(self):
        path = self.add_ticket("01")
        outside = self.root / "outside.md"
        content = path.read_text(encoding="utf-8")
        outside.write_text(content, encoding="utf-8")
        path.unlink()
        try:
            path.symlink_to(outside)
        except OSError:
            self.skipTest("This account cannot create symlinks")
        self.assert_problem(self.command("check"), "redirected")
        path.unlink()
        path.write_text(content, encoding="utf-8")
        index = self.backlog / "TICKET_STATUS.md"
        index.symlink_to(outside)
        self.assert_problem(self.command("index", "--write"), "redirected")
        self.assertEqual(content, outside.read_text(encoding="utf-8"))

    def test_hardlinked_ticket_cannot_be_replaced(self):
        path = self.add_ticket("01")
        alias = self.root / "alias.md"
        try:
            os.link(path, alias)
        except OSError:
            self.skipTest("Filesystem does not support hardlinks")
        before = alias.read_bytes()
        self.assert_problem(self.command("move", "01", "DONE", "--reason", "cancelled",
                                         "--evidence", "No longer required"), "hard-linked")
        self.assertEqual(before, alias.read_bytes())


class GitPathTests(TicketToolTestCase):
    def test_non_ascii_renames_and_dirty_paths_keep_their_exact_names(self):
        module = importlib.import_module("scripts.tickets")
        old_path = self.root / "src" / "evaluación antigua.py"
        new_path = self.root / "src" / "evaluación nueva.py"
        old_path.write_text("original content\n", encoding="utf-8")
        base = self.commit_fixture()
        old_path.rename(new_path)
        head = self.commit_fixture("rename unicode path")
        changed = module.changed_paths(self.root, base, head)
        self.assertIn(old_path.relative_to(self.root).as_posix(), changed)
        self.assertIn(new_path.relative_to(self.root).as_posix(), changed)
        new_path.write_text("edited content\n", encoding="utf-8")
        self.assertIn(new_path.relative_to(self.root).as_posix(), module.dirty_paths(self.root))


class LargeGraphTests(unittest.TestCase):
    def test_deep_dependency_and_replacement_chains_do_not_use_python_recursion(self):
        module = importlib.import_module("scripts.tickets")
        size = 1200
        edges = {str(i): [str(i + 1)] for i in range(size - 1)}
        edges[str(size - 1)] = []
        self.assertEqual([], module._find_cycles(edges))
        edges[str(size - 1)] = ["0"]
        self.assertEqual(size + 1, len(module._find_cycles(edges)[0]))

        tickets = {}
        for index in range(size):
            ticket_id = str(index)
            closure = {"reason": "duplicate", "replacement": str(index + 1),
                       "reviewed_by": "Reviewer", "evidence": ["Same requirement"], "commit": None}
            if index == size - 1:
                closure.update(reason="implemented", replacement=None, reviewed_by="Reviewer")
            tickets[ticket_id] = module.Ticket(Path(ticket_id), ticket_id, "DONE", ticket_id, "",
                                              {"id": ticket_id, "closure": closure})
        self.assertIsNone(module._effective_blocker("0", tickets))


if __name__ == "__main__":
    unittest.main()
