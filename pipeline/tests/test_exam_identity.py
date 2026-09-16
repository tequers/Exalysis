"""Offline path-boundary and collision checks for ticket 10."""

from contextlib import ExitStack
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_roi.identity import ExamIdentityError, exam_record_path, validate_exam_id

with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}):
    app = importlib.import_module("pipeline")


BAD_IDS = [None, 123, '', ' ', '.', '..', '../outside', '..\\outside',
           '/absolute', 'C:\\absolute', 'C:relative', '\\\\server\\share',
           '\\\\?\\C:\\absolute', 'folder/name', 'folder\\name', 'name:stream',
           'name*', 'name?', 'name<', 'name>', 'name|', 'name"', 'name\x00', 'name\n',
           'trailing.', 'trailing ', ' leading', 'CON', 'con.txt', 'NUL', 'nul.json',
           'PRN', 'AUX', 'COM1', 'LPT9', 'COM¹.txt', 'LPT²', 'CONIN$', 'CONOUT$.txt',
           'CON .txt', 'a' * 251, 'é' * 126, '\ud800']


def directory_link(link, target):
    """Use a Windows junction when creating symlinks requires privileges."""
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        if os.name != 'nt':
            raise
        result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)],
                                capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)


class IdValidationTests(unittest.TestCase):
    def test_rejects_paths_reserved_names_and_invalid_filename_components(self):
        for value in BAD_IDS:
            with self.subTest(value=repr(value)), self.assertRaisesRegex(ExamIdentityError, 'Choose a plain ID'):
                validate_exam_id(value)

    def test_preserves_valid_custom_identifiers(self):
        for value in ['exam_2026_A', 'Historia-España.ordinaria', 'My exam 2026',
                      'COM10', 'CONTEXT', 'prn_result', '.hidden', 'a' * 250]:
            with self.subTest(value=value):
                self.assertEqual(validate_exam_id(value), value)

    def test_module_import_does_not_configure_cli_or_need_credentials(self):
        env = {**os.environ, 'LLM_PROVIDER': 'invalid',
               'PYTHONPATH': str(Path(__file__).resolve().parents[1])}
        result = subprocess.run([sys.executable, '-c',
            'import sys; before=sys.stdout; import exam_roi.identity; assert sys.stdout is before'],
            env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')


class StateBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.course = self.root / 'course'
        self.course.mkdir()
        self.outside = self.root / 'outside'
        self.outside.mkdir()
        self.context = app.setup_course_folder(self.course)
        self.paper = self.course / 'paper_2026.txt'
        self.paper.write_text('Use elimination.', encoding='utf-8')

    def fake_analysis(self, during_extraction=None):
        stack = ExitStack()
        q = {'q_id': 'Q1', 'text': 'Use elimination.', 'marks': 10, 'format': 'short_answer'}
        extractor = stack.enter_context(patch.object(app, 'stage1_extract', return_value=([q], 2026)))
        if during_extraction is not None:
            def extract(*args, **kwargs):
                during_extraction()
                return [q], 2026
            extractor.side_effect = extract
        stack.enter_context(patch.object(app, 'stage2_tag_score', return_value={'per_topic': {}, 'new_topic_names': []}))
        stack.enter_context(patch.object(app, 'build_candidate_analysis', side_effect=lambda **kwargs: {
            'exam_id': kwargs['exam_id'], 'per_topic': {}, 'sentinel': 'new candidate'}))
        stack.enter_context(patch.object(app, 'aggregate_taxonomy', return_value={'topics': {}}))
        stack.enter_context(patch.object(app, 'finalize_candidate_analysis', side_effect=lambda candidate, *args: candidate))
        return stack

    def write_record(self, state, exam_id, source=None):
        folder = self.course / state
        folder.mkdir(exist_ok=True)
        record = {'exam_id': exam_id, 'per_topic': {},
                  'source_path': str(source or self.paper.resolve()), 'sentinel': 'original'}
        path = folder / (exam_id + '.json')
        path.write_text(json.dumps(record), encoding='utf-8')
        return path

    def test_invalid_ids_never_create_state_files_or_call_a_model_even_with_force(self):
        no_model = Mock(side_effect=AssertionError('model was called'))
        for value in [value for value in BAD_IDS if value is not None]:
            for force in [False, True]:
                with self.subTest(value=repr(value), force=force), patch.object(app, 'call_llm', no_model):
                    with self.assertRaises(ExamIdentityError):
                        app.process_exam_file(self.paper, exam_id=value, force=force, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        no_model.assert_not_called()
        self.assertFalse(self.context.parsed_dir.exists())
        self.assertFalse(self.context.candidates_dir.exists())
        self.assertEqual(list(self.outside.iterdir()), [])

    def test_plain_destination_is_resolved_inside_the_requested_state(self):
        for state in ['parsed', 'candidates']:
            destination = exam_record_path(self.course, state, 'My exam')
            self.assertEqual(destination, self.course.resolve() / state / 'My exam.json')
        with self.assertRaises(ExamIdentityError):
            exam_record_path(self.course, '../outside', 'paper')

    def test_state_directory_redirect_is_rejected_for_both_states(self):
        for state in ['parsed', 'candidates']:
            with self.subTest(state=state):
                link = self.course / state
                directory_link(link, self.outside)
                try:
                    with patch.object(app, 'call_llm') as model:
                        with self.assertRaisesRegex(ExamIdentityError, 'Unsafe state directory'):
                            app.process_exam_file(self.paper, exam_id='escape', force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
                        model.assert_not_called()
                    self.assertEqual(list(self.outside.iterdir()), [])
                finally:
                    if link.is_symlink():
                        link.unlink()
                    else:
                        link.rmdir()  # removes the junction, not its target

    def test_existing_hardlink_cannot_redirect_a_forced_write(self):
        victim = self.outside / 'victim.json'
        victim.write_text('outside data', encoding='utf-8')
        for state in ['parsed', 'candidates']:
            folder = self.course / state
            folder.mkdir(exist_ok=True)
            linked = folder / 'linked.json'
            os.link(victim, linked)
            try:
                with self.subTest(state=state), patch.object(app, 'call_llm') as model:
                    with self.assertRaisesRegex(ExamIdentityError, 'hard-linked'):
                        app.process_exam_file(self.paper, exam_id='linked', force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
                    model.assert_not_called()
                self.assertEqual(victim.read_text(encoding='utf-8'), 'outside data')
            finally:
                linked.unlink()

    def test_file_symlink_cannot_redirect_an_existing_or_new_record(self):
        folder = self.course / 'candidates'
        folder.mkdir()
        for exists in [False, True]:
            victim = self.outside / ('existing.json' if exists else 'new.json')
            if exists:
                victim.write_text('outside data', encoding='utf-8')
            linked = folder / 'linked.json'
            try:
                linked.symlink_to(victim)
            except OSError as exc:
                self.skipTest(f'File symlinks unavailable on this host: {exc}')
            try:
                with self.subTest(exists=exists), self.assertRaisesRegex(ExamIdentityError, 'redirected'):
                    app.process_exam_file(self.paper, exam_id='linked', force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
                self.assertEqual(victim.exists(), exists)
                if exists:
                    self.assertEqual(victim.read_text(encoding='utf-8'), 'outside data')
            finally:
                linked.unlink()

    def test_destination_directory_is_not_a_record_file(self):
        folder = self.course / 'candidates' / 'paper.json'
        folder.mkdir(parents=True)
        with self.assertRaisesRegex(ExamIdentityError, 'directories'):
            app.process_exam_file(self.paper, exam_id='paper', force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)

    def test_containment_is_checked_again_after_analysis(self):
        def redirect():
            self.context.candidates_dir.rmdir()
            directory_link(self.context.candidates_dir, self.outside)
        with self.fake_analysis(redirect):
            with self.assertRaisesRegex(ExamIdentityError, 'Unsafe state directory'):
                app.process_exam_file(self.paper, exam_id='paper', force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        self.assertEqual(list(self.outside.iterdir()), [])

    def test_changed_course_root_cannot_redirect_the_final_write(self):
        def redirect():
            self.course.rename(self.root / 'original-course')
            directory_link(self.course, self.outside)
        with self.fake_analysis(redirect):
            with self.assertRaises((ExamIdentityError, PermissionError)) as raised:
                app.process_exam_file(self.paper, exam_id='paper', force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        if isinstance(raised.exception, PermissionError):
            # Windows may prevent moving a directory with an open lock file.
            self.assertEqual(os.name, 'nt')
            self.assertTrue(self.course.is_dir())
        else:
            self.assertIn('course destination changed', str(raised.exception))
        self.assertEqual(list(self.outside.iterdir()), [])

    def test_file_link_inserted_during_analysis_is_rejected(self):
        victim = self.outside / 'victim.json'
        victim.write_text('outside data', encoding='utf-8')
        def redirect():
            os.link(victim, self.context.candidates_dir / 'paper.json')
        with self.fake_analysis(redirect):
            with self.assertRaisesRegex(ExamIdentityError, 'hard-linked'):
                app.process_exam_file(self.paper, exam_id='paper', force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        self.assertEqual(victim.read_text(encoding='utf-8'), 'outside data')

    def test_final_save_rechecks_a_destination_changed_after_validation(self):
        victim = self.outside / 'victim.json'
        victim.write_text('outside data', encoding='utf-8')
        def finalize(candidate, *args):
            os.link(victim, self.context.candidates_dir / 'paper.json')
            return candidate
        with self.fake_analysis(), patch.object(app, 'finalize_candidate_analysis', side_effect=finalize):
            with self.assertRaisesRegex(ExamIdentityError, 'hard-linked'):
                app.process_exam_file(self.paper, exam_id='paper', force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
        self.assertEqual(victim.read_text(encoding='utf-8'), 'outside data')

    def test_valid_custom_id_and_force_replace_only_the_named_candidate(self):
        exam_id = 'Historia España.2026'
        accepted = self.write_record('parsed', exam_id)
        candidate = self.write_record('candidates', exam_id)
        untouched = self.write_record('candidates', 'another')
        accepted_bytes, untouched_bytes = accepted.read_bytes(), untouched.read_bytes()
        with patch.object(app, 'call_llm') as model:
            self.assertEqual(app.process_exam_file(self.paper, exam_id=exam_id, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm),
                             app.ExamOutcome.SKIPPED_ACCEPTED)
            model.assert_not_called()
        with self.fake_analysis():
            self.assertEqual(app.process_exam_file(self.paper, exam_id=exam_id, force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm),
                             app.ExamOutcome.SAVED)
        saved = json.loads(candidate.read_text(encoding='utf-8'))
        review = saved.pop('independent_review')
        self.assertEqual(saved, {'exam_id': exam_id, 'per_topic': {}, 'sentinel': 'new candidate'})
        self.assertFalse(review['enabled'])
        self.assertEqual(review['disposition'], 'disabled')
        self.assertEqual(accepted.read_bytes(), accepted_bytes)
        self.assertEqual(untouched.read_bytes(), untouched_bytes)
        self.assertEqual(app.resolve_exam_id(self.paper, exam_id, course=self.context), exam_id)

    def test_automatic_id_collision_uses_source_folder_and_rechecks_it(self):
        first = self.root / '2025' / self.paper.name
        self.write_record('parsed', self.paper.stem, source=first)
        self.assertEqual(app.resolve_exam_id(self.paper, course=self.context), f'course_{self.paper.stem}')
        self.write_record('candidates', f'course_{self.paper.stem}')
        self.assertEqual(app.resolve_exam_id(self.paper, course=self.context), f'course_{self.paper.stem}')
        with patch.object(app, 'call_llm') as model:
            self.assertEqual(app.process_exam_file(self.paper, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm), app.ExamOutcome.SKIPPED_CANDIDATE)
            model.assert_not_called()

    def test_exhausted_automatic_ids_fail_instead_of_returning_an_unchecked_collision(self):
        base = self.paper.stem
        names = [base]
        for depth, parent in enumerate(self.paper.resolve().parents):
            folder = parent.name.replace(' ', '_')
            names.append(f'{folder}_{base}' if folder else f'{base}_{depth + 2}')
        for name in set(names):
            self.write_record('candidates', name, source=self.outside / 'other.txt')
        with patch.object(app, 'call_llm') as model:
            with self.assertRaisesRegex(ExamIdentityError, 'All automatic IDs'):
                app.process_exam_file(self.paper, force=True, course=self.context, extraction_client=app.call_llm, analysis_client=app.call_llm)
            model.assert_not_called()

    def test_automatic_ids_keep_existing_space_normalization(self):
        self.assertEqual(app.resolve_exam_id(self.course / 'My exam.txt', course=self.context), 'My_exam')

    def test_cli_rejects_invalid_explicit_id_before_creating_course(self):
        for value in ['../outside', '', 'NUL', 'C:\\escape']:
            new_course = self.root / 'uncreated'
            result = subprocess.run([sys.executable, str(Path(app.__file__)), str(new_course),
                                     'add-exam', str(self.paper), '--exam-id', value, '--force'],
                                    env={**os.environ, 'LLM_PROVIDER': 'anthropic'},
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('--exam-id', result.stderr)
            self.assertIn('Choose a plain ID', result.stderr)
            self.assertFalse(new_course.exists())


if __name__ == '__main__':
    unittest.main()
