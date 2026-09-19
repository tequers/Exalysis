"""Offline integration tests for the ticket-ground-truth tooling.

These tests deliberately create small temporary Git repositories.  They do not
read the real backlog or call models, so they are safe to run on every machine.
"""

from __future__ import annotations

import importlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPT = REPOSITORY / "scripts" / "tickets.py"
MIGRATION = REPOSITORY / "scripts" / "migrate_tickets.py"
BACKLOG = "tickets"


def metadata(
    ticket_id: str,
    *,
    priority: str = "P2",
    queue_order: int | None = None,
    areas: list[str] | None = None,
    depends_on: list[str] | None = None,
    related_to: list[str] | None = None,
    references: list[str] | None = None,
    verification: object = None,
    closure: object = None,
) -> dict[str, object]:
    """Return the complete schema so each fixture varies only relevant facts."""
    return {
        "schema_version": 1,
        "id": ticket_id,
        "priority": priority,
        "queue_order": int(ticket_id) if queue_order is None else queue_order,
        "areas": ["core"] if areas is None else areas,
        "depends_on": [] if depends_on is None else depends_on,
        "related_to": [] if related_to is None else related_to,
        "references": ["src/core.py"] if references is None else references,
        "verification": verification,
        "closure": closure,
    }


class TicketToolTestCase(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.backlog = self.root / BACKLOG
        self.issues = self.backlog / "issues"
        for state in ("OPEN", "BLOCKED", "IN_PROGRESS", "TO_REVIEW", "DONE"):
            (self.issues / state).mkdir(parents=True, exist_ok=True)
        (self.root / "src").mkdir()
        (self.root / "src" / "core.py").write_text("initial\n", encoding="utf-8")
        (self.root / "src" / "other.py").write_text("initial\n", encoding="utf-8")
        (self.backlog / "areas.json").write_text(
            json.dumps({"core": ["src/core.py"], "other": ["src/other.py"], "shared": ["shared/**"]}),
            encoding="utf-8",
        )
        self.git("init")
        self.git("config", "user.email", "tickets@example.test")
        self.git("config", "user.name", "Ticket tests")
        self.git("add", ".")
        self.git("commit", "-m", "initial fixture")
        self.initial_commit = self.git("rev-parse", "HEAD").stdout.strip()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def git(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=self.root, text=True, capture_output=True, check=check
        )

    def command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), "--backlog", BACKLOG, *arguments],
            cwd=self.root,
            text=True,
            capture_output=True,
        )

    def add_ticket(
        self,
        ticket_id: str,
        state: str = "OPEN",
        *,
        title: str | None = None,
        body: str = "## Remaining acceptance criteria\n\n- The behaviour still needs work.\n",
        **overrides: object,
    ) -> Path:
        values = metadata(ticket_id)
        values.update(overrides)
        path = self.issues / state / f"{ticket_id}-ticket-{ticket_id}.md"
        content = f"# {title or 'Ticket ' + ticket_id}\n\n```json\n{json.dumps(values, indent=2)}\n```\n\n{body}"
        path.write_text(content, encoding="utf-8")
        return path

    def assert_ok(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(0, result.returncode, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

    def assert_problem(self, result: subprocess.CompletedProcess[str], *fragments: str) -> None:
        self.assertNotEqual(0, result.returncode, "command unexpectedly succeeded")
        text = (result.stdout + result.stderr).lower()
        for fragment in fragments:
            self.assertIn(fragment.lower(), text, result.stdout + result.stderr)

    def commit_fixture(self, message: str = "fixture update") -> str:
        self.git("add", ".")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def implemented_closure(self, commit: str | None = None) -> dict[str, object]:
        return {
            "reason": "implemented",
            "commit": commit or self.initial_commit,
            "replacement": None,
            "reviewed_by": "reviewer@example.test",
            "evidence": ["Reviewed in the fixture."],
        }

    def verified(self, commit: str | None = None, *, criteria: str = "criteria") -> dict[str, object]:
        ticket_module = importlib.import_module("scripts.tickets")
        return {
            "commit": commit or self.initial_commit,
            "checked_at": "2026-09-15",
            "criteria_digest": ticket_module.criteria_digest(criteria),
            "checker": "ticket-test",
            "result": "still_valid",
            "evidence": ["Checked from fixture."],
            "provisional": False,
        }

    def set_verification(self, ticket_id: str, commit: str, criteria: str, state: str = "OPEN") -> Path:
        """Add fixture verification after the ticket itself exists at ``commit``."""
        path = self.issues / state / f"{ticket_id}-ticket-{ticket_id}.md"
        content = path.read_text(encoding="utf-8")
        opening = content.index("```json\n") + len("```json\n")
        closing = content.index("\n```", opening)
        values = json.loads(content[opening:closing])
        values["verification"] = self.verified(commit, criteria=criteria)
        path.write_text(content[:opening] + json.dumps(values, indent=2) + content[closing:], encoding="utf-8")
        return path


class StructureAndIndexTests(TicketToolTestCase):
    def test_check_detects_duplicate_ids_missing_targets_and_cycles(self) -> None:
        self.add_ticket("01")
        duplicate_path = self.issues / "OPEN" / "01-duplicate.md"
        duplicate_path.write_text(
            self.add_ticket("01", title="Duplicate").read_text(encoding="utf-8"), encoding="utf-8"
        )
        duplicate = self.command("check")
        self.assert_problem(duplicate, "01", "duplicate")

        (self.issues / "OPEN" / "01-ticket-01.md").unlink()
        self.add_ticket("02", depends_on=["99"])
        missing = self.command("check")
        self.assert_problem(missing, "02", "99")

        (self.issues / "OPEN" / "02-ticket-02.md").unlink()
        self.add_ticket("02", depends_on=["03"])
        self.add_ticket("03", depends_on=["02"])
        cycle = self.command("check")
        self.assert_problem(cycle, "02", "cycle")

    def test_check_detects_replacement_cycles_and_unreviewed_historical_closure(self) -> None:
        self.add_ticket(
            "01", "DONE", closure={"reason": "duplicate", "commit": None, "replacement": "02", "reviewed_by": None, "evidence": ["same"]}
        )
        self.add_ticket(
            "02", "DONE", closure={"reason": "superseded", "commit": None, "replacement": "01", "reviewed_by": None, "evidence": ["same"]}
        )
        result = self.command("check")
        self.assert_problem(result, "replacement", "cycle")

        (self.issues / "DONE" / "02-ticket-02.md").unlink()
        self.add_ticket(
            "02", "DONE", closure={"reason": "implemented", "commit": self.initial_commit, "replacement": None, "reviewed_by": None, "evidence": ["old"]}
        )
        self.assert_ok(self.command("index", "--write"))
        result = self.command("check")
        self.assert_ok(result)
        self.assertIn("review", (result.stdout + result.stderr).lower())

    def test_index_is_stale_until_written_then_repeatable_and_links_resolve_after_move(self) -> None:
        self.add_ticket("01", "IN_PROGRESS")
        self.add_ticket("02", "BLOCKED", depends_on=["01"])
        stale = self.command("check")
        self.assert_problem(stale, "index")

        self.assert_ok(self.command("index", "--write"))
        before = (self.backlog / "TICKET_STATUS.md").read_text(encoding="utf-8")
        self.assert_ok(self.command("check"))
        self.assert_ok(self.command("index", "--write"))
        self.assertEqual(before, (self.backlog / "TICKET_STATUS.md").read_text(encoding="utf-8"))

        moved = self.command("move", "01", "TO_REVIEW")
        self.assert_ok(moved)
        shown = self.command("show", "01")
        self.assert_ok(shown)
        self.assertIn("01", shown.stdout)
        index = (self.backlog / "TICKET_STATUS.md").read_text(encoding="utf-8")
        self.assertIn("issues/TO_REVIEW/01-ticket-01.md", index.replace("\\", "/"))

    def test_generated_index_uses_authoritative_blockers_and_review_is_not_ready(self) -> None:
        self.add_ticket("01", "TO_REVIEW")
        self.add_ticket("02", "BLOCKED", depends_on=["01"])
        self.add_ticket("03")
        self.assert_ok(self.command("index", "--write"))
        next_result = self.command("next")
        self.assert_ok(next_result)
        self.assertIn("03", next_result.stdout)
        self.assertNotIn("02", next_result.stdout)
        index = (self.backlog / "TICKET_STATUS.md").read_text(encoding="utf-8")
        self.assertIn("01", index)
        self.assertIn("02", index)


class WorkflowAndFreshnessTests(TicketToolTestCase):
    def test_implemented_dependency_and_reviewed_replacement_clear_blockers_but_cancelled_does_not(self) -> None:
        self.add_ticket("01", "DONE", closure=self.implemented_closure())
        self.add_ticket("02", depends_on=["01"])
        self.add_ticket(
            "03", "DONE", closure={"reason": "duplicate", "commit": None, "replacement": "01", "reviewed_by": "reviewer@example.test", "evidence": ["same"]}
        )
        self.add_ticket("04", depends_on=["03"])
        self.add_ticket(
            "05", "DONE", closure={"reason": "cancelled", "commit": None, "replacement": None, "reviewed_by": "reviewer@example.test", "evidence": ["stopped"]}
        )
        self.add_ticket("06", "BLOCKED", depends_on=["05"])
        self.assert_ok(self.command("index", "--write"))
        ready = self.command("next")
        self.assert_ok(ready)
        self.assertIn("02", ready.stdout)
        self.assertIn("04", ready.stdout)
        self.assertNotIn("06", ready.stdout)

    def test_preflight_rejects_missing_commit_changed_criteria_and_dirty_relevant_files(self) -> None:
        criteria = "## Remaining acceptance criteria\n\n- Preserve the remaining condition.\n"
        self.add_ticket("01", body=criteria)
        verification_commit = self.commit_fixture("add verifiable ticket")
        self.set_verification("01", verification_commit, criteria)
        current = self.command("preflight", "01")
        self.assert_ok(current)

        ticket_path = self.issues / "OPEN" / "01-ticket-01.md"
        ticket_path.write_text(ticket_path.read_text(encoding="utf-8").replace("remaining condition", "changed condition"), encoding="utf-8")
        changed_criteria = self.command("preflight", "01")
        self.assert_problem(changed_criteria, "criteria")

        ticket_path.write_text(ticket_path.read_text(encoding="utf-8").replace("changed condition", "remaining condition"), encoding="utf-8")
        (self.root / "src" / "core.py").write_text("dirty relevant change\n", encoding="utf-8")
        dirty = self.command("preflight", "01")
        self.assert_problem(dirty, "dirty")

        values = metadata("02", verification=self.verified("missing"))
        values["verification"] = dict(values["verification"], commit="deadbeef")
        self.add_ticket("02", verification=values["verification"])
        missing = self.command("preflight", "02")
        self.assert_problem(missing, "commit")

    def test_preflight_handles_renames_and_unavailable_history_conservatively(self) -> None:
        self.add_ticket("01", references=[])
        verification_commit = self.commit_fixture("add verifiable ticket")
        self.set_verification("01", verification_commit, "## Remaining acceptance criteria\n\n- The behaviour still needs work.\n")
        self.git("mv", "src/core.py", "src/renamed.py")
        renamed_commit = self.commit_fixture("rename relevant source")
        self.assertNotEqual(self.initial_commit, renamed_commit)
        renamed = self.command("preflight", "01")
        self.assert_problem(renamed, "relevant")

        values = self.verified(commit="f" * 40)
        self.add_ticket("02", verification=values)
        absent = self.command("preflight", "02")
        self.assert_problem(absent, "commit")

    def test_verify_records_provisional_evidence_without_claiming_clean_head_verification(self) -> None:
        self.add_ticket("01")
        result = self.command(
            "verify", "01", "--result", "still_valid", "--checker", "ticket-test", "--evidence", "manual fixture", "--provisional"
        )
        self.assert_ok(result)
        contents = (self.issues / "OPEN" / "01-ticket-01.md").read_text(encoding="utf-8")
        self.assertIn('"provisional": true', contents.lower())
        preflight = self.command("preflight", "01")
        self.assert_problem(preflight, "provisional")

    def test_verifying_with_dirty_changed_criteria_automatically_records_provisional(self) -> None:
        first_criteria = "## Remaining acceptance criteria\n\n- Criterion A.\n"
        self.add_ticket("01", body=first_criteria)
        base = self.commit_fixture("add ticket with criterion A")
        path = self.issues / "OPEN" / "01-ticket-01.md"
        path.write_text(path.read_text(encoding="utf-8").replace("Criterion A", "Criterion B"), encoding="utf-8")
        verified = self.command(
            "verify", "01", "--result", "still_valid", "--checker", "ticket-test", "--evidence", "criterion B checked", "--commit", base,
        )
        self.assert_ok(verified)
        contents = path.read_text(encoding="utf-8")
        self.assertIn('"provisional": true', contents.lower())
        self.assert_problem(self.command("preflight", "01"), "provisional")

    def test_unknown_dirty_code_at_verify_time_stays_provisional_after_the_file_is_removed(self) -> None:
        criteria = "## Remaining acceptance criteria\n\n- Inspect the existing behavior.\n"
        self.add_ticket("01", body=criteria)
        base = self.commit_fixture("add ticket")
        unknown_code = self.root / "scratch_unmapped.py"
        unknown_code.write_text("print('temporary')\n", encoding="utf-8")
        verified = self.command(
            "verify", "01", "--result", "still_valid", "--checker", "ticket-test", "--evidence", "manual check", "--commit", base,
        )
        self.assert_ok(verified)
        unknown_code.unlink()
        contents = (self.issues / "OPEN" / "01-ticket-01.md").read_text(encoding="utf-8")
        self.assertIn('"provisional": true', contents.lower())
        self.assert_problem(self.command("preflight", "01"), "provisional")

    def test_same_state_done_can_record_missing_review_and_committed_verify_does_not_invalidate_itself(self) -> None:
        self.add_ticket(
            "01", "DONE", closure={"reason": "implemented", "commit": self.initial_commit, "replacement": None, "reviewed_by": None, "evidence": ["historical"]}
        )
        historical_review = self.command(
            "move", "01", "DONE", "--reason", "implemented", "--commit", self.initial_commit,
            "--reviewed-by", "reviewer@example.test", "--evidence", "review confirmed",
        )
        self.assert_ok(historical_review)
        self.assertIn('"reviewed_by": "reviewer@example.test"', (self.issues / "DONE" / "01-ticket-01.md").read_text(encoding="utf-8"))

        criteria = "## Remaining acceptance criteria\n\n- Needs verification.\n"
        self.add_ticket("02", body=criteria)
        before_verify = self.commit_fixture("add ticket for verification")
        verified = self.command(
            "verify", "02", "--result", "still_valid", "--checker", "ticket-test", "--evidence", "manual fixture", "--commit", before_verify,
        )
        self.assert_ok(verified)
        self.commit_fixture("record verification")
        preflight = self.command("preflight", "02")
        self.assert_ok(preflight)

    def test_metadata_reference_change_invalidates_verification_even_when_criteria_stay_the_same(self) -> None:
        criteria = "## Remaining acceptance criteria\n\n- The behaviour is still valid.\n"
        self.add_ticket("01", body=criteria)
        verification_commit = self.commit_fixture("add verifiable ticket")
        self.set_verification("01", verification_commit, criteria)
        self.assert_ok(self.command("preflight", "01"))
        ticket = self.issues / "OPEN" / "01-ticket-01.md"
        ticket.write_text(
            ticket.read_text(encoding="utf-8").replace('"src/core.py"', '"src/other.py"'), encoding="utf-8"
        )
        changed_reference = self.command("preflight", "01")
        self.assert_problem(changed_reference, "reference")

    def test_check_remains_structural_without_git_but_preflight_reports_missing_history(self) -> None:
        self.add_ticket("01")
        self.assert_ok(self.command("index", "--write"))
        (self.root / ".git").rename(self.root / "_git_metadata_hidden")
        structural = self.command("check")
        self.assert_ok(structural)
        preflight = self.command("preflight", "01")
        self.assert_problem(preflight, "git")

    def test_normal_completion_unblocks_dependents_and_regenerates_the_index(self) -> None:
        self.add_ticket("01", "TO_REVIEW")
        self.add_ticket("02", "BLOCKED", depends_on=["01"])
        completed = self.command(
            "move", "01", "DONE", "--reason", "implemented", "--commit", self.initial_commit,
            "--reviewed-by", "reviewer@example.test", "--evidence", "review accepted",
        )
        self.assert_ok(completed)
        dependent = self.issues / "OPEN" / "02-ticket-02.md"
        self.assertTrue(dependent.exists(), "normal completion should advance an unblocked dependent to OPEN")
        index = (self.backlog / "TICKET_STATUS.md").read_text(encoding="utf-8")
        self.assertIn("02", index)
        self.assertIn("OPEN", index)

    def test_force_reopen_does_not_bypass_a_stale_preflight(self) -> None:
        self.add_ticket("01", "DONE", closure=self.implemented_closure())
        reopened = self.command("move", "01", "IN_PROGRESS", "--force")
        self.assert_problem(reopened, "preflight")


class ImpactAndSafetyTests(TicketToolTestCase):
    def test_impact_includes_area_reverse_dependencies_ticket_only_changes_and_unknown_paths(self) -> None:
        self.add_ticket("01", areas=["core"])
        self.add_ticket("02", "BLOCKED", areas=["other"], depends_on=["01"])
        self.add_ticket("03", areas=["other"], related_to=["01"])
        base = self.initial_commit
        (self.root / "src" / "core.py").write_text("changed\n", encoding="utf-8")
        head = self.commit_fixture("change core")
        area_impact = self.command("impact", "--base", base, "--head", head)
        self.assert_ok(area_impact)
        self.assertIn("01", area_impact.stdout)
        self.assertIn("02", area_impact.stdout)

        ticket = self.issues / "OPEN" / "01-ticket-01.md"
        ticket.write_text(ticket.read_text(encoding="utf-8") + "\nExtra evidence.\n", encoding="utf-8")
        ticket_head = self.commit_fixture("ticket-only relationship change")
        ticket_impact = self.command("impact", "--base", head, "--head", ticket_head)
        self.assert_ok(ticket_impact)
        self.assertIn("02", ticket_impact.stdout)

        (self.root / "unmapped.txt").write_text("changed\n", encoding="utf-8")
        unknown_head = self.commit_fixture("unmapped change")
        unknown = self.command("impact", "--base", ticket_head, "--head", unknown_head)
        self.assertEqual(1, unknown.returncode, unknown.stdout + unknown.stderr)
        self.assertIn("unmapped", (unknown.stdout + unknown.stderr).lower())

    def test_move_and_verify_reject_malformed_metadata_without_losing_authoritative_content(self) -> None:
        path = self.add_ticket("01")
        original = path.read_text(encoding="utf-8")
        path.write_text(original.replace('"priority": "P2"', '"priority": "P9"'), encoding="utf-8")
        malformed = path.read_text(encoding="utf-8")
        move = self.command("move", "01", "IN_PROGRESS")
        self.assert_problem(move, "priority")
        self.assertEqual(malformed, path.read_text(encoding="utf-8"))

        safe_path = self.add_ticket("02")
        before = safe_path.read_text(encoding="utf-8")
        unsafe = self.command("move", "02", "../DONE")
        self.assert_problem(unsafe, "state")
        self.assertEqual(before, safe_path.read_text(encoding="utf-8"))
        self.assertTrue(safe_path.exists())

    def test_malformed_area_entries_return_a_validation_error_without_a_traceback(self) -> None:
        self.add_ticket("01", areas=[{"not": "an area name"}])
        result = self.command("check")
        self.assert_problem(result, "areas")
        self.assertNotIn("traceback", (result.stdout + result.stderr).lower())

    def test_move_rejects_destination_collision_and_invalid_closure_without_overwriting(self) -> None:
        source = self.add_ticket("01")
        destination = self.issues / "DONE" / source.name
        destination.write_text("keep this unrelated ticket content\n", encoding="utf-8")
        collision = self.command("move", "01", "DONE", "--reason", "implemented")
        self.assert_problem(collision)
        self.assertEqual("keep this unrelated ticket content\n", destination.read_text(encoding="utf-8"))
        self.assertTrue(source.exists())


@unittest.skipUnless(MIGRATION.exists(), "migration command is supplied with the migration implementation")
class MigrationTests(TicketToolTestCase):
    def test_known_backlog_migration_preview_and_repeated_apply_are_idempotent(self) -> None:
        """Exercise the known 21-ticket migrator only in a disposable copy."""
        shutil.rmtree(self.backlog)
        source_backlog = REPOSITORY / BACKLOG
        shutil.copytree(source_backlog, self.backlog)

        # Recreate the legacy source shape from the checked-in records.  This
        # makes the test prove conversion as well as a no-op on current files.
        states = {
            "OPEN": "Open",
            "BLOCKED": "Open",
            "IN_PROGRESS": "In Progress",
            "TO_REVIEW": "Review",
            "DONE": "Done",
        }
        legacy_ids = {f"{number:02d}" for number in range(1, 22)}
        legacy_ticket_count = 0
        total_ticket_count = 0
        references: list[str] = []
        for ticket_file in (self.backlog / "issues").rglob("*.md"):
            source = ticket_file.read_text(encoding="utf-8")
            opening = source.index("```json\n") + len("```json\n")
            closing = source.index("\n```", opening)
            values = json.loads(source[opening:closing])
            total_ticket_count += 1
            references.extend(values["references"])
            if values["id"] not in legacy_ids:
                continue
            title = source.splitlines()[0]
            remainder = source[closing + len("\n```"):].lstrip("\n")
            prerequisite_text = "; ".join(f"{item}: prerequisite" for item in values["depends_on"]) or "none"
            legacy = (
                f"{title}\n\n**Priority:** {values['priority']}\n\n"
                f"**Status:** {states[ticket_file.parent.name]}\n\n"
                f"**Depends on:** {prerequisite_text}\n\n{remainder}"
            )
            ticket_file.write_text(legacy, encoding="utf-8")
            legacy_ticket_count += 1
        self.assertEqual(21, legacy_ticket_count)
        for generated_name in ("areas.json", "TEMPLATE.md", "MIGRATION_REPORT.md"):
            generated = self.backlog / generated_name
            if generated.exists():
                generated.unlink()

        # The real records deliberately refer to project contracts and ADRs.
        # The migrator validates those paths, so provide inert local stand-ins
        # without copying or modifying the actual repository files.
        for reference in references:
            reference_path = Path(reference)
            if reference_path.is_absolute() or ".." in reference_path.parts:
                continue
            stand_in = self.root / reference_path
            stand_in.parent.mkdir(parents=True, exist_ok=True)
            stand_in.touch(exist_ok=True)
        for ticket_file in (self.backlog / "issues").rglob("*.md"):
            source = ticket_file.read_text(encoding="utf-8")
            for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", source):
                target = (ticket_file.parent / link).resolve()
                try:
                    target.relative_to(self.root.resolve())
                except ValueError:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch(exist_ok=True)

        def snapshot() -> dict[str, bytes]:
            return {
                path.relative_to(self.backlog).as_posix(): path.read_bytes()
                for path in self.backlog.rglob("*.md")
            }

        before = snapshot()
        preview = subprocess.run(
            [sys.executable, str(MIGRATION), "--root", str(self.root), "--backlog", BACKLOG, "--preview"],
            cwd=self.root, text=True, capture_output=True,
        )
        self.assertEqual(0, preview.returncode, preview.stdout + preview.stderr)
        self.assertEqual(before, snapshot(), "preview must not change the copied backlog")
        apply = subprocess.run(
            [sys.executable, str(MIGRATION), "--root", str(self.root), "--backlog", BACKLOG, "--apply"],
            cwd=self.root, text=True, capture_output=True,
        )
        self.assertEqual(0, apply.returncode, apply.stdout + apply.stderr)
        after_first_apply = snapshot()
        self.assertNotEqual(before, after_first_apply)
        metadata_count = sum(
            "```json" in ticket_file.read_text(encoding="utf-8")
            for ticket_file in (self.backlog / "issues").rglob("*.md")
        )
        self.assertEqual(total_ticket_count, metadata_count)
        again = subprocess.run(
            [sys.executable, str(MIGRATION), "--root", str(self.root), "--backlog", BACKLOG, "--apply"],
            cwd=self.root, text=True, capture_output=True,
        )
        self.assertEqual(0, again.returncode, again.stdout + again.stderr)
        self.assertEqual(after_first_apply, snapshot())


class PerformanceTests(TicketToolTestCase):
    def test_thousand_ticket_operations_are_offline_and_finish_in_reasonable_time(self) -> None:
        for number in range(1, 1001):
            ticket_id = f"{number:04d}"
            depends_on = [f"{number - 1:04d}"] if number > 1 else []
            state = "BLOCKED" if depends_on else "OPEN"
            self.add_ticket(ticket_id, state, queue_order=number, depends_on=depends_on)
        self.assert_ok(self.command("index", "--write"))
        fixture_commit = self.commit_fixture("add 1000-ticket fixture")
        (self.root / "src" / "core.py").write_text("real impacted source change\n", encoding="utf-8")
        change_commit = self.commit_fixture("change core for impact selection")
        started = time.monotonic()
        indexed = self.command("index", "--write")
        checked = self.command("check")
        impacted = self.command("impact", "--base", fixture_commit, "--head", change_commit)
        elapsed = time.monotonic() - started
        self.assert_ok(indexed)
        self.assert_ok(checked)
        self.assert_ok(impacted)
        print(f"1000-ticket index/check/impact: {elapsed:.2f}s")
        # This is a smoke ceiling, not a benchmark.  It catches quadratic scans
        # and accidental network work while allowing slow developer laptops.
        self.assertLess(elapsed, 30.0, f"1000-ticket commands took {elapsed:.1f}s")


if __name__ == "__main__":
    unittest.main()
