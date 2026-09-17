#!/usr/bin/env python3
"""
Exam ROI Pipeline
=================
Processes exam files through an LLM to extract topics, score ROI variables,
and produce a ranked Excel spreadsheet.

The MVP processing path has two model stages:
  1. extract the questions and marks from the paper;
  2. tag concepts and calculate the topic scores saved in the candidate.

The independent reviewer remains implemented for later work, but the MVP CLI
does not run it.

Formula: Priority = 100 × (Freq × G_Marks × Conn) / (Diff × Fmt)
  Freq    = fraction of exams where topic appeared  (0–1, computed)
  G_Marks = average mark fraction when present       (0–1, computed)
  Conn    = direct downstream usefulness             (1–3, qualitative estimate)
  Diff    = conceptual / reasoning complexity        (1–6, qualitative estimate)
  Fmt     = response-mode weight                     (1=MCQ · 2=short answer · 3=write code)

Setup:
  The pipeline loads a local .env file from the repository root. Values already
  present in the process environment take precedence.

  Pick a provider with the LLM_PROVIDER env var (default: anthropic).
  Supported out of the box: anthropic, deepseek, openai, openrouter and unorouter.
  share one OpenAI-compatible code path, so any other provider that speaks
  the same chat-completions API (Groq, local vLLM/Ollama, ...) works by
  adding one entry to the PROVIDERS dict below.

    LLM_PROVIDER=anthropic  pip install anthropic
                             export ANTHROPIC_API_KEY=sk-ant-...
    LLM_PROVIDER=deepseek   pip install openai
                             export DEEPSEEK_API_KEY=sk-...
    LLM_PROVIDER=openai     pip install openai
                             export OPENAI_API_KEY=sk-...
    LLM_PROVIDER=openrouter pip install openai
                             export OPENROUTER_API_KEY=sk-or-...
                             export LLM_MODEL_STAGE1=your-openrouter-model-id
                             export LLM_MODEL_STAGE2=your-openrouter-model-id
    LLM_PROVIDER=unorouter  pip install openai
                             export UNOROUTER_API_KEY=your-key
                             export LLM_MODEL_STAGE1=your-unorouter-model-id
                             export LLM_MODEL_STAGE2=your-unorouter-model-id

  (Windows CMD: use `set VAR=value` instead of `export VAR=value`.)
  Optionally override the models: LLM_MODEL_STAGE1 / LLM_MODEL_STAGE2.
  Models that support it also accept LLM_REASONING_EFFORT_STAGE1 / STAGE2.
  OpenRouter and UnoRouter require both model variables, using exact catalog IDs.

Usage:
  python pipeline.py COURSE_FOLDER COMMAND [data]

  COURSE_FOLDER always comes first, and is the only place the pipeline reads or
  writes state: it is created on first use and updated in place on every run
  after that. One folder = one exam's worth of state; nothing is shared between
  folders.

  python pipeline.py Exams/Historia add-exam exam_2023.pdf
  python pipeline.py Exams/Historia add-exam                 # every exam file in the folder
  python pipeline.py Exams/Historia add-exam papers/ --recursive
  python pipeline.py Exams/Historia add-exam exam_2023.pdf --year 2023 --total-marks 120
  python pipeline.py Exams/Historia add-exam exam_2024.txt --force   # reprocess existing
  python pipeline.py Exams/Historia rebuild                  # rebuild outputs only
  python pipeline.py Exams/Historia status                   # show current state
  python pipeline.py Exams/Historia edit-topic "Big-O Notation" --diff 2 --conn 3

Exam files the pipeline can read:
  .txt   plain text, encoded as UTF-8 (a byte-order mark is fine). Any other
         encoding is reported and refused rather than patched over, because a
         replaced character is a hole in the paper nobody sees.
  .pdf   a PDF with a text layer. No page is rendered and no OCR is run, so a
         scanned paper has to be OCRed first (e.g. `ocrmypdf in.pdf out.pdf`).

  A paper is refused before any AI call when it holds no text, when it is not
  valid UTF-8, or when any of its pages has no text layer — reading on would
  silently drop those questions. The check only asks whether a page produced any
  text: garbled, partial or out-of-order extraction still gets through, so skim
  a converted paper before trusting its analysis.

  The extracted text is sent to the configured provider (LLM_PROVIDER above) to
  be analysed. Nothing else in the file is uploaded, and the file itself stays
  on disk.

File layout — everything lives in COURSE_FOLDER:
    COURSE_FOLDER/
    taxonomy.json                    canonical topic list with Diff and Conn per topic
    parsed/                          one JSON file per accepted exam (audit trail)
    candidates/                      validated analyses awaiting acceptance/review
    Exam_ROI_Pipeline.xlsx           ranked output, formatted (overwritten on each rebuild)
    Exam_ROI_Pipeline.json           same ranked output, flat JSON (overwritten on each rebuild) —
                                      the one to point an LLM or a script at

  Exam files may sit in COURSE_FOLDER itself, in its exams/ subfolder, or anywhere
  else add-exam is pointed at — see docs/adr/0006-course-folder-as-cli-argument.md.

Several papers per year (models, sittings, resits) are the normal case: each gets its
own record, its own columns, and a label made from whatever its filename does not share
with the others ("2022 Lunes", "2022 Martes"). The year is read from the filename, else
from the paper, else from Stage 1 — and an academic year like "2021-2022" means the
paper was sat in 2022. See docs/adr/0007-one-record-per-paper-and-the-sitting-year.md.
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path

from exam_roi.inputs import (
    ExtractionError, InputSelectionError, collect_exam_files, extract_exam_text,
)
from exam_roi.storage import CoursePaths, CourseStore, StorageError
from exam_roi.taxonomy import aggregate_taxonomy
from exam_roi.identity import ExamIdentityError, exam_record_path, validate_exam_id
from exam_roi.review import review_candidate, MAX_CORRECTIONS
from exam_roi.llm import (
    ModelClient, ModelConfigurationError, RequestLimits, RequestLimitError, TruncatedResponse, configured_model_client,
    estimate_tokens, run_batches,
    text_from_anthropic as _text_from_anthropic,
    text_from_openai as _text_from_openai,
)
from exam_roi.question_context import (
    source_questions, related_source_units, retain_source_context, question_evidence,
)
from exam_roi.reports import exam_labels, weighted_fmt, write_json, write_xlsx
from exam_roi.scoring import aggregate_paper_scores, build_ranked_report
from exam_roi.evaluation import (
    CONTRACT_TEXT, LEGACY_VERSION, CandidateValidationError, build_candidate_analysis,
    contract_metadata, difficulty_version, finalize_candidate_analysis,
    project_extraction_questions,
    tag_evidence, validate_extraction, validate_tags,
    validate_topic_scores, validate_connection_review, CONTRACT_VERSION,
)

# ── CLI outcomes and exit codes ─────────────────────────────────────────────────
# Per ADR 0008, outcome rendering and exit-code selection live only here in the CLI
# layer; process_exam_file and friends return one of the outcomes below or raise a
# defined failure, never sys.exit and never print a verdict of their own.
#
# Exit codes, so a script (or a person reading $?/$LASTEXITCODE) can tell these
# apart without parsing text:
#   0  every requested unit of work succeeded. Skips and no-op rebuilds count as
#      success — they did what was asked, which was nothing.
#   1  a setup/usage problem stopped the command before any of the work ran (bad
#      arguments, an unreadable course folder, missing provider credentials, an
#      unknown topic name, ...). This is the existing sys.exit("ERROR: ...") path.
#      (argparse's own usage errors — an unknown flag, a bad choice — keep their
#      own exit code 2; both mean "nothing ran", just from different code.)
#   3  at least one requested paper failed to process. Papers that did succeed
#      keep their saved candidates; this code means "partial", not "crashed".
#   4  the ranked outputs (.xlsx/.json) could not be written. Parsed papers and
#      taxonomy already on disk are unaffected; rerunning rebuild once the cause
#      (e.g. the spreadsheet is open elsewhere) is cleared is the whole fix.
#   5  course state is locked, corrupt, incompatible, or needs commit recovery.
#      Follow the named record/lock diagnostic before retrying; this is separate
#      from an export failure and --force never bypasses it.
EXIT_OK             = 0
EXIT_SETUP_ERROR    = 1
EXIT_PAPER_FAILURE  = 3
EXIT_EXPORT_FAILURE = 4
EXIT_STATE_FAILURE  = 5

# Keep the independent-review implementation available for later work without
# exposing a third model stage in the MVP command path.
MVP_INDEPENDENT_REVIEW_ENABLED = False


class ExamOutcome(Enum):
    """What happened to one paper requested on an add-exam run.

    Only outcomes the pipeline can actually produce today are represented — see
    docs/adr/0008 and ticket 15: there is no promotion-to-accepted step yet, and
    no candidate is ever silently discarded, so neither state exists here.
    """
    SAVED                 = "saved"                  # new candidate saved; nothing flagged
    SAVED_PENDING_REVIEW  = "saved_pending_review"    # new candidate saved; a person should check it
    SKIPPED_ACCEPTED      = "skipped_accepted"        # parsed/<id>.json already exists — nothing to do
    SKIPPED_CANDIDATE     = "skipped_candidate"       # candidates/<id>.json already exists — use --force


class RecoveryKind(Enum):
    """What kind of action, if any, would move a failed paper or a failed export forward."""
    NONE             = "none"               # already in a final, acceptable state
    INPUT_CORRECTION = "input_correction"   # the source file itself needs fixing, then a rerun
    REVIEW           = "review"             # a person needs to read the saved candidate
    REPROCESSING     = "reprocessing"       # rerun add-exam after a transient processing failure
    EXAM_ID          = "exam_id"            # automatic filename IDs collided
    MODEL_CONFIGURATION = "model_configuration"  # model or request budget must change
    REBUILD          = "rebuild"            # papers are fine; rerun rebuild once possible

    @property
    def instruction(self):
        return {
            RecoveryKind.NONE:             "nothing to do",
            RecoveryKind.INPUT_CORRECTION: "fix the input file, then rerun add-exam",
            RecoveryKind.REVIEW:           "read the saved candidate — a person needs to review it before it can be accepted",
            RecoveryKind.REPROCESSING:     "rerun add-exam after resolving the problem",
            RecoveryKind.EXAM_ID:          "choose a distinct --exam-id, then rerun add-exam",
            RecoveryKind.MODEL_CONFIGURATION: "adjust the model or LLM request-limit configuration, then rerun add-exam",
            RecoveryKind.REBUILD:          "rerun rebuild once the cause above is fixed",
        }[self]


class PaperFailure:
    """One requested paper that add-exam could not save this run.

    Never raised itself — built by the CLI from whatever defined failure
    process_exam_file let through, so the batch summary and the exit code have a
    single place to read every failure from.
    """
    __slots__ = ("path", "recovery", "reason")

    def __init__(self, path, recovery, reason):
        self.path = path
        self.recovery = recovery
        self.reason = reason


def _classify_paper_failure(path, exc) -> PaperFailure:
    """Turn one processing exception into a PaperFailure with a matching recovery kind.

    ExtractionError and CandidateValidationError already carry the information a
    reusable module is expected to raise (see ADR 0008). Explicit identity and
    request-budget failures need their own remedy; other processing failures can
    be retried normally without suggesting --force.
    """
    if isinstance(exc, ExtractionError):
        return PaperFailure(path, RecoveryKind.INPUT_CORRECTION, f"{exc.reason} {exc.remedy}")
    if isinstance(exc, CandidateValidationError):
        # needs_review means the model's own output was too ambiguous to resolve
        # automatically (a person has to look); correction_required means the
        # output was simply wrong against the contract, worth retrying.
        recovery = (RecoveryKind.REVIEW if exc.disposition == "needs_review"
                    else RecoveryKind.REPROCESSING)
        return PaperFailure(path, recovery,
                            f"analysis rejected ({exc.disposition.replace('_', ' ')}): {exc.reason}")
    if isinstance(exc, ExamIdentityError) and "All automatic IDs" in str(exc):
        return PaperFailure(path, RecoveryKind.EXAM_ID, f"{type(exc).__name__}: {exc}")
    if isinstance(exc, (ModelConfigurationError, RequestLimitError, TruncatedResponse)):
        return PaperFailure(path, RecoveryKind.MODEL_CONFIGURATION,
                            f"{type(exc).__name__}: {exc}")
    return PaperFailure(path, RecoveryKind.REPROCESSING, f"{type(exc).__name__}: {exc}")


def load_dotenv(path: Path) -> None:
    """Load simple KEY=VALUE entries without overriding the process environment."""
    if not path.exists():
        return

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"Invalid .env entry on line {line_number}: expected KEY=VALUE")

        key, value = (part.strip() for part in line.split("=", 1))
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ValueError(f"Invalid .env variable name on line {line_number}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


DOTENV_FILE = Path(__file__).resolve().parent.parent / ".env"
def setup_course_folder(folder: Path) -> CoursePaths:
    """Prepare and return this course's destinations without selecting global state."""
    course = CoursePaths(folder)
    if course.folder.exists() and not course.folder.is_dir():
        raise ValueError(f"COURSE_FOLDER is not a folder: {folder}")
    if not course.folder.exists():
        course.folder.mkdir(parents=True)
        print(f"\n📂 Created course folder: {folder}")
    else:
        print(f"\n📂 Course folder: {folder}")
    return course


