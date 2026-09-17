"""Offline coverage for full question evidence, request budgets, and recovery."""

from contextlib import redirect_stdout
import importlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_roi.llm import (ModelClient, RequestLimitError, RequestLimits,
                          TruncatedResponse, estimate_tokens,
                          configured_model_client, text_from_anthropic,
                          text_from_openai, text_from_openai_stream)
from exam_roi.question_context import source_questions
from exam_roi.evaluation import CandidateValidationError, CONTRACT_TEXT

with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}):
    app = importlib.import_module("pipeline")


def question(q_id="Q1", topic="Equations", text="Use elimination."):
    return {"q_id": q_id, "text": text, "marks": 10, "format": "short_answer", "topics": [topic]}


def judgment(questions):
    return {
        "question_difficulty": [{"q_id": q["q_id"], "level": 3,
            "quote": q.get("source_context", q["text"])[-16:],
            "rationale": "Use a standard multi-step method.", "uncertainties": []} for q in questions],
        "difficulty_rationale": "Standard methods are required.",
        "assumed_prerequisites": [], "prerequisite_evidence": [],
        "Conn": 1, "connection_rationale": "No downstream use is supported.",
        "connection_evidence": [{"q_id": questions[0]["q_id"],
            "quote": questions[0].get("source_context", questions[0]["text"])[-16:]}],
        "connection_edges": [], "unlocks": [], "prerequisites": [], "uncertainties": [],
    }


def fake_scoring(system, user, **kwargs):
    names = re.search(r'TOPICS TESTED.*?\n(.*?)\n\nINFER', user, re.S)[1]
    names = [line[2:] for line in names.splitlines()]
    evidence = json.JSONDecoder().raw_decode(user.split('SOURCE QUESTIONS', 1)[1].split('\n', 1)[1])[0]
    return json.dumps({name: judgment([q for q in evidence if name in q['topics']]) for name in names})


def fake_tags(system, user, **kwargs):
    batch = json.JSONDecoder().raw_decode(user.split('of 1):\n', 1)[1])[0]
    return json.dumps({"tags": {q["q_id"]: {"topics": ["Equations"],
        "quote": q.get("source_context", q["text"])[-16:], "rationale": "The task tests equations.",
        "uncertainties": []} for q in batch}, "new_topic_names": []})


