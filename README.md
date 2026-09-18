# Exam ROI Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pipeline/requirements.txt)

A Python CLI that reads past exam papers and ranks topics by relative study priority.
It accepts text files and PDFs with a text layer, keeps each course's state in one
folder, and writes the ranking as Excel and JSON.

For development, start with the [contributor guide](CONTRIBUTING.md). Use the
[documentation index](docs/README.md) to find a guide by task, or read the
[current architecture](docs/architecture.md) to trace the two-stage MVP.

> [!IMPORTANT]
> The current `add-exam` command saves validated analyses to `candidates/`. It does
> not promote them into accepted `parsed/` records. The repository does not yet have
> a CLI command for that promotion, so adding a new paper is not an end-to-end path
> to a new ranking. `rebuild` only uses records already accepted into `parsed/`.

---

## The idea

Given a pile of past exams, topics differ in their observed exam value. Some topics appear on
every paper and are worth many marks; others show up once, worth two. The pipeline scores every
topic using observed frequency and marks, downstream usefulness, conceptual and reasoning
complexity, and response mode. It combines them into one **Priority Score**:

```
Priority = 100 × (Freq × G_Marks × Conn) / (Diff × Fmt)
  Freq    = fraction of past exams the topic appeared in     (0–1, computed)
  G_Marks = average mark share when it did appear             (0–1, computed)
  Conn    = connection value: how much it unlocks downstream (1–3, qualitative estimate)
  Diff    = conceptual and reasoning complexity               (1–6, qualitative estimate)
  Fmt     = response-mode weight: MCQ=1, answer/derive=2, code/proof=3
```

The pipeline does not teach or evaluate understanding. It only answers "where should
I start?" See [`pipeline/docs/Topic_ROI_Exam_Analysis_System.md`](pipeline/docs/Topic_ROI_Exam_Analysis_System.md)
for the supported methodology behind the formula. This is a relative ranking heuristic,
not predicted marks or a study-duration estimate. Difficulty is independent of marks and
response format; the separate format weight remains part of the existing ranking formula.

The authoritative [evaluation contract 1.2.0](pipeline/exam_roi/contracts/evaluation-v1.2.0.md)
defines the six difficulty anchors, evidence requirements, and ambiguity rules. New topic
scores cite their source questions and record the contract version.

The MVP has two model stages:

- Stage 1 extracts questions and marks.
- Stage 2 tags topics and supplies qualitative judgments with evidence.

Python validates both responses and calculates the deterministic metrics. Independent
model review is disabled in the MVP CLI. The
[independent review reference](pipeline/docs/independent-review.md) describes the retained
implementation for later work.

Each candidate records judgments for every topic the paper tests, including
existing topics, and proposes taxonomy changes without applying them. `rebuild`
recomputes accepted taxonomy summaries from compatible accepted records.
Connection counts distinct supported dependencies, and difficulty combines question
levels with equal weight per paper. Conflicts are flagged; more evidence does not
guarantee a higher score or greater accuracy.

The pipeline works from exam papers alone. It infers background assumptions and
records supporting quotes and reasons. No manual prerequisite list or syllabus is
needed. Human overrides remain protected while automatic estimates update separately.
Reprocessing with `--force` replaces its candidate after successful analysis.

Older parsed records may lack the required dependency evidence. `add-exam --force`
can produce a new candidate but cannot update those accepted records. `rebuild`
refreshes the taxonomy and exports from accepted evidence without model calls;
it does not convert older judgments. Review notes identify excluded older evidence
and conflicting judgments. Candidate promotion remains pending in ticket 08.

## Example output

Running `rebuild` on accepted papers produces a ranked list like this. This is an
illustrative excerpt; the empty `Courses/Example_Course/` folder does not contain
accepted sample data.

| Rank | Topic | Priority | Freq | G_Marks | Conn | Diff | Fmt | Tier |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Hypothesis Testing | 18.9 | 1.00 | 0.22 | 3 | 2 | 1.75 | Tier 1 |
| 2 | Confidence Intervals | 11.8 | 0.83 | 0.19 | 3 | 2 | 2.00 | Tier 1 |
| 3 | Regression Basics | 8.0 | 0.67 | 0.24 | 2 | 2 | 2.00 | Tier 1 |
| 4 | Bayes' Theorem | 3.0 | 0.50 | 0.12 | 3 | 3 | 2.00 | |
| 5 | Sampling Distributions | 1.1 | 0.33 | 0.09 | 3 | 4 | 2.00 | |

Each successful rebuild also writes this ranking as a flat JSON array
(`Exam_ROI_Pipeline.json`) alongside the formatted `.xlsx`. A script or model can read
the JSON without a spreadsheet library.