# ── LLM provider configuration ────────────────────────────────────────────────
# The pipeline only needs two things from an LLM: a (system, user) prompt in,
# plain text out, with an explicit signal when a reply was cut off by the
# token limit. That contract is implemented once per SDK family in call_llm()
# below. "deepseek" and "openai" share the same "openai" SDK family because
# both expose an OpenAI-compatible chat-completions endpoint — swapping
# between them, or adding a new OpenAI-compatible provider, needs no code
# changes, just a new PROVIDERS entry (or none, for another OpenAI-compatible
# host — see base_url).
PROVIDERS = {
    "unorouter": {
        "sdk":             "openai",
        "key_env":         "UNOROUTER_API_KEY",
        "key_env_aliases": ("OPENROUTER_API_KEY",),
        "base_url":        "https://api.unorouter.com/v1",
        "default_stage1":  None,
        "default_stage2":  None,
    },
    "openrouter": {
        "sdk":             "openai",
        "key_env":         "OPENROUTER_API_KEY",
        "base_url":        "https://openrouter.ai/api/v1",
        "default_stage1":  None,
        "default_stage2":  None,
    },
    "anthropic": {
        "sdk":             "anthropic",
        "key_env":         "ANTHROPIC_API_KEY",
        "base_url":        None,
        "default_stage1":  "claude-haiku-4-5-20251001",
        "default_stage2":  "claude-sonnet-5",
    },
    "deepseek": {
        "sdk":             "openai",
        "key_env":         "DEEPSEEK_API_KEY",
        "base_url":        "https://api.deepseek.com",
        "default_stage1":  "deepseek-chat",
        "default_stage2":  "deepseek-chat",
    },
    "openai": {
        "sdk":             "openai",
        "key_env":         "OPENAI_API_KEY",
        "base_url":        None,
        "default_stage1":  "gpt-4o-mini",
        "default_stage2":  "gpt-4o",
    },
}

MODEL_REQUEST_LIMITS = {
    ("unorouter", "glm-5.3-flash"): RequestLimits(1_000_000, 128_000, 1024),
    ("unorouter", "glm-5.3"): RequestLimits(1_000_000, 128_000, 1024),
}


def configure_model_clients(env, *, review=False, progress=None):
    """Build each command's clients from its startup environment snapshot."""
    provider = env.get("LLM_PROVIDER", "anthropic").lower()
    if provider not in PROVIDERS:
        raise ModelConfigurationError(
            f"Unknown LLM_PROVIDER '{provider}'. Choose from: {', '.join(PROVIDERS)}")
    models = [env.get(f"LLM_MODEL_STAGE{stage}", PROVIDERS[provider][f"default_stage{stage}"])
              for stage in (1, 2)]
    if any(not model or not model.strip() for model in models):
        raise ModelConfigurationError(
            f"Set LLM_MODEL_STAGE1 and LLM_MODEL_STAGE2 to exact {provider} model IDs before reading exams.")

    def request_limits(model, stage):
        defaults = MODEL_REQUEST_LIMITS.get((provider, model))
        return RequestLimits.from_env(env, stage, defaults)

    try:
        result = {
            name: configured_model_client(provider, model, request_limits(model, stage),
                                          providers=PROVIDERS, env=env,
                                          reasoning_effort=env.get(
                                              f"LLM_REASONING_EFFORT_STAGE{stage}"),
                                          progress=progress)
            for name, model, stage in zip(("extraction_client", "analysis_client"), models, (1, 2))
        }
    except ModelConfigurationError:
        raise
    except ValueError as exc:
        raise ModelConfigurationError(f"Invalid LLM request-limit configuration: {exc}") from exc
    if review:
        result.update(configure_reviewer(env, provider, progress=progress))
    return result


