"""Offline discovery and CLI checks for ticket 12."""

from contextlib import redirect_stdout
import importlib
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_roi.inputs import InputSelectionError, collect_exam_files
from test_exam_identity import directory_link

with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}):
    app = importlib.import_module("pipeline")


class InputSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.course = self.root / "course"
        self.course.mkdir()
        self.cwd = self.root / "shell"
        self.cwd.mkdir()

    def paper(self, name):
        path = self.course / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Synthetic exam question", encoding="utf-8")
        return path

    def select(self, paths=(), recursive=False):
        return collect_exam_files(self.course, paths, recursive, working_dir=self.cwd)

    def test_default_combines_root_and_exams_in_stable_order(self):
        root_b = self.paper("b.PDF")
        root_a = self.paper("a.txt")
        nested = self.paper("exams/c.TXT")
        self.paper("exams/deeper/not_selected.txt")
        self.paper("notes.md")
        self.assertEqual(self.select(), [root_a, root_b, nested])

    def test_default_exams_only_and_root_only(self):
        nested = self.paper("exams/paper.pdf")
        self.assertEqual(self.select(), [nested])
        nested.unlink()
        root = self.paper("paper.txt")
        self.assertEqual(self.select(), [root])

    def test_explicit_files_and_folders_replace_default_and_deduplicate(self):
        self.paper("unrelated.txt")
        first = self.paper("exams/a.pdf")
        second = self.paper("exams/b.txt")
        self.assertEqual(self.select([str(second), "exams", str(first), "exams/../exams/a.pdf"]),
                         [second, first])

    def test_recursive_search_is_opt_in_for_explicit_folders(self):
        paper = self.paper("papers/deep/paper.txt")
        with self.assertRaisesRegex(InputSelectionError, "--recursive"):
            self.select(["papers"])
        self.assertEqual(self.select(["papers"], recursive=True), [paper])

    def test_recursive_default_deduplicates_exams_and_excludes_state(self):
        first = self.paper("exams/deep/paper.txt")
        second = self.paper("other/paper.PDF")
        self.paper("parsed/extracted.txt")
        self.paper("candidates/deep/extracted.pdf")
        self.assertEqual(self.select(recursive=True), [first, second])
        self.assertEqual(self.select([str(self.root)], recursive=True), [first, second])

    def test_explicit_state_files_and_folders_are_rejected(self):
        for state in ("candidates", "parsed"):
            paper = self.paper(f"{state}/paper.txt")
            for path in (paper, paper.parent):
                with self.subTest(path=path), self.assertRaisesRegex(InputSelectionError, "pipeline-managed"):
                    self.select([str(path)])

    def test_directory_aliases_cannot_select_managed_state(self):
        self.paper("candidates/paper.txt")
        alias = self.course / "exams"
        directory_link(alias, self.course / "candidates")
        self.addCleanup(alias.unlink if alias.is_symlink() else alias.rmdir)
        paper = self.paper("real.txt")
        self.assertEqual(self.select(recursive=True), [paper])
        with self.assertRaisesRegex(InputSelectionError, "pipeline-managed"):
            self.select([str(alias)])

    def test_resolved_aliases_are_deduplicated(self):
        paper = self.paper("papers/paper.txt")
        alias = self.course / "alias"
        directory_link(alias, paper.parent)
        self.addCleanup(alias.unlink if alias.is_symlink() else alias.rmdir)
        self.assertEqual(self.select([str(alias / paper.name), str(paper), str(alias)]), [paper])

    def test_recursive_search_does_not_follow_directory_links_or_loops(self):
        paper = self.paper("papers/paper.txt")
        loop = self.course / "papers" / "loop"
        directory_link(loop, self.course)
        self.addCleanup(loop.unlink if loop.is_symlink() else loop.rmdir)
        outside = self.cwd / "outside.txt"
        outside.write_text("Synthetic paper", encoding="utf-8")
        alias = self.course / "alias"
        directory_link(alias, self.cwd)
        self.addCleanup(alias.unlink if alias.is_symlink() else alias.rmdir)
        self.assertEqual(self.select(recursive=True), [paper])
        self.assertEqual(self.select([str(alias)], recursive=True), [outside])

    def test_relative_paths_prefer_shell_then_fall_back_to_course(self):
        course_paper = self.paper("same.txt")
        shell_paper = self.cwd / "same.txt"
        shell_paper.write_text("Different synthetic paper", encoding="utf-8")
        self.assertEqual(self.select(["same.txt"]), [shell_paper])
        self.assertEqual(self.select([str(course_paper)]), [course_paper])
        shell_paper.unlink()
        self.assertEqual(self.select(["same.txt"]), [course_paper])

    def test_empty_missing_and_unsupported_inputs_have_diagnostics(self):
        with self.assertRaisesRegex(InputSelectionError, "No .txt/.pdf"):
            self.select()
        with self.assertRaisesRegex(InputSelectionError, "Looked in"):
            self.select(["missing.txt"])
        self.paper("notes.md")
        with self.assertRaisesRegex(InputSelectionError, "Unsupported paper"):
            self.select(["notes.md"])

    def test_two_course_contexts_do_not_share_selection(self):
        first = self.paper("first.txt")
        second = self.cwd / "second.txt"
        second.write_text("Synthetic question", encoding="utf-8")
        self.assertEqual(collect_exam_files(self.course), [first])
        self.assertEqual(collect_exam_files(self.cwd), [second])
        self.assertEqual(collect_exam_files(self.course), [first])

    def test_cli_lists_every_resolved_path_before_processing(self):
        first = self.paper("first.txt")
        second = self.paper("exams/second.txt")
        app.setup_course_folder(self.course)
        output = StringIO()
        args = SimpleNamespace(paths=[], recursive=False, year=None, exam_id=None,
                               total_marks=None, force=False)

        def process(path, **kwargs):
            self.assertIn(str(first), output.getvalue())
            self.assertIn(str(second), output.getvalue())
            return app.ExamOutcome.SAVED

        with redirect_stdout(output), patch.object(app, "process_exam_file", side_effect=process) as process_mock:
            app.cmd_add_exam(args)
        self.assertEqual([call.args[0] for call in process_mock.call_args_list], [first, second])

    def test_dry_run_cli_from_both_working_directories_creates_no_state(self):
        first = self.paper("first.txt")
        second = self.paper("exams/second.txt")
        repo = Path(__file__).resolve().parents[2]
        for cwd, script in ((repo, "pipeline/pipeline.py"), (repo / "pipeline", "pipeline.py")):
            result = subprocess.run(
                [sys.executable, script, str(self.course), "add-exam", "--dry-run"],
                cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                env={**os.environ, "LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": ""})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(first), result.stdout)
            self.assertIn(str(second), result.stdout)
            self.assertIn("Dry run complete", result.stdout)
        self.assertEqual(set(self.course.iterdir()), {first, second.parent})

    def test_dry_run_never_calls_processing(self):
        self.paper("paper.txt")
        app.setup_course_folder(self.course)
        args = SimpleNamespace(paths=[], recursive=False, year=None, exam_id=None, dry_run=True)
        with redirect_stdout(StringIO()), patch.object(app, "process_exam_file") as process:
            app.cmd_add_exam(args)
        process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
