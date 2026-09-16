"""Opt-in stage evaluation and offline replay using the production pipeline.

Run this file explicitly. Importing it never configures a provider or reads keys.
"""

import argparse
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path

import pipeline as app
from exam_roi.evaluation import (
    build_candidate_analysis, contract_metadata, project_extraction_questions,
    validate_extraction,
)
from exam_roi.llm import RequestLimits


RUNS = {"stage1": 1, "stage2": 2, "chain_stage1": 1, "chain_stage2": 2}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode("utf-8")).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return app.parse_json_from(Path(path).read_text(encoding="utf-8"))


def write_new_json(path, value):
    """Evaluation outputs never overwrite a previous capture or reference."""
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


class PendingRequest(Exception):
    """A GPT sub-agent must answer the recorded system and user messages."""


class ExchangeClient:
    """Accept responses by request hash; missing responses expose the real prompt."""

    def __init__(self, run, answers):
        self.run = run
        self.answers = answers
        self.index = 0

    def __call__(self, system, user, max_tokens):
        request_id = digest([self.run, self.index, system, user, max_tokens])
        self.index += 1
        if request_id not in self.answers:
            raise PendingRequest(request_id)
        answer = self.answers[request_id]
        if not isinstance(answer, str):
            raise ValueError("Exchange answers must be raw JSON response strings")
        return answer


class ReplayClient:
    """Replay only the captured requests, including their exact prompt contents."""

    def __init__(self, calls):
        self.calls = deepcopy(calls)
        self.index = 0

    def __call__(self, system, user, max_tokens):
        if self.index >= len(self.calls):
            raise ValueError("Replay requested an uncaptured model call")
        call = self.calls[self.index]
        self.index += 1
        if call["request"] != {"system": system, "user": user, "max_tokens": max_tokens}:
            raise ValueError("Replay prompt changed; capture and review new evidence")
        if "response" not in call:
            raise ValueError("Replay requires a completed response")
        return call["response"]

    def finish(self):
        if self.index != len(self.calls):
            raise ValueError("Replay left captured model calls unused")


def validate_case(case):
    if not isinstance(case, dict) or case.get("schema_version") != 1:
        raise ValueError("Expected evaluation case schema_version 1")
    for key in ("id", "source_text", "source_name"):
        if not isinstance(case.get(key), str) or not case[key].strip():
            raise ValueError(f"Case requires nonempty {key}")
    marks = case.get("total_marks")
    if type(marks) not in (int, float) or not math.isfinite(marks) or marks <= 0:
        raise ValueError("Case total_marks must be finite and positive")
    validate_extraction(case["frozen_stage1"], app.EARLIEST_YEAR, 9999)
    if not isinstance(case["taxonomy"].get("topics"), dict):
        raise ValueError("Case taxonomy requires topics")
    if not isinstance(case.get("expectations"), dict):
        raise ValueError("Case requires explicit expectations")
    for key in ("local_values", "topics", "difficulty_levels", "new_topic_names"):
        if key not in case["expectations"]:
            raise ValueError(f"Case expectations require {key}")
    return deepcopy(case)


