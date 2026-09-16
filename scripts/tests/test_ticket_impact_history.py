import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ticket_history import HistorySnapshot, HistoricalTicket, select_impact, snapshot_at_commit


def historical(ticket_id, areas=(), depends_on=(), related_to=(), references=(), replacement=None):
    return HistoricalTicket(
        ticket_id,
        f".scratch/reliable-exam-analysis/issues/OPEN/{ticket_id}-ticket.md",
        tuple(areas),
        tuple(depends_on),
        tuple(related_to),
        tuple(references),
        replacement,
    )


def snapshot(revision, tickets, areas=None):
    return HistorySnapshot(
        revision,
        ".scratch/reliable-exam-analysis",
        areas or {"core": ("src/**",)},
        {ticket.id: ticket for ticket in tickets},
    )


class ImpactHistorySelectionTests(unittest.TestCase):
    def test_removed_relationship_uses_base_and_head_union(self):
        base = snapshot("base", [historical("01", related_to=("02",)), historical("02")])
        head = snapshot("head", [historical("01"), historical("02")])

        result = select_impact(
            [".scratch/reliable-exam-analysis/issues/OPEN/01-ticket.md"], base, head
        )

        self.assertIn("01", result.reasons)
        self.assertIn("02", result.reasons)

    def test_changed_ticket_old_and_new_areas_select_siblings(self):
        base = snapshot(
            "base",
            [historical("01", areas=("old",)), historical("02", areas=("old",))],
            {"old": ("old/**",), "new": ("new/**",)},
        )
        head = snapshot(
            "head",
            [historical("01", areas=("new",)), historical("02", areas=("old",)), historical("03", areas=("new",))],
            {"old": ("old/**",), "new": ("new/**",)},
        )

        result = select_impact(
            [".scratch/reliable-exam-analysis/issues/OPEN/01-ticket.md"], base, head
        )

        self.assertEqual({"01", "02", "03"}, set(result.reasons))

    def test_unknown_backlog_file_warns_but_known_support_file_does_not(self):
        base = snapshot("base", [historical("01")])
        head = snapshot("head", [historical("01")])

        result = select_impact(
            [
                ".scratch/reliable-exam-analysis/issues/OPEN/notes.md",
                ".scratch/reliable-exam-analysis/TICKET_STATUS.md",
            ],
            base,
            head,
        )

        self.assertEqual(
            [".scratch/reliable-exam-analysis/issues/OPEN/notes.md"], result.unknown_paths
        )


class CommitSnapshotTests(unittest.TestCase):
    def test_snapshot_reads_requested_commit_instead_of_working_tree(self):
        with tempfile.TemporaryDirectory(prefix="ticket-history-") as directory:
            root = Path(directory)
            backlog = root / ".scratch" / "reliable-exam-analysis"
            issue = backlog / "issues" / "OPEN"
            issue.mkdir(parents=True)
            (backlog / "areas.json").write_text(
                json.dumps({"core": ["src/**"]}), encoding="utf-8"
            )
            ticket = issue / "01-ticket.md"
            ticket.write_text(self.ticket_body(["02"]), encoding="utf-8")
            self.git(root, "init", "-q")
            self.git(root, "config", "user.email", "history@example.invalid")
            self.git(root, "config", "user.name", "History test")
            self.git(root, "add", ".")
            self.git(root, "commit", "-qm", "with relation")
            requested = self.git(root, "rev-parse", "HEAD")
            ticket.write_text(self.ticket_body([]), encoding="utf-8")
            self.git(root, "add", ".")
            self.git(root, "commit", "-qm", "without relation")

            result = snapshot_at_commit(
                root, ".scratch/reliable-exam-analysis", requested
            )

            self.assertEqual(("02",), result.tickets["01"].related_to)

    def test_invalid_historical_ticket_is_reported_even_when_its_path_area_matches(self):
        with tempfile.TemporaryDirectory(prefix="ticket-history-invalid-") as directory:
            root = Path(directory)
            backlog = root / ".scratch" / "reliable-exam-analysis"
            issue = backlog / "issues" / "OPEN"
            issue.mkdir(parents=True)
            (backlog / "areas.json").write_text(
                json.dumps({"core": [".scratch/reliable-exam-analysis/issues/**"]}),
                encoding="utf-8",
            )
            (issue / ".gitkeep").write_text("", encoding="utf-8")
            bad_path = issue / "01-bad.md"
            bad_path.write_text(
                "# 01: Bad\n\n```json\n"
                '{"schema_version": 1, "id": "01", "areas": [], "areas": ["core"], '
                '"depends_on": [], "related_to": [], "references": [], "closure": null}'
                "\n```\n",
                encoding="utf-8",
            )
            self.git(root, "init", "-q")
            self.git(root, "config", "user.email", "history@example.invalid")
            self.git(root, "config", "user.name", "History test")
            self.git(root, "add", ".")
            self.git(root, "commit", "-qm", "invalid historical ticket")
            revision = self.git(root, "rev-parse", "HEAD")

            history = snapshot_at_commit(
                root, ".scratch/reliable-exam-analysis", revision
            )
            result = select_impact([history.unknown_issue_paths[0]], history, history)

            self.assertEqual(
                (".scratch/reliable-exam-analysis/issues/OPEN/01-bad.md",),
                history.unknown_issue_paths,
            )
            self.assertEqual(list(history.unknown_issue_paths), result.unknown_paths)

    @staticmethod
    def ticket_body(related_to):
        metadata = {
            "schema_version": 1,
            "id": "01",
            "priority": "P1",
            "queue_order": 1,
            "areas": ["core"],
            "depends_on": [],
            "related_to": related_to,
            "references": [],
            "verification": None,
            "closure": None,
        }
        return f"# 01: Ticket\n\n```json\n{json.dumps(metadata, indent=2)}\n```\n\n- [ ] Criterion\n"

    @staticmethod
    def git(root, *args):
        result = subprocess.run(
            ["git", *args], cwd=root, text=True, capture_output=True, check=True
        )
        return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