def _print_llm_settings(clients):
    """Print effective non-secret model settings for a live analysis run."""
    print("\nLLM settings:")
    for stage, name in ((1, "extraction_client"), (2, "analysis_client")):
        client = clients[name]
        limits = client.limits
        provider = client.provider or f"{client.sdk}-compatible"
        print(
            f"   Stage {stage}: provider={provider}, model={client.model}, "
            f"context={limits.context_tokens:,}, max_output={limits.output_tokens:,}, "
            f"overhead={limits.overhead_tokens:,} tokens, "
            f"reasoning={client.reasoning_effort or 'provider-default'}"
        )


def configure_reviewer(env, analyzer_provider, *, progress=None):
    """Keep reviewer setup failures in the existing saved-review failure path."""
    provider = env.get("LLM_REVIEW_PROVIDER", analyzer_provider).lower()
    model = env.get("LLM_REVIEW_MODEL")
    try:
        limits = RequestLimits(
            context_tokens=int(env.get("LLM_REVIEW_CONTEXT_TOKENS", 128000)),
            output_tokens=int(env.get("LLM_REVIEW_MAX_OUTPUT_TOKENS", 32000)),
            overhead_tokens=int(env.get("LLM_REVIEW_OVERHEAD_TOKENS", 1024)))
        if not model or not model.strip():
            raise ModelConfigurationError("Set LLM_REVIEW_MODEL to an exact reviewer model ID")
        client = configured_model_client(
            provider, model, limits, providers=PROVIDERS, env=env,
            reasoning_effort=env.get("LLM_REVIEW_REASONING_EFFORT"),
            progress=progress)
    except ValueError as exc:
        limits = None
        def client(system, user, max_tokens, error=exc):
            raise error
    return {"reviewer_client": client, "reviewer_limits": limits,
            "reviewer_provider": provider, "reviewer_model": model}


def _stage_request(stage, client=None, limits=None):
    if isinstance(client, ModelClient):
        if limits is not None and limits != client.limits:
            raise ValueError("Injected limits must match the ModelClient limits")
        return client, client.limits
    if client is None:
        raise ModelConfigurationError(f"Supply a client for analysis stage {stage}")
    return client, limits or RequestLimits()


# ── File helpers ───────────────────────────────────────────────────────────────

def load_taxonomy(course: CoursePaths) -> dict:
    with CourseStore(course) as store:
        return store.load().taxonomy

def save_taxonomy(tax: dict, course: CoursePaths):
    with CourseStore(course) as store:
        store.commit(taxonomy=tax)

def load_all_exams(course: CoursePaths) -> dict:
    """Return {exam_id: exam_dict} for every file in parsed/."""
    with CourseStore(course) as store:
        return store.load().papers

EARLIEST_YEAR = 1990