def pointer(value, path):
    """Resolve a JSON Pointer used for explicit, human-readable expectations."""
    if not path.startswith("/"):
        raise ValueError("Expectation paths must be JSON Pointers")
    for part in path[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def compare_result(case, stage, result):
    """Source facts and arithmetic are exact; judgment choices are enumerated."""
    exact, judgments = [], []
    extracted = result if stage == 1 else {
        "exam_year": result["year"],
        "questions": project_extraction_questions(result["questions"]),
    }
    frozen = case["frozen_stage1"]
    if extracted["exam_year"] != frozen["exam_year"]:
        exact.append("Sitting year changed")
    if [q["q_id"] for q in extracted["questions"]] != [q["q_id"] for q in frozen["questions"]]:
        exact.append("Question coverage or order changed")
    expected_questions = {q["q_id"]: q for q in frozen["questions"]}
    for question in extracted["questions"]:
        original = expected_questions.get(question["q_id"], {})
        for field in ("text", "marks", "format", "source_context"):
            if question.get(field) != original.get(field):
                exact.append(f"{question['q_id']}: exact {field} changed")
    if stage == 1:
        return exact, judgments
    expected = case["expectations"]
    for path, value in expected["local_values"].items():
        try:
            actual = pointer(result, path)
        except (KeyError, IndexError, TypeError):
            exact.append(f"Missing local value {path}")
        else:
            if actual != value:
                exact.append(f"{path}: expected {value!r}, got {actual!r}")
    by_id = {q["q_id"]: q for q in result["questions"]}
    if set(by_id) != set(expected["topics"]):
        judgments.append("Topic expectations must cover every question")
    for q_id, choices in expected["topics"].items():
        actual = sorted(by_id.get(q_id, {}).get("topics", []))
        if actual not in [sorted(choice) for choice in choices]:
            judgments.append(f"{q_id}: unaccepted topic assignment {actual!r}")
    if sorted(result["new_topic_names"]) not in [sorted(v) for v in expected["new_topic_names"]]:
        judgments.append("Unaccepted proposed topic names")
    actual_levels = {
        topic: {item["q_id"]: item["level"] for item in judgment["question_difficulty"]}
        for topic, judgment in result["topic_judgments"].items()
    }
    if set(actual_levels) != set(expected["difficulty_levels"]):
        judgments.append("Difficulty expectations must cover every tested topic")
    for topic, levels in actual_levels.items():
        choices = expected["difficulty_levels"].get(topic, {})
        if set(levels) != set(choices):
            judgments.append(f"{topic}: difficulty expectations must cover every tagged question")
        for q_id, level in levels.items():
            if level not in choices.get(q_id, []):
                judgments.append(f"{topic}/{q_id}: unaccepted difficulty level {level!r}")
    return exact, judgments


def evaluate_case(case, *, extraction_client=None, analysis_client=None,
                  client_factory=None, provider="gpt-subagent", model="unspecified",
                  generated_at=None, limits=None):
    """Exercise independent stages and a fresh chain; return all stage outcomes.

    The two injected clients are the same callables accepted by production.
    client_factory supplies independent transcript streams for exchange/replay.
    """
    case = validate_case(case)
    generated_at = generated_at or utc_now()
    limits = limits or RequestLimits()
    source = {"file_name": case["source_name"],
              "resolved_path": f"evaluation-case:{case['id']}",
              "sha256": hashlib.sha256(case["source_text"].encode("utf-8")).hexdigest(),
              "extraction": {"extraction_kind": "evaluation-source-text",
                             "character_count": len(case["source_text"]), "segments": [
                  {"label": "whole file", "page": None, "char_start": 0,
                   "char_end": len(case["source_text"]), "line_start": 1,
                   "line_count": case["source_text"].count("\n") + 1}]}}
    report = {"schema_version": 1, "record_kind": "staged-evaluation",
              **contract_metadata(), "case": case, "source_provenance": source,
              "provider": provider, "model": model, "generated_at": generated_at,
              "limits": asdict(limits), "human_review": {"status": "pending"}, "runs": {}}

    def run(name, stage_input):
        stage = RUNS[name]
        record = {"stage": stage, "input": deepcopy(stage_input), "calls": [],
                  "human_review": "pending", "generated_at": generated_at,
                  "provider": provider, "model": model, **contract_metadata()}
        report["runs"][name] = record
        delegate = (client_factory(name, stage) if client_factory else
                    extraction_client if stage == 1 else analysis_client)

        def capture(system, user, max_tokens):
            request = {"system": system, "user": user, "max_tokens": max_tokens}
            call = {"request_id": digest([name, len(record["calls"]), system, user, max_tokens]),
                    "request": request, "prompt_sha256": digest(request),
                    "provider": provider, "model": model, "generated_at": generated_at}
            record["calls"].append(call)
            try:
                call["response"] = delegate(system, user, max_tokens=max_tokens)
                return call["response"]
            except Exception as exc:
                call["error"] = str(exc)
                raise

        try:
            if stage == 1:
                questions, year = app.stage1_extract(stage_input, case["total_marks"],
                                                    client=capture, limits=limits)
                result = {"exam_year": year, "questions": questions}
            else:
                questions, year = validate_extraction(stage_input, app.EARLIEST_YEAR, 9999)
                analysis = app.stage2_tag_score(questions, deepcopy(case["taxonomy"]),
                                               case["total_marks"], client=capture, limits=limits)
                result = build_candidate_analysis(
                    exam_id=case["id"], year=year, year_label=None,
                    total_marks=case["total_marks"], analysis=analysis,
                    known_topics=case["taxonomy"]["topics"], source_provenance=source,
                    model_provenance={"provider": provider, "extraction_model": model,
                                      "analysis_model": model}, processed_at=generated_at)
                # Candidate compatibility shape omits proposals; keep them as evaluation evidence.
                result["new_topic_names"] = analysis["new_topic_names"]
                if project_extraction_questions(result["questions"]) != stage_input["questions"]:
                    raise ValueError("Stage 2 changed its frozen Stage 1 input")
            if isinstance(delegate, ReplayClient):
                delegate.finish()
            record["result"] = result
            exact, judgments = compare_result(case, stage, result)
            record.update(exact_failures=exact, judgment_failures=judgments,
                          status="failed" if exact or judgments else "passed")
        except PendingRequest:
            record["status"] = "pending"
        except Exception as exc:
            record.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        return record

    run("stage1", case["source_text"])
    run("stage2", case["frozen_stage1"])
    chain = run("chain_stage1", case["source_text"])
    # Keep a Stage 1 fact failure visible while exercising its validated output downstream.
    if "result" in chain:
        run("chain_stage2", chain["result"])
    else:
        report["runs"]["chain_stage2"] = {"stage": 2, "status": "skipped",
                                                   "reason": "chain_stage1 produced no validated result"}
    report["status"] = ("passed" if all(r["status"] == "passed" for r in report["runs"].values())
                        else "pending" if any(r["status"] == "pending" for r in report["runs"].values())
                        and not any(r["status"] == "failed" for r in report["runs"].values())
                        else "failed")
    return report


def review_digest(report):
    body = deepcopy(report)
    body.pop("human_review", None)
    return digest(body)


def require_approved(report):
    review = report.get("human_review", {})
    if (report.get("status") != "passed" or review.get("status") != "approved"
            or not review.get("reviewer") or not review.get("reviewed_at")
            or not review.get("notes") or review.get("content_sha256") != review_digest(report)):
        raise ValueError("A person must approve this exact passing capture before reference replay")


def replay(report, *, require_reference=True):
    """Evidence replay proves repeatability only; reference replay also needs approval."""
    if require_reference:
        require_approved(report)
    if (report.get("status") not in {"passed", "failed"}
            or any(r["status"] == "pending" for r in report["runs"].values())
            or any("response" not in call for r in report["runs"].values()
                   for call in r.get("calls", []))):
        raise ValueError("Replay requires a complete capture with model responses")
    if any(report.get(key) != value for key, value in contract_metadata().items()):
        raise ValueError("Evaluation contract changed; capture and review new evidence")
    result = evaluate_case(
        report["case"], client_factory=lambda name, stage: ReplayClient(report["runs"][name]["calls"]),
        provider=report["provider"], model=report["model"], generated_at=report["generated_at"],
        limits=RequestLimits(**report["limits"]))
    for name in RUNS:
        if result["runs"][name].get("result") != report["runs"][name].get("result"):
            result["runs"][name]["status"] = "failed"
            result["runs"][name]["replay_error"] = "Captured result changed during deterministic replay"
        elif result["runs"][name]["status"] != report["runs"][name]["status"]:
            result["runs"][name]["status"] = "failed"
            result["runs"][name]["replay_error"] = "Captured stage outcome changed during replay"
        elif any(result["runs"][name].get(field) != report["runs"][name].get(field)
                 for field in ("exact_failures", "judgment_failures", "error_type", "error")):
            result["runs"][name]["status"] = "failed"
            result["runs"][name]["replay_error"] = "Captured stage diagnostics changed during replay"
    if any(r["status"] != "passed" for r in result["runs"].values()):
        result["status"] = "failed"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    exchange = commands.add_parser("exchange", help="Export real prompts for GPT sub-agent responses")
    exchange.add_argument("case")
    exchange.add_argument("--answers", help="JSON object mapping request_id to raw response string")
    exchange.add_argument("--model", required=True)
    exchange.add_argument("--output", required=True)
    live = commands.add_parser("live", help="Explicitly send the case to the configured provider")
    live.add_argument("case")
    live.add_argument("--allow-live", action="store_true", required=True)
    live.add_argument("--model", required=True, help="Exact model ID, never a model alias chosen by this tool")
    live.add_argument("--provider", default="openai", choices=sorted(app.PROVIDERS))
    live.add_argument("--output", required=True)
    for name in ("replay", "audit"):
        command = commands.add_parser(name, help="Replay approved reference" if name == "replay" else
                                      "Replay unreviewed evidence for repeatability only")
        command.add_argument("capture")
        command.add_argument("--output", required=True)
    approve = commands.add_parser("approve", help="Human reviewer records approval of an exact capture")
    approve.add_argument("capture")
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--notes", required=True)
    approve.add_argument("--content-sha256", required=True)
    approve.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if Path(args.output).exists():
            raise FileExistsError(f"Evaluation output already exists: {args.output}")
        if args.command == "exchange":
            answers = read_json(args.answers) if args.answers else {}
            report = evaluate_case(read_json(args.case), model=args.model,
                                   client_factory=lambda name, stage: ExchangeClient(name, answers))
        elif args.command == "live":
            env = dict(os.environ, LLM_PROVIDER=args.provider,
                       LLM_MODEL_STAGE1=args.model, LLM_MODEL_STAGE2=args.model)
            clients = app.configure_model_clients(env)
            # Both stages use one explicit budget for this small prototype.
            limits = clients["extraction_client"].limits
            if limits != clients["analysis_client"].limits:
                raise ValueError("Use matching Stage 1 and Stage 2 request limits for this prototype")
            report = evaluate_case(read_json(args.case), **clients, provider=args.provider,
                                   model=args.model, limits=limits)
        else:
            captured = read_json(args.capture)
            if args.command == "approve":
                if captured.get("status") != "passed" or args.content_sha256 != review_digest(captured):
                    raise ValueError("Approval requires the content hash of a passing capture")
                if not args.reviewer.strip() or not args.notes.strip():
                    raise ValueError("Human reviewer and review notes must be nonempty")
                verified = replay(captured, require_reference=False)
                if verified["status"] != "passed":
                    raise ValueError("Capture no longer replays; review a fresh capture")
                report = deepcopy(captured)
                report["human_review"] = {"status": "approved", "reviewer": args.reviewer,
                    "reviewed_at": utc_now(), "notes": args.notes,
                    "content_sha256": review_digest(captured)}
            else:
                report = replay(captured, require_reference=args.command == "replay")
        write_new_json(args.output, report)
        print(json.dumps({"status": report["status"], "content_sha256": review_digest(report),
                          "stages": {k: v["status"] for k, v in report["runs"].items()}}))
        return 0 if report["status"] == "passed" else 3 if report["status"] == "pending" else 1
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Evaluation failed: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
