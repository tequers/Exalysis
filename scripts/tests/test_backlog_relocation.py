"""Backlog relocation must preserve committed history without borrowing other boards."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

from test_tickets import SCRIPT, TicketToolTestCase

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from ticket_history import HistoryError, snapshot_at_commit
import tickets


LEGACY_BACKLOG = ".scratch/reliable-exam-analysis"


class BacklogRelocationTests(TicketToolTestCase):
    def default_command(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *arguments],
            cwd=self.root, text=True, capture_output=True,
        )

    def make_legacy_base(self):
        self.add_ticket("01", areas=[], references=[], related_to=["02"])
        self.add_ticket("02", areas=[], references=[])
        legacy = self.root / LEGACY_BACKLOG
        legacy.parent.mkdir(parents=True, exist_ok=True)
        self.backlog.rename(legacy)
        base = self.commit_fixture("legacy backlog with relationship")
        legacy.rename(self.backlog)
        return base

    def test_default_cli_compares_old_base_and_new_head_with_removed_ticket(self):
        base = self.make_legacy_base()
        (self.issues / "OPEN" / "02-ticket-02.md").unlink()
        self.add_ticket("01", areas=[], references=[], related_to=[])
        head = self.commit_fixture("relocate and remove historical relationship")

        old = snapshot_at_commit(self.root, "tickets", base)
        new = snapshot_at_commit(self.root, "tickets", head)
        self.assertEqual(LEGACY_BACKLOG, old.backlog_path)
        self.assertEqual(("02",), old.tickets["01"].related_to)
        self.assertEqual("tickets", new.backlog_path)
        self.assertNotIn("02", new.tickets)
        result = self.default_command("impact", "--base", base, "--head", head)
        self.assert_ok(result)
        self.assertIn("- 02:", result.stdout)
        self.assertIn("depends on or relates to affected ticket 01", result.stdout)
        self.assertNotIn("unmapped-path", result.stdout)
        self.assert_ok(self.default_command("show", "01"))

    def test_historical_verification_reads_body_and_metadata_before_move(self):
        base = self.make_legacy_base()
        self.commit_fixture("relocate backlog")
        board = tickets.load_backlog(self.root, "tickets")
        ticket = board.by_id["01"]
        metadata = tickets._ticket_metadata_at_commit(board, ticket, base)
        body = tickets._ticket_body_at_commit(board, ticket, base)
        self.assertEqual(["02"], metadata["related_to"])
        self.assertIn('"02"', body)

    def test_existing_malformed_current_backlog_never_uses_valid_legacy(self):
        self.add_ticket("01")
        legacy = self.root / LEGACY_BACKLOG
        legacy.parent.mkdir(parents=True, exist_ok=True)
        self.backlog.rename(legacy)
        self.backlog.mkdir()
        (self.backlog / "issues").mkdir()
        (self.backlog / "issues" / "notes.md").write_text("malformed", encoding="utf-8")
        for area_text in (None, "invalid JSON"):
            with self.subTest(area_text=area_text):
                if area_text is not None:
                    (self.backlog / "areas.json").write_text(area_text, encoding="utf-8")
                revision = self.commit_fixture("malformed current backlog")
                with self.assertRaisesRegex(HistoryError, "tickets/areas.json"):
                    snapshot_at_commit(self.root, "tickets", revision)

    def test_custom_backlog_is_read_explicitly_and_never_falls_back(self):
        self.add_ticket("01")
        custom = self.root / "planning" / "board"
        (custom / "issues" / "OPEN").mkdir(parents=True)
        (custom / "areas.json").write_text(json.dumps({"core": ["src/**"]}), encoding="utf-8")
        source = self.issues / "OPEN" / "01-ticket-01.md"
        (custom / "issues" / "OPEN" / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        base = self.commit_fixture("custom and default boards")
        (self.root / "src" / "core.py").write_text("changed\n", encoding="utf-8")
        head = self.commit_fixture("change custom board area")
        result = self.default_command("--backlog", "planning/board", "impact", "--base", base, "--head", head)
        self.assert_ok(result)
        self.assertIn("- 01:", result.stdout)
        self.assertEqual("planning/board", snapshot_at_commit(self.root, "planning/board", base).backlog_path)
        with self.assertRaisesRegex(HistoryError, "missing-board/areas.json is missing"):
            snapshot_at_commit(self.root, "missing-board", base)


if __name__ == "__main__":
    unittest.main()
