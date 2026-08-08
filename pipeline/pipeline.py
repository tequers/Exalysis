#!/usr/bin/env python3
"""
Exam ROI Pipeline
=================
Processes exam files through an LLM to extract topics, score ROI variables,
and produce a ranked Excel spreadsheet.

Formula: Priority = 100 × (F × G × C) / (D × Fmt)
  F   = fraction of exams where topic appeared  (0–1, computed)
  G   = average mark fraction when present       (0–1, computed)
  C   = connection / node value                  (1–3, AI-estimated once)
  D   = difficulty bucket                        (1–6, AI-estimated once)
  Fmt = format depth                             (1=MCQ · 2=short answer · 3=write code)

Setup:
  Pick a provider with the LLM_PROVIDER env var (default: anthropic).
  Supported out of the box: anthropic, deepseek, openai — the latter two
  share one OpenAI-compatible code path, so any other provider that speaks
  the same chat-completions API (Groq, local vLLM/Ollama, ...) works by
  adding one entry to the PROVIDERS dict below.

    LLM_PROVIDER=anthropic  pip install anthropic
                             export ANTHROPIC_API_KEY=sk-ant-...
    LLM_PROVIDER=deepseek   pip install openai
                             export DEEPSEEK_API_KEY=sk-...
    LLM_PROVIDER=openai     pip install openai
                             export OPENAI_API_KEY=sk-...

  (Windows CMD: use `set VAR=value` instead of `export VAR=value`.)
  Optionally override the models: LLM_MODEL_STAGE1 / LLM_MODEL_STAGE2.

Usage:
  python pipeline.py add exam_2022.txt
  python pipeline.py add exam_2023.pdf --year 2023 --total-marks 120
  python pipeline.py add exam_2024.txt --force        # reprocess existing
  python pipeline.py add-folder exams/computer_vision # parse every .txt/.pdf in a folder
  python pipeline.py add-folder exams/ --recursive --force
  python pipeline.py rebuild                          # rebuild spreadsheet only
  python pipeline.py status                           # show current state
  python pipeline.py edit-topic "Big-O Notation" --d 2 --c 3   # override scores

File layout (all relative to this script):
  taxonomy.json        canonical topic list with D and C per topic
  parsed/              one JSON file per processed exam (audit trail)
  Exam_ROI_Pipeline.xlsx  output spreadsheet (overwritten on each rebuild)
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(errors="replace")
sys.stderr.reconfigure(errors="replace")

# ── Configuration ──────────────────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent
TAXONOMY_FILE = SCRIPT_DIR / "taxonomy.json"
PARSED_DIR    = SCRIPT_DIR / "parsed"
OUTPUT_XLSX   = SCRIPT_DIR / "Exam_ROI_Pipeline.xlsx"

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

# Output-token budgets. Modern frontier models allow 32k+ output tokens; the
# old 8k/16k defaults truncated mid-JSON on long exams.
MAX_TOKENS_STAGE1 = 32000   # question extraction (scales with exam length)
MAX_TOKENS_STAGE2 = 32000   # topic tagging / scoring
# Stage 2 tags questions in batches so its output can never outgrow the budget.
STAGE2_BATCH_SIZE = 40

# Format → integer score (MVP scale 1–3)
FMT_SCORE = {
    "mcq":                 1,
    "short_answer":        2,
    "explain_derive":      2,
    "write_code_or_proof": 3,
}


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

def read_exam_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            import pypdf
        except ImportError:
            sys.exit("ERROR: Install pypdf to read PDFs:  pip install pypdf")

        reader = pypdf.PdfReader(str(path))
        pages  = []
        empty  = 0
        for i, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text(extraction_mode="layout") or ""
            except TypeError:
                # pypdf < 4 does not support extraction_mode
                text = page.extract_text() or ""
            if not text.strip():
                empty += 1
            pages.append(f"[Page {i}]\n{text}")

        if empty:
            print(
                f"   ⚠  {empty}/{len(reader.pages)} page(s) returned no text "
                f"— PDF may contain scanned images. Those pages will be skipped."
            )

        return "\n\n".join(pages)

    return path.read_text(encoding="utf-8", errors="replace")


# ── LLM API helpers ────────────────────────────────────────────────────────────

def _client():
    key = os.environ.get(_PROVIDER["key_env"])
    if not key:
        sys.exit(
            f"ERROR: {_PROVIDER['key_env']} is not set (provider={LLM_PROVIDER}).\n"
            f"       export {_PROVIDER['key_env']}=...   "
            f"(Windows: set {_PROVIDER['key_env']}=...)"
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


class TruncatedResponse(RuntimeError):
    """Raised when the model stopped because it hit max_tokens — output is incomplete."""


def _text_from_anthropic(msg) -> str:
    """Concatenate the text blocks of an Anthropic response, skipping thinking/tool blocks."""
    parts = [
        b.text for b in msg.content
        if getattr(b, "type", None) == "text" and getattr(b, "text", None)
    ]
    if not parts:
        kinds = ", ".join(getattr(b, "type", "?") for b in msg.content) or "none"
        raise ValueError(f"No text block in response (blocks: {kinds})")
    if getattr(msg, "stop_reason", None) == "max_tokens":
        used = getattr(getattr(msg, "usage", None), "output_tokens", "?")
        raise TruncatedResponse(
            f"Response hit max_tokens ({used} output tokens) — the JSON is incomplete. "
            "Increase MAX_TOKENS_STAGE1/MAX_TOKENS_STAGE2 or lower STAGE2_BATCH_SIZE."
        )
    return "\n".join(parts)


def _text_from_openai(resp) -> str:
    """Extract text from an OpenAI-compatible chat-completions response."""
    choice = resp.choices[0]
    text   = choice.message.content or ""
    if choice.finish_reason == "length":
        raise TruncatedResponse(
            "Response hit the token limit — the JSON is incomplete. "
            "Increase MAX_TOKENS_STAGE1/MAX_TOKENS_STAGE2 or lower STAGE2_BATCH_SIZE."
        )
    if not text.strip():
        raise ValueError(f"Empty response (finish_reason: {choice.finish_reason})")
    return text


def call_llm(system: str, user: str, max_tokens: int = MAX_TOKENS_STAGE2,
             model: str = MODEL_STAGE2) -> str:
    """
    Provider-agnostic completion call — dispatches on _PROVIDER["sdk"].
    Anthropic uses streaming because a non-streaming call at these token
    budgets is rejected by that SDK for exceeding its 10-minute non-streaming
    ceiling; the OpenAI-compatible family has no such restriction.
    """
    client = _client()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if _PROVIDER["sdk"] == "anthropic":
                with client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                ) as stream:
                    msg = stream.get_final_message()
                return _text_from_anthropic(msg)
            else:
                resp = client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                return _text_from_openai(resp)
        except TruncatedResponse:
            raise                      # deterministic — retrying won't help
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = 2 ** attempt
            print(f"   ⚠  API error (attempt {attempt}/{MAX_RETRIES}): {exc}. Retrying in {wait}s…")
            time.sleep(wait)


def parse_json_from(text: str):
    """Extract JSON from the model's response (handles ```json fences and bare JSON)."""
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1)
    text = text.strip()
    start = next((i for i, ch in enumerate(text) if ch in "{["), None)
    if start is None:
        raise ValueError(f"No JSON found in response:\n{text[:500]}")
    try:
        # raw_decode ignores any trailing prose after the JSON value
        return json.JSONDecoder().raw_decode(text, start)[0]
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Malformed JSON from the model ({exc}). "
            f"Response was {len(text)} chars; tail:\n…{text[-300:]}"
        ) from exc