class BudgetTests(unittest.TestCase):
    def test_unorouter_streams_response_and_reports_connection_state(self):
        sdk = Mock()
        sdk.chat.completions.create.return_value = iter([
            NS(id="completion-1", choices=[NS(
                delta=NS(content='{"ok":'), finish_reason=None)]),
            NS(id="completion-1", choices=[NS(
                delta=NS(content="true}"), finish_reason="stop")]),
        ])
        progress = []
        client = ModelClient(
            sdk, "openai", "glm-5.3", RequestLimits(200, 50, 10),
            provider="unorouter", progress=progress.append,
        )

        self.assertEqual(client("system", "user"), '{"ok":true}')
        request = sdk.chat.completions.create.call_args.kwargs
        self.assertTrue(request["stream"])
        self.assertIn("attempt 1/3", progress[0])
        self.assertTrue(any("connected; receiving response" in line for line in progress))
        self.assertTrue(any("response complete" in line for line in progress))

    def test_retryable_524_honors_server_delay_and_reports_retry(self):
        class Retryable524(Exception):
            status_code = 524
            body = {"retryable": True, "retry_after": 120}
            request_id = "req-timeout-524"

        sdk = Mock()
        sdk.chat.completions.create.side_effect = [
            Retryable524("origin response timeout"),
            iter([NS(id="completion-2", choices=[NS(
                delta=NS(content="{}"), finish_reason="stop")])]),
        ]
        progress, delays = [], []
        client = ModelClient(
            sdk, "openai", "glm-5.3", RequestLimits(200, 50, 10),
            provider="unorouter", progress=progress.append, sleep=delays.append,
        )

        self.assertEqual(client("system", "user"), "{}")
        self.assertEqual(delays, [120])
        self.assertEqual(sdk.chat.completions.create.call_count, 2)
        retry = next(line for line in progress if "retrying" in line)
        self.assertIn("HTTP 524", retry)
        self.assertIn("request_id=req-timeout-524", retry)
        self.assertIn("120 seconds", retry)

    def test_non_retryable_http_error_is_not_retried(self):
        class AuthenticationFailure(Exception):
            status_code = 401
            body = {"retryable": False}

        sdk = Mock()
        sdk.chat.completions.create.side_effect = AuthenticationFailure("bad key")
        progress, delays = [], []
        client = ModelClient(
            sdk, "openai", "glm-5.3", RequestLimits(200, 50, 10),
            provider="unorouter", progress=progress.append, sleep=delays.append,
        )

        with self.assertRaises(AuthenticationFailure):
            client("system", "user")
        self.assertEqual(sdk.chat.completions.create.call_count, 1)
        self.assertEqual(delays, [])
        self.assertTrue(any("not retryable" in line for line in progress))

    def test_configured_openai_client_disables_sdk_retries(self):
        sdk = Mock()
        sdk.chat.completions.create.return_value = iter([
            NS(id="completion-3", choices=[NS(
                delta=NS(content="{}"), finish_reason="stop")]),
        ])
        openai_module = NS(OpenAI=Mock(return_value=sdk))
        providers = {"unorouter": {
            "sdk": "openai", "base_url": "https://api.unorouter.test/v1",
            "key_env": "UNOROUTER_API_KEY", "key_env_aliases": (),
        }}
        output = io.StringIO()

        with patch.dict(sys.modules, {"openai": openai_module}), redirect_stdout(output):
            client = configured_model_client(
                "unorouter", "glm-5.3", RequestLimits(200, 50, 10),
                providers=providers, env={"UNOROUTER_API_KEY": "test-key"},
                progress=print,
            )
            self.assertEqual(client("system", "user"), "{}")

        self.assertEqual(openai_module.OpenAI.call_args.kwargs["max_retries"], 0)
        self.assertIn("attempt 1/3", output.getvalue())

    def test_openai_request_receives_configured_reasoning_effort(self):
        sdk = Mock()
        sdk.chat.completions.create.return_value = iter([
            NS(id="completion-4", choices=[NS(
                delta=NS(content="{}"), finish_reason="stop")]),
        ])
        client = ModelClient(
            sdk, "openai", "glm-5.3", RequestLimits(200, 50, 10),
            provider="unorouter", reasoning_effort="low",
        )

        self.assertEqual(client("system", "user"), "{}")
        self.assertEqual(
            sdk.chat.completions.create.call_args.kwargs["reasoning_effort"], "low")

    def test_checks_include_system_utf8_framing_and_reserved_output(self):
        limits = RequestLimits(100, 20, 10)
        limits.check('s' * 30, 'u' * 40, 20)
        for system, user, output in [('s' * 31, 'u' * 40, 20), ('s' * 30, 'é' * 40, 20), ('', '', 21)]:
            with self.subTest(system=system), self.assertRaises(RequestLimitError):
                limits.check(system, user, output)

    def test_invalid_configuration_and_per_stage_environment(self):
        for values in [(0, 20, 1), (20, 20, 1), (30, True, 1)]:
            with self.assertRaises(ValueError):
                RequestLimits(*values)
        env = {'LLM_CONTEXT_TOKENS_STAGE1': '9999', 'LLM_MAX_OUTPUT_TOKENS_STAGE1': '2000',
               'LLM_OVERHEAD_TOKENS_STAGE1': '100'}
        self.assertEqual(RequestLimits.from_env(env, 1), RequestLimits(9999, 2000, 100))
        self.assertEqual(RequestLimits.from_env(env, 2), RequestLimits())

    def test_overflow_fails_before_sdk_or_credentials(self):
        sdk = Mock()
        client = ModelClient(sdk, 'openai', 'one', RequestLimits(100, 20, 10))
        with self.assertRaises(RequestLimitError):
            client('system', 'x' * 100)
        sdk.chat.completions.create.assert_not_called()
        create = Mock()
        lazy_client = ModelClient(None, 'openai', 'one', RequestLimits(100, 20, 10),
                                  client_factory=create)
        with self.assertRaises(RequestLimitError):
            app.call_llm('s', 'x' * 100, client=lazy_client)
        create.assert_not_called()

    def test_clients_keep_models_and_limits_separate(self):
        for model, cap in [('one', 20), ('two', 40)]:
            sdk = Mock()
            sdk.chat.completions.create.return_value = NS(choices=[NS(finish_reason='stop', message=NS(content='{}'))])
            client = ModelClient(sdk, 'openai', model, RequestLimits(200, cap, 10))
            self.assertEqual(client('system', 'user'), '{}')
            self.assertEqual(sdk.chat.completions.create.call_args.kwargs['model'], model)
            self.assertEqual(sdk.chat.completions.create.call_args.kwargs['max_tokens'], cap)

    def test_provider_truncation_rejects_even_complete_json_and_thinking_only(self):
        with self.assertRaises(TruncatedResponse):
            text_from_openai(NS(choices=[NS(finish_reason='length', message=NS(content='{}'))]))
        with self.assertRaises(TruncatedResponse):
            text_from_openai_stream(iter([NS(choices=[NS(
                finish_reason='length', delta=NS(content='{}'))])]))
        for content in [[], [NS(type='text', text='{}')], [NS(type='thinking')]]:
            with self.assertRaises(TruncatedResponse):
                text_from_anthropic(NS(stop_reason='max_tokens', content=content))

    def test_provider_truncation_is_not_retried_unchanged(self):
        sdk = Mock()
        sdk.chat.completions.create.return_value = NS(choices=[NS(finish_reason='length', message=NS(content='{}'))])
        with self.assertRaises(TruncatedResponse):
            ModelClient(sdk, 'openai', 'model', RequestLimits(200, 50, 10))('s', 'u')
        self.assertEqual(sdk.chat.completions.create.call_count, 1)

    def test_reusable_modules_have_no_import_side_effects(self):
        env = {**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1]), 'LLM_PROVIDER': 'invalid'}
        run = subprocess.run([sys.executable, '-c',
            'import sys; before=sys.stdout; import exam_roi.llm, exam_roi.question_context; assert sys.stdout is before'],
            env=env, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, '')


