"""Course transactions are tested with actual process death and kernel locks."""

from contextlib import redirect_stdout
from io import StringIO
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PIPELINE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE_DIR))
from exam_roi.storage import CoursePaths, CourseStore, CourseLockError, RecordError, StorageError

app = importlib.import_module("pipeline")


def paper(exam_id="paper", revision="old"):
    return {"exam_id": exam_id, "year": 2026, "total_marks": 10,
            "questions": [], "per_topic": {}, "revision": revision}


OLD_TAXONOMY = {"topics": {"Algebra": {"Diff": 2, "Conn": 1}}}
NEW_TAXONOMY = {"topics": {"Algebra": {"Diff": 4, "Conn": 2}}}
NEW_CANDIDATE = {**paper("pending", "new"), "record_kind": "candidate-analysis",
                 "candidate_status": "validated"}
UPDATES = {"taxonomy": NEW_TAXONOMY, "papers": {"paper": paper(revision="new")},
           "candidates": {"pending": NEW_CANDIDATE}}
BOUNDARIES = [
    "prepare:staged", "prepare:replaced",
    "record:taxonomy.json:staged", "record:taxonomy.json:replaced",
    "record:parsed/paper.json:staged", "record:parsed/paper.json:replaced",
    "record:candidates/pending.json:staged", "record:candidates/pending.json:replaced",
    "commit:staged", "commit:replaced", "cleanup",
]


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = CoursePaths(self.root)
        with CourseStore(self.paths) as store:
            store.commit(taxonomy=OLD_TAXONOMY, papers={"paper": paper()})

    def run_child(self, code, *, course=None):
        prefix = f"import sys; sys.path.insert(0, {str(PIPELINE_DIR)!r})\n"
        prefix += "import os\nfrom pathlib import Path\nfrom exam_roi.storage import CoursePaths, CourseStore\n"
        prefix += f"paths = CoursePaths(Path({str(course or self.root)!r}))\n"
        return subprocess.run([sys.executable, "-c", prefix + code],
                              capture_output=True, text=True, encoding="utf-8", timeout=20)

    def state_bytes(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in [self.paths.taxonomy_file, *self.paths.parsed_dir.glob("*.json"),
                             *self.paths.candidates_dir.glob("*.json")]}

    def interrupt(self, boundary, *, recovery=False):
        code = f"def stop(boundary):\n    if boundary == {boundary!r}: os._exit(73)\n"
        code += "with CourseStore(paths, checkpoint=stop) as store:\n"
        code += "    store.load()\n" if recovery else f"    store.commit(**{UPDATES!r})\n"
        result = self.run_child(code)
        self.assertEqual(result.returncode, 73, result.stdout + result.stderr)

    def test_process_death_at_every_commit_boundary_recovers_all_old_or_all_new(self):
        for boundary in BOUNDARIES:
            with self.subTest(boundary=boundary):
                # A fresh course keeps create and replace cases in every run.
                with tempfile.TemporaryDirectory(dir=self.root) as folder:
                    paths = CoursePaths(Path(folder))
                    with CourseStore(paths) as store:
                        store.commit(taxonomy=OLD_TAXONOMY, papers={"paper": paper()})
                    before = {path: path.read_bytes() for path in
                              [paths.taxonomy_file, paths.parsed_dir / "paper.json"]}
                    code = f"def stop(boundary):\n    if boundary == {boundary!r}: os._exit(73)\n"
                    code += f"with CourseStore(paths, checkpoint=stop) as store:\n    store.commit(**{UPDATES!r})\n"
                    result = self.run_child(code, course=folder)
                    self.assertEqual(result.returncode, 73, result.stdout + result.stderr)
                    with CourseStore(paths) as store:
                        snapshot = store.load()
                        committed = boundary in {"commit:replaced", "cleanup"}
                        self.assertEqual(snapshot.taxonomy, NEW_TAXONOMY if committed else OLD_TAXONOMY)
                        self.assertEqual(snapshot.papers, {"paper": paper(revision="new" if committed else "old")})
                        self.assertEqual(snapshot.candidates, {"pending": NEW_CANDIDATE} if committed else {})
                        if not committed:
                            for path, data in before.items():
                                self.assertEqual(path.read_bytes(), data, "rollback must preserve exact old bytes")
                        self.assertFalse((paths.folder / ".course-transaction.json").exists())
                        store.commit(**UPDATES)
                        self.assertEqual(store.load().papers["paper"]["revision"], "new")

    def test_recovery_itself_can_be_interrupted_and_repeated(self):
        boundaries = ["recovery:taxonomy.json:staged", "recovery:taxonomy.json:replaced",
                      "recovery:parsed/paper.json:staged", "recovery:parsed/paper.json:replaced",
                      "recovery:candidates/pending.json:removed", "recovery:cleaned"]
        before = self.state_bytes()
        for boundary in boundaries:
            with self.subTest(boundary=boundary):
                self.interrupt("commit:staged")
                self.interrupt(boundary, recovery=True)
                with CourseStore(self.paths) as store:
                    self.assertEqual(store.load().taxonomy, OLD_TAXONOMY)
                self.assertEqual(self.state_bytes(), before)

    def test_active_process_blocks_writers_and_reads_then_death_releases_stale_lock(self):
        code = (f"import sys; sys.path.insert(0, {str(PIPELINE_DIR)!r})\n"
                "from pathlib import Path\nfrom exam_roi.storage import CoursePaths, CourseStore\n"
                f"with CourseStore(CoursePaths(Path({str(self.root)!r}))) as store:\n"
                "    print('locked', flush=True)\n    sys.stdin.read()\n")
        child = subprocess.Popen([sys.executable, "-u", "-c", code], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), "locked")
            before = self.state_bytes()
            with self.assertRaises(CourseLockError) as raised:
                with CourseStore(self.paths):
                    self.fail("second writer entered the session")
            self.assertIn(str(child.pid), str(raised.exception))
            self.assertIn("Do not delete .course.lock", str(raised.exception))
            self.assertIn("retry", str(raised.exception))
            result = self.run_child("import pipeline as app\nsys.argv = ['pipeline.py', str(paths.folder), 'rebuild']\nsys.exit(app.main())\n")
            self.assertEqual(result.returncode, app.EXIT_STATE_FAILURE, result.stdout + result.stderr)
            self.assertIn("locked by another command", result.stderr)
            other = self.root / "other-course"
            other.mkdir()
            with CourseStore(CoursePaths(other)) as store:
                store.commit(taxonomy=NEW_TAXONOMY)
            self.assertEqual(self.state_bytes(), before)
        finally:
            child.kill()
            child.communicate(timeout=10)
        # No age heuristic or manual lock deletion is needed after a crash.
        with CourseStore(self.paths) as store:
            store.commit(taxonomy=NEW_TAXONOMY)
            self.assertEqual(store.load().taxonomy, NEW_TAXONOMY)

    def test_unknown_or_malformed_owner_metadata_does_not_create_a_stale_lock(self):
        (self.root / ".course.lock").write_bytes(b"\nold host / invalid JSON / pid 1")
        with CourseStore(self.paths) as store:
            self.assertEqual(store.load().taxonomy, OLD_TAXONOMY)

    def test_same_process_store_instances_cannot_overlap(self):
        with CourseStore(self.paths):
            with self.assertRaises(CourseLockError):
                with CourseStore(self.paths):
                    pass

    def test_corrupt_and_incompatible_saved_records_are_named_and_preserved(self):
        target = self.paths.parsed_dir / "paper.json"
        valid = target.read_bytes()
        bad_records = [b'{', b'\xff', b'[]', b'{"exam_id":"paper","exam_id":"other"}',
                       b'{"exam_id":"paper","per_topic":{},"total_marks":NaN}',
                       b'{"exam_id":"paper","per_topic":{},"total_marks":1e999}',
                       json.dumps({**paper(), "exam_id": "wrong"}).encode(),
                       json.dumps({**paper(), "per_topic": []}).encode(),
                       json.dumps({**paper(), "storage_schema_version": 2}).encode(),
                       json.dumps({**paper(), "storage_schema_version": True}).encode(),
                       json.dumps({**paper(), "evaluation_contract_version": "999.0.0"}).encode(),
                       json.dumps({**paper(), "record_kind": "future-record"}).encode()]
        bad_records += [json.dumps({**paper(), **fields}).encode() for fields in (
            {"record_kind": []}, {"candidate_status": []},
            {"per_topic": {"Algebra": {"marks_total": "ten"}}},
            {"per_topic": {"Algebra": {"format_distribution": []}}},
            {"source_provenance": {"resolved_path": 42}},
            {"evaluation_contract_version": "1.2.0"},
            {"evaluation_contract_version": "1.2.0", "topic_judgments": {"Algebra": "bad"},
             "per_topic": {"Algebra": {}}},
            {"evaluation_contract_version": "1.2.0", "topic_judgments": {},
             "questions": [{"q_id": ["bad"]}]},
        )]
        try:
            for data in bad_records:
                with self.subTest(data=data):
                    target.write_bytes(data)
                    before = self.state_bytes()
                    with CourseStore(self.paths) as store:
                        with self.assertRaises(RecordError) as raised:
                            store.load()
                        self.assertEqual(raised.exception.path, target)
                        with self.assertRaises(RecordError):
                            store.commit(**UPDATES)
                    self.assertEqual(self.state_bytes(), before)
                    self.assertFalse((self.root / ".course-transaction.json").exists())
        finally:
            target.write_bytes(valid)
        with CourseStore(self.paths) as store:
            store.commit(**UPDATES)
            self.assertEqual(store.load().taxonomy, NEW_TAXONOMY)

    def test_corrupt_taxonomy_or_candidate_blocks_force_before_any_model_call(self):
        source = self.root / "paper.txt"
        source.write_text("Use elimination.", encoding="utf-8")
        self.paths.candidates_dir.mkdir()
        candidate = self.paths.candidates_dir / "paper.json"
        for target in (self.paths.taxonomy_file, candidate):
            with self.subTest(target=target):
                original = target.read_bytes() if target.exists() else None
                target.write_bytes(b'{"broken":true}')
                before = self.state_bytes()
                try:
                    with patch.object(app, "stage1_extract") as model:
                        for explicit in (None, "paper"):
                            with self.assertRaises(RecordError) as raised:
                                app.process_exam_file(source, exam_id=explicit, force=True, course=self.paths)
                            self.assertEqual(raised.exception.path, target)
                        model.assert_not_called()
                    self.assertEqual(self.state_bytes(), before)
                finally:
                    if original is None:
                        target.unlink()
                    else:
                        target.write_bytes(original)

    def test_recovery_refuses_unexpected_record_changes_and_corrupt_journal(self):
        self.interrupt("record:parsed/paper.json:replaced")
        journal = self.root / ".course-transaction.json"
        journal_bytes = journal.read_bytes()
        target = self.paths.parsed_dir / "paper.json"
        replaced_bytes = target.read_bytes()
        target.write_bytes(b"externally damaged")
        before = self.state_bytes()
        with self.assertRaisesRegex(RecordError, "both transaction images"):
            with CourseStore(self.paths):
                pass
        self.assertEqual(self.state_bytes(), before)
        self.assertEqual(journal.read_bytes(), journal_bytes)
        target.write_bytes(replaced_bytes)
        journal.write_bytes(b"{")
        with self.assertRaises(RecordError) as raised:
            with CourseStore(self.paths):
                pass
        self.assertEqual(raised.exception.path, journal)
        self.assertEqual(journal.read_bytes(), b"{")
        journal.write_bytes(journal_bytes)
        with CourseStore(self.paths) as store:
            self.assertEqual(store.load().taxonomy, OLD_TAXONOMY)

    def test_failed_commit_cannot_leak_partial_state_in_the_same_session(self):
        def full_disk(boundary):
            if boundary == "record:parsed/paper.json:staged":
                raise OSError("disk full")
        with CourseStore(self.paths, checkpoint=full_disk) as store:
            with self.assertRaisesRegex(StorageError, "not an export failure"):
                store.commit(**UPDATES)
            with self.assertRaisesRegex(StorageError, "reopen"):
                store.load()
            with self.assertRaisesRegex(StorageError, "reopen"):
                store.load_record("parsed", "paper")
            with self.assertRaisesRegex(StorageError, "reopen"):
                store.commit(taxonomy=OLD_TAXONOMY)
        with CourseStore(self.paths) as store:
            self.assertEqual(store.load().taxonomy, OLD_TAXONOMY)

    def test_incompatible_journal_and_bad_image_checksum_block_recovery(self):
        self.interrupt("commit:staged")
        path = self.root / ".course-transaction.json"
        original = path.read_bytes()
        before = self.state_bytes()
        for change in ("version", "phase", "checksum", "target"):
            with self.subTest(change=change):
                journal = json.loads(original)
                if change == "version":
                    journal["version"] = 2
                elif change == "phase":
                    journal["phase"] = []
                elif change == "checksum":
                    journal["entries"]["taxonomy.json"]["before"]["sha256"] = "bad"
                else:
                    journal["entries"][".course.lock"] = journal["entries"]["taxonomy.json"]
                damaged = json.dumps(journal).encode()
                path.write_bytes(damaged)
                with self.assertRaises(RecordError):
                    with CourseStore(self.paths):
                        pass
                self.assertEqual(self.state_bytes(), before)
                self.assertEqual(path.read_bytes(), damaged)
        path.write_bytes(original)
        with CourseStore(self.paths) as store:
            self.assertEqual(store.load().taxonomy, OLD_TAXONOMY)

    def test_cli_commit_io_failure_reports_state_failure_and_recovers(self):
        before = self.state_bytes()
        code = ("from unittest.mock import patch\nimport pipeline as app\n"
                "original = CourseStore._atomic_write\n"
                "def fail(store, relative, data, boundary):\n"
                "    if boundary == 'record:taxonomy.json': raise OSError('disk full')\n"
                "    return original(store, relative, data, boundary)\n"
                "sys.argv = ['pipeline.py', str(paths.folder), 'edit-topic', 'Algebra', '--diff', '5']\n"
                "with patch.object(CourseStore, '_atomic_write', fail):\n    sys.exit(app.main())\n")
        result = self.run_child(code)
        self.assertEqual(result.returncode, app.EXIT_STATE_FAILURE, result.stdout + result.stderr)
        self.assertIn("commit interrupted", result.stderr)
        self.assertNotIn("Set Diff", result.stdout)
        self.assertNotIn("Export failed", result.stdout)
        with CourseStore(self.paths) as store:
            self.assertEqual(store.load().taxonomy, OLD_TAXONOMY)
        self.assertEqual(self.state_bytes(), before)

    def test_state_failure_and_export_failure_have_distinct_cli_exit_codes(self):
        bad = self.paths.parsed_dir / "paper.json"
        original = bad.read_bytes()
        bad.write_bytes(b"{")
        result = self.run_child("import pipeline as app\nsys.argv = ['pipeline.py', str(paths.folder), 'rebuild']\nsys.exit(app.main())\n")
        self.assertEqual(result.returncode, app.EXIT_STATE_FAILURE, result.stdout + result.stderr)
        self.assertIn(str(bad), result.stderr)
        self.assertNotIn("Export failed", result.stdout)
        bad.write_bytes(original)
        before = self.state_bytes()
        output = StringIO()
        with patch.object(app, "write_xlsx", side_effect=OSError("spreadsheet is open")), redirect_stdout(output):
            self.assertEqual(app.cmd_rebuild(None, self.paths), app.EXIT_EXPORT_FAILURE)
        self.assertIn("Export failed", output.getvalue())
        self.assertEqual(self.state_bytes(), before)

    def test_taxonomy_named_paper_and_course_named_parsed_are_unambiguous(self):
        other = self.root / "parsed-course" / "parsed"
        other.mkdir(parents=True)
        with CourseStore(CoursePaths(other)) as store:
            store.commit(taxonomy=OLD_TAXONOMY, papers={"taxonomy": paper("taxonomy")})
            snapshot = store.load()
            self.assertEqual(snapshot.taxonomy, OLD_TAXONOMY)
            self.assertEqual(snapshot.papers["taxonomy"]["exam_id"], "taxonomy")


if __name__ == "__main__":
    unittest.main()
