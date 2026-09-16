"""Offline checks for independent courses, clients, and import-safe entry points."""

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import MagicMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline as app
from exam_roi.llm import ModelClient, ModelConfigurationError, RequestLimits
from exam_roi.review import CATEGORIES
from exam_roi.storage import CoursePaths
from test_candidate_validation import question, scores, tag


PIPELINE = Path(__file__).resolve().parents[1]
REPO = PIPELINE.parent


def completion(text):
    return NS(choices=[NS(finish_reason="stop", message=NS(content=text))])


class IndependentConfigurationTests(unittest.TestCase):
    def test_two_course_contexts_and_analyzer_reviewer_clients_do_not_leak(self):
        q = question()
        q.pop("topics")
        source = q["text"]
        extraction = json.dumps({"exam_year": 2026, "questions": [q]})
        tagging = json.dumps({"tags": {"Q1": tag(["Equations"])},
                              "new_topic_names": ["Equations"]})
        sdk = Mock()
        sdk.chat.completions.create.side_effect = [completion(text) for text in
            [extraction, tagging, json.dumps(scores())] * 2]
        analyzer = ModelClient(sdk, "openai", "analyzer-test", RequestLimits(), provider="openai")
        review_sdk = MagicMock()
        review = json.dumps({"disposition": "no_issue", "findings": [
            {"category": category, "disposition": "no_issue", "severity": "info",
             "rationale": "The source supports this assessment.", "evidence": [source]}
            for category in CATEGORIES]})
        stream = review_sdk.messages.stream.return_value.__enter__.return_value = Mock()
        stream.get_final_message.return_value = NS(
            stop_reason="end_turn", content=[NS(type="text", text=review)])
        reviewer = ModelClient(review_sdk, "anthropic", "reviewer-test",
                               RequestLimits(250000, 4000, 1024), provider="anthropic")
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            first = app.setup_course_folder(Path(temp) / "first")
            second = app.setup_course_folder(Path(temp) / "second")
            for course, topic in ((first, "First only"), (second, "Second only")):
                app.save_taxonomy({"topics": {topic: {"Diff": 2, "Conn": 1}}}, course)
                (course.folder / "paper.txt").write_text(source, encoding="utf-8")
            # Exercise the first after creating the second, the old global-state failure.
            for course in (first, second):
                outcome = app.process_exam_file(course.folder / "paper.txt", course=course,
                    extraction_client=analyzer, analysis_client=analyzer,
                    review_enabled=True, reviewer_client=reviewer)
                self.assertEqual(outcome, app.ExamOutcome.SAVED)
                candidate = json.loads((course.candidates_dir / "paper.json").read_text(encoding="utf-8"))
                self.assertEqual(candidate["source_provenance"]["resolved_path"],
                                 str(course.folder / "paper.txt"))
                self.assertEqual(candidate["model_provenance"]["analysis_model"], "analyzer-test")
                self.assertEqual(candidate["independent_review"]["model"], "reviewer-test")
                self.assertEqual(candidate["independent_review"]["provider"], "anthropic")
                self.assertEqual(app.load_all_exams(course), {})
            self.assertEqual(set(app.load_taxonomy(first)["topics"]), {"First only"})
            self.assertEqual(set(app.load_taxonomy(second)["topics"]), {"Second only"})
        self.assertEqual(sdk.chat.completions.create.call_count, 6)
        self.assertEqual(review_sdk.messages.stream.call_count, 2)
        for request in sdk.chat.completions.create.call_args_list:
            self.assertEqual(request.kwargs["model"], "analyzer-test")
            self.assertEqual(request.kwargs["max_tokens"], 32000)
        for request in review_sdk.messages.stream.call_args_list:
            self.assertEqual(request.kwargs["model"], "reviewer-test")
            self.assertEqual(request.kwargs["max_tokens"], 4000)

    def test_startup_captures_routing_keys_models_and_limits_before_environment_changes(self):
        env = {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "first-test-key",
               "OPENAI_BASE_URL": "https://first.example/v1", "OPENAI_ORG_ID": "first-org",
               "OPENAI_PROJECT_ID": "first-project",
               "LLM_MODEL_STAGE1": "first-model", "LLM_MAX_OUTPUT_TOKENS_STAGE1": "100"}
        first = app.configure_model_clients(env)["extraction_client"]
        env.update(OPENAI_API_KEY="second-test-key", LLM_MODEL_STAGE1="second-model",
                   OPENAI_BASE_URL="https://second.example/v1", OPENAI_ORG_ID="second-org",
                   OPENAI_PROJECT_ID="second-project",
                   LLM_MAX_OUTPUT_TOKENS_STAGE1="200")
        second = app.configure_model_clients(env)["extraction_client"]
        env.clear()
        self.assertIsNone(first.client)
        self.assertIsNone(second.client)
        first_sdk, second_sdk = Mock(), Mock()
        first_sdk.chat.completions.create.return_value = completion("first answer")
        second_sdk.chat.completions.create.return_value = completion("second answer")
        factory = Mock(side_effect=[first_sdk, second_sdk])
        changed_environment = {"OPENAI_API_KEY": "late-test-key", "OPENAI_BASE_URL": "https://late.example/v1",
                               "OPENAI_ORG_ID": "late-org", "OPENAI_PROJECT_ID": "late-project"}
        with patch.dict(sys.modules, {"openai": NS(OpenAI=factory)}), \
             patch.dict(os.environ, changed_environment, clear=True):
            self.assertEqual(first("s", "u"), "first answer")
            self.assertEqual(second("s", "u"), "second answer")
            self.assertEqual(first("s", "u"), "first answer")
            self.assertEqual(dict(os.environ), changed_environment)
        self.assertEqual([call.kwargs for call in factory.call_args_list], [
            {"api_key": "first-test-key", "base_url": "https://first.example/v1",
             "organization": "first-org", "project": "first-project"},
            {"api_key": "second-test-key", "base_url": "https://second.example/v1",
             "organization": "second-org", "project": "second-project"}])
        self.assertEqual(first_sdk.chat.completions.create.call_args.kwargs["model"], "first-model")
        self.assertEqual(second_sdk.chat.completions.create.call_args.kwargs["model"], "second-model")
        self.assertEqual(first.limits.output_tokens, 100)
        self.assertEqual(second.limits.output_tokens, 200)

    def test_absent_routing_settings_do_not_inherit_later_sdk_environment_defaults(self):
        import openai
        import httpx

        client = app.configure_model_clients({"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"})[
            "extraction_client"]
        self.assertIsNone(client.client)
        transport = Mock(side_effect=AssertionError("No HTTP request is expected"))
        with httpx.Client(transport=httpx.MockTransport(transport)) as http_client:
            sdk_constructor = openai.OpenAI
            with patch.dict(os.environ, {"OPENAI_BASE_URL": "https://late.example/v1",
                    "OPENAI_ORG_ID": "late-org", "OPENAI_PROJECT_ID": "late-project"}), \
                 patch.object(openai, "OpenAI", side_effect=lambda **kwargs:
                              sdk_constructor(http_client=http_client, **kwargs)):
                sdk = client.client_factory()
            self.assertEqual(str(sdk.base_url), "https://api.openai.com/v1/")
            self.assertEqual(sdk.organization, "")
            self.assertEqual(sdk.project, "")
        transport.assert_not_called()

    def test_anthropic_startup_captures_endpoints_and_keys_before_environment_changes(self):
        env = {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "first-test-key",
               "ANTHROPIC_BASE_URL": "https://first.example"}
        first = app.configure_model_clients(env)["extraction_client"]
        env.update(ANTHROPIC_API_KEY="second-test-key", ANTHROPIC_BASE_URL="https://second.example")
        second = app.configure_model_clients(env)["extraction_client"]
        env.clear()
        self.assertIsNone(first.client)
        self.assertIsNone(second.client)
        first_sdk, second_sdk = MagicMock(), MagicMock()
        for sdk, answer in ((first_sdk, "first answer"), (second_sdk, "second answer")):
            stream = sdk.messages.stream.return_value.__enter__.return_value
            stream.get_final_message.return_value = NS(
                stop_reason="end_turn", content=[NS(type="text", text=answer)])
        factory = Mock(side_effect=[first_sdk, second_sdk])
        changed_environment = {"ANTHROPIC_API_KEY": "late-test-key", "ANTHROPIC_BASE_URL": "https://late.example"}
        with patch.dict(sys.modules, {"anthropic": NS(Anthropic=factory)}), \
             patch.dict(os.environ, changed_environment, clear=True):
            self.assertEqual(first("s", "u"), "first answer")
            self.assertEqual(second("s", "u"), "second answer")
            self.assertEqual(first("s", "u"), "first answer")
            self.assertEqual(dict(os.environ), changed_environment)
        self.assertEqual([call.kwargs for call in factory.call_args_list], [
            {"api_key": "first-test-key", "base_url": "https://first.example"},
            {"api_key": "second-test-key", "base_url": "https://second.example"}])

    def test_absent_anthropic_endpoint_uses_explicit_sdk_default(self):
        client = app.configure_model_clients({"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "test-key"})[
            "extraction_client"]
        self.assertIsNone(client.client)
        factory = Mock()
        changed_environment = {"ANTHROPIC_API_KEY": "late-test-key", "ANTHROPIC_BASE_URL": "https://late.example"}
        with patch.dict(sys.modules, {"anthropic": NS(Anthropic=factory)}), \
             patch.dict(os.environ, changed_environment, clear=True):
            client.client_factory()
            self.assertEqual(dict(os.environ), changed_environment)
        factory.assert_called_once_with(api_key="test-key", base_url="https://api.anthropic.com")

    def test_documented_defaults_alias_and_missing_credentials(self):
        for provider, models in (("anthropic", ("claude-haiku-4-5-20251001", "claude-sonnet-5")),
                                 ("deepseek", ("deepseek-chat", "deepseek-chat")),
                                 ("openai", ("gpt-4o-mini", "gpt-4o"))):
            clients = app.configure_model_clients({"LLM_PROVIDER": provider})
            self.assertEqual(tuple(client.model for client in clients.values()), models)
            with self.assertRaises(ModelConfigurationError):
                clients["extraction_client"]("s", "u")
        self.assertEqual(app.configure_model_clients({})["analysis_client"].provider, "anthropic")
        sdk = Mock()
        sdk.chat.completions.create.return_value = completion("ok")
        factory = Mock(return_value=sdk)
        clients = app.configure_model_clients({"LLM_PROVIDER": "unorouter",
            "OPENROUTER_API_KEY": "alias-test-key", "LLM_MODEL_STAGE1": "one", "LLM_MODEL_STAGE2": "two"})
        with patch.dict(sys.modules, {"openai": NS(OpenAI=factory)}):
            clients["analysis_client"]("s", "u")
        factory.assert_called_once_with(api_key="alias-test-key", base_url="https://api.unorouter.com/v1",
                                        organization="", project="")

    def test_glm_53_defaults_cover_a_twenty_page_exam_and_keep_env_overrides(self):
        env = {
            "LLM_PROVIDER": "unorouter",
            "LLM_MODEL_STAGE1": "glm-5.3-flash",
            "LLM_MODEL_STAGE2": "glm-5.3",
        }
        clients = app.configure_model_clients(env)
        for client in clients.values():
            self.assertEqual(client.limits, RequestLimits(1_000_000, 128_000, 1024))

        paper = "\n\n".join(
            f"[Page {page}]\n" + "Question text and choices. " * 300
            for page in range(1, 21)
        )
        prompt = app._extraction_prompt(paper, None)
        clients["extraction_client"].limits.check(
            app._S1_SYSTEM, prompt, clients["extraction_client"].limits.output_tokens)

        overridden = app.configure_model_clients({
            **env,
            "LLM_CONTEXT_TOKENS_STAGE1": "300000",
            "LLM_MAX_OUTPUT_TOKENS_STAGE1": "64000",
            "LLM_OVERHEAD_TOKENS_STAGE1": "2048",
        })["extraction_client"]
        self.assertEqual(overridden.limits, RequestLimits(300_000, 64_000, 2048))

    def test_course_construction_and_missing_analysis_client_have_no_implicit_setup(self):
        with tempfile.TemporaryDirectory() as temp:
            course = CoursePaths(Path(temp) / "absent")
            self.assertFalse(course.folder.exists())
        with self.assertRaises(ModelConfigurationError):
            app.stage1_extract("Question 1\nUse elimination.", 10)


class StartupTests(unittest.TestCase):
    def test_add_exam_prints_effective_llm_settings_without_credentials(self):
        env = {
            "LLM_PROVIDER": "unorouter",
            "UNOROUTER_API_KEY": "secret-test-key",
            "LLM_MODEL_STAGE1": "glm-5.3-flash",
            "LLM_MODEL_STAGE2": "glm-5.3",
        }
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as temp, \
             patch.dict(os.environ, env, clear=True), \
             patch.object(sys, "argv", ["pipeline.py", temp, "add-exam"]), \
             patch.object(app, "load_dotenv"), \
             patch.object(app, "cmd_add_exam", return_value=app.EXIT_OK), \
             redirect_stdout(out):
            self.assertEqual(app.main(), app.EXIT_OK)
        self.assertIn("LLM settings", out.getvalue())
        self.assertIn(
            "Stage 1: provider=unorouter, model=glm-5.3-flash, "
            "context=1,000,000, max_output=128,000, overhead=1,024 tokens",
            out.getvalue(),
        )
        self.assertIn(
            "Stage 2: provider=unorouter, model=glm-5.3, "
            "context=1,000,000, max_output=128,000, overhead=1,024 tokens",
            out.getvalue(),
        )
        self.assertNotIn("secret-test-key", out.getvalue())

    def test_dry_run_does_not_configure_or_print_llm_settings(self):
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(sys, "argv", ["pipeline.py", temp, "add-exam", "--dry-run"]), \
             patch.object(app, "configure_model_clients",
                          side_effect=AssertionError("dry run configured a model")), \
             patch.object(app, "cmd_add_exam", return_value=app.EXIT_OK), \
             redirect_stdout(out):
            self.assertEqual(app.main(), app.EXIT_OK)
        self.assertNotIn("LLM settings", out.getvalue())

    def test_explicit_dotenv_loading_preserves_environment_and_raises_defined_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            dotenv = Path(temp) / "settings.env"
            dotenv.write_text('LLM_PROVIDER=deepseek\nexport LLM_MODEL_STAGE1="chosen-model"\n',
                              encoding="utf-8")
            with patch.dict(os.environ, {"LLM_PROVIDER": "openai"}, clear=True):
                app.load_dotenv(dotenv)
                self.assertEqual(os.environ["LLM_PROVIDER"], "openai")
                self.assertEqual(os.environ["LLM_MODEL_STAGE1"], "chosen-model")
            dotenv.write_text("invalid entry\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid .env entry"):
                app.load_dotenv(dotenv)
            with self.assertRaisesRegex(ValueError, "COURSE_FOLDER is not a folder"):
                app.setup_course_folder(dotenv)

    def test_import_does_not_read_env_create_files_or_reconfigure_streams(self):
        script = '''
import io, os, pathlib, sys
from unittest.mock import patch
class GuardedStream(io.StringIO):
    def reconfigure(self, **kwargs):
        raise AssertionError("import reconfigured a stream")
out, err = GuardedStream(), GuardedStream()
before = dict(os.environ)
with patch.object(sys, "stdout", out), patch.object(sys, "stderr", err), \\
     patch.object(pathlib.Path, "mkdir", side_effect=AssertionError("import created a directory")), \\
     patch.object(pathlib.Path, "write_text", side_effect=AssertionError("import wrote a file")):
    original = pathlib.Path.read_text
    def read(path, *args, **kwargs):
        if path.name == ".env":
            raise AssertionError("import read environment defaults")
        return original(path, *args, **kwargs)
    with patch.object(pathlib.Path, "read_text", read):
        import pipeline, exam_roi.llm, exam_roi.storage, exam_roi.reports, exam_roi.scoring
assert os.environ == before
assert not out.getvalue() and not err.getvalue()
'''
        result = subprocess.run([sys.executable, "-c", script], cwd=PIPELINE,
            env={**os.environ, "LLM_PROVIDER": "invalid-on-purpose"}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_help_and_rebuild_without_credentials_from_both_working_directories(self):
        env = {**os.environ, "LLM_PROVIDER": "invalid-on-purpose"}
        for config in app.PROVIDERS.values():
            env[config["key_env"]] = ""
        with tempfile.TemporaryDirectory() as temp:
            course = Path(temp) / "course"
            for cwd, entry in ((REPO, "pipeline/pipeline.py"), (PIPELINE, "pipeline.py")):
                for args in (("--help",), (str(course), "add-exam", "--help"), (str(course), "rebuild")):
                    result = subprocess.run([sys.executable, entry, *args], cwd=cwd, env=env,
                        capture_output=True, text=True, encoding="utf-8")
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_maps_missing_analyzer_credentials_to_setup_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            course = Path(temp)
            paper = course / "paper.txt"
            paper.write_text("Question 1\nUse elimination.", encoding="utf-8")
            env = {**os.environ, "LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": ""}
            result = subprocess.run([sys.executable, "pipeline.py", str(course), "add-exam", str(paper)],
                cwd=PIPELINE, env=env, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, app.EXIT_SETUP_ERROR, result.stdout + result.stderr)
            self.assertIn("ANTHROPIC_API_KEY is not set", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(list((course / "candidates").glob("*.json")))


if __name__ == "__main__":
    unittest.main()