# ── Stage 1: Extract questions ─────────────────────────────────────────────────

_S1_SYSTEM = (
    "You are an exam parsing engine. Extract every distinct question and sub-question "
    "from the provided exam text. Output a single JSON array only — no prose, no markdown fences."
)

def stage1_extract(exam_text: str, total_marks) -> list:
    tm_str = str(total_marks) if total_marks else "unknown — sum from questions if possible"
    user = (
        f"Total exam marks: {tm_str}\n\n"
        "Extract every distinct question and sub-question. For each output one JSON object:\n"
        '  "q_id"   : unique label e.g. "Q1", "Q2a", "Q3b"\n'
        '  "text"   : verbatim question text (enough to identify the concept)\n'
        '  "marks"  : integer point value, or null if not stated\n'
        '  "format" : exactly one of these strings:\n'
        '               "mcq"                  — multiple choice / true-false / matching\n'
        '               "short_answer"         — define / fill-in / short explanation\n'
        '               "explain_derive"       — explain concept / trace code / derive formula\n'
        '               "write_code_or_proof"  — write code, proof, or design from scratch\n\n'
        "Output only a JSON array. No other text.\n\n"
        f"EXAM TEXT:\n{exam_text}"
    )
    raw = call_llm(_S1_SYSTEM, user, max_tokens=MAX_TOKENS_STAGE1, model=MODEL_STAGE1)
    return parse_json_from(raw)


# ── Stage 2: Tag topics and score parameters ───────────────────────────────────

_S2_SYSTEM = (
    "You are a computer science curriculum analyst. You tag exam questions with canonical "
    "topic labels and estimate study parameters for ROI scoring. Output valid JSON only — "
    "no markdown, no prose outside the JSON."
)

_S2A_TEMPLATE = """\
CANONICAL TOPIC TAXONOMY
(Reuse these labels. Only propose a NEW label if the concept is genuinely absent.)
{taxonomy_list}

QUESTIONS (batch {batch_no} of {batch_count}):
{questions_json}

YOUR TASK
Assign 1–2 canonical topic labels to every question.
Reuse existing taxonomy labels wherever possible.
Merge near-synonyms (e.g. "pointers" and "pointer arithmetic" → one canonical label).
Only invent a new label when the concept is genuinely absent from the taxonomy.

Echo back the q_id only — do NOT repeat the question text.

OUTPUT exactly this JSON structure (no extra keys, no prose):
{{
  "tags": {{ "Q1": ["Label A"], "Q2a": ["Label A", "Label B"] }},
  "new_topic_names": ["New Label 1"]
}}"""

