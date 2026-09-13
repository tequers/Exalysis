# Exam ROI Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pipeline/requirements.txt)

A CLI that reads a course's past exam papers and ranks topics by
relative study priority — for text-based exams across subjects.

---

## The idea

Given a pile of past exams, topics differ in their observed exam value. Some topics appear on
every paper and are worth many marks; others show up once, worth two. The pipeline scores every
topic using observed frequency and marks, downstream usefulness, conceptual and reasoning
complexity, and response mode — and ranks them by a single **Priority Score**:

```
Priority = 100 × (Freq × G_Marks × Conn) / (Diff × Fmt)
  Freq    = fraction of past exams the topic appeared in     (0–1, computed)
  G_Marks = average mark share when it did appear             (0–1, computed)
  Conn    = connection value — how much it unlocks downstream (1–3, qualitative estimate)
  Diff    = conceptual and reasoning complexity               (1–6, qualitative estimate)
  Fmt     = response-mode weight: MCQ=1, answer/derive=2, code/proof=3
```

The pipeline does not teach and does not evaluate understanding — it only answers "where should
I start?" See [`pipeline/docs/Topic_ROI_Exam_Analysis_System.md`](pipeline/docs/Topic_ROI_Exam_Analysis_System.md)
for the supported methodology behind the formula. This is a relative ranking heuristic,
not predicted marks or a study-duration estimate. Difficulty is independent of marks and
response format; the separate format weight remains part of the existing ranking formula.

The authoritative [evaluation contract 1.2.0](pipeline/exam_roi/contracts/evaluation-v1.2.0.md)
defines the six difficulty anchors, evidence requirements, and ambiguity rules. New topic
scores cite their source questions and record the contract version.

Add `--review` to `add-exam` to run an independent evidence review before saving
the candidate. Configure `LLM_REVIEW_MODEL` and optionally `LLM_REVIEW_PROVIDER`.
Review failures and unresolved findings leave a `needs-review` candidate. See
[independent review](pipeline/docs/independent-review.md) for correction limits,
request budgets, and saved review history.

Each paper contributes independent judgments for every topic it tests, including
existing topics. The taxonomy is recomputed from all compatible stored evidence:
connection counts distinct supported dependencies, and difficulty combines question
levels with equal weight per paper. New topic names also trigger a connection review
of earlier papers, so relationships can be found regardless of discovery order.
These reviews add model calls when the taxonomy grows. Conflicts are flagged;
more evidence does not guarantee a higher score or greater accuracy.

The pipeline works from exam papers alone. It infers background assumptions and
records supporting quotes and reasons. No manual prerequisite list or syllabus is
needed. Human overrides remain protected while automatic estimates update separately.
Reprocessing a paper replaces its contribution instead of double-counting it.

Older parsed records lack the required dependency evidence. Reprocess their source
papers once with `add-exam --force` to include them in the new cumulative analysis.
`rebuild` refreshes the taxonomy and exports from stored current-version judgments,
without model calls; it does not convert older judgments. Review notes identify
excluded older evidence and conflicting judgments.

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
| 5 | Sampling Distributions | 1.1 | 0.33 | 0.09 | 3 | 4 | 2.00 | |

Every run also writes this same ranking as a flat JSON array
(`Exam_ROI_Pipeline.json`, alongside the formatted `.xlsx`) — meant to be read directly by a
script, or handed straight to an LLM, no spreadsheet library required.

## Quickstart

Every command has the same shape — **the course folder always comes first**:

```
python pipeline.py COURSE_FOLDER COMMAND [data]
```

That folder is where the pipeline both reads its state and writes its results. It is created on
the first run and updated in place on every run after it, so you never point at output files,
only at the folder that holds them. Run `python pipeline.py` with no arguments for the whole
of it on one screen, or `python pipeline.py COURSE_FOLDER add-exam --help` for one command's
options.

```bash
cd pipeline
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # or DEEPSEEK_API_KEY / OPENAI_API_KEY — see below

# put your past exams (.txt or .pdf) in a folder — anywhere on disk
python pipeline.py ~/Exams/Statistics add-exam exam_2023.pdf   # one paper
python pipeline.py ~/Exams/Statistics add-exam                 # every paper in the folder
python pipeline.py ~/Exams/Statistics status                   # what the folder holds now
python pipeline.py ~/Exams/Statistics rebuild                  # redo the ranking, no LLM calls
```

### Exit codes

Every command returns one of these, so a script (or `$?`/`$LASTEXITCODE`) can tell a clean
run from a partial one without parsing the log:

