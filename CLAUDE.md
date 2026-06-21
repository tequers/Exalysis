# Exam ROI Pipeline

A CLI pipeline that processes past CS exam files through Claude to extract topics, score ROI variables, and produce a ranked Excel study-priority spreadsheet.

## What this does

Given one or more past exams (text or PDF), the pipeline:
1. Extracts every question with its marks and format type
2. Tags each question with a canonical topic label (reusing existing labels, creating new ones only when necessary)
3. Estimates difficulty (D) and connection (C) scores for each topic via Claude
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
Computer Science Exams Pipeline/
├── pipeline.py          # main script — all logic lives here
├── requirements.txt     # anthropic, openpyxl, pypdf
├── taxonomy.json        # canonical topic list with D, C, prerequisites (auto-created)
├── parsed/              # one JSON file per processed exam (audit trail, auto-created)
│   └── exam_YYYY.json
├── Exam_ROI_Pipeline.xlsx  # output spreadsheet (rebuilt on every run)
└── CLAUDE.md            # this file
```

**Do not edit** `parsed/*.json` by hand — they are the source of truth for aggregation. To fix a bad AI score, use `edit-topic` or edit `taxonomy.json` directly, then run `rebuild`.

## Key commands

```bash
# Install dependencies (once)
pip install anthropic openpyxl pypdf

# Set API key (required)
export ANTHROPIC_API_KEY=sk-ant-...   # Mac/Linux
set ANTHROPIC_API_KEY=sk-ant-...      # Windows CMD

# Add an exam and rebuild the spreadsheet
python pipeline.py add exam_2022.txt
python pipeline.py add exam_2023.pdf --year 2023 --total-marks 100
python pipeline.py add exam_2024.txt --force    # reprocess an existing exam

# Rebuild spreadsheet without re-running AI (fast)
python pipeline.py rebuild

# Show what's been processed
python pipeline.py status

# Override a bad AI score for a topic, then rebuild
python pipeline.py edit-topic "Big-O Notation" --d 2 --c 3
```

## Two-stage AI pipeline (in pipeline.py)

**Stage 1 — `stage1_extract()`**: One Claude call per exam. Extracts `{q_id, text, marks, format}` for every question. Format must be one of: `mcq`, `short_answer`, `explain_derive`, `write_code_or_proof`.

**Stage 2 — `stage2_tag_score()`**: One Claude call per exam. Receives the questions from Stage 1 plus the current `taxonomy.json`. Tags each question with topic labels (reusing existing ones), and for each topic outputs `marks_total`, `mark_fraction`, `format_distribution`, `difficulty_d`, `difficulty_hours`, `connection_c`, `prerequisites`. The prompt explicitly instructs the model to copy D and C from existing taxonomy entries rather than re-estimating.

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

## parsed/exam_YYYY.json schema

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

## Common tasks for Claude Code

- **Fix JSON parse errors**: Stage 1 or 2 response may include markdown fences or prose before the JSON. `parse_json_from()` in pipeline.py handles this — if it breaks, check that function first.
- **Add a new format type**: Add to `FMT_SCORE` dict and update both stage prompts.
- **Change the model**: Edit `MODEL = "claude-sonnet-4-6"` at the top of pipeline.py.
- **Add recency weighting**: Aggregate loop in `cmd_rebuild()` — weight each exam by `lambda^age` before computing F and G.
- **Debug a bad topic extraction**: Check `parsed/<exam_id>.json` — the raw AI output is stored there verbatim.