class ExtractionTests(unittest.TestCase):
    def paper(self, count=4):
        return 'Course background: elimination is taught.\n' + ''.join(
            f'Question {n}: ' + 'introduction ' * 40 + f'\n[Page {n+1}]\nDecisive task {n}.\n'
            for n in range(1, count + 1))

    def fake(self, system, user, **kwargs):
        text = user.split('EXAM TEXT:\n', 1)[1]
        ids = re.findall(r'^Question (\d+):', text, re.M)
        return json.dumps({'exam_year': 2026, 'questions': [
            {'q_id': 'Q' + n, 'text': 'Decisive task ' + n + '.', 'marks': 10, 'format': 'short_answer'}
            for n in ids]})

    def test_oversized_paper_keeps_page_continuation_and_stable_ids(self):
        paper = self.paper()
        client = Mock(side_effect=self.fake)
        # Output estimate allows a whole question but forces smaller batches.
        out, year = app.stage1_extract(paper, 40, client=client, limits=RequestLimits(30000, 1800, 100))
        self.assertGreater(client.call_count, 1)
        self.assertEqual([q['q_id'] for q in out], ['Q1', 'Q2', 'Q3', 'Q4'])
        self.assertEqual(year, 2026)
        for n, q in enumerate(out, 1):
            self.assertIn(f'[Page {n+1}]\nDecisive task {n}.', q['source_context'])
            self.assertIn('elimination is taught', q['source_context'])
        prefix, units = source_questions(paper)
        self.assertEqual(prefix + ''.join(unit.text for unit in units), paper)

    def test_input_limit_splits_without_cutting_questions(self):
        paper = self.paper()
        prefix, units = source_questions(paper)
        one = app._extraction_prompt(prefix + units[0].text, 40)
        limits = RequestLimits(estimate_tokens(app._S1_SYSTEM) + estimate_tokens(one) + 5000 + 100, 5000, 100)
        client = Mock(side_effect=self.fake)
        out, _ = app.stage1_extract(paper, 40, client=client, limits=limits)
        self.assertEqual(len(out), 4)
        self.assertEqual(client.call_count, 4)

    def test_missing_heading_or_restarted_id_is_rejected(self):
        def missing(system, user, **kwargs):
            data = json.loads(self.fake(system, user, **kwargs))
            data['questions'] = data['questions'][:1]
            return json.dumps(data)
        with self.assertRaisesRegex(CandidateValidationError, 'Missing source questions'):
            app.stage1_extract(self.paper(), 40, client=missing)
        def restarted(system, user, **kwargs):
            data = json.loads(self.fake(system, user, **kwargs))
            data['questions'][0]['q_id'] = 'Q99'
            return json.dumps(data)
        with self.assertRaisesRegex(CandidateValidationError, 'unstable question ID'):
            app.stage1_extract(self.paper(1), 10, client=restarted)

    def test_conflicting_years_across_batches_fail(self):
        def different_years(system, user, **kwargs):
            data = json.loads(self.fake(system, user, **kwargs))
            data['exam_year'] = 2025 if data['questions'][0]['q_id'] == 'Q1' else 2026
            return json.dumps(data)
        with self.assertRaisesRegex(CandidateValidationError, 'Conflicting sitting years'):
            app.stage1_extract(self.paper(2), 20, client=different_years, limits=RequestLimits(30000, 1200, 100))

    def test_truncation_splits_and_discards_failed_batch(self):
        def truncated(system, user, **kwargs):
            if len(re.findall(r'^Question \d+:', user, re.M)) > 1:
                raise TruncatedResponse('cut off')
            return self.fake(system, user, **kwargs)
        client = Mock(side_effect=truncated)
        out, _ = app.stage1_extract(self.paper(2), 20, client=client)
        self.assertEqual(client.call_count, 3)
        self.assertEqual([q['q_id'] for q in out], ['Q1', 'Q2'])

    def test_ambiguous_or_single_oversized_question_fails_without_dispatch(self):
        for paper in ['No question headings. ' * 10000, self.paper(1)]:
            client = Mock()
            with self.assertRaises(RequestLimitError):
                app.stage1_extract(paper, 10, client=client, limits=RequestLimits(20000, 500, 100))
            client.assert_not_called()

    def test_subquestion_keeps_parent_and_cross_page_context(self):
        paper = 'Question 1: Shared setup.\n(a) First task.\n[Page 2]\n(b) Decisive task.'
        answer = {'exam_year': None, 'questions': [
            {'q_id': name, 'text': text, 'marks': 5, 'format': 'short_answer'}
            for name, text in [('Q1a', 'First task.'), ('Q1b', 'Decisive task.')]]}
        out, _ = app.stage1_extract(paper, 10, client=lambda *a, **kw: json.dumps(answer))
        self.assertEqual([q['q_id'] for q in out], ['Q1a', 'Q1b'])
        self.assertEqual(out[1]['source_context'], paper)

    def test_cross_referenced_question_survives_a_batch_boundary(self):
        paper = 'Question 1: A supplied formula.\nQuestion 2: Use Question 1 to solve this.\n'
        prompts = []
        def extract(system, user, **kwargs):
            prompts.append(user)
            target_text = user.split('SUPPORTING SOURCE CONTEXT ONLY', 1)[0]
            return self.fake(system, target_text, **kwargs)
        out, _ = app.stage1_extract(paper, 20, client=extract, limits=RequestLimits(30000, 500, 100))
        self.assertEqual(len(prompts), 2)
        self.assertIn('SUPPORTING SOURCE CONTEXT ONLY', prompts[1])
        self.assertIn('A supplied formula.', prompts[1])
        self.assertIn('A supplied formula.', out[1]['source_context'])
        self.assertIn('Use Question 1 to solve this.', out[1]['source_context'])

    def test_unmarked_truncated_json_is_rejected(self):
        with self.assertRaisesRegex(CandidateValidationError, 'malformed JSON'):
            app.stage1_extract(self.paper(1), 10, client=lambda *a, **kw: '{"exam_year": 2026, "questions": [')