_S2B_TEMPLATE = """\
EXISTING TAXONOMY (for prerequisite references only)
{taxonomy_list}

NEW TOPICS TO SCORE
{new_topics}

For each new topic estimate:

  difficulty_d      : 1–6 bucket — time for a competent student to become exam-ready
                      <30 min=1  30min–1h=2  1–3h=3  3–6h=4  6–15h=5  >15h=6
                      "Exam-ready" = passing competency, not mastery.
  difficulty_hours  : matching range string, e.g. "1–3h"
  connection_c      : 1–3 integer
                      1 = isolated (helps no other exam topic)
                      2 = helps 1–2 other topics
                      3 = foundational (many other topics depend on it)
  prerequisites     : list of topic names this concept requires
                      (use existing taxonomy labels or other new topic names only)

OUTPUT exactly this JSON structure (no extra keys, no prose):
{{
  "Topic Name": {{
    "difficulty_d": 3,
    "difficulty_hours": "1–3h",
    "connection_c": 2,
    "prerequisites": []
  }}
}}"""


def _compact_questions(questions: list) -> list:
    """Strip questions down to what tagging actually needs, capping text length."""
    out = []
    for q in questions:
        text = str(q.get("text", ""))
        out.append({
            "q_id":   q.get("q_id"),
            "marks":  q.get("marks"),
            "format": q.get("format"),
            "text":   text if len(text) <= 500 else text[:500] + " …",
        })
    return out


