#!/usr/bin/env python3
"""
Exam ROI Pipeline
=================
Processes exam files through an LLM to extract topics, score ROI variables,
and produce a ranked Excel spreadsheet.

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
import functools
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
from exam_roi.taxonomy import aggregate_taxonomy
from exam_roi.identity import ExamIdentityError, exam_record_path, validate_exam_id
from exam_roi.review import review_candidate, MAX_CORRECTIONS
from exam_roi.llm import (
    ModelClient, RequestLimits, RequestLimitError, TruncatedResponse, configured_model_client,
    estimate_tokens, run_batches,
    text_from_anthropic as _text_from_anthropic,
    text_from_openai as _text_from_openai,
)
from exam_roi.question_context import (
    source_questions, related_source_units, retain_source_context, question_evidence,
)
from exam_roi.reports import exam_labels, weighted_fmt, write_json, write_xlsx
from exam_roi.evaluation import (
    CONTRACT_TEXT, LEGACY_VERSION, CandidateValidationError, build_candidate_analysis,
    contract_metadata, difficulty_version, finalize_candidate_analysis,
    project_extraction_questions,
    tag_evidence, validate_extraction, validate_tags,
    validate_topic_scores, validate_connection_review, CONTRACT_VERSION,
)

# Windows consoles default to a legacy codepage, which turns every arrow, tick and
# em dash in the run log into "?". errors="replace" is the last-resort net for a
# terminal that still cannot encode something.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


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
EXIT_OK             = 0
EXIT_SETUP_ERROR    = 1
EXIT_PAPER_FAILURE  = 3
EXIT_EXPORT_FAILURE = 4


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
    REPROCESSING     = "reprocessing"       # rerun add-exam (typically with --force)
    REBUILD          = "rebuild"            # papers are fine; rerun rebuild once possible

    @property
    def instruction(self):
        return {
            RecoveryKind.NONE:             "nothing to do",
            RecoveryKind.INPUT_CORRECTION: "fix the input file, then rerun add-exam",
            RecoveryKind.REVIEW:           "read the saved candidate — a person needs to review it before it can be accepted",
            RecoveryKind.REPROCESSING:     "rerun add-exam (--force to reprocess)",
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
    reusable module is expected to raise (see ADR 0008); everything else (a model
    or network problem, a limits/identity error, ...) gets the same reprocessing
    guidance a transient failure needs.
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
            sys.exit(f"ERROR: Invalid .env entry on line {line_number}: expected KEY=VALUE")

        key, value = (part.strip() for part in line.split("=", 1))
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            sys.exit(f"ERROR: Invalid .env variable name on line {line_number}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


DOTENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(DOTENV_FILE)

# ── Configuration ──────────────────────────────────────────────────────────────
# All set by setup_course_folder() in main() from the COURSE_FOLDER argument,
# before any command runs — see docs/adr/0006-course-folder-as-cli-argument.md.
COURSE_FOLDER = None
TAXONOMY_FILE = None
PARSED_DIR    = None
CANDIDATES_DIR = None
OUTPUT_XLSX   = None
OUTPUT_JSON   = None


def setup_course_folder(folder: Path):
    """
    Point every output path at COURSE_FOLDER, creating the folder if it is new.

    This is the pipeline's whole notion of "where am I working": one folder, named
    explicitly on every command, holding one exam's taxonomy, parsed papers and
    ranked output. An empty (or missing) folder gets those files created on the
    first run; a folder that already has them gets them updated in place.
    """
    global COURSE_FOLDER, TAXONOMY_FILE, PARSED_DIR, CANDIDATES_DIR, OUTPUT_XLSX, OUTPUT_JSON

    if folder.exists() and not folder.is_dir():
        sys.exit(f"ERROR: COURSE_FOLDER is not a folder: {folder}")
    if not folder.exists():
        folder.mkdir(parents=True)
        print(f"\n📂 Created course folder: {folder}")
    else:
        print(f"\n📂 Course folder: {folder}")

    COURSE_FOLDER = folder
    TAXONOMY_FILE = folder / "taxonomy.json"
    PARSED_DIR    = folder / "parsed"
    CANDIDATES_DIR = folder / "candidates"
    OUTPUT_XLSX   = folder / "Exam_ROI_Pipeline.xlsx"
    OUTPUT_JSON   = folder / "Exam_ROI_Pipeline.json"


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

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()
if LLM_PROVIDER not in PROVIDERS:
    sys.exit(
        f"ERROR: Unknown LLM_PROVIDER '{LLM_PROVIDER}'. "
        f"Choose from: {', '.join(PROVIDERS)}"
    )
_PROVIDER = PROVIDERS[LLM_PROVIDER]

MODEL_STAGE1 = os.environ.get("LLM_MODEL_STAGE1", _PROVIDER["default_stage1"])
MODEL_STAGE2 = os.environ.get("LLM_MODEL_STAGE2", _PROVIDER["default_stage2"])
MAX_RETRIES  = 3

# Limits are configured per stage at the call boundary. They are deployment
# settings, not assertions about any provider's current model catalog.
def _stage_request(stage, client=None, limits=None):
    if isinstance(client, ModelClient):
        if limits is not None and limits != client.limits:
            raise ValueError("Injected limits must match the ModelClient limits")
        return client, client.limits
    limits = limits or RequestLimits.from_env(os.environ, stage)
    if client is not None:
        return client, limits
    model = MODEL_STAGE1 if stage == 1 else MODEL_STAGE2

    def complete(system, user, max_tokens):
        return call_llm(system, user, max_tokens=max_tokens, model=model, limits=limits)
    return complete, limits


# ── File helpers ───────────────────────────────────────────────────────────────

def load_taxonomy() -> dict:
    if TAXONOMY_FILE.exists():
        return json.loads(TAXONOMY_FILE.read_text(encoding="utf-8-sig"))
    return {"topics": {}}

def save_taxonomy(tax: dict):
    TAXONOMY_FILE.write_text(json.dumps(tax, indent=2, ensure_ascii=False), encoding='utf-8')

def load_all_exams() -> dict:
    """Return {exam_id: exam_dict} for every file in parsed/."""
    if not PARSED_DIR.exists():
        return {}
    return {
        f.stem: json.loads(f.read_text(encoding="utf-8"))
        for f in sorted(PARSED_DIR.glob("*.json"))
    }

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

@functools.lru_cache(maxsize=1)
def _client():
    if LLM_PROVIDER in {"openrouter", "unorouter"} and (
        not MODEL_STAGE1 or not MODEL_STAGE1.strip()
        or not MODEL_STAGE2 or not MODEL_STAGE2.strip()
    ):
        sys.exit(
            "ERROR: Set LLM_MODEL_STAGE1 and LLM_MODEL_STAGE2 to exact "
            f"{LLM_PROVIDER} model IDs before reading exams."
        )
    key_names = (_PROVIDER["key_env"], *_PROVIDER.get("key_env_aliases", ()))
    key = next((os.environ.get(name) for name in key_names if os.environ.get(name)), None)
    if not key:
        # The one setup step that can only fail at runtime, so it explains itself in
        # full here rather than relying on --help having been read first.
        sys.exit(
            f"ERROR: {_PROVIDER['key_env']} is not set, and reading exams needs AI calls.\n"
            f"       set {_PROVIDER['key_env']}=...       (Windows)\n"
            f"       export {_PROVIDER['key_env']}=...    (macOS/Linux)\n"
            f"       Provider is '{LLM_PROVIDER}' — set LLM_PROVIDER to "
            f"{' or '.join(k for k in PROVIDERS if k != LLM_PROVIDER)} to use another."
        )
    if _PROVIDER["sdk"] == "anthropic":
        try:
            import anthropic
        except ImportError:
            sys.exit("ERROR: Install the Anthropic SDK:  pip install anthropic")
        return anthropic.Anthropic(api_key=key)
    else:  # "openai" SDK family — covers any OpenAI-compatible endpoint
        try:
            import openai
        except ImportError:
            sys.exit("ERROR: Install the OpenAI SDK:  pip install openai")
        kwargs = {"api_key": key}
        if _PROVIDER["base_url"]:
            kwargs["base_url"] = _PROVIDER["base_url"]
        return openai.OpenAI(**kwargs)


def call_llm(system: str, user: str, max_tokens=None, model=None, *, limits=None) -> str:
    """CLI adapter; reusable provider mechanics live in exam_roi.llm."""
    model = model or MODEL_STAGE2
    stage = 1 if model == MODEL_STAGE1 and model != MODEL_STAGE2 else 2
    limits = limits or RequestLimits.from_env(os.environ, stage)
    max_tokens = limits.output_tokens if max_tokens is None else max_tokens
    # Check before constructing an SDK client or looking up credentials.
    limits.check(system, user, max_tokens)
    return ModelClient(_client(), _PROVIDER["sdk"], model, limits,
                       attempts=MAX_RETRIES, provider=LLM_PROVIDER)(system, user, max_tokens=max_tokens)


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

    def prompt(batch):
        return _S2A_TEMPLATE.format(
            taxonomy_list=_fmt_taxonomy(list(topic_names) + new_names),
            batch_no=1, batch_count=1,
            questions_json=json.dumps(question_evidence(batch), ensure_ascii=False))

    def consume(raw, batch):
        batch_tags, names = validate_tags(parse_json_from(raw), batch, list(topic_names) + new_names)
        if set(tags) & set(batch_tags):
            raise CandidateValidationError("topic tagging", "Duplicate question IDs across batches")
        tags.update(batch_tags)
        new_names.extend(name for name in names if name not in new_names)

    run_batches(questions, prompt, consume, system=_S2_SYSTEM, client=client, limits=limits,
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


def refresh_connections(paper, topic_names):
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
    return validate_connection_review(parse_json_from(call_llm(_S2_SYSTEM, user)),
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

    # Attach topics back onto the full question objects
    tagged = []
    for q in questions:
        q = dict(q)
        tag = tags[q["q_id"]]
        q["topics"] = tag["topics"]
        q["topic_tagging"] = tag_evidence(tag)
        tagged.append(q)

    # Any label absent from the taxonomy is new, whether or not the model flagged it
    seen_topics = {t for q in tagged for t in q["topics"]}
    new_names   = [t for t in proposed_new if t in seen_topics and t not in taxonomy["topics"]]
    new_names  += [t for t in sorted(seen_topics)
                   if t not in taxonomy["topics"] and t not in new_names]

    paper_scores = _stage2_score_topics(sorted(seen_topics), taxonomy_list, tagged,
                                  topic_names + new_names, **dependencies)

    # ── Local aggregation ──
    total_marks = float(total_marks) or 1.0
    agg = {}
    for q in tagged:
        topics = q["topics"]
        if not topics:
            continue
        marks = q.get("marks")
        marks = float(marks) if isinstance(marks, (int, float)) else 0.0
        share = marks / len(topics)
        fmt   = q.get("format") or "short_answer"
        for t in topics:
            a = agg.setdefault(t, {"marks": 0.0, "by_fmt": {}})
            a["marks"] += share
            a["by_fmt"][fmt] = a["by_fmt"].get(fmt, 0.0) + share

    per_topic = {}
    for t, a in agg.items():
        judgment = paper_scores[t]
        tot   = a["marks"]
        dist  = ({f: round(v / tot, 3) for f, v in a["by_fmt"].items()} if tot
                 else {f: round(1 / len(a["by_fmt"]), 3) for f in a["by_fmt"]})
        per_topic[t] = {
            "marks_total":         round(tot, 2),
            "mark_fraction":       round(tot / total_marks, 4),
            "format_distribution": dist,
            "dominant_format":     max(dist, key=dist.get) if dist else "short_answer",
            "Diff":                judgment.get("Diff"),
            "Conn":                judgment.get("Conn"),
            "prerequisites":       judgment.get("prerequisites", []),
            "evaluation_contract_version": judgment.get("evaluation_contract_version", LEGACY_VERSION),
            "difficulty_contract_version": difficulty_version(judgment),
            "is_new_topic":        t in new_names,
        }
        per_topic[t].update(paper_scores[t])

    return {"questions": tagged, "new_topic_names": new_names, "per_topic": per_topic,
            "topic_judgments": paper_scores}


# ── Commands ───────────────────────────────────────────────────────────────────

def resolve_exam_id(path: Path, explicit_id=None) -> str:
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
    base = validate_exam_id(path.stem.replace(" ", "_"))
    here = str(path.resolve())
    candidates = [base]
    for depth, parent in enumerate(path.resolve().parents):
        folder = parent.name.replace(" ", "_")
        candidate = f"{folder}_{base}" if folder else f"{base}_{depth + 2}"
        if candidate not in candidates:
            candidates.append(candidate)
    for candidate in candidates:
        existing = [exam_record_path(COURSE_FOLDER, state, candidate)
                    for state in ("parsed", "candidates")]
        existing = [record_path for record_path in existing if record_path.exists()]
        if not existing:
            return candidate
        claimed_paths = []
        for record_path in existing:
            try:
                record = json.loads(record_path.read_text(encoding="utf-8"))
                claimed = (record.get("source_provenance", {}).get("resolved_path")
                           or record.get("source_path"))
            except (ValueError, OSError):
                claimed = None
            claimed_paths.append(claimed)
        if all(claimed is None or claimed == here for claimed in claimed_paths):
            return candidate          # same paper, or a legacy record without a source path
    raise ExamIdentityError(
        f"All automatic IDs for {path.name!r} are already used by other papers. "
        "Choose a distinct --exam-id; --force does not bypass automatic collisions.")


def _model_provenance(extraction_client, analysis_client):
    def identity(client, default_model):
        if client is None:
            return LLM_PROVIDER, default_model
        if isinstance(client, ModelClient):
            return client.provider or f"{client.sdk}-compatible", client.model
        return "injected-callable", "injected-callable"

    extraction_provider, extraction_model = identity(extraction_client, MODEL_STAGE1)
    analysis_provider, analysis_model = identity(analysis_client, MODEL_STAGE2)
    record = {"provider": extraction_provider if extraction_provider == analysis_provider else "mixed",
              "extraction_model": extraction_model, "analysis_model": analysis_model}
    if extraction_provider != analysis_provider:
        record.update(extraction_provider=extraction_provider, analysis_provider=analysis_provider)
    return record


def process_exam_file(path: Path, year=None, total_marks=None, exam_id=None, force=False, *,
                      extraction_client=None, analysis_client=None,
                      extraction_limits=None, analysis_limits=None,
                      review_enabled=False, reviewer_client=None, reviewer_limits=None,
                      max_corrections=0) -> ExamOutcome:
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
    if not path.exists():
        # Vanished between selection and processing (or a caller-supplied path
        # that never existed) — an input problem, not a model or export one.
        raise ExtractionError(
            "missing_file", f"{path} does not exist.",
            "Check the path and rerun add-exam, or remove it from the request.",
        )

    exam_id = resolve_exam_id(path, exam_id)
    accepted_file = exam_record_path(COURSE_FOLDER, "parsed", exam_id)
    candidate_file = exam_record_path(COURSE_FOLDER, "candidates", exam_id)
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
    print(f"   → {extraction.summary()} — sent to {LLM_PROVIDER} for analysis")

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
        taxonomy = load_taxonomy()
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
        exam_record_path(COURSE_FOLDER, "parsed", exam_id, expected_path=accepted_file)
        exam_record_path(COURSE_FOLDER, "candidates", exam_id, expected_path=candidate_file)
        accepted_exams = load_all_exams()
        proposed_exams = dict(accepted_exams)
        proposed_exams[exam_id] = candidate  # A forced reparse replaces this paper's contribution.
        proposed_taxonomy = aggregate_taxonomy(taxonomy, proposed_exams)
        candidate = finalize_candidate_analysis(
            candidate, proposed_taxonomy, taxonomy.get("topics", {}))
        return candidate

    candidate = make_candidate()
    provider, model = None, None
    if review_enabled and reviewer_client is None:
        provider = os.environ.get("LLM_REVIEW_PROVIDER", LLM_PROVIDER).lower()
        model = os.environ.get("LLM_REVIEW_MODEL")
        try:
            reviewer_limits = reviewer_limits or RequestLimits(
                context_tokens=int(os.environ.get("LLM_REVIEW_CONTEXT_TOKENS", 128000)),
                output_tokens=int(os.environ.get("LLM_REVIEW_MAX_OUTPUT_TOKENS", 32000)),
                overhead_tokens=int(os.environ.get("LLM_REVIEW_OVERHEAD_TOKENS", 1024)))
        except ValueError as exc:
            def failed_reviewer(system, user, max_tokens, error=exc):
                raise error
            reviewer_client = failed_reviewer
        else:
            # Delay SDK/credential setup until after the complete request fits.
            def configured_reviewer(system, user, max_tokens):
                return configured_model_client(
                    provider, model, reviewer_limits, providers=PROVIDERS, env=os.environ,
                    attempts=MAX_RETRIES)(
                    system, user, max_tokens=max_tokens)
            reviewer_client = configured_reviewer
    candidate, review = review_candidate(
        candidate, exam_text, enabled=review_enabled, client=reviewer_client,
        limits=reviewer_limits, provider=provider,
        model=model, correct=make_candidate, max_corrections=max_corrections)
    candidate["independent_review"] = review
    if review["disposition"] == "needs_review":
        candidate["candidate_status"] = "needs-review"
    if review_enabled:
        print(f"   Independent review: {review['disposition']}"
              f" ({review.get('reason', 'evidence checks completed')})")
    candidate_file = exam_record_path(COURSE_FOLDER, "candidates", exam_id, expected_path=candidate_file)
    candidate_file.write_text(json.dumps(candidate, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"   ✓ Saved candidate → candidates/{exam_id}.json")
    print("     Accepted papers and taxonomy were not changed.")
    if candidate.get("candidate_status") == "needs-review":
        print("     Status: pending review — a person should check this candidate before it is accepted.")
        return ExamOutcome.SAVED_PENDING_REVIEW
    return ExamOutcome.SAVED


def cmd_add_exam(args):
    if getattr(args, "review_corrections", 0) and not getattr(args, "review", False):
        raise ValueError("--review-corrections requires --review")
    try:
        files = collect_exam_files(COURSE_FOLDER, args.paths, args.recursive)
    except InputSelectionError as exc:
        sys.exit(f"ERROR: {exc}")

    # --year and --exam-id describe one specific paper; silently applying either to
    # a whole batch would stamp every exam with the same year, or overwrite one
    # parsed file repeatedly under the same id.
    if len(files) > 1 and (args.year or args.exam_id):
        sys.exit(
            f"ERROR: --year/--exam-id describe a single exam, but {len(files)} files matched.\n"
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
                year=args.year,
                total_marks=args.total_marks,
                exam_id=args.exam_id,
                force=args.force,
                review_enabled=getattr(args, "review", False),
                max_corrections=getattr(args, "review_corrections", 0),
            )
            counts[outcome] += 1
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
    if failures and not processed:
        print(f"   All {len(failures)} requested paper(s) failed — nothing was added; "
              "outputs left unchanged. See the recovery notes above.")
    elif failures:
        print(f"   {processed} candidate(s) saved despite {len(failures)} failure(s) — "
              "accepted outputs are unchanged. See the recovery notes above for what to fix.")
    elif processed:
        review_note = f" ({pending_review} pending review)" if pending_review else ""
        print(f"   {processed} candidate(s) await acceptance or review{review_note}; "
              "accepted outputs are unchanged.")
    else:
        print("   Nothing new to add — outputs left unchanged (use --force to reprocess).")

    return EXIT_PAPER_FAILURE if failures else EXIT_OK


def cmd_rebuild(_args):
    print("\n📊 Rebuilding spreadsheet…")
    taxonomy  = load_taxonomy()
    all_exams = load_all_exams()
    updated_taxonomy = aggregate_taxonomy(taxonomy, all_exams)
    if updated_taxonomy != taxonomy:
        save_taxonomy(updated_taxonomy)
    taxonomy = updated_taxonomy

    if not all_exams:
        print("   No accepted exams found. Candidate analyses do not enter reports until accepted.")
        return EXIT_OK

    # A paper with no year sorts first, before every dated one, rather than crashing
    # the comparison against None.
    exam_list = sorted(all_exams.values(), key=lambda e: (e.get("year") or 0, e["exam_id"]))
    n_exams   = len(exam_list)
    labels    = exam_labels(exam_list)

    # Collect every topic that has appeared in at least one exam
    all_topics: set[str] = set()
    for exam in exam_list:
        all_topics.update(exam["per_topic"].keys())

    rows = []
    for topic in sorted(all_topics):
        tax = taxonomy["topics"].get(topic, {})

        # Per-exam breakdown
        per_exam: dict[str, dict] = {}
        for exam in exam_list:
            eid = exam["exam_id"]
            td  = exam["per_topic"].get(topic)
            # year and label travel with every entry: exam ids alone do not tell a
            # reader of the JSON which sitting a column belongs to, and one year can
            # hold several.
            common = {"year": exam.get("year"), "label": labels.get(eid, eid),
                      "evaluation_contract_version": exam.get("evaluation_contract_version", LEGACY_VERSION)}
            if td:
                per_exam[eid] = {
                    **common,
                    "present":       1,
                    "mark_fraction": td.get("mark_fraction", 0),
                    "marks_total":   td.get("marks_total", 0),
                    "fmt_score":     weighted_fmt(td.get("format_distribution", {})),
                }
            else:
                per_exam[eid] = {
                    **common,
                    "present": 0, "mark_fraction": 0,
                    "marks_total": 0, "fmt_score": 0,
                }

        # Aggregate variables
        appearances   = sum(1 for d in per_exam.values() if d["present"])
        Freq          = appearances / n_exams
        present_marks = [d["mark_fraction"] for d in per_exam.values() if d["present"]]
        G_Marks       = sum(present_marks) / len(present_marks) if present_marks else 0
        fmt_vals      = [d["fmt_score"]    for d in per_exam.values() if d["present"]]
        Fmt           = sum(fmt_vals) / len(fmt_vals) if fmt_vals else 2.0
        Conn          = tax.get("Conn") or 1
        Diff          = tax.get("Diff") or 3

        priority = (100 * Freq * G_Marks * Conn / (Diff * Fmt)) if (Diff * Fmt) > 0 else 0

        rows.append({
            "topic":         topic,
            "per_exam":      per_exam,
            "Freq":          round(Freq,    3),
            "G_Marks":       round(G_Marks, 3),
            "Conn":          Conn,
            "Diff":          Diff,
            "difficulty_contract_version": difficulty_version(tax),
            "evaluation_contract_version": tax.get("evaluation_contract_version", LEGACY_VERSION),
            "human_overrides": tax.get("human_overrides", {}),
            "model_estimate": tax.get("model_estimate", {}),
            "contributing_exam_ids": tax.get("contributing_exam_ids", []),
            "connection_evidence": tax.get("connection_evidence", []),
            "review_notes": "; ".join(label for flag, label in (
                (tax.get("difficulty_review_required"), "Difficulty needs review"),
                (tax.get("connection_review_required"), "Conflicting dependencies"),
                (tax.get("excluded_legacy_exam_ids"), "Older evidence excluded"),
                (tax.get("evaluation_contract_version") != CONTRACT_VERSION, "Older judgment basis"),
            ) if flag),
            "Fmt":           round(Fmt, 2),
            "priority":      round(priority, 4),
            "appearances":   appearances,
            "prerequisites": ", ".join(tax.get("prerequisites", [])),
        })

    rows.sort(key=lambda r: r["priority"], reverse=True)
    tier1_n = max(1, round(len(rows) * 0.2))
    for i, row in enumerate(rows):
        row["rank"] = i + 1
        row["tier"] = "★ Tier 1" if i < tier1_n else ""

    # Parsed papers and taxonomy are already safely on disk at this point — only
    # the write below can still fail (a locked file, a full disk, a missing
    # openpyxl install), so it gets its own outcome rather than an uncaught
    # traceback standing in for "rebuild failed".
    try:
        write_xlsx(rows, exam_list, taxonomy, OUTPUT_XLSX)
        write_json(rows, OUTPUT_JSON)
    except Exception as exc:
        print(f"   ✗ Export failed — {type(exc).__name__}: {exc}")
        print("     Parsed papers and taxonomy on disk are unchanged. "
              f"Recovery: {RecoveryKind.REBUILD.instruction}.")
        return EXIT_EXPORT_FAILURE

    print(f"   ✓ {OUTPUT_XLSX.name}, {OUTPUT_JSON.name}  ({len(rows)} topics · {n_exams} exams · {tier1_n} Tier 1)")
    return EXIT_OK


def cmd_status(_args):
    taxonomy  = load_taxonomy()
    all_exams = load_all_exams()
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
    print(f"   Spreadsheet : {'✓ exists' if OUTPUT_XLSX.exists() else 'not created yet'}")
    print(f"   Ranked JSON : {'✓ exists' if OUTPUT_JSON.exists() else 'not created yet'}")
    print()
    return EXIT_OK


def cmd_edit_topic(args):
    taxonomy = load_taxonomy()
    name     = args.name
    if name not in taxonomy["topics"]:
        known = sorted(taxonomy["topics"].keys())
        sys.exit(
            f"Topic not found: '{name}'\n"
            f"Known topics: {', '.join(known) if known else '(none yet)'}"
        )
    changed = False
    if args.diff is not None:
        if not 1 <= args.diff <= 6:
            sys.exit("Diff must be 1–6")
        _record_override(taxonomy["topics"][name], "Diff", args.diff)
        print(f"   Set Diff={args.diff} for '{name}'")
        changed = True
    if args.conn is not None:
        if not 1 <= args.conn <= 3:
            sys.exit("Conn must be 1–3")
        _record_override(taxonomy["topics"][name], "Conn", args.conn)
        print(f"   Set Conn={args.conn} for '{name}'")
        changed = True
    if not changed:
        print("Nothing changed — pass --diff or --conn (or both).")
        return EXIT_OK
    save_taxonomy(taxonomy)
    # edit-topic's own exit status has to reflect a failed rebuild too — an
    # override that saved correctly but could not be exported is not a success.
    return cmd_rebuild(None)


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
    p = BriefHelpParser(
        prog="pipeline.py",
        usage="pipeline.py COURSE_FOLDER COMMAND [data]",
    )
    p.add_argument(
        "course_folder",
        metavar="COURSE_FOLDER",
        help="Folder holding this exam's papers and results (created if it does not exist)",
    )
    # parser_class: without it the subcommands inherit BriefHelpParser, and
    # `add-exam --help` would reprint the top-level screen instead of its options.
    sub = p.add_subparsers(dest="cmd", metavar="COMMAND",
                           parser_class=argparse.ArgumentParser)

    pa = sub.add_parser("add-exam", help="Validate exam papers and save candidate analyses")
    pa.add_argument("paths", nargs="*", metavar="PATH",
                    help="Exam file(s) or folder(s): UTF-8 .txt, or .pdf with a text layer "
                         "(default: papers in both COURSE_FOLDER and its exams/ subfolder; "
                         "relative paths prefer the working directory, then COURSE_FOLDER)")
    pa.add_argument("--year",        type=int,            help="Year this paper was sat (read from the filename or the paper itself if omitted)")
    pa.add_argument("--total-marks", type=float,          help="Total marks (summed from questions if omitted)")
    pa.add_argument("--exam-id", type=_exam_id_argument,
                    help="Custom filename ID, not a path (defaults to the filename with spaces replaced by underscores)")
    pa.add_argument("--force",       action="store_true", help="Reprocess papers with a candidate or accepted record")
    pa.add_argument("--review", action="store_true",
                    help="Run an independent evidence review before saving the candidate")
    pa.add_argument("--review-corrections", type=int, choices=range(MAX_CORRECTIONS + 1), default=0,
                    help="Maximum analyzer correction attempts after review findings (default: 0)")
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

    setup_course_folder(Path(args.course_folder))

    dispatch = {
        "add-exam":   cmd_add_exam,
        "rebuild":    cmd_rebuild,
        "status":     cmd_status,
        "edit-topic": cmd_edit_topic,
    }
    # Every dispatched command returns one of the EXIT_* codes above; this is the
    # one place that turns that into the process's actual exit status.
    return dispatch[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