def _year_candidates(text: str) -> list:
    """
    Every plausible exam year in a string, in the order they appear.

    An academic year is written as a range ("2021-2022", "Curso 2021/22") and the
    paper is sat in its later half, so a range resolves to the second year — taking
    the first number would date every EVAU paper a year early. A pair of years that
    are not one apart is not an academic year, so only the first is taken.
    """
    out = []
    pattern = r"(?<!\d)(?P<a>(?:19|20)\d{2})(?!\d)(?:\s*[-/_–]\s*(?P<b>\d{2,4})(?!\d))?"
    for m in re.finditer(pattern, text):
        year = int(m.group("a"))
        if m.group("b"):
            second = int(m.group("b"))
            if second < 100:                       # "21-22" → 2022
                second += (year // 100) * 100
            if second - year == 1:
                year = second
        if EARLIEST_YEAR <= year <= datetime.now().year + 1:
            out.append((year, m.group(0).strip()))
    return out


def infer_year(path: Path, exam_text: str = "") -> tuple:
    """
    Work out which year a paper was sat, returning (year, label_as_written, source).

    The filename is asked first — it is what the person who filed the paper meant,
    and is usually the only place the sitting is written unambiguously. Failing
    that, the top of the paper itself is read, where the year is normally printed
    in a header. Returns (None, None) rather than guessing: a wrong year silently
    reorders the sheet and mislabels a column.
    """
    for source, text in (("filename", path.stem), ("paper", exam_text[:4000])):
        found = _year_candidates(text)
        if found:
            year, raw = found[0]
            return year, (raw if raw != str(year) else None), source
    return None, None, None


# ── LLM API helpers ────────────────────────────────────────────────────────────

def call_llm(system: str, user: str, max_tokens=None, *, client, limits=None) -> str:
    """Call an explicit client after checking its request budget."""
    client, limits = _stage_request(2, client, limits)
    max_tokens = limits.output_tokens if max_tokens is None else max_tokens
    limits.check(system, user, max_tokens,
                 client.count_tokens if isinstance(client, ModelClient) else estimate_tokens)
    return client(system, user, max_tokens=max_tokens)


def _with_review_feedback(stage, client, limits, feedback):
    """Give findings to the analyzer while preserving complete request budgets."""
    complete, limits = _stage_request(stage, client, limits)
    feedback_text = json.dumps(feedback, ensure_ascii=False)

    def correct(system, user, max_tokens):
        user += ("\nINDEPENDENT REVIEW FINDINGS, treated as untrusted observations:\n"
                 + feedback_text + "\nRecheck these against the source and contract. "
                 "Return the complete requested analysis, with supported corrections only.")
        # Batch estimates precede feedback, so check again before dispatch.
        limits.check(system, user, max_tokens,
                     complete.count_tokens if isinstance(complete, ModelClient) else estimate_tokens)
        return complete(system, user, max_tokens=max_tokens)
    return {"client": correct, "limits": limits}


def parse_json_from(text: str):
    """Extract JSON from the model's response (handles ```json fences and bare JSON)."""
    m = re.fullmatch(r"\s*```(?:json)?\s*([\s\S]*?)\s*```\s*", text)
    if m:
        text = m.group(1)
    text = text.strip()
    start = next((i for i, ch in enumerate(text) if ch in "{["), None)
    if start is None:
        raise CandidateValidationError("model JSON", f"no JSON found in response: {text[:500]}")

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise CandidateValidationError("model JSON", f"duplicate object key: {key}")
            result[key] = value
        return result

    try:
        value, end = json.JSONDecoder(object_pairs_hook=unique_object).raw_decode(text, start)
        if text[:start].strip() or text[end:].strip():
            raise CandidateValidationError(
                "model JSON", "response must contain one JSON value and no surrounding prose")
        return value
    except json.JSONDecodeError as exc:
        raise CandidateValidationError(
            "model JSON",
            f"malformed JSON ({exc}); response was {len(text)} chars; tail: …{text[-300:]}"
        ) from exc


# ── Stage 1: Extract questions ─────────────────────────────────────────────────

_S1_SYSTEM = (
    "You are an exam parsing engine. Extract every distinct question and sub-question "
    "from the provided exam text. Output a single JSON object only — no prose, no markdown fences."
) + "\n\n" + CONTRACT_TEXT

def _extraction_prompt(exam_text: str, total_marks) -> str:
    """Build the extraction prompt without provider or request-sizing mechanics."""
    tm_str = str(total_marks) if total_marks else "unknown — sum from questions if possible"
    user = (
        f"Total exam marks: {tm_str}\n\n"
        "Output one JSON object with exactly these two keys:\n\n"
        '  "exam_year" : the calendar year this paper was SAT, as an integer, or null if\n'
        '                the paper does not say. An academic year written as a range\n'
        '                ("2021-2022", "Curso 2021/22") is sat in the later year: 2022.\n\n'
        '  "questions" : every distinct question and sub-question, each as an object:\n'
        '      "q_id"   : unique label e.g. "Q1", "Q2a", "Q3b"\n'
        '      "text"   : complete verbatim task text, including all choices and constraints\n'
        '      "marks"  : integer point value, or null if not stated\n'
        '      "format" : exactly one of these strings:\n'
        '                   "mcq"                  — multiple choice / true-false / matching\n'
        '                   "short_answer"         — define / fill-in / short explanation\n'
        '                   "explain_derive"       — explain concept / trace code / derive formula\n'
        '                   "write_code_or_proof"  — write code, proof, or design from scratch\n\n'
        "Keep printed question numbers as Q1, Q2, etc.; preserve subpart suffixes "
        "such as Q2a. Never restart numbering in a batch. Include parent instructions "
        "and shared passages needed to answer each subquestion.\n"
        "Output only that JSON object. No other text.\n\n"
        f"EXAM TEXT:\n{exam_text}"
    )
    return user


def stage1_extract(exam_text: str, total_marks, *, client=None, limits=None) -> tuple:
    """Extract complete source units, then validate identity and coverage on merge."""
    client, limits = _stage_request(1, client, limits)
    prefix, units = source_questions(exam_text)
    questions, years = [], set()

    def prompt(batch):
        user = _extraction_prompt(prefix + "".join(unit.text for unit in batch), total_marks)
        related = [unit for unit in related_source_units(batch, units) if unit not in batch]
        if related:
            user += ("\n\nSUPPORTING SOURCE CONTEXT ONLY, do not extract these questions. "
                     "Extract only these target IDs and their subparts: "
                     + ", ".join(unit.q_id for unit in batch) + "\n"
                     + "".join(unit.text for unit in related))
        return user

    def consume(raw, batch):
        extracted, year = validate_extraction(parse_json_from(raw), EARLIEST_YEAR,
                                               datetime.now().year + 1)
        retain_source_context(extracted, batch, prefix, units)
        questions.extend(extracted)
        if year is not None:
            years.add(year)

    run_batches(units, prompt, consume, system=_S1_SYSTEM, client=client, limits=limits,
                output_estimate=lambda batch: estimate_tokens(prefix + "".join(u.text for u in batch))
                                              + 256 * len(batch),
                label="question extraction")
    if len(years) > 1:
        raise CandidateValidationError("question extraction", "Conflicting sitting years across batches")
    return validate_extraction({"exam_year": next(iter(years), None), "questions": questions},
                               EARLIEST_YEAR, datetime.now().year + 1)


# ── Stage 2: Tag topics and score parameters ───────────────────────────────────

_S2_SYSTEM = (
    "You are an academic curriculum analyst. You tag exam questions from any subject with "
    "canonical topic labels and estimate qualitative parameters for relative priority. Output valid JSON "
    "only — no markdown, no prose outside the JSON."
) + "\n\n" + CONTRACT_TEXT

_S2A_TEMPLATE = """\
CANONICAL TOPIC TAXONOMY
(Reuse these labels. Only propose a NEW label if the concept is genuinely absent.)
{taxonomy_list}

QUESTIONS (batch {batch_no} of {batch_count}):
{questions_json}

YOUR TASK
Assign 1–2 canonical topic labels to every question.
Read the complete text and source_context before judging. Focus on q_id's task;
shared instructions and sibling subparts provide context. Quote either source field.
Reuse existing taxonomy labels wherever possible.
Merge near-synonyms (e.g. "pointers" and "pointer arithmetic" → one canonical label).
Only invent a new label when the concept is genuinely absent from the taxonomy.

For each q_id, cite a short exact quote, explain why the labels fit, and list any
uncertainties. Do not repeat the full question text.

OUTPUT exactly this JSON structure (no extra keys, no prose):
{{
  "tags": {{
    "Q1": {{
      "topics": ["Label A"],
      "quote": "short exact source excerpt",
      "rationale": "Why this excerpt supports the label.",
      "uncertainties": []
    }}
  }},
  "new_topic_names": ["New Label 1"]
}}"""

_S2B_TEMPLATE = """\
EXISTING TAXONOMY (for canonical references only)
{taxonomy_list}

TOPICS TESTED IN THIS PAPER (score existing topics again as well as new ones)
{new_topics}

INFER BACKGROUND KNOWLEDGE FROM THE EXAM
No manual course prerequisites or syllabus are supplied. Infer only the background
knowledge supported by the source questions, for each topic. Record it in
assumed_prerequisites and support each assumption with prerequisite_evidence:
prerequisite, q_id, exact quote, and a brief rationale. These are estimates, not
source facts. Use empty lists when no additional background assumption is needed.
Do not assume the reasoning being tested is already solved. Note uncertainty about
course context; use null level only when it prevents a defensible difficulty judgment.

COURSE BASELINE
Apply the contract's exam-inferred background rule to the complete source evidence
below. source_context contains original instructions and passages, including text
across page boundaries. Focus on the task identified by q_id; sibling subparts
are context, not additional tasks to score. Cite text or source_context verbatim.

SOURCE QUESTIONS (full text and tags; cite q_id and a short verbatim quote)
{questions_json}

Apply the evaluation contract in the system message. For each listed topic judge
every question tagged with it. Supply question levels; Python computes topic Diff.
Do not infer difficulty from response mode or scoring instructions in the text.
Conn must match the number of supported direct downstream labels in unlocks.
For Conn=1 cite the assessed task and explain the absence of supported edges.
Use only existing or new canonical labels for prerequisites and unlocks.
For every dependency, supply connection_edges with prerequisite, dependent, q_id,
quote, and rationale. Direction: prerequisite -> dependent. Cite the task that
needs this dependency. Include links from known topics even if they are not directly
tested here: a new topic can show that an older topic supports it. Repeated words or
co-occurrence alone do not prove dependency. Report only this paper's evidence;
Python combines evidence across papers and preserves human overrides.
Record uncertainty explicitly; do not fabricate a resolved level under ambiguity.

OUTPUT exactly this JSON structure (no extra keys, no prose):
{{
  "Topic Name": {{
    "question_difficulty": [{{
      "q_id": "Q1", "level": 3, "quote": "verbatim source excerpt",
      "rationale": "Reasoning required and why this level fits.", "uncertainties": []
    }}],
    "difficulty_rationale": "How the questions represent the topic.",
    "assumed_prerequisites": [],
    "prerequisite_evidence": [],
    "Conn": 1,
    "connection_rationale": "No direct downstream use supported in this paper.",
    "connection_evidence": [{{"q_id": "Q1", "quote": "verbatim source excerpt"}}],
    "connection_edges": [],
    "unlocks": [], "prerequisites": [], "uncertainties": []
  }}
}}"""


def _fmt_taxonomy(topic_names: list) -> str:
    """One label per line — a JSON array of bare strings pays for quotes, commas
    and indentation on every label, in every batch prompt."""
    if not topic_names:
        return "(empty — taxonomy has no labels yet; propose all new topic labels)"
    return "\n".join(f"- {n}" for n in sorted(topic_names))


def _stage2_tag(questions: list, topic_names: list, *, client=None, limits=None) -> tuple:
    """Tag full evidence in size-aware batches, preserving exact ID coverage."""
    client, limits = _stage_request(2, client, limits)
    tags, new_names = {}, []
    active_batch = []

    def prompt(batch):
        nonlocal active_batch
        active_batch = batch
        return _S2A_TEMPLATE.format(
            taxonomy_list=_fmt_taxonomy(list(topic_names) + new_names),
            batch_no=1, batch_count=1,
            questions_json=json.dumps(question_evidence(batch), ensure_ascii=False))

    def call_with_one_correction(system, user, max_tokens):
        raw = client(system, user, max_tokens=max_tokens)
        try:
            validate_tags(
                parse_json_from(raw), active_batch, list(topic_names) + new_names)
        except CandidateValidationError as exc:
            if exc.disposition != "correction_required":
                raise
            print(
                "   ↻ Stage 2 validation: response rejected; "
                f"correction attempt 1/1 ({exc.reason})")
            corrected_user = (
                user
                + "\n\nDETERMINISTIC VALIDATION FAILURE:\n"
                + exc.reason
                + "\nReturn the complete corrected JSON for every question in this batch. "
                  "Copy every evidence quote as an exact contiguous substring of that "
                  "question's supplied source text. Do not return commentary or a partial patch."
            )
            limits.check(
                system, corrected_user, max_tokens,
                client.count_tokens if isinstance(client, ModelClient) else estimate_tokens)
            return client(system, corrected_user, max_tokens=max_tokens)
        return raw

    def consume(raw, batch):
        batch_tags, names = validate_tags(parse_json_from(raw), batch, list(topic_names) + new_names)
        if set(tags) & set(batch_tags):
            raise CandidateValidationError("topic tagging", "Duplicate question IDs across batches")
        tags.update(batch_tags)
        new_names.extend(name for name in names if name not in new_names)

    run_batches(questions, prompt, consume, system=_S2_SYSTEM,
                client=call_with_one_correction, limits=limits,
                output_estimate=lambda batch: 512 * len(batch), label="topic tagging")
    return validate_tags({"tags": tags, "new_topic_names": new_names}, questions, topic_names)


def _merge_topic_parts(parts):
    """Combine evidence, then derive Conn from the union of supported edges."""
    merged = {}
    for part in parts:
        for key, value in part.items():
            if isinstance(value, list):
                target = merged.setdefault(key, [])
                for item in value:
                    if item not in target:
                        target.append(item)
            elif key != "Conn":
                previous = merged.get(key, "")
                merged[key] = previous + ("\n" if previous else "") + value
    merged["Conn"] = 1 if not merged["unlocks"] else 2 if len(merged["unlocks"]) <= 2 else 3
    return merged


def _stage2_score_topics(tested_topic_names: list, taxonomy_list: str, questions: list,
                         allowed_topics: list, *, client=None, limits=None) -> dict:
    """Batch topics and, when necessary, their questions without dropping evidence."""
    if not tested_topic_names:
        return {}
    client, limits = _stage_request(2, client, limits)
    scores = {}

    def prompt(names, evidence):
        return _S2B_TEMPLATE.format(
            taxonomy_list=_fmt_taxonomy(allowed_topics),
            new_topics="\n".join(f"- {name}" for name in names),
            questions_json=json.dumps(question_evidence(evidence), ensure_ascii=False))

    def validate(raw, names, evidence):
        data = parse_json_from(raw)
        try:
            validate_topic_scores(data, names, evidence, allowed_topics)
        except CandidateValidationError:
            raise
        except ValueError as exc:
            raise CandidateValidationError("topic scoring", str(exc)) from exc
        return data

    def score_group(names):
        evidence = [q for q in questions if set(names).intersection(q["topics"])]
        if len(names) == 1:
            parts = []
            run_batches(evidence, lambda batch: prompt(names, batch),
                        lambda raw, batch: parts.append(validate(raw, names, batch)[names[0]]),
                        system=_S2_SYSTEM, client=client, limits=limits,
                        output_estimate=lambda batch: 1024 + 512 * len(batch), label="topic scoring")
            scores[names[0]] = _merge_topic_parts(parts)
            return
        user = prompt(names, evidence)
        try:
            limits.check(_S2_SYSTEM, user, limits.output_tokens,
                         client.count_tokens if isinstance(client, ModelClient) else estimate_tokens)
            if 1024 * len(names) + 512 * sum(len(set(names).intersection(q["topics"])) for q in evidence) > limits.output_tokens:
                raise RequestLimitError("Estimated topic output is too large")
        except RequestLimitError:
            pass
        else:
            try:
                raw = client(_S2_SYSTEM, user, max_tokens=limits.output_tokens)
            except TruncatedResponse:
                pass
            else:
                scores.update(validate(raw, names, evidence))
                return
        middle = len(names) // 2
        score_group(names[:middle])
        score_group(names[middle:])

    score_group(tested_topic_names)
    try:
        return validate_topic_scores(scores, tested_topic_names, questions, allowed_topics)
    except CandidateValidationError:
        raise
    except ValueError as exc:
        raise CandidateValidationError("topic scoring", str(exc)) from exc


def refresh_connections(paper, topic_names, *, client, limits=None):
    """Revisit an earlier paper with the expanded vocabulary; keep original judgments."""
    user = (
        "REVIEW DEPENDENCIES IN THIS STORED PAPER\n"
        "The taxonomy has grown. Reconsider all dependencies against these canonical labels:\n"
        + _fmt_taxonomy(topic_names)
        + "\nReturn JSON {\"edges\": [{\"prerequisite\": \"label\", \"dependent\": \"label\", "
        "\"q_id\": \"Q1\", \"quote\": \"exact excerpt\", \"rationale\": \"why required\"}]}. "
        "Use an empty edges list when none are supported. Include every supported direct edge, "
        "including those previously known. Cite this paper's questions only. At least one endpoint "
        "must be tested in the cited question. Co-occurrence alone is not a dependency. "
        "Do not assign difficulty or modify original observations.\nSOURCE QUESTIONS:\n"
        + json.dumps(question_evidence(paper["questions"]), ensure_ascii=False)
    )
    return validate_connection_review(parse_json_from(call_llm(_S2_SYSTEM, user, client=client, limits=limits)),
                                      paper["questions"], topic_names)


def stage2_tag_score(questions: list, taxonomy: dict, total_marks: float, *, client=None, limits=None) -> dict:
    """
    Tag every question with topics and build the per-topic score table.

    The LLM is asked only for judgement calls (which topic, how hard, how connected).
    All arithmetic — marks_total, mark_fraction, format_distribution — is computed
    locally. Model output is reserved for qualitative judgments and their evidence;
    all model requests preserve source context and respect configured limits.
    """
    questions, _ = validate_extraction(
        {"exam_year": None, "questions": project_extraction_questions(questions)},
        EARLIEST_YEAR, datetime.now().year + 1)
    topic_names   = sorted(taxonomy["topics"].keys())
    taxonomy_list = _fmt_taxonomy(topic_names)

    dependencies = {"client": client, "limits": limits} if client is not None or limits is not None else {}
    tags, proposed_new = _stage2_tag(questions, topic_names, **dependencies)

    tagged = [
        {**q, "topics": tags[q["q_id"]]["topics"],
         "topic_tagging": tag_evidence(tags[q["q_id"]])}
        for q in questions
    ]

    # Any label absent from the taxonomy is new, whether or not the model flagged it
    seen_topics = {t for q in tagged for t in q["topics"]}
    new_names   = [t for t in proposed_new if t in seen_topics and t not in taxonomy["topics"]]
    new_names  += [t for t in sorted(seen_topics)
                   if t not in taxonomy["topics"] and t not in new_names]

    paper_scores = _stage2_score_topics(sorted(seen_topics), taxonomy_list, tagged,
                                  topic_names + new_names, **dependencies)

    return aggregate_paper_scores(
        questions=questions,
        assignments=tags,
        topic_scores=paper_scores,
        total_marks=total_marks,
        known_topic_names=topic_names,
        proposed_new_topic_names=proposed_new,
    )


# ── Commands ───────────────────────────────────────────────────────────────────

def resolve_exam_id(path: Path, explicit_id=None, *, course: CoursePaths, _store=None) -> str:
    """
    The id under which this paper is filed in candidates/ or parsed/ — unique per
    paper, not per filename.

    Papers are often filed one folder per year, and the models within a year carry
    the same names in each ("modelo_A.pdf" in 2022/ and in 2023/). Keyed on the
    filename alone the second one would look like the first, already parsed, and be
    skipped — losing an exam silently. So an id already taken by a paper at a
    different path is qualified with the folder the paper came from.
    """
    if explicit_id is not None:
        return validate_exam_id(explicit_id)
    if _store is None:
        with CourseStore(course) as store:
            return resolve_exam_id(path, course=course, _store=store)
    base = validate_exam_id(path.stem.replace(" ", "_"))
    here = str(path.resolve())
    candidates = [base]
    for depth, parent in enumerate(path.resolve().parents):
        folder = parent.name.replace(" ", "_")
        candidate = f"{folder}_{base}" if folder else f"{base}_{depth + 2}"
        if candidate not in candidates:
            candidates.append(candidate)
    for candidate in candidates:
        existing = [exam_record_path(course.folder, state, candidate)
                    for state in ("parsed", "candidates")]
        existing = [record_path for record_path in existing if record_path.exists()]
        if not existing:
            return candidate
        claimed_paths = []
        for record_path in existing:
            record = _store.load_record(record_path.parent.name, candidate)
            claimed = (record.get("source_provenance", {}).get("resolved_path")
                       or record.get("source_path"))
            claimed_paths.append(claimed)
        if all(claimed is None or claimed == here for claimed in claimed_paths):
            return candidate          # same paper, or a legacy record without a source path
    raise ExamIdentityError(
        f"All automatic IDs for {path.name!r} are already used by other papers. "
        "Choose a distinct --exam-id; --force does not bypass automatic collisions.")


def _model_provenance(extraction_client, analysis_client):
    def identity(client):
        if client is None:
            return None, None
        if isinstance(client, ModelClient):
            return client.provider or f"{client.sdk}-compatible", client.model
        return "injected-callable", "injected-callable"

    extraction_provider, extraction_model = identity(extraction_client)
    analysis_provider, analysis_model = identity(analysis_client)
    record = {"provider": extraction_provider if extraction_provider == analysis_provider else "mixed",
              "extraction_model": extraction_model, "analysis_model": analysis_model}
    if extraction_provider != analysis_provider:
        record.update(extraction_provider=extraction_provider, analysis_provider=analysis_provider)
    return record


def process_exam_file(path: Path, year=None, total_marks=None, exam_id=None, force=False, *,
                      course: CoursePaths, extraction_client=None, analysis_client=None,
                      extraction_limits=None, analysis_limits=None,
                      review_enabled=False, reviewer_client=None, reviewer_limits=None,
                      max_corrections=0, reviewer_provider=None, reviewer_model=None,
                      _store=None) -> ExamOutcome:
    """
    Parse one exam, validate it, and save a candidate without changing accepted
    papers or taxonomy.

    Returns an ExamOutcome — SKIPPED_ACCEPTED/SKIPPED_CANDIDATE when an existing
    record meant nothing was reprocessed, SAVED/SAVED_PENDING_REVIEW when a new
    candidate was written. This is a reusable path (see docs/adr/0008): it never
    calls sys.exit and never decides an exit code — it raises ExtractionError,
    CandidateValidationError, ExamIdentityError or another defined failure, and
    the CLI (cmd_add_exam) turns that into the batch's reported outcome.
    """
    if _store is None:
        with CourseStore(course) as store:
            return process_exam_file(
                path, year, total_marks, exam_id, force, course=course,
                extraction_client=extraction_client, analysis_client=analysis_client,
                extraction_limits=extraction_limits, analysis_limits=analysis_limits,
                review_enabled=review_enabled, reviewer_client=reviewer_client,
                reviewer_limits=reviewer_limits, max_corrections=max_corrections,
                reviewer_provider=reviewer_provider, reviewer_model=reviewer_model, _store=store)
    if not path.exists():
        # Vanished between selection and processing (or a caller-supplied path
        # that never existed) — an input problem, not a model or export one.
        raise ExtractionError(
            "missing_file", f"{path} does not exist.",
            "Check the path and rerun add-exam, or remove it from the request.",
        )

    exam_id = resolve_exam_id(path, exam_id, course=course, _store=_store)
    accepted_file = exam_record_path(course.folder, "parsed", exam_id)
    candidate_file = exam_record_path(course.folder, "candidates", exam_id)
    snapshot = _store.load()
    accepted_file.parent.mkdir(exist_ok=True)
    candidate_file.parent.mkdir(exist_ok=True)

    if (accepted_file.exists() or candidate_file.exists()) and not force:
        if accepted_file.exists():
            print(f"   ⏭  Skipping {path.name} — parsed/{exam_id}.json is already accepted (use --force to reprocess)")
            return ExamOutcome.SKIPPED_ACCEPTED
        print(f"   ⏭  Skipping {path.name} — candidates/{exam_id}.json already exists (use --force to reprocess)")
        return ExamOutcome.SKIPPED_CANDIDATE

    print(f"\n📄 Exam : {path.name}")
    source_bytes = path.read_bytes()
    # Raises before Stage 1, so a paper the pipeline cannot fully read is never
    # sent to the provider and never half-analysed — see ticket 04.
    extraction = extract_exam_text(path, source_bytes)
    exam_text = extraction.text
    provider = _model_provenance(extraction_client, analysis_client)["provider"]
    print(f"   → {extraction.summary()} — sent to {provider or 'the supplied client'} for analysis")

    requested_year, requested_marks = year, total_marks

    def make_candidate(_previous=None, feedback=None):
        year, total_marks = requested_year, requested_marks
        year_label, source = None, "--year"
        if not year:
            year, year_label, found_in = infer_year(path, exam_text)
            source = f"from the {found_in}" if found_in else None

        # ── Stage 1 ──
        print("🤖 Stage 1 : Extracting questions…")
        extraction_dependencies = ({"client": extraction_client, "limits": extraction_limits}
            if extraction_client is not None or extraction_limits is not None else {})
        if feedback is not None:
            extraction_dependencies = _with_review_feedback(
                1, extraction_client, extraction_limits, feedback)
        questions, year_from_model = stage1_extract(exam_text, total_marks, **extraction_dependencies)
        print(f"   → {len(questions)} questions extracted")

        if not year and year_from_model:
            year, source = year_from_model, "from the paper, via the model"
        if year:
            print(f"   → Year : {year_label or year}  ({source})")
        else:
            print(
                f"   ⚠  No year found in the filename or the paper — filed without one. "
                f"Re-run with --year <YYYY> to set it."
            )

        if not total_marks:
            marks_vals  = [q["marks"] for q in questions if isinstance(q.get("marks"), (int, float))]
            total_marks = sum(marks_vals) if marks_vals else 100
            print(f"   → Total marks : {total_marks} (summed from questions)")

        # ── Stage 2 ──
        taxonomy = snapshot.taxonomy
        print("🤖 Stage 2 : Tagging topics and scoring parameters…")
        analysis_dependencies = ({"client": analysis_client, "limits": analysis_limits}
            if analysis_client is not None or analysis_limits is not None else {})
        if feedback is not None:
            analysis_dependencies = _with_review_feedback(
                2, analysis_client, analysis_limits, feedback)
        result = stage2_tag_score(questions, taxonomy, total_marks, **analysis_dependencies)
        per_topic = result.get("per_topic", {})
        new_names = result.get("new_topic_names", [])
        print(f"   → {len(per_topic)} topics tagged  ({len(new_names)} new)")
        if new_names:
            print(f"   ⚠  New topics : {', '.join(new_names)}")
            print("      Review proposed_taxonomy_changes in the saved candidate.")

        # Build the candidate and its proposed taxonomy completely in memory. Invalid
        # model output raises before accepted paper or taxonomy files are touched.
        candidate = build_candidate_analysis(
            exam_id=exam_id,
            year=year,
            year_label=year_label,      # academic year as written, e.g. "2021-2022"
            total_marks=total_marks,
            analysis=result,
            known_topics=sorted(taxonomy["topics"]),
            source_provenance={
                "file_name": path.name,
                "resolved_path": str(path.resolve()),
                "sha256": hashlib.sha256(source_bytes).hexdigest(),
                # Page and offset references for later evidence checks: where in the
                # source each piece of the analysed text came from.
                "extraction": extraction.provenance(),
            },
            model_provenance=_model_provenance(extraction_client, analysis_client),
            processed_at=datetime.now().isoformat(),
        )
        # Model work can take minutes. Check both boundaries again before reading
        # accepted records or saving a candidate, including forced reprocessing.
        exam_record_path(course.folder, "parsed", exam_id, expected_path=accepted_file)
        exam_record_path(course.folder, "candidates", exam_id, expected_path=candidate_file)
        accepted_exams = _store.load().papers
        proposed_exams = dict(accepted_exams)
        proposed_exams[exam_id] = candidate  # A forced reparse replaces this paper's contribution.
        proposed_taxonomy = aggregate_taxonomy(taxonomy, proposed_exams)
        candidate = finalize_candidate_analysis(
            candidate, proposed_taxonomy, taxonomy.get("topics", {}))
        return candidate

    candidate = make_candidate()
    candidate, review = review_candidate(
        candidate, exam_text, enabled=review_enabled, client=reviewer_client,
        limits=reviewer_limits, provider=reviewer_provider,
        model=reviewer_model, correct=make_candidate, max_corrections=max_corrections)
    candidate["independent_review"] = review
    if review["disposition"] == "needs_review":
        candidate["candidate_status"] = "needs-review"
    if review_enabled:
        print(f"   Independent review: {review['disposition']}"
              f" ({review.get('reason', 'evidence checks completed')})")
    candidate_file = exam_record_path(course.folder, "candidates", exam_id, expected_path=candidate_file)
    _store.commit(candidates={exam_id: candidate})
    print(f"   ✓ Saved candidate → candidates/{exam_id}.json")
    print("     Accepted papers and taxonomy were not changed.")
    if candidate.get("candidate_status") == "needs-review":
        print("     Status: pending review — a person should check this candidate before it is accepted.")
        return ExamOutcome.SAVED_PENDING_REVIEW
    return ExamOutcome.SAVED


def cmd_add_exam(args, course: CoursePaths, *, _store=None, **clients):
    if _store is None and not getattr(args, "dry_run", False):
        with CourseStore(course) as store:
            return cmd_add_exam(args, course, _store=store, **clients)
    if getattr(args, "review_corrections", 0) and not getattr(args, "review", False):
        raise ValueError("--review-corrections requires --review")
    try:
        files = collect_exam_files(course.folder, args.paths, args.recursive)
    except InputSelectionError as exc:
        raise ValueError(str(exc)) from exc

    # --year and --exam-id describe one specific paper; silently applying either to
    # a whole batch would stamp every exam with the same year, or overwrite one
    # parsed file repeatedly under the same id.
    if len(files) > 1 and (args.year or args.exam_id):
        raise ValueError(
            f"--year/--exam-id describe a single exam, but {len(files)} files matched.\n"
            f"       Name one file, or drop the flag (each paper's year is read from its "
            f"filename or its own text)."
        )

    print(f"\nSelected {len(files)} paper(s):")
    for path in files:
        print(f"  {path}")
    if getattr(args, "dry_run", False):
        print("Dry run complete. No papers were processed.")
        return EXIT_OK

    # Tally every outcome ExamOutcome can name, plus every failure the CLI turns
    # a raised exception into, so the summary below can differentiate all of
    # them instead of collapsing to a single processed/skipped/failed count.
    counts = {outcome: 0 for outcome in ExamOutcome}
    failures: list[PaperFailure] = []
    for path in files:
        try:
            outcome = process_exam_file(
                path,
                course=course,
                _store=_store,
                **clients,
                year=args.year,
                total_marks=args.total_marks,
                exam_id=args.exam_id,
                force=args.force,
                review_enabled=getattr(args, "review", False),
                max_corrections=getattr(args, "review_corrections", 0),
            )
            counts[outcome] += 1
        except (ModelConfigurationError, StorageError):
            raise
        except Exception as exc:
            failure = _classify_paper_failure(path, exc)
            print(f"   ✗ Not saved — {failure.reason}")
            print(f"      Recovery: {failure.recovery.instruction}")
            failures.append(failure)

    saved          = counts[ExamOutcome.SAVED]
    pending_review = counts[ExamOutcome.SAVED_PENDING_REVIEW]
    processed      = saved + pending_review
    skipped_accepted  = counts[ExamOutcome.SKIPPED_ACCEPTED]
    skipped_candidate = counts[ExamOutcome.SKIPPED_CANDIDATE]
    skipped        = skipped_accepted + skipped_candidate

    if len(files) > 1 or failures:
        print(
            f"\n📦 {processed} processed ({pending_review} pending review) · "
            f"{skipped} skipped ({skipped_accepted} already accepted, "
            f"{skipped_candidate} already a candidate) · {len(failures)} failed"
        )
        if failures:
            print(f"   Failed files: {', '.join(f.path.name for f in failures)}")

    # The summary sentence is what "did this run work?" boils down to for a
    # person or a script skimming the last line, so it must never claim success
    # (or silently omit) a batch where every requested paper failed — ticket 15.
    if failures and processed:
        print(f"   {processed} candidate(s) saved despite {len(failures)} failure(s) — "
              "accepted outputs are unchanged. See the recovery notes above for what to fix.")
    elif failures and skipped:
        print(f"   {skipped} requested paper(s) were skipped because they already have records; "
              f"{len(failures)} failure(s) need attention. No new candidates were saved. "
              "See the recovery notes above.")
    elif failures:
        print(f"   All {len(failures)} requested paper(s) failed — nothing was added; "
              "outputs left unchanged. See the recovery notes above.")
    elif processed:
        review_note = f" ({pending_review} pending review)" if pending_review else ""
        print(f"   {processed} candidate(s) await acceptance or review{review_note}; "
              "accepted outputs are unchanged.")
    else:
        print("   Nothing new to add — outputs left unchanged (use --force to reprocess).")

    return EXIT_PAPER_FAILURE if failures else EXIT_OK


def cmd_rebuild(_args, course: CoursePaths, *, _store=None):
    if _store is None:
        with CourseStore(course) as store:
            return cmd_rebuild(_args, course, _store=store)
    print("\n📊 Rebuilding spreadsheet…")
    snapshot = _store.load()
    taxonomy, all_exams = snapshot.taxonomy, snapshot.papers
    updated_taxonomy = aggregate_taxonomy(taxonomy, all_exams)
    if updated_taxonomy != taxonomy:
        _store.commit(taxonomy=updated_taxonomy)
    taxonomy = updated_taxonomy

    if not all_exams:
        print("   No accepted exams found. Candidate analyses do not enter reports until accepted.")
        return EXIT_OK

    labels = exam_labels(list(all_exams.values()))
    report = build_ranked_report(all_exams, taxonomy, exam_labels_by_id=labels)
    rows = report.rows
    exam_list = report.exam_list
    n_exams = len(exam_list)
    tier1_n = report.tier1_count

    # Parsed papers and taxonomy are already safely on disk at this point — only
    # the write below can still fail (a locked file, a full disk, a missing
    # openpyxl install), so it gets its own outcome rather than an uncaught
    # traceback standing in for "rebuild failed".
    try:
        write_xlsx(rows, exam_list, taxonomy, course.output_xlsx)
        write_json(rows, course.output_json)
    except Exception as exc:
        print(f"   ✗ Export failed — {type(exc).__name__}: {exc}")
        print("     Parsed papers and taxonomy on disk are unchanged. "
              f"Recovery: {RecoveryKind.REBUILD.instruction}.")
        return EXIT_EXPORT_FAILURE

    print(f"   ✓ {course.output_xlsx.name}, {course.output_json.name}  ({len(rows)} topics · {n_exams} exams · {tier1_n} Tier 1)")
    return EXIT_OK


def cmd_status(_args, course: CoursePaths):
    with CourseStore(course) as store:
        snapshot = store.load()
    taxonomy, all_exams = snapshot.taxonomy, snapshot.papers
    print("\n📚 Exam ROI Pipeline")
    print(f"   Taxonomy    : {len(taxonomy['topics'])} topics")
    exam_list = sorted(all_exams.values(), key=lambda e: (e.get("year") or 0, e["exam_id"]))
    years     = {e.get("year") for e in exam_list if e.get("year")}
    undated   = sum(1 for e in exam_list if not e.get("year"))
    spread    = f" across {len(years)} year(s)" if years else ""
    print(f"   Parsed exams: {len(exam_list)}{spread}"
          f"{f' · {undated} with no year' if undated else ''}")
    labels = exam_labels(exam_list)
    for exam in exam_list:
        n = len(exam.get("per_topic", {}))
        print(f"     {labels[exam['exam_id']]:<18} {exam['exam_id']}"
              f"  ({n} topics · {exam.get('total_marks', '?')} marks)")
    print(f"   Spreadsheet : {'✓ exists' if course.output_xlsx.exists() else 'not created yet'}")
    print(f"   Ranked JSON : {'✓ exists' if course.output_json.exists() else 'not created yet'}")
    print()
    return EXIT_OK


def cmd_edit_topic(args, course: CoursePaths, *, _store=None):
    if _store is None:
        with CourseStore(course) as store:
            return cmd_edit_topic(args, course, _store=store)
    taxonomy = _store.load().taxonomy
    name     = args.name
    if name not in taxonomy["topics"]:
        known = sorted(taxonomy["topics"].keys())
        raise ValueError(
            f"Topic not found: '{name}'\n"
            f"Known topics: {', '.join(known) if known else '(none yet)'}"
        )
    changed = False
    if args.diff is not None:
        if not 1 <= args.diff <= 6:
            raise ValueError("Diff must be 1–6")
        _record_override(taxonomy["topics"][name], "Diff", args.diff)
        changed = True
    if args.conn is not None:
        if not 1 <= args.conn <= 3:
            raise ValueError("Conn must be 1–3")
        _record_override(taxonomy["topics"][name], "Conn", args.conn)
        changed = True
    if not changed:
        print("Nothing changed — pass --diff or --conn (or both).")
        return EXIT_OK
    _store.commit(taxonomy=taxonomy)
    if args.diff is not None:
        print(f"   Set Diff={args.diff} for '{name}'")
    if args.conn is not None:
        print(f"   Set Conn={args.conn} for '{name}'")
    # edit-topic's own exit status has to reflect a failed rebuild too — an
    # override that saved correctly but could not be exported is not a success.
    return cmd_rebuild(None, course, _store=_store)


def _record_override(topic, field, value):
    previous_version = (difficulty_version(topic) if field == "Diff" else
                        topic.get("evaluation_contract_version", LEGACY_VERSION))
    topic.setdefault("human_overrides", {})[field] = {
        "value": value, "previous_value": topic.get(field),
        "previous_contract_version": previous_version,
        "source": "edit-topic", "updated_at": datetime.now().isoformat(),
        **contract_metadata(),
    }
    topic[field] = value


# ── Entry point ────────────────────────────────────────────────────────────────

COMMANDS = ("add-exam", "rebuild", "status", "edit-topic")

# Deliberately ASCII-only: this screen is the first thing a new user sees, and it has
# to survive a terminal in any codepage.
HELP = """\
Exam ROI Pipeline - ranks a course's topics by relative study priority.

USAGE
  python pipeline.py COURSE_FOLDER COMMAND [data]

  COURSE_FOLDER is one folder per exam, holding its past papers. Name it on every
  command. It is created if new, and every file the pipeline writes goes in it.

COMMANDS
  add-exam [FILE|FOLDER ...]  Read past papers and save validated candidate analyses.
                              No argument: reads .txt/.pdf in COURSE_FOLDER and exams/.
                              --dry-run lists selected paths without AI calls.
  status                      Show what the folder holds so far.
  rebuild                     Redo the ranking from papers already read (no AI calls).
  edit-topic TOPIC            Correct a topic's scores by hand, then rebuild.

EXAMPLES
  python pipeline.py Exams/History add-exam exam_2023.pdf
  python pipeline.py Exams/History add-exam
  python pipeline.py Exams/History status
  python pipeline.py Exams/History edit-topic "Cold War" --diff 4 --conn 3

EXAM FILES
  .txt papers must be UTF-8; .pdf papers must have a text layer (nothing is
  rendered and no OCR is run - OCR a scanned paper first, e.g. ocrmypdf).
  A paper with no text, with a bad encoding, or with any page missing its text
  layer is refused before any AI call, so nothing is analysed half-read. The
  check only asks whether a page produced text: garbled or partial extraction
  still gets through, so skim a converted paper before trusting it.
  The text that is extracted is sent to the configured provider to be analysed.

RESULTS, written into COURSE_FOLDER
  Exam_ROI_Pipeline.xlsx   the ranked topics, formatted
  Exam_ROI_Pipeline.json   the same ranking, for a script or an LLM to read
  taxonomy.json            each topic's difficulty and connection - edit to correct
  parsed/                  one JSON per accepted paper
  candidates/              validated analyses and proposed taxonomy changes

BEFORE THE FIRST RUN
  pip install -r requirements.txt
  set ANTHROPIC_API_KEY=sk-ant-...     (Windows;  export ANTHROPIC_API_KEY=... elsewhere)

  Reading exams costs AI calls, so the pipeline needs a key. Another provider:
  set LLM_PROVIDER to deepseek, openai, openrouter or unorouter and supply its key.
  For OpenRouter (PowerShell):
  $env:LLM_PROVIDER = "openrouter"
  $env:OPENROUTER_API_KEY = "your-key"
  $env:LLM_MODEL_STAGE1 = "your-openrouter-model-id"
  $env:LLM_MODEL_STAGE2 = "your-openrouter-model-id"

Every option of a command:  python pipeline.py COURSE_FOLDER add-exam --help
"""


class BriefHelpParser(argparse.ArgumentParser):
    """
    Prints HELP above instead of argparse's generated layout.

    argparse leads with a bracketed usage line and an options table; what someone
    running this for the first time needs is the command shape, the four commands,
    and the two lines of setup without which the first run cannot work at all.
    Per-command --help keeps the generated layout, where exhaustive is the point.
    """

    def format_help(self):
        return HELP


def _exam_id_argument(value):
    try:
        return validate_exam_id(value)
    except ExamIdentityError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    p = BriefHelpParser(
        prog="pipeline.py",
        usage="pipeline.py COURSE_FOLDER COMMAND [data]",
    )
    p.add_argument(
        "course_folder",
        type=Path,
        metavar="COURSE_FOLDER",
        help="Folder holding this exam's papers and results (created if it does not exist)",
    )
    # parser_class: without it the subcommands inherit BriefHelpParser, and
    # `add-exam --help` would reprint the top-level screen instead of its options.
    sub = p.add_subparsers(dest="cmd", metavar="COMMAND",
                           parser_class=argparse.ArgumentParser)

    pa = sub.add_parser(
        "add-exam",
        help="Validate exam papers and save candidate analyses",
        description=(
            "Supported input: UTF-8 .txt (a UTF-8 byte-order mark is accepted), or .pdf "
            "with a text layer. Scanned PDFs are unsupported in the MVP; OCR is not included. "
            "Every PDF page must yield some text; this does not detect garbled, partial, or "
            "out-of-order extraction. Extracted text is sent to the configured provider for analysis."
        ),
    )
    pa.add_argument("paths", nargs="*", type=Path, metavar="PATH",
                    help="Exam file(s) or folder(s): UTF-8 .txt, or .pdf with a text layer "
                         "(default: papers in both COURSE_FOLDER and its exams/ subfolder; "
                         "relative paths prefer the working directory, then COURSE_FOLDER)")
    pa.add_argument("--year",        type=int,            help="Year this paper was sat (read from the filename or the paper itself if omitted)")
    pa.add_argument("--total-marks", type=float,          help="Total marks (summed from questions if omitted)")
    pa.add_argument("--exam-id", type=_exam_id_argument,
                    help="Custom filename ID, not a path (defaults to the filename with spaces replaced by underscores)")
    pa.add_argument("--force",       action="store_true", help="Reprocess papers with a candidate or accepted record")
    pa.add_argument("--review", action="store_true",
                    help="Unavailable in the MVP; independent review is retained for later work")
    pa.add_argument("--review-corrections", type=int, choices=range(MAX_CORRECTIONS + 1), default=0,
                    help="Unavailable in the MVP; retained for the later independent-review stage")
    pa.add_argument("--recursive", action="store_true",
                    help="Search subfolders; excludes course candidates/ and parsed/ state")
    pa.add_argument("--dry-run", action="store_true",
                    help="List selected resolved .txt/.pdf paths and stop before processing")

    sub.add_parser("rebuild", help="Rebuild the spreadsheet and JSON from the papers already parsed")
    sub.add_parser("status",  help="Show what this course folder currently holds")

    pe = sub.add_parser("edit-topic", help="Override the AI's scores for one topic and rebuild")
    pe.add_argument("name",             metavar="TOPIC", help="Exact topic name (case-sensitive)")
    pe.add_argument("--diff", type=int, help="Override difficulty (Diff, 1–6)")
    pe.add_argument("--conn", type=int, help="Override connection (Conn, 1–3)")

    # The course folder comes first, so a bare command in that slot would otherwise
    # be read as a folder name and fail with a confusing "invalid choice" further on.
    if len(sys.argv) > 1 and sys.argv[1] in COMMANDS:
        sys.exit(
            f"ERROR: the course folder comes first:\n"
            f"       python pipeline.py COURSE_FOLDER {' '.join(sys.argv[1:])}\n"
            f"       e.g. python pipeline.py Exams/History {' '.join(sys.argv[1:])}"
        )
    if len(sys.argv) == 1:
        p.print_help()
        return EXIT_OK

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        print(f"\nERROR: which command? Pick one of: {', '.join(COMMANDS)}")
        return EXIT_SETUP_ERROR

    if (args.cmd == "add-exam" and not MVP_INDEPENDENT_REVIEW_ENABLED
            and (args.review or args.review_corrections)):
        print(
            "ERROR: Independent review is outside the MVP. "
            "Run add-exam without --review or --review-corrections; "
            "the command will stop after Stage 2 and save the candidate.",
            file=sys.stderr,
        )
        return EXIT_SETUP_ERROR

    dispatch = {
        "add-exam":   cmd_add_exam,
        "rebuild":    cmd_rebuild,
        "status":     cmd_status,
        "edit-topic": cmd_edit_topic,
    }
    # Every dispatched command returns one of the EXIT_* codes above; this is the
    # one place that turns that into the process's actual exit status.
    try:
        clients = {}
        if args.cmd == "add-exam" and not args.dry_run:
            load_dotenv(DOTENV_FILE)
            clients = configure_model_clients(
                dict(os.environ), review=args.review, progress=print)
            _print_llm_settings(clients)
        course = setup_course_folder(args.course_folder)
        return dispatch[args.cmd](args, course, **clients)
    except StorageError as exc:
        print(f"ERROR: Course state unavailable: {exc}", file=sys.stderr)
        return EXIT_STATE_FAILURE
    except ModelConfigurationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"Recovery: {RecoveryKind.MODEL_CONFIGURATION.instruction}.", file=sys.stderr)
        return EXIT_SETUP_ERROR
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_SETUP_ERROR


if __name__ == "__main__":
    sys.exit(main())