def _batched(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def _fmt_taxonomy(topic_names: list) -> str:
    if not topic_names:
        return '[]  ← taxonomy is empty; propose all new topic labels'
    return json.dumps(sorted(topic_names), indent=2, ensure_ascii=False)


def _stage2_tag(questions: list, topic_names: list) -> tuple:
    """Ask the LLM for q_id → topics. Batched so the reply can never be truncated."""
    compact  = _compact_questions(questions)
    batches  = list(_batched(compact, STAGE2_BATCH_SIZE))
    tags, new_names = {}, []

    for n, batch in enumerate(batches, 1):
        if len(batches) > 1:
            print(f"   · tagging batch {n}/{len(batches)} ({len(batch)} questions)…")
        # Feed labels coined in earlier batches forward, so later batches reuse
        # them instead of inventing near-duplicates.
        user = _S2A_TEMPLATE.format(
            taxonomy_list=_fmt_taxonomy(list(topic_names) + new_names),
            batch_no=n,
            batch_count=len(batches),
            questions_json=json.dumps(batch, indent=2, ensure_ascii=False),
        )
        data = parse_json_from(call_llm(_S2_SYSTEM, user, max_tokens=MAX_TOKENS_STAGE2))
        tags.update(data.get("tags", {}))
        for name in data.get("new_topic_names", []):
            if name not in new_names:
                new_names.append(name)
    return tags, new_names


def _stage2_score_new(new_names: list, taxonomy_list: str) -> dict:
    """Estimate D / C / prerequisites for genuinely new topics only."""
    if not new_names:
        return {}
    user = _S2B_TEMPLATE.format(
        taxonomy_list=taxonomy_list,
        new_topics=json.dumps(new_names, indent=2, ensure_ascii=False),
    )
    return parse_json_from(call_llm(_S2_SYSTEM, user, max_tokens=MAX_TOKENS_STAGE2))


def stage2_tag_score(questions: list, taxonomy: dict, total_marks: float) -> dict:
    """
    Tag every question with topics and build the per-topic score table.

    The LLM is asked only for judgement calls (which topic, how hard, how connected).
    All arithmetic — marks_total, mark_fraction, format_distribution — is computed
    locally, which is both exact and the reason the response can no longer overflow
    max_tokens on a long exam.
    """
    topic_names   = sorted(taxonomy["topics"].keys())
    taxonomy_list = _fmt_taxonomy(topic_names)

    tags, proposed_new = _stage2_tag(questions, topic_names)

    # Attach topics back onto the full question objects
    tagged = []
    for q in questions:
        q = dict(q)
        q["topics"] = tags.get(q.get("q_id"), [])
        tagged.append(q)

    # Any label absent from the taxonomy is new, whether or not the model flagged it
    seen_topics = {t for q in tagged for t in q["topics"]}
    new_names   = [t for t in proposed_new if t in seen_topics and t not in taxonomy["topics"]]
    new_names  += [t for t in sorted(seen_topics)
                   if t not in taxonomy["topics"] and t not in new_names]

    new_scores = _stage2_score_new(new_names, taxonomy_list)

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
        known = taxonomy["topics"].get(t, {})
        est   = new_scores.get(t, {})
        tot   = a["marks"]
        dist  = ({f: round(v / tot, 3) for f, v in a["by_fmt"].items()} if tot
                 else {f: round(1 / len(a["by_fmt"]), 3) for f in a["by_fmt"]})
        per_topic[t] = {
            "marks_total":         round(tot, 2),
            "mark_fraction":       round(tot / total_marks, 4),
            "format_distribution": dist,
            "dominant_format":     max(dist, key=dist.get) if dist else "short_answer",
            "difficulty_d":        known.get("difficulty_d")     or est.get("difficulty_d", 3),
            "difficulty_hours":    known.get("difficulty_hours") or est.get("difficulty_hours", "1–3h"),
            "connection_c":        known.get("connection_c")     or est.get("connection_c", 2),
            "prerequisites":       known.get("prerequisites")    or est.get("prerequisites", []),
            "is_new_topic":        t in new_names,
        }

    untagged = [q.get("q_id") for q in tagged if not q["topics"]]
    if untagged:
        print(f"   ⚠  {len(untagged)} question(s) came back untagged: {', '.join(map(str, untagged[:10]))}")

    return {"questions": tagged, "new_topic_names": new_names, "per_topic": per_topic}


# ── Aggregation helpers ────────────────────────────────────────────────────────

def weighted_fmt(fmt_dist: dict) -> float:
    """Mark-weighted average format score across a topic's format distribution."""
    total, weighted = 0.0, 0.0
    for fmt, frac in fmt_dist.items():
        weighted += FMT_SCORE.get(fmt, 2) * frac
        total += frac
    return round(weighted / total, 3) if total else 2.0


# ── Excel writer ───────────────────────────────────────────────────────────────

def write_xlsx(rows: list, exam_list: list, taxonomy: dict):
    """
    rows      : list of topic dicts, sorted by priority desc, each containing:
                topic, F, G, C, D, D_hours, Fmt, priority, rank, tier,
                prerequisites, per_exam={exam_id: {present, mark_fraction, fmt_score}}
    exam_list : list of exam dicts sorted by year
    taxonomy  : full taxonomy dict (for Taxonomy sheet)
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.formatting.rule import ColorScaleRule, FormulaRule
    from openpyxl.utils import get_column_letter as gcl

    wb = Workbook()

    # ── Micro-helpers ──
    P = dict(
        dk_blue="1F4E79", md_blue="2E75B6", lt_blue="BDD7EE", pale="DEEAF1",
        frm="E2EFDA",   frm2="EBF5EB",
        audit="FFF8EE", audit2="FEF3E2",
        tier1="C6EFCE",
        white="FFFFFF",  gray="F2F2F2",  gray2="EDEDED",
        brown="7B3F00",  dk_gray="4A4A4A",
    )
    def fn(sz=10, bold=False, color="000000", italic=False):
        return Font(name="Arial", size=sz, bold=bold, color=color, italic=italic)
    def fl(h): return PatternFill("solid", fgColor=h)
    def al(h="left", v="center", w=True):
        return Alignment(horizontal=h, vertical=v, wrap_text=w)
    def bd(color="C0C0C0"):
        s = Side(style="thin", color=color)
        return Border(left=s, right=s, top=s, bottom=s)

    exam_ids = [e["exam_id"] for e in exam_list]

    # ── Column definitions ──
    # (header, width, data_key, group)
    # data_key is either a string (row field) or (exam_id, field) tuple for per-exam cols
    FIXED = [
        ("Rank",       7,  "rank",     "scores"),
        ("Tier",      13,  "tier",     "scores"),
        ("Topic",     32,  "topic",    "scores"),
        ("F\n(0–1)",   9,  "F",        "scores"),
        ("G\n(0–1)",   9,  "G",        "scores"),
        ("C\n(1–3)",   8,  "C",        "scores"),
        ("D\n(1–6)",   8,  "D",        "scores"),
        ("Fmt\n(avg)", 9,  "Fmt",      "scores"),
        ("Priority",  12,  "priority", "scores"),
    ]
    EXAM_COLS = []
    for eid in exam_ids:
        exam = next(e for e in exam_list if e["exam_id"] == eid)
        yr = str(exam.get("year", eid))
        EXAM_COLS += [
            (f"{yr}\n✓",      7,  (eid, "present"),       "audit"),
            (f"{yr}\nmarks%", 10, (eid, "mark_fraction"),  "audit"),
            (f"{yr}\nFmt",     8, (eid, "fmt_score"),      "audit"),
        ]
    TAIL = [
        ("D hours",       13, "D_hours",       "taxonomy"),
        ("Prerequisites", 34, "prerequisites", "taxonomy"),
    ]

    ALL = FIXED + EXAM_COLS + TAIL
    NF = len(FIXED)
    NE = len(EXAM_COLS)

    for i, (_, w, _, _) in enumerate(ALL):
        wb.active.column_dimensions[gcl(i + 1)].width = w

    # ════════════════════════════
    #  Sheet 1: ROI Scores
    # ════════════════════════════
    ws = wb.active
    ws.title = "ROI Scores"
    ws.sheet_view.showGridLines = False

    n_topics = len(rows)
    n_exams  = len(exam_list)
    tier1_n  = sum(1 for r in rows if r["tier"])

    # Row 1: title
    ws.row_dimensions[1].height = 28
    ws.merge_cells(f"A1:{gcl(len(ALL))}1")
    c = ws["A1"]
    c.value = (
        f"Exam ROI Analysis  ·  {n_topics} topics  ·  {n_exams} exam{'s' if n_exams != 1 else ''}"
        f"  ·  {tier1_n} Tier 1  ·  Priority = 100 × (F × G × C) / (D × Fmt)"
    )
    c.font = fn(12, bold=True, color=P["white"])
    c.fill = fl(P["dk_blue"])
    c.alignment = al("left", "center")

    # Row 2: group headers
    ws.row_dimensions[2].height = 18
    GROUP_BG = {"scores": P["md_blue"], "audit": P["brown"], "taxonomy": P["dk_gray"]}
    spans = [
        (1,       NF,          "SCORES",          P["md_blue"]),
        (NF+1,    NF+NE,       "PER-EXAM AUDIT",  P["brown"]),
        (NF+NE+1, len(ALL),    "TAXONOMY",        P["dk_gray"]),
    ]
    for start, end, label, bg in spans:
        if start > end:
            continue
        ws.merge_cells(f"{gcl(start)}2:{gcl(end)}2")
        c = ws[f"{gcl(start)}2"]
        c.value     = label
        c.font      = fn(9, bold=True, color=P["white"])
        c.fill      = fl(bg)
        c.alignment = al("center", "center")
        c.border    = bd()

    # Row 3: column headers
    ws.row_dimensions[3].height = 50
    ws.freeze_panes = "D4"
    for i, (hdr, _, _, grp) in enumerate(ALL):
        c = ws[f"{gcl(i+1)}3"]
        c.value     = hdr
        c.font      = fn(9, bold=True, color=P["white"])
        c.fill      = fl(GROUP_BG[grp])
        c.alignment = al("center", "center", w=True)
        c.border    = bd()

    # Data rows
    last_row = 3 + n_topics
    for ri, row in enumerate(rows):
        r   = ri + 4
        alt = ri % 2 == 0
        ws.row_dimensions[r].height = 18

        for ci, (_, _, key, grp) in enumerate(ALL):
            c = ws[f"{gcl(ci+1)}{r}"]
            c.font   = fn(10)
            c.border = bd(color="DDDDDD")

            # Background by group
            if grp == "scores":
                c.fill = fl(P["frm2"] if alt else P["frm"])
            elif grp == "audit":
                c.fill = fl(P["audit2"] if alt else P["audit"])
            else:
                c.fill = fl(P["gray2"] if alt else P["white"])

            # Value & number format
            if isinstance(key, tuple):
                eid, field = key
                val = row["per_exam"][eid][field]
                c.value     = val
                c.alignment = al("center", "center")
                if field == "mark_fraction" and val:
                    c.number_format = "0.0%"
                elif field == "fmt_score":
                    c.number_format = "0.0"
            else:
                val = row.get(key, "")
                c.value = val

                if key == "topic":
                    c.font      = fn(10, bold=True)
                    c.fill      = fl(P["gray2"] if alt else P["white"])
                    c.alignment = al("left", "center", w=False)
                elif key == "tier":
                    c.alignment = al("center", "center")
                    if val == "★ Tier 1":
                        c.font = fn(10, bold=True, color="166534")
                elif key == "rank":
                    c.alignment = al("center", "center")
                elif key == "priority":
                    c.number_format = "0.00"
                    c.alignment     = al("center", "center")
                elif key in ("F", "G"):
                    c.number_format = "0.00"
                    c.alignment     = al("center", "center")
                elif key in ("C", "D"):
                    c.alignment = al("center", "center")
                elif key == "Fmt":
                    c.number_format = "0.0"
                    c.alignment     = al("center", "center")
                else:
                    c.alignment = al("left", "center")

    # Conditional formatting
    if rows:
        data_range  = f"A4:{gcl(len(ALL))}{last_row}"
        tier_col    = gcl(next(i+1 for i, (_, _, k, _) in enumerate(ALL) if k == "tier"))
        pri_col     = gcl(next(i+1 for i, (_, _, k, _) in enumerate(ALL) if k == "priority"))

        ws.conditional_formatting.add(
            data_range,
            FormulaRule(
                formula=[f'${tier_col}4="★ Tier 1"'],
                fill=PatternFill("solid", fgColor=P["tier1"]),
            ),
        )
        ws.conditional_formatting.add(
            f"{pri_col}4:{pri_col}{last_row}",
            ColorScaleRule(
                start_type="min",       start_color="FF9999",
                mid_type="percentile",  mid_value=50, mid_color="FFFF99",
                end_type="max",         end_color="63BE7B",
            ),
        )

    # ════════════════════════════
    #  Sheet 2: Taxonomy
    # ════════════════════════════
    ws2 = wb.create_sheet("Taxonomy")
    ws2.sheet_view.showGridLines = False

    ws2.row_dimensions[1].height = 28
    ws2.merge_cells("A1:G1")
    c = ws2["A1"]
    c.value     = "Topic Taxonomy  —  D and C scores  (yellow cells = editable overrides)"
    c.font      = fn(12, bold=True, color=P["white"])
    c.fill      = fl(P["dk_blue"])
    c.alignment = al("left", "center")

    TAX_HDRS   = ["Topic", "D (1–6)", "D hours", "C (1–3)", "First seen", "Appearances", "Prerequisites"]
    TAX_WIDTHS = [32, 9, 14, 9, 16, 14, 42]
    for i, (h, w) in enumerate(zip(TAX_HDRS, TAX_WIDTHS)):
        ws2.column_dimensions[gcl(i+1)].width = w
        c = ws2[f"{gcl(i+1)}2"]
        c.value     = h
        c.font      = fn(10, bold=True, color=P["white"])
        c.fill      = fl(P["md_blue"])
        c.alignment = al("center", "center")
        c.border    = bd()
    ws2.row_dimensions[2].height = 22

    all_exams = load_all_exams()
    appearances_map: dict[str, int] = {}
    for exam in all_exams.values():
        for t in exam.get("per_topic", {}):
            appearances_map[t] = appearances_map.get(t, 0) + 1

    for ri, (tname, tdata) in enumerate(sorted(taxonomy["topics"].items())):
        r   = ri + 3
        alt = ri % 2 == 0
        bg  = P["gray2"] if alt else P["white"]
        YLW = "FFF2CC"

        vals = [
            (tname,                                "left",   bg),
            (tdata.get("difficulty_d", ""),        "center", YLW),
            (tdata.get("difficulty_hours", ""),    "center", bg),
            (tdata.get("connection_c", ""),        "center", YLW),
            (tdata.get("first_seen", ""),          "center", bg),
            (appearances_map.get(tname, 0),        "center", bg),
            (", ".join(tdata.get("prerequisites", [])), "left", bg),
        ]
        for ci, (val, align, bg_c) in enumerate(vals):
            c = ws2[f"{gcl(ci+1)}{r}"]
            c.value     = val
            c.font      = fn(10)
            c.fill      = fl(bg_c)
            c.alignment = al(align, "center")
            c.border    = bd(color="DDDDDD")
        ws2.row_dimensions[r].height = 18

    # ════════════════════════════
    #  Sheet 3: Exam Log
    # ════════════════════════════
    ws3 = wb.create_sheet("Exam Log")
    ws3.sheet_view.showGridLines = False

    ws3.row_dimensions[1].height = 28
    ws3.merge_cells("A1:F1")
    c = ws3["A1"]
    c.value     = "Exam Log  —  one row per processed exam"
    c.font      = fn(12, bold=True, color=P["white"])
    c.fill      = fl(P["dk_blue"])
    c.alignment = al("left", "center")

    LOG_HDRS   = ["Exam ID", "Year", "Total Marks", "Topics Found", "Source File", "Processed At"]
    LOG_WIDTHS = [24, 8, 13, 14, 32, 22]
    for i, (h, w) in enumerate(zip(LOG_HDRS, LOG_WIDTHS)):
        ws3.column_dimensions[gcl(i+1)].width = w
        c = ws3[f"{gcl(i+1)}2"]
        c.value     = h
        c.font      = fn(10, bold=True, color=P["white"])
        c.fill      = fl(P["md_blue"])
        c.alignment = al("center", "center")
        c.border    = bd()
    ws3.row_dimensions[2].height = 22

    for ri, exam in enumerate(exam_list):
        r   = ri + 3
        bg  = P["gray2"] if ri % 2 == 0 else P["white"]
        processed = exam.get("processed_at", "")
        if processed:
            processed = processed[:10]
        for ci, (val, align) in enumerate([
            (exam["exam_id"],                      "left"),
            (exam.get("year", ""),                 "center"),
            (exam.get("total_marks", ""),          "center"),
            (len(exam.get("per_topic", {})),       "center"),
            (exam.get("source_file", ""),          "left"),
            (processed,                            "center"),
        ]):
            c = ws3[f"{gcl(ci+1)}{r}"]
            c.value     = val
            c.font      = fn(10)
            c.fill      = fl(bg)
            c.alignment = al(align, "center")
            c.border    = bd(color="DDDDDD")
        ws3.row_dimensions[r].height = 18

    wb.save(str(OUTPUT_XLSX))


# ── Commands ───────────────────────────────────────────────────────────────────

def process_exam_file(path: Path, year=None, total_marks=None, exam_id=None, force=False) -> bool:
    """
    Parse a single exam file (Stage 1 + Stage 2), update the taxonomy, and save
    parsed/<exam_id>.json. Returns True if the file was processed, False if it
    was skipped (already parsed and not --force). Does NOT rebuild the spreadsheet
    — callers are responsible for calling cmd_rebuild() once they're done.
    """
    if not path.exists():
        sys.exit(f"ERROR: File not found: {path}")

    exam_id = (exam_id or path.stem).replace(" ", "_")
    PARSED_DIR.mkdir(exist_ok=True)
    out_file = PARSED_DIR / f"{exam_id}.json"

    if out_file.exists() and not force:
        print(f"   ⏭  Skipping {path.name} — parsed/{exam_id}.json already exists (use --force to reprocess)")
        return False

    # Infer year from filename if not given
    if not year:
        m = re.search(r"20\d{2}", path.name)
        year = int(m.group()) if m else datetime.now().year

    print(f"\n📄 Exam : {path.name}  (year={year})")
    exam_text = read_exam_file(path)

    # ── Stage 1 ──
    print("🤖 Stage 1 : Extracting questions…")
    questions = stage1_extract(exam_text, total_marks)
    print(f"   → {len(questions)} questions extracted")

    if not total_marks:
        marks_vals  = [q["marks"] for q in questions if isinstance(q.get("marks"), (int, float))]
        total_marks = sum(marks_vals) if marks_vals else 100
        print(f"   → Total marks : {total_marks} (summed from questions)")

    # ── Stage 2 ──
    taxonomy = load_taxonomy()
    print("🤖 Stage 2 : Tagging topics and scoring parameters…")
    result    = stage2_tag_score(questions, taxonomy, total_marks)
    per_topic = result.get("per_topic", {})
    new_names = result.get("new_topic_names", [])
    print(f"   → {len(per_topic)} topics tagged  ({len(new_names)} new)")
    if new_names:
        print(f"   ⚠  New topics : {', '.join(new_names)}")
        print("      Check taxonomy.json afterwards — merge any near-duplicates by hand.")

    # ── Update taxonomy ──
    for tname, tdata in per_topic.items():
        if tname not in taxonomy["topics"]:
            taxonomy["topics"][tname] = {
                "difficulty_d":     tdata.get("difficulty_d"),
                "difficulty_hours": tdata.get("difficulty_hours"),
                "connection_c":     tdata.get("connection_c"),
                "prerequisites":    tdata.get("prerequisites", []),
                "first_seen":       exam_id,
            }
        else:
            # Preserve existing D/C; add prerequisites if previously empty
            ex = taxonomy["topics"][tname]
            if tdata.get("prerequisites") and not ex.get("prerequisites"):
                ex["prerequisites"] = tdata["prerequisites"]
    save_taxonomy(taxonomy)

    # ── Save parsed exam ──
    parsed = {
        "exam_id":      exam_id,
        "year":         year,
        "total_marks":  total_marks,
        "source_file":  path.name,
        "processed_at": datetime.now().isoformat(),
        "questions":    result.get("questions", questions),
        "per_topic":    per_topic,
    }
    out_file.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"   ✓ Saved → parsed/{exam_id}.json")
    return True


def cmd_add(args):
    path = Path(args.file)
    process_exam_file(
        path,
        year=args.year,
        total_marks=args.total_marks,
        exam_id=args.exam_id,
        force=args.force,
    )
    cmd_rebuild(None)


EXAM_EXTENSIONS = (".txt", ".pdf")


def cmd_add_folder(args):
    folder = Path(args.folder)
    if not folder.exists() or not folder.is_dir():
        sys.exit(f"ERROR: Folder not found: {folder}")

    pattern = "**/*" if args.recursive else "*"
    files = sorted(
        f for f in folder.glob(pattern)
        if f.is_file() and f.suffix.lower() in EXAM_EXTENSIONS
    )

    if not files:
        sys.exit(f"ERROR: No .txt/.pdf files found in {folder}")

    print(f"\n📁 Folder : {folder}  ({len(files)} file(s) found)")

    processed = 0
    skipped   = 0
    failed    = []
    for f in files:
        try:
            if process_exam_file(f, total_marks=args.total_marks, force=args.force):
                processed += 1
            else:
                skipped += 1
        except Exception as exc:
            print(f"   ✗ Failed on {f.name}: {exc}")
            failed.append(f.name)

    print(f"\n📦 Batch complete — {processed} processed · {skipped} skipped · {len(failed)} failed")
    if failed:
        print(f"   Failed files: {', '.join(failed)}")

    if processed:
        cmd_rebuild(None)
    else:
        print("   No new exams processed — spreadsheet not rebuilt.")


def cmd_rebuild(_args):
    print("\n📊 Rebuilding spreadsheet…")
    taxonomy  = load_taxonomy()
    all_exams = load_all_exams()

    if not all_exams:
        print("   No parsed exams found.  Run:  python pipeline.py add <file>")
        return

    exam_list = sorted(all_exams.values(), key=lambda e: (e.get("year", 0), e["exam_id"]))
    n_exams   = len(exam_list)

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
            if td:
                per_exam[eid] = {
                    "present":       1,
                    "mark_fraction": td.get("mark_fraction", 0),
                    "marks_total":   td.get("marks_total", 0),
                    "fmt_score":     weighted_fmt(td.get("format_distribution", {})),
                }
            else:
                per_exam[eid] = {
                    "present": 0, "mark_fraction": 0,
                    "marks_total": 0, "fmt_score": 0,
                }

        # Aggregate variables
        appearances   = sum(1 for d in per_exam.values() if d["present"])
        F             = appearances / n_exams
        present_marks = [d["mark_fraction"] for d in per_exam.values() if d["present"]]
        G             = sum(present_marks) / len(present_marks) if present_marks else 0
        fmt_vals      = [d["fmt_score"]    for d in per_exam.values() if d["present"]]
        Fmt           = sum(fmt_vals) / len(fmt_vals) if fmt_vals else 2.0
        C             = tax.get("connection_c") or 1
        D             = tax.get("difficulty_d") or 3

        priority = (100 * F * G * C / (D * Fmt)) if (D * Fmt) > 0 else 0

        rows.append({
            "topic":         topic,
            "per_exam":      per_exam,
            "F":             round(F,   3),
            "G":             round(G,   3),
            "C":             C,
            "D":             D,
            "D_hours":       tax.get("difficulty_hours", ""),
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

    write_xlsx(rows, exam_list, taxonomy)
    print(f"   ✓ {OUTPUT_XLSX.name}  ({len(rows)} topics · {n_exams} exams · {tier1_n} Tier 1)")


def cmd_status(_args):
    taxonomy  = load_taxonomy()
    all_exams = load_all_exams()
    print(f"\n📚 Exam ROI Pipeline  —  {SCRIPT_DIR}")
    print(f"   Taxonomy    : {len(taxonomy['topics'])} topics")
    print(f"   Parsed exams: {len(all_exams)}")
    for eid, exam in sorted(all_exams.items(), key=lambda x: x[1].get("year", 0)):
        n = len(exam.get("per_topic", {}))
        print(f"     {exam.get('year', '?')}  {eid}  ({n} topics · {exam.get('total_marks', '?')} marks)")
    print(f"   Spreadsheet : {'✓ exists' if OUTPUT_XLSX.exists() else 'not created yet'}")
    print()


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
    if args.d is not None:
        if not 1 <= args.d <= 6:
            sys.exit("D must be 1–6")
        taxonomy["topics"][name]["difficulty_d"] = args.d
        print(f"   Set D={args.d} for '{name}'")
        changed = True
    if args.c is not None:
        if not 1 <= args.c <= 3:
            sys.exit("C must be 1–3")
        taxonomy["topics"][name]["connection_c"] = args.c
        print(f"   Set C={args.c} for '{name}'")
        changed = True
    if not changed:
        print("Nothing changed — pass --d or --c (or both).")
        return
    save_taxonomy(taxonomy)
    cmd_rebuild(None)


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        prog="pipeline.py",
        description="Exam ROI Pipeline — rank study topics by exam value over effort.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python pipeline.py add exam_2022.txt
  python pipeline.py add exam_2023.pdf --year 2023 --total-marks 120
  python pipeline.py add exam_2024.txt --force
  python pipeline.py add-folder exams/computer_vision
  python pipeline.py add-folder exams/ --recursive --force
  python pipeline.py rebuild
  python pipeline.py status
  python pipeline.py edit-topic "Big-O Notation" --d 2 --c 3
        """,
    )
    sub = p.add_subparsers(dest="cmd")

    pa = sub.add_parser("add", help="Process a new exam file and update the spreadsheet")
    pa.add_argument("file",                                    help="Exam file (.txt or .pdf)")
    pa.add_argument("--year",         type=int,                help="Exam year (inferred from filename if omitted)")
    pa.add_argument("--total-marks",  type=float,              help="Total marks (summed from questions if omitted)")
    pa.add_argument("--exam-id",                               help="Custom ID (defaults to filename stem)")
    pa.add_argument("--force",        action="store_true",     help="Reprocess even if already parsed")

    pf = sub.add_parser("add-folder", help="Process every .txt/.pdf exam in a folder and update the spreadsheet")
    pf.add_argument("folder",                                  help="Folder containing exam files")
    pf.add_argument("--total-marks",  type=float,              help="Total marks applied to every file (summed from questions if omitted)")
    pf.add_argument("--force",        action="store_true",     help="Reprocess files even if already parsed")
    pf.add_argument("--recursive",    action="store_true",     help="Also search subfolders")

    sub.add_parser("rebuild", help="Rebuild spreadsheet from all stored exams")
    sub.add_parser("status",  help="Show pipeline state")

    pe = sub.add_parser("edit-topic", help="Override AI scores for a topic and rebuild")
    pe.add_argument("name",          help="Exact topic name (case-sensitive)")
    pe.add_argument("--d", type=int, help="Override difficulty D (1–6)")
    pe.add_argument("--c", type=int, help="Override connection C (1–3)")

    args = p.parse_args()
    dispatch = {
        "add":        cmd_add,
        "add-folder": cmd_add_folder,
        "rebuild":    cmd_rebuild,
        "status":     cmd_status,
        "edit-topic": cmd_edit_topic,
    }
    dispatch.get(args.cmd, lambda _: p.print_help())(args)


if __name__ == "__main__":
    main()