| Code | Meaning |
|---:|---|
| 0 | Everything requested succeeded. A skip (already accepted/candidate) or a no-op rebuild still counts as success — they did what was asked. |
| 1 | A setup or usage problem stopped the command before any work ran: a bad course folder, missing provider credentials, an unknown topic name, and the like. |
| 2 | Reserved by argparse for its own usage errors (an unknown flag, an invalid choice) — unrelated to the codes below, but also "nothing ran". |
| 3 | At least one requested paper failed to process on `add-exam`. Papers that *did* succeed keep their saved candidates — this is a partial result, not a crash. The failed files are named, along with what each one needs: fixing the input, a human review, or simply rerunning. |
| 4 | `rebuild` (or the rebuild step inside `edit-topic`) could not write `Exam_ROI_Pipeline.xlsx`/`.json`. Parsed papers and taxonomy already on disk are unaffected; rerunning `rebuild` once the cause (e.g. the spreadsheet open elsewhere) is cleared is the whole fix. |

### What it can read

With no input paths, `add-exam` combines `.txt` and `.pdf` files in the course
root and its `exams/` subfolder. `--recursive` also searches deeper folders.
The course's `candidates/` and `parsed/` directories are excluded, including
resolved aliases. Recursive searches do not follow directory symlinks.
Selected files are resolved to absolute paths and deduplicated, then listed
before processing. Use `add-exam --dry-run` to inspect the list without model calls.

Every matching TXT/PDF is treated as a paper, including notes or slides saved in
those formats. To leave unrelated material out, name only the intended files or
folders, for example `add-exam exams/2024.pdf exams/2025.pdf`. Explicit paths
replace the default search. An existing relative path in the shell's working
directory takes precedence over the same name inside the course folder. If it
does not exist there, the course folder is tried. Use an absolute path to remove
ambiguity. Inputs retain argument order, and each folder's matches are sorted.

Papers go in as **UTF-8 `.txt`**, or as **`.pdf` with a text layer**. Nothing is rendered and
no OCR is run, so a scanned paper has to be OCRed first (`ocrmypdf scan.pdf paper.pdf`) or
retyped as text. The text that comes out is sent to the configured provider to be analysed;
the file itself stays on your disk.

A paper is refused *before any AI call* — and so costs nothing — when it holds no text, when a
`.txt` file is not valid UTF-8 (the bad byte is reported rather than quietly replaced with `�`),
or when **any** page of a PDF has no text layer, since reading on would drop those questions
without saying so. Each message names the file, the problem, and the fix.

That check only asks whether a page produced *any* text. Garbled glyphs, half-read columns,
formulas flattened into noise and text pulled out of reading order all pass it, so skim a
converted paper before trusting its ranking. Page and offset references for every accepted
paper are kept in its record under `source_provenance.extraction`.

Each `add-exam` run writes a validated record to `candidates/`, including its evidence,
provenance, uncertainty, and proposed taxonomy changes. It does not change `parsed/`,
`taxonomy.json`, or the ranked outputs. Promotion into accepted course state is a separate
workflow so malformed or unresolved model output cannot affect the study ranking. That
acceptance workflow is intentionally outside ticket 02.

Several papers in the same year — models, sittings, resits — are the normal case, so each paper
is its own record and its own set of columns, labelled by whatever its filename doesn't share
with the others (`2022 Lunes`, `2022 Martes`). The year comes from the filename, or from the
paper itself when the filename is silent, and an academic year like `2021-2022` counts as the
year the paper was sat: 2022. Pass `--year` to overrule it. See
[`docs/adr/0007-one-record-per-paper-and-the-sitting-year.md`](docs/adr/0007-one-record-per-paper-and-the-sitting-year.md).

It picks a provider via the `LLM_PROVIDER` environment variable (`anthropic` by default;
`openai`, `deepseek`, or any other OpenAI-compatible endpoint also work — see the docstring at
the top of [`pipeline/pipeline.py`](pipeline/pipeline.py) for full setup and every subcommand).

One folder holds one exam's worth of state, and nothing is shared between folders — a second
exam is simply a second folder, named on its own commands (see
[`docs/adr/0006-course-folder-as-cli-argument.md`](docs/adr/0006-course-folder-as-cli-argument.md)).
To set up a new course from scratch, see
[`docs/solid/new-course-setup.md`](docs/solid/new-course-setup.md).

### Paper IDs and replacement

