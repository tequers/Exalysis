# Exam ROI Pipeline

A CLI pipeline that processes past CS exam files through an LLM to extract topics, score ROI variables, and produce a ranked Excel study-priority spreadsheet.

## What this does

Given one or more past exams (text or PDF), the pipeline:
1. Extracts every question with its marks and format type
2. Tags each question with a canonical topic label (reusing existing labels, creating new ones only when necessary)
3. Estimates difficulty (D) and connection (C) scores for each new topic
4. Aggregates F, G, Fmt across all exams and computes `Priority = 100 × (F × G × C) / (D × Fmt)`
5. Writes `Exam_ROI_Pipeline.xlsx` with the ranked topic list and per-exam audit data

## Formula variables

| Var | Meaning | Type | Source |
|-----|---------|------|--------|
| F | Fraction of exams where topic appeared (0–1) | computed | programmatic |
| G | Average mark fraction when present (0–1) | computed | from exam marks |
| C | Connection / node value (1–3) | integer | AI, stored in taxonomy.json |
| D | Difficulty bucket (1–6, hour-based) | integer | AI, stored in taxonomy.json |
| Fmt | Format depth (1=MCQ, 2=short answer, 3=write code) | float | weighted from exam data |

D and C are estimated **once per topic** and stored in `taxonomy.json`. They are never re-estimated when a new exam is added — only new topics get scored.

## File layout

```
pipeline/
├── pipeline.py          # main script — all logic lives here
├── taxonomy.json         # canonical topic list with D, C, prerequisites (auto-created)
├── parsed/                # one JSON file per processed exam (audit trail, auto-created)
│   └── <exam_id>.json
├── Exam_ROI_Pipeline.xlsx # output spreadsheet (rebuilt on every run)
└── docs/
    └── pipeline_docs.md   # this file
```

**Do not edit** `parsed/*.json` by hand — they are the source of truth for aggregation. To fix a bad AI score, use `edit-topic` or edit `taxonomy.json` directly, then run `rebuild`.

## LLM provider

The pipeline talks to whichever provider `LLM_PROVIDER` selects (default `anthropic`). `deepseek` and `openai` both use the OpenAI-compatible chat-completions API, so switching between them — or pointing at any other OpenAI-compatible host — needs no code changes, only a new entry in the `PROVIDERS` dict in `pipeline.py` if the provider isn't already listed.

```bash
# Anthropic (default)
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# DeepSeek
pip install openai
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY=sk-...

# OpenAI
pip install openai
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

Windows CMD: use `set VAR=value` instead of `export VAR=value`.

Override the default models per provider with `LLM_MODEL_STAGE1` / `LLM_MODEL_STAGE2` if needed.

## Key commands

```bash
# Install dependencies (once) — see "LLM provider" above for which SDK to install
pip install -r requirements.txt

# Add a single exam and rebuild the spreadsheet
python pipeline.py add exam_2022.txt
python pipeline.py add exam_2023.pdf --year 2023 --total-marks 100
python pipeline.py add exam_2024.txt --force              # reprocess an existing exam

# Add every .txt/.pdf in a folder in one go
python pipeline.py add-folder exams/computer_vision
python pipeline.py add-folder exams/ --recursive --force

# Rebuild spreadsheet without re-running the LLM (fast)
python pipeline.py rebuild

# Show what's been processed
python pipeline.py status

# Override a bad AI score for a topic, then rebuild
python pipeline.py edit-topic "Big-O Notation" --d 2 --c 3
```

## Two-stage AI pipeline (in pipeline.py)

**Stage 1 — `stage1_extract()`**: One LLM call per exam. Extracts `{q_id, text, marks, format}` for every question. Format must be one of: `mcq`, `short_answer`, `explain_derive`, `write_code_or_proof`.

**Stage 2 — `stage2_tag_score()`**: Tags every question with topic labels, then scores only the genuinely new topics. Internally this is two sub-steps to keep responses well under the token budget on long exams:
- `_stage2_tag()` — tags questions in batches of `STAGE2_BATCH_SIZE` (default 40), reusing existing taxonomy labels and carrying newly-coined labels forward across batches so later batches don't invent near-duplicates.
- `_stage2_score_new()` — estimates `difficulty_d`, `difficulty_hours`, `connection_c`, `prerequisites` only for topics that don't already exist in `taxonomy.json`.

All arithmetic (`marks_total`, `mark_fraction`, `format_distribution`) is computed locally in Python from the tags, not by the LLM — this keeps the model's job to judgement calls only, and means a response can never overflow its token budget on a long exam.

`call_llm()` streams the Anthropic response (required at 32k output tokens — the SDK rejects that large a non-streaming call) and raises `TruncatedResponse` if the reply was cut off by the token limit, so a truncated JSON never gets silently parsed.

## taxonomy.json schema

```json
{
  "topics": {
    "Topic Name": {
      "difficulty_d": 3,
      "difficulty_hours": "1–3h",
      "connection_c": 2,
      "prerequisites": ["Other Topic"],
      "first_seen": "exam_2022"
    }
  }
}
```

## parsed/\<exam_id\>.json schema

```json
{
  "exam_id": "exam_2022",
  "year": 2022,
  "total_marks": 100,
  "source_file": "exam_2022.txt",
  "processed_at": "2024-01-01T00:00:00",
  "questions": [{ "q_id": "Q1", "text": "...", "marks": 10, "format": "mcq", "topics": ["Big-O Notation"] }],
  "per_topic": {
    "Big-O Notation": {
      "marks_total": 10,
      "mark_fraction": 0.1,
      "format_distribution": { "mcq": 1.0 },
      "dominant_format": "mcq",
      "difficulty_d": 3,
      "difficulty_hours": "1–3h",
      "connection_c": 3,
      "prerequisites": [],
      "is_new_topic": false
    }
  }
}
```

## Spreadsheet structure

**ROI Scores sheet** — one row per topic, sorted by Priority descending:
- Fixed cols: Rank · Tier · Topic · F · G · C · D · Fmt · Priority
- Per-exam audit cols (one set per exam): `YYYY ✓` (0/1) · `YYYY marks%` · `YYYY Fmt`
- Tail cols: D hours · Prerequisites

**Taxonomy sheet** — one row per topic, D and C columns are yellow (editable overrides).

**Exam Log sheet** — one row per processed exam.

## Common tasks

- **Fix JSON parse errors**: a Stage 1/2 response may include markdown fences or prose before the JSON. `parse_json_from()` in pipeline.py handles this — if it breaks, check that function first.
- **Add a new format type**: add to `FMT_SCORE` and update the Stage 1 format list in `_S1_SYSTEM`/the extraction prompt.
- **Change the model**: set `LLM_MODEL_STAGE1` / `LLM_MODEL_STAGE2`, or edit the `default_stage1` / `default_stage2` entries in `PROVIDERS`.
- **Add a new provider**: add an entry to `PROVIDERS` in pipeline.py — if it's OpenAI-compatible, `"sdk": "openai"` is enough; nothing else in the file needs to change.
- **Add recency weighting**: aggregate loop in `cmd_rebuild()` — weight each exam by `lambda^age` before computing F and G.
- **Debug a bad topic extraction**: check `parsed/<exam_id>.json` — the raw tagged output is stored there verbatim.
