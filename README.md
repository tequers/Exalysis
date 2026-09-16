# Exam ROI Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pipeline/requirements.txt)

A CLI that reads a course's past exam papers and tells you which topics are worth the most exam
marks per hour of study — for any text-based exam, any subject.

---

## The idea

Given a pile of past exams, not every topic is worth equal study time. Some topics appear on
every paper and are worth many marks; others show up once, worth two. The pipeline scores every
topic on four factors — how often it appears, how many marks it's worth, how foundational it is
(does understanding it unlock other topics), and how deeply it's tested (multiple choice vs.
writing a proof) — and ranks them by a single **Priority Score**:

```
Priority = 100 × (Freq × G_Marks × Conn) / (Diff × Fmt)
  Freq    = fraction of past exams the topic appeared in     (0–1, computed)
  G_Marks = average mark share when it did appear             (0–1, computed)
  Conn    = connection value — how much it unlocks downstream (1–3, LLM-estimated once)
  Diff    = difficulty                                        (1–6, LLM-estimated once)
  Fmt     = format depth: MCQ < short answer < derivation/code (1–3)
```

The pipeline does not teach and does not evaluate understanding — it only answers "where should
I start?" See [`pipeline/docs/Topic_ROI_Exam_Analysis_System.md`](pipeline/docs/Topic_ROI_Exam_Analysis_System.md)
for the full methodology behind the formula.

## Example output

Running `rebuild` on a course's past papers produces a ranked list like this — an illustrative
excerpt (top 5 of a longer list; values satisfy the formula above) — see
[Quickstart](#quickstart) to generate your own from `Courses/Example_Course/`):

| Rank | Topic | Priority | Freq | G_Marks | Conn | Diff | Fmt | Tier |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Hypothesis Testing | 18.9 | 1.00 | 0.22 | 3 | 2 | 1.75 | ★ Tier 1 |
| 2 | Confidence Intervals | 11.8 | 0.83 | 0.19 | 3 | 2 | 2.00 | ★ Tier 1 |
| 3 | Regression Basics | 8.0 | 0.67 | 0.24 | 2 | 2 | 2.00 | ★ Tier 1 |
| 4 | Bayes' Theorem | 3.0 | 0.50 | 0.12 | 3 | 3 | 2.00 | |
| 5 | Sampling Distributions | 1.5 | 0.33 | 0.09 | 4 | 4 | 2.00 | |

Every run also writes this same ranking as a flat JSON array
(`Exam_ROI_Pipeline.json`, alongside the formatted `.xlsx`) — meant to be read directly by a
script, or handed straight to an LLM, no spreadsheet library required.

## Quickstart

```bash
cd pipeline
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # or DEEPSEEK_API_KEY / OPENAI_API_KEY — see below

# drop a past exam (.txt or .pdf, real or made up) into Courses/Example_Course/final_01_01_2026/exams/
# — real course material is never committed, so this folder starts empty (see .gitignore)
mkdir -p "../Courses/Example_Course/final_01_01_2026/exams"

python pipeline.py add-folder "../Courses/Example_Course/final_01_01_2026/exams" --total-marks 100
python pipeline.py rebuild      # writes Exam_ROI_Pipeline.xlsx + .json
python pipeline.py status       # show current state
```

It picks a provider via the `LLM_PROVIDER` environment variable (`anthropic` by default;
`openai`, `deepseek`, or any other OpenAI-compatible endpoint also work — see the docstring at
the top of [`pipeline/pipeline.py`](pipeline/pipeline.py) for full setup and every subcommand).

It auto-detects the active `Courses/<Course>/<Exam>/` folder when exactly one exists, and needs
`--course`/`--exam` the moment a second one does — see
[`docs/adr/0003-active-exam-resolution.md`](docs/adr/0003-active-exam-resolution.md). To add a
new course from scratch, see
[`docs/solid/new-course-setup.md`](docs/solid/new-course-setup.md).

## Repository map

```
.
├── pipeline/                   the CLI and its docs
│   ├── pipeline.py             run this
│   ├── requirements.txt
│   └── docs/                   the ROI methodology spec
│
├── Courses/                    per-course, per-exam data (see CONTEXT.md)
│   ├── Example_Course/                 the one example shipped in the repo (synthetic)
│   └── <Course>/<type>_<date>/         e.g. final_26_08_2026 — one self-contained Exam
│       ├── exams/                      source past-paper files (gitignored)
│       ├── parsed/                     pipeline output: one JSON per past exam (gitignored)
│       ├── taxonomy.json               pipeline output: per-topic Diff, Conn, prerequisites
│       └── Exam_ROI_Pipeline.{xlsx,json}   pipeline output: the ranked study agenda
│
├── docs/
│   ├── adr/                    architecture decisions — why, not what
│   └── solid/                  usage guides (e.g. adding a new course)
│
└── CONTEXT.md                  glossary — Course, Exam, Topic, Priority Score
```

## Studying with the output

This repo's scope ends at the ranked list above — it decides *what* to study, not how. A separate
project, [`exam-prep-prompt`](https://github.com/tequers/exam-prep-prompt), reads this pipeline's
output and turns it into an actual study session with whatever LLM you have open. It's optional
and shares no code with this repo — the two are linked only by the files the pipeline produces.

## Conventions (so this stays scalable)

- **`Courses/<Course>/<Exam>/` is the atomic state boundary.** Course is purely organizational;
  each Exam owns its own past-paper corpus, taxonomy, and ROI sheet — nothing is shared across
  Exams, even within one Course. See [`CONTEXT.md`](CONTEXT.md) and
  [`docs/adr/0001-course-exam-hierarchy.md`](docs/adr/0001-course-exam-hierarchy.md).
- **Exam folder names are `<type>_<date>`**, e.g. `final_26_08_2026`, `theory_20_08_2026`.
- **Course materials are never committed.** Lecture slides, exam papers, exercise sheets, and
  the pipeline's verbatim text extractions (`parsed/*.json`) are copyrighted or personal — see
  `.gitignore`. The pipeline reads them locally; the repo only ships the code that processes
  them, plus one synthetic example.

See [`docs/adr/`](docs/adr/) for the reasoning behind these decisions, in particular
[ADR 0005](docs/adr/0005-portfolio-cleanup-and-repo-split.md) for why the repo looks the way it
does today.

## License

[MIT](LICENSE) © 2026 Alberto Antequera Fernandez Palacios