`--exam-id` takes a filename ID, such as `exam_2026_A`, never a path. Valid custom
IDs retain their spelling, including internal spaces and Unicode. Without an
explicit ID, the pipeline uses the source filename without its extension and
replaces spaces with underscores. For an older custom ID whose spaces were
converted to underscores, use the stored underscore spelling when reprocessing.

Empty IDs, traversal, separators, reserved device names, invalid filename
characters, and trailing dots or spaces are rejected. IDs must fit a 255-byte
UTF-8 filename and a 255-unit UTF-16 filename, including `.json`.

An existing candidate or accepted record is skipped unless `--force` is supplied.
An automatic ID already claimed by another source gains a source-folder prefix.
If all generated names are taken, choose a distinct `--exam-id`; `--force` does not
bypass automatic collisions. An explicit ID selects that record deliberately,
including when reprocessing a source stored at a different path. With `--force`,
only its candidate is replaced after successful analysis. Accepted records remain
unchanged.

The pipeline checks that record paths stay inside the course's `parsed/` and
`candidates/` directories, including immediately before saving. Redirected state
directories, file symlinks, and hard-linked records are rejected. These checks do
not provide writer locking or transactional recovery; those remain separate
storage work.

## Repository map

```
.
├── pipeline/                   the CLI and its docs
│   ├── pipeline.py             run this
│   ├── requirements.txt
│   ├── exam_roi/             versioned evaluation contract, input reading, pure rules
│   ├── tests/                offline regression checks and synthetic rubric examples
│   └── docs/                   the ROI methodology spec
│
├── Courses/                    a place to keep course folders (they can live anywhere)
│   ├── Example_Course/                 the one example shipped in the repo (synthetic)
│   └── <Course>/<type>_<date>/         a COURSE_FOLDER — one self-contained exam
│       ├── <past papers>.pdf           source files, here or in an exams/ subfolder (gitignored)
│       ├── candidates/                 validated analyses awaiting acceptance or review
│       ├── parsed/                     accepted analyses: one JSON per past exam (gitignored)
│       ├── taxonomy.json               pipeline output: per-topic Diff, Conn, prerequisites
│       └── Exam_ROI_Pipeline.{xlsx,json}   pipeline output: the ranked study agenda
│
├── docs/
│   ├── adr/                    architecture decisions — why, not what
│   └── solid/                  usage guides (e.g. adding a new course)
│
└── CONTEXT.md                  glossary — Course, Exam, Topic, Priority Score
```

Architecture and implementation backlog: [ADR 0008 — proposed modular pipeline](docs/adr/0008-modular-pipeline-architecture.md) records the rationale, module responsibilities, and migration tradeoffs; [Ticket status](.scratch/reliable-exam-analysis/TICKET_STATUS.md) shows the current queue and unresolved blockers. The repository map above describes the current implementation.

## Studying with the output

This repo's scope ends at the ranked list above — it decides *what* to study, not how. A separate
project, [`exam-prep-prompt`](https://github.com/tequers/exam-prep-prompt), reads this pipeline's
output and turns it into an actual study session with whatever LLM you have open. It's optional
and shares no code with this repo — the two are linked only by the files the pipeline produces.

## Conventions (so this stays scalable)

- **One course folder is the atomic state boundary.** Each holds one exam's past-paper corpus,
  taxonomy, and ROI sheet — nothing is shared across folders, even for the same subject. See
  [`CONTEXT.md`](CONTEXT.md) and
  [`docs/adr/0001-course-exam-hierarchy.md`](docs/adr/0001-course-exam-hierarchy.md).
- **Exam folder names are `<type>_<date>`**, e.g. `final_26_08_2026`, `theory_20_08_2026`.
- **Grouping them as `Courses/<Course>/<Exam>/` is a convention, not a requirement.** The CLI
  takes whatever folder you hand it; this repo arranges its own under `Courses/`.
- **Course materials are never committed.** Lecture slides, exam papers, exercise sheets, and
  the pipeline's verbatim text extractions (`candidates/*.json` and `parsed/*.json`) are
  copyrighted or personal — see
  `.gitignore`. The pipeline reads them locally; the repo only ships the code that processes
  them, plus one synthetic example.

See [`docs/adr/`](docs/adr/) for the reasoning behind these decisions, in particular
[ADR 0005](docs/adr/0005-portfolio-cleanup-and-repo-split.md) for why the repo looks the way it
does today.

## License

[MIT](LICENSE) © 2026 Alberto Antequera Fernandez Palacios