class AnalysisBatchTests(unittest.TestCase):
    def test_tail_and_original_context_survive_tagging_scoring_and_candidate(self):
        tail = 'Choose and justify an elimination method.'
        q = question(text='Introduction. ' * 200 + tail)
        q['source_context'] = 'Original course instructions. ' * 200 + tail
        tag_client = Mock(side_effect=fake_tags)
        tags, _ = app._stage2_tag([q], ['Equations'], client=tag_client)
        score_client = Mock(side_effect=fake_scoring)
        out = app._stage2_score_topics(['Equations'], '', [q], ['Equations'], client=score_client)
        for client in [tag_client, score_client]:
            prompt = client.call_args.args[1]
            self.assertIn(q['text'], prompt)
            self.assertIn(q['source_context'], prompt)
            self.assertIn(CONTRACT_TEXT, client.call_args.args[0])
        self.assertEqual(out['Equations']['Diff'], 3)
        self.assertIn('COURSE BASELINE', score_client.call_args.args[1])
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            self.context = app.setup_course_folder(folder)
            paper = folder / 'paper_2026.txt'
            paper.write_text(q['source_context'], encoding='utf-8')
            with patch.object(app, 'stage1_extract', return_value=([q], 2026)), \
                 patch.object(app, '_stage2_tag', return_value=(tags, [])), \
                 patch.object(app, 'load_taxonomy', return_value={'topics': {'Equations': {}}}):
                app.process_exam_file(paper, analysis_client=fake_scoring, course=self.context, extraction_client=app.call_llm)
            candidate = json.loads((self.context.candidates_dir / 'paper_2026.json').read_text(encoding='utf-8'))
            self.assertEqual(candidate['questions'][0]['source_context'], q['source_context'])

    def test_tagging_output_batches_and_final_exact_coverage(self):
        questions = [question(f'Q{i}') for i in range(10)]
        client = Mock(side_effect=fake_tags)
        tags, _ = app._stage2_tag(questions, ['Equations'], client=client, limits=RequestLimits(30000, 1200, 100))
        self.assertEqual(set(tags), {q['q_id'] for q in questions})
        self.assertGreater(client.call_count, 1)

    def test_new_topic_names_feed_forward_into_later_batches(self):
        prompts = []
        def tag(system, user, **kwargs):
            prompts.append(user)
            data = json.loads(fake_tags(system, user, **kwargs))
            data['new_topic_names'] = ['Equations'] if len(prompts) == 1 else []
            return json.dumps(data)
        tags, names = app._stage2_tag([question('Q1'), question('Q2')], [], client=tag,
                                      limits=RequestLimits(30000, 600, 100))
        self.assertEqual(names, ['Equations'])
        self.assertIn('- Equations', prompts[1])
        self.assertEqual(set(tags), {'Q1', 'Q2'})

    def test_large_topic_set_and_many_questions_per_topic_merge(self):
        for questions in [[question(f'Q{i}', f'Topic {i}') for i in range(15)],
                          [question(f'Q{i}') for i in range(15)]]:
            topics = sorted({t for q in questions for t in q['topics']})
            client = Mock(side_effect=fake_scoring)
            result = app._stage2_score_topics(topics, '', questions, topics, client=client,
                                             limits=RequestLimits(30000, 2400, 100))
            self.assertGreater(client.call_count, 1)
            self.assertEqual(set(result), set(topics))
            for topic in topics:
                self.assertEqual({j['q_id'] for j in result[topic]['question_difficulty']},
                                 {q['q_id'] for q in questions if topic in q['topics']})
                self.assertEqual(result[topic]['Diff'], 3)

    def test_truncation_recovery_for_tagging_and_scoring_is_bounded(self):
        questions = [question('Q1'), question('Q2')]
        def recover(fake):
            def call(system, user, **kwargs):
                source = (user.split('SOURCE QUESTIONS', 1)[1].split('\n', 1)[1]
                          if 'SOURCE QUESTIONS' in user else user.split('of 1):\n', 1)[1])
                if len(json.JSONDecoder().raw_decode(source)[0]) > 1:
                    raise TruncatedResponse('incomplete')
                return fake(system, user, **kwargs)
            return Mock(side_effect=call)
        tagger, scorer = recover(fake_tags), recover(fake_scoring)
        app._stage2_tag(questions, ['Equations'], client=tagger)
        app._stage2_score_topics(['Equations'], '', questions, ['Equations'], client=scorer)
        self.assertEqual(tagger.call_count, 3)
        self.assertEqual(scorer.call_count, 3)
        for stage in [lambda c: app._stage2_tag(questions[:1], ['Equations'], client=c),
                      lambda c: app._stage2_score_topics(['Equations'], '', questions[:1], ['Equations'], client=c)]:
            client = Mock(side_effect=TruncatedResponse('incomplete'))
            with self.assertRaisesRegex(TruncatedResponse, 'no partial answer'):
                stage(client)
            self.assertEqual(client.call_count, 1)

    def test_merged_scores_recompute_median_and_union_connections(self):
        questions = [question(f'Q{i}') for i in range(5)]
        levels = [1, 2, 5, 6, 6]
        def score(system, user, **kwargs):
            data = json.loads(fake_scoring(system, user, **kwargs))
            part = data['Equations']
            edges = []
            for item in part['question_difficulty']:
                number = int(item['q_id'][1:])
                item['level'] = levels[number]
                dependent = f'Dependent {number}'
                edges.append({'prerequisite': 'Equations', 'dependent': dependent,
                              'q_id': item['q_id'], 'quote': item['quote'], 'rationale': 'The task uses this method.'})
            part.update(connection_edges=edges, unlocks=[e['dependent'] for e in edges],
                        Conn=2 if len(edges) <= 2 else 3)
            return json.dumps(data)
        result = app._stage2_score_topics(['Equations'], '', questions,
            ['Equations'] + [f'Dependent {i}' for i in range(5)], client=score,
            limits=RequestLimits(30000, 2100, 100))['Equations']
        self.assertEqual(result['Diff'], 5)
        self.assertEqual(result['Conn'], 3)
        self.assertEqual(len(result['connection_edges']), 5)
        self.assertEqual(len(result['question_difficulty']), 5)

    def test_complete_fence_followed_by_partial_json_is_rejected(self):
        with self.assertRaises(CandidateValidationError):
            app.parse_json_from('```json\n{}\n```\n{"unfinished":')

    def test_injected_models_are_recorded_in_provenance(self):
        one = ModelClient(Mock(), 'openai', 'extract-model', RequestLimits(), provider='first-provider')
        two = ModelClient(Mock(), 'anthropic', 'score-model', RequestLimits(), provider='second-provider')
        provenance = app._model_provenance(one, two)
        self.assertEqual(provenance['extraction_model'], 'extract-model')
        self.assertEqual(provenance['analysis_model'], 'score-model')
        self.assertEqual(provenance['provider'], 'mixed')
        self.assertEqual(provenance['analysis_provider'], 'second-provider')

    def test_huge_taxonomy_is_never_silently_trimmed(self):
        topics = ['Topic ' + str(i) for i in range(10000)]
        client = Mock()
        with self.assertRaises(RequestLimitError):
            app._stage2_tag([question()], topics, client=client, limits=RequestLimits(30000, 2000, 100))
        client.assert_not_called()
        with self.assertRaises(RequestLimitError):
            app._stage2_score_topics(['Equations'], '', [question()], topics + ['Equations'],
                                    client=client, limits=RequestLimits(30000, 2000, 100))
        client.assert_not_called()

    def test_missing_score_or_question_evidence_is_rejected(self):
        for mutate in [lambda d: d.clear(), lambda d: d['Equations']['question_difficulty'].pop()]:
            def bad(system, user, **kwargs):
                data = json.loads(fake_scoring(system, user, **kwargs))
                mutate(data)
                return json.dumps(data)
            with self.assertRaises(CandidateValidationError):
                app._stage2_score_topics(['Equations'], '', [question('Q1'), question('Q2')],
                                         ['Equations'], client=bad)


if __name__ == '__main__':
    unittest.main()