## Quickstart

Follow the [offline environment setup](CONTRIBUTING.md#set-up-offline-development)
first. No provider credentials are needed for tests, help, status, dry runs, or
rebuilding existing accepted records. Run commands from the repository root.

Live analysis requires the separate [provider setup and approval](CONTRIBUTING.md#optional-live-provider-setup).
The provider receives extracted text. Approve the provider, exact models, and
expected cost before running `add-exam` without `--dry-run`.

Every command has this shape. The course folder always comes first:

```text
python pipeline/pipeline.py COURSE_FOLDER COMMAND [options]
```

`COURSE_FOLDER` holds the papers, saved state, and generated reports. The CLI creates
it on first use.

```powershell
# Preview which files the command would read. This makes no API calls.
python pipeline/pipeline.py "Courses/Statistics/final_01_06_2027" add-exam --dry-run

# Inspect the taxonomy, accepted papers, and whether report files exist.
python pipeline/pipeline.py "Courses/Statistics/final_01_06_2027" status

# Regenerate Excel and JSON from records already accepted in parsed/. No API calls.
python pipeline/pipeline.py "Courses/Statistics/final_01_06_2027" rebuild
```

After live-provider approval and configuration, analyze one paper with
`python pipeline/pipeline.py "Courses/Statistics/final_01_06_2027" add-exam "exam_2026.pdf"`.
This saves a candidate. With no accepted papers, `rebuild` creates no new reports.

Run `python pipeline/pipeline.py` for the short help screen, or append `--help` to a
command for all of its options.

### Commands

| Command | What it does |
|---|---|
| `add-exam [FILE\|FOLDER ...]` | Validates selected papers, runs the two-stage model analysis, and saves candidate JSON. |
| `status` | Shows taxonomy and accepted-paper counts, plus whether the Excel and JSON reports exist. |
| `rebuild` | Recomputes the ranking and rewrites Excel and JSON from accepted records, without model calls. |
| `edit-topic TOPIC` | Overrides a topic's difficulty or connection score, then rebuilds the reports. |

### Exit codes

Every command returns one of these, so a script (or `$?`/`$LASTEXITCODE`) can tell a clean
run from a partial one without parsing the log:

| Code | Meaning |
|---:|---|
| 0 | Everything requested succeeded. A skip for an existing record or a no-op rebuild still counts as success. |
| 1 | A setup or usage problem stopped the command before any work ran, such as a bad course folder, missing credentials, or an unknown topic name. |
| 2 | Reserved by argparse for usage errors such as an unknown flag or invalid choice. Nothing ran. |
| 3 | At least one requested paper failed during `add-exam`. Successful papers keep their saved candidates. The error names each failed file and its recovery action. |
| 4 | `rebuild` (or the rebuild step inside `edit-topic`) could not write `Exam_ROI_Pipeline.xlsx`/`.json`. Parsed papers and taxonomy already on disk are unaffected; rerunning `rebuild` once the cause (e.g. the spreadsheet open elsewhere) is cleared is the whole fix. |
| 5 | Course state is locked, corrupt, incompatible, or needs transaction recovery. Follow the named lock or record diagnostic before retrying; `--force` cannot bypass a state failure. |

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

Papers go in as UTF-8 `.txt`, or as `.pdf` with a text layer. The pipeline does not
render pages or run OCR. Scanned papers are unsupported; use a text-layer copy or
transcribe the source. Adding an OCR service requires separate approval and an
expected cost. Live analysis sends extracted text to the configured provider;
the source file stays on disk.

A paper is refused *before any AI call*, so it costs nothing, when it holds no text, when a
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
step so malformed or unresolved model output cannot affect the study ranking. The current
repository does not provide that step as a CLI command.

Several papers in the same year, including models, sittings, and resits, are normal. Each paper
is its own record and its own set of columns, labelled by whatever its filename doesn't share
with the others (`2022 Lunes`, `2022 Martes`). The year comes from the filename, or from the
paper itself when the filename is silent, and an academic year like `2021-2022` counts as the
year the paper was sat: 2022. Pass `--year` to overrule it. See
[`docs/adr/0007-one-record-per-paper-and-the-sitting-year.md`](docs/adr/0007-one-record-per-paper-and-the-sitting-year.md).

The `LLM_PROVIDER` variable selects Anthropic, DeepSeek, OpenAI, OpenRouter, or
UnoRouter. Anthropic is the default when it is absent. See the
[provider setup](CONTRIBUTING.md#optional-live-provider-setup) for configuration.

One folder holds one exam's worth of state, and nothing is shared between folders. A second
exam uses a second folder, named on its own commands (see
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
`candidates/` directories, including immediately before saving. It rejects redirected
state directories, file symlinks, and hard-linked records. Each course has an
operating-system lock, so two commands cannot update the same course at once. A
transaction journal restores a complete old or new state after an interrupted write.
See [course state and interruption recovery](docs/course-state-recovery.md) for the
recovery rules and filesystem requirements.

## Repository map

```
.
├── pipeline/
│   ├── pipeline.py              main course CLI
│   ├── staged_evaluation.py     model evaluation and replay CLI
│   ├── requirements.txt
│   ├── exam_roi/                inputs, model clients, validation, storage, scoring, reports
│   │   └── contracts/           versioned evaluation contracts
│   ├── tests/                   offline regression tests and synthetic fixtures
│   └── docs/                    methodology, request limits, and review behavior
│
├── Courses/                     optional home for local course folders
│   ├── Example_Course/          empty synthetic scaffold
│   └── <Course>/<type>_<date>/  one self-contained COURSE_FOLDER
│       ├── <past papers>.pdf    source files, optionally under exams/
│       ├── candidates/          validated analyses awaiting acceptance or review
│       ├── parsed/              accepted analyses, one JSON file per paper
│       ├── taxonomy.json        topic difficulty, connections, and prerequisites
│       └── Exam_ROI_Pipeline.{xlsx,json}
│
├── docs/
│   ├── adr/                     architecture decisions
│   └── solid/                   setup and usage guides
│
├── scripts/                     ticket backlog validation and maintenance
└── CONTEXT.md                   project glossary
```

The production CLI now delegates input handling, model access, evaluation, storage,
scoring, and report generation to `exam_roi` modules. [ADR 0008](docs/adr/0008-modular-pipeline-architecture.md)
explains the intended module boundaries. The current backlog is in
[Ticket status](.scratch/reliable-exam-analysis/TICKET_STATUS.md).

The [ticket workflow](docs/ticket-workflow.md) explains how to check that a problem
still exists before starting work and find older tickets affected by a change.
Ticket folders and metadata are authoritative; the status table is generated.
Run `python scripts/check_tickets.py` to validate the backlog and run its offline tests.

## More documentation

| Document | Use it for |
|---|---|
| [New course setup](docs/solid/new-course-setup.md) | Course folder conventions and the per-course workflow. |
| [Evaluation contract 1.2.0](pipeline/exam_roi/contracts/evaluation-v1.2.0.md) | Required evidence, difficulty anchors, and ambiguity rules. |
| [Independent review](pipeline/docs/independent-review.md) | Retained reviewer implementation, disabled in the MVP CLI. |
| [Model request limits](pipeline/docs/model-request-limits.md) | Context and output token budgets for both model stages. |
| [Course state recovery](docs/course-state-recovery.md) | Locking, transaction recovery, and damaged-state handling. |
| [Staged evaluation](docs/staged-evaluation.md) | Capture, audit, approve, and replay model evaluation fixtures. |

## Studying with the output

This repo's scope ends at the ranked list above. It decides *what* to study, not how. A separate
project, [`exam-prep-prompt`](https://github.com/tequers/exam-prep-prompt), reads this pipeline's
output and turns it into an actual study session with whatever LLM you have open. It's optional
and shares no code with this repo. The generated files are the only link between the projects.

## Course folder conventions

- **One course folder is the atomic state boundary.** Each holds one exam's past-paper corpus,
  taxonomy, and ROI sheet. Nothing is shared across folders, even for the same subject. See
  [`CONTEXT.md`](CONTEXT.md) and
  [`docs/adr/0001-course-exam-hierarchy.md`](docs/adr/0001-course-exam-hierarchy.md).
- **Exam folder names are `<type>_<date>`**, e.g. `final_26_08_2026`, `theory_20_08_2026`.
- **Grouping them as `Courses/<Course>/<Exam>/` is a convention, not a requirement.** The CLI
  takes whatever folder you hand it; this repo arranges its own under `Courses/`.
- **Course materials are never committed.** Lecture slides, exam papers, exercise sheets, and
  the pipeline's verbatim text extractions (`candidates/*.json` and `parsed/*.json`) are
  copyrighted or personal. See
  `.gitignore`. The pipeline reads them locally; the repo only ships the code that processes
  them, plus one synthetic example.

See [`docs/adr/`](docs/adr/) for the reasoning behind these decisions, in particular
[ADR 0005](docs/adr/0005-portfolio-cleanup-and-repo-split.md) for why the repo looks the way it
does today.

## License

[MIT](LICENSE) © 2026 Alberto Antequera Fernandez Palacios
