# Exam ROI Pipeline

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pipeline/requirements.txt)

A Python CLI that reads past exam papers and ranks topics by relative study priority.
It accepts text files and PDFs with a text layer, keeps each course's state in one
folder, and writes the ranking as Excel and JSON.

Use these documents to understand and run the project:

- [Documentation index](docs/README.md). Find a guide by task.
- [Current architecture](docs/architecture.md). Trace the two-stage MVP from input
  selection to candidate storage and accepted-record reports.

> [!IMPORTANT]
> The current `add-exam` command saves validated analyses to `candidates/`. It does
> not promote them into accepted `parsed/` records. The repository does not yet have
> a CLI command for that promotion, so adding a new paper is not an end-to-end path
> to an accepted ranking. For an unreviewed demonstration, `--prototype` builds
> Excel and JSON directly from saved candidates. `rebuild` without that flag only
> uses records already accepted into `parsed/`.

---

## How the ranking works

Past exams give each topic a different observed value. The pipeline combines that
evidence into one **Priority Score**:

```
Priority = 100 × (Freq × G_Marks × Conn) / (Diff × Fmt)
```

The score uses these inputs:

- `Freq`: The fraction of accepted past exams that test the topic. Python computes
  this value from 0 to 1.
- `G_Marks`: The average mark share when the topic appears. Python computes this
  value from 0 to 1.
- `Conn`: An evidence-backed estimate of how much the topic unlocks downstream,
  from 1 to 3.
- `Diff`: An evidence-backed estimate of conceptual and reasoning complexity,
  from 1 to 6.
- `Fmt`: A response-mode weight. Multiple choice is 1, explanation or derivation is
  2, and code or proof is 3.

The score answers "where should I start?" It does not predict marks, estimate study
time, teach the material, or evaluate a student's understanding. Difficulty is
independent of marks and response format. See the
[ranking methodology](docs/guides/scoring-methodology.md) for the supported
formula and its limits.

The authoritative [evaluation contract 1.2.0](pipeline/exam_roi/contracts/evaluation-v1.2.0.md)
defines the six difficulty anchors, evidence requirements, and ambiguity rules. New topic
scores cite their source questions and record the contract version.

The MVP has two model stages:

- Stage 1 extracts questions and marks.
- Stage 2 tags topics and supplies qualitative judgments with evidence.

After the model stages:

- Python validates both responses and calculates the deterministic metrics.
- Independent model review stays disabled in the MVP CLI. The
  [independent review reference](docs/guides/independent-review.md) describes the
  retained implementation for later work.

Each candidate contains:

- A judgment for every topic that the paper tests, including existing topics.
- A supporting quote and reason for each model judgment.
- Proposed taxonomy changes that the pipeline does not apply automatically.
- Source and model provenance for later review.

Accepted records follow these rules:

- `add-exam` writes a validated candidate. It does not change `parsed/`,
  `taxonomy.json`, or the ranked outputs.
- `rebuild` recalculates taxonomy summaries and reports from compatible records in
  `parsed/`. It makes no model calls.
- Connection counts distinct supported dependencies.
- Difficulty gives each accepted paper equal weight when it combines question levels.
- Conflicting judgments are flagged. More evidence does not guarantee a higher score
  or greater accuracy.

The pipeline works from question-only exam papers. It infers background assumptions,
so it does not require a syllabus or a manual prerequisite list. Human overrides remain
protected while automatic estimates update separately. Reprocessing with `--force`
replaces only the candidate after a successful analysis.

## Example output

Running `rebuild` on accepted papers produces a ranked list like this. This is an
illustrative excerpt. The repository does not include accepted sample course data.

| Rank | Topic                  | Priority | Freq | G_Marks | Conn | Diff |  Fmt | Tier   |
| ---: | ---------------------- | -------: | ---: | ------: | ---: | ---: | ---: | ------ |
|    1 | Hypothesis Testing     |     18.9 | 1.00 |    0.22 |    3 |    2 | 1.75 | Tier 1 |
|    2 | Confidence Intervals   |     11.8 | 0.83 |    0.19 |    3 |    2 | 2.00 | Tier 1 |
|    3 | Regression Basics      |      8.0 | 0.67 |    0.24 |    2 |    2 | 2.00 | Tier 1 |
|    4 | Bayes' Theorem         |      3.0 | 0.50 |    0.12 |    3 |    3 | 2.00 |        |
|    5 | Sampling Distributions |      1.1 | 0.33 |    0.09 |    3 |    4 | 2.00 |        |

Each successful rebuild also writes this ranking as a flat JSON array
(`Exam_ROI_Pipeline.json`) alongside the formatted `.xlsx`. A script or model can read
the JSON without a spreadsheet library.

## Real example: three LAW exams

The first complete prototype run processed three LAW papers from 2023, 2024, and
2025. The two model stages extracted the questions, marks, topics, and provisional
judgments. Python then calculated the ranking and produced two views of the same
32-topic result:

```text
3 LAW exam PDFs -> question extraction -> topic analysis -> Excel + agent JSON
```

Create `Courses/LAW_1/exams/` and place the three LAW PDFs there first; exam files
are intentionally not included in the repository. Run the example from the
repository root in PowerShell and replace the API key placeholder with your own
UnoRouter key:

```powershell
$env:LLM_PROVIDER = "unorouter"
$env:UNOROUTER_API_KEY = "<your-api-key>"
$env:LLM_MODEL_STAGE1 = "deepseek-v4.1-flash"
$env:LLM_MODEL_STAGE2 = "deepseek-v4.1-flash"

$env:LLM_CONTEXT_TOKENS_STAGE1 = "1000000"
$env:LLM_CONTEXT_TOKENS_STAGE2 = "1000000"
$env:LLM_MAX_OUTPUT_TOKENS_STAGE1 = "655536"
$env:LLM_MAX_OUTPUT_TOKENS_STAGE2 = "655536"

python -X utf8 pipeline/pipeline.py "Courses/LAW_1" add-exam exams/ --prototype --total-marks 100
```

`Courses/LAW_1` is relative to the repository root. For an explicit input such as
`exams/`, the CLI first checks the current working directory and then the course
folder. Because the repository root has no `exams/` folder, this command resolves
it to `Courses/LAW_1/exams/`.

- `Courses/LAW_1/prototype/Exam_ROI_Pipeline.xlsx` gives a person a ranked
  overview, topic taxonomy, and exam log.
- `Courses/LAW_1/prototype/Exam_ROI_Pipeline.json` gives an AI agent the same
  ranked data in a flat array.

The top of this unreviewed prototype was:

| Rank | Topic                                 | Exams | Priority |
| ---: | ------------------------------------- | ----: | -------: |
|    1 | Lay Magistrates                       |   2/3 |   3.3333 |
|    2 | Criminal Courts and Trial Procedure   |   2/3 |   3.2945 |
|    3 | Non-Fatal Offences Against the Person |   2/3 |   2.7083 |

These values demonstrate the workflow; they still require subject-matter review.
See [run the LAW prototype](docs/guides/run-law-prototype.md) for the commands and
[prototype output format](docs/guides/prototype-output-format.md) for the workbook
and JSON fields.

> **Visual placeholder:** Add a screenshot or short GIF that shows the ranked LAW
> topics in the Excel workbook, then opens the matching JSON output.

## Quickstart

Before you run a command:

- Complete the [offline environment setup](docs/development/workflow.md#set-up-offline-development).
- Run commands from the repository root.
- You do not need provider credentials for tests, help, `status`, dry runs, or
  rebuilding accepted records.
- Before live analysis, complete the
  [provider setup and approval](docs/development/workflow.md#optional-live-provider-setup).
  The provider receives the extracted exam text. Approve the provider, exact models,
  and expected cost before you run `add-exam` without `--dry-run`.

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

| Command                       | What it does                                                                                   |
| ----------------------------- | ---------------------------------------------------------------------------------------------- |
| `add-exam [FILE\|FOLDER ...]` | Validates selected papers, runs the two-stage model analysis, and saves candidate JSON.        |
| `status`                      | Shows taxonomy and accepted-paper counts, plus whether the Excel and JSON reports exist.       |
| `rebuild`                     | Recomputes the ranking and rewrites Excel and JSON from accepted records, without model calls. |
| `edit-topic TOPIC`            | Overrides a topic's difficulty or connection score, then rebuilds the reports.                 |

### Exit codes

Every command returns one of these, so a script (or `$?`/`$LASTEXITCODE`) can tell a clean
run from a partial one without parsing the log:

| Code | Meaning                                                                                                                                                                                                                                                          |
| ---: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|    0 | Everything requested succeeded. A skip for an existing record or a no-op rebuild still counts as success.                                                                                                                                                        |
|    1 | A setup or usage problem stopped the command before any work ran, such as a bad course folder, missing credentials, or an unknown topic name.                                                                                                                    |
|    2 | Reserved by argparse for usage errors such as an unknown flag or invalid choice. Nothing ran.                                                                                                                                                                    |
|    3 | At least one requested paper failed during `add-exam`. Successful papers keep their saved candidates. The error names each failed file and its recovery action.                                                                                                  |
|    4 | `rebuild`, or the rebuild step inside `edit-topic`, could not write `Exam_ROI_Pipeline.xlsx` and `Exam_ROI_Pipeline.json`. Parsed papers and taxonomy remain unchanged. Close the spreadsheet if it is open, fix any other write error, and run `rebuild` again. |
|    5 | Course state is locked, corrupt, incompatible, or needs transaction recovery. Follow the lock or record diagnostic before retrying. `--force` cannot bypass a state failure.                                                                                     |

### Input files

**Use past papers without solutions.** The pipeline is designed for exams where only
the question paper is available. Do not include answer keys, marking schemes, worked
solutions, or model answers. If a source contains both questions and solutions, make a
question-only copy before you process it.

The pipeline accepts these file types:

- A UTF-8 `.txt` file.
- A `.pdf` file with a text layer on every page.

The pipeline does not render pages or run OCR. For a scanned paper, use a text-layer
copy or transcribe the source. Adding an OCR service requires separate approval and
an expected cost. During live analysis, the provider receives extracted text. The
source file stays on disk.

#### Select papers

`add-exam` selects papers with these rules:

- With no input paths, it scans the course root and its `exams/` subfolder.
- Explicit file or folder paths replace the default search. For example, use
  `add-exam exams/2024.pdf exams/2025.pdf`.
- `--recursive` searches below the selected folders. Recursive searches do not
  follow directory symlinks.
- The command excludes `candidates/` and `parsed/`, including resolved aliases.
- A relative path first resolves from the shell's working directory. If no path
  exists there, the command tries the course folder.
- An absolute path removes that resolution ambiguity.
- The command preserves input order, sorts each folder's matches, resolves paths,
  removes duplicates, and lists the final selection before processing.

Every matching `.txt` or `.pdf` file counts as a paper. This includes notes and
slides that use those extensions. Name the intended files or folders to exclude
unrelated material. Run `add-exam --dry-run` to inspect the selection without a
model call.

#### Validate extracted text

The pipeline rejects a paper before any model call when:

- The paper contains no text.
- A `.txt` file is not valid UTF-8. The error identifies the invalid byte.
- Any PDF page has no text layer. Continuing would omit that page's questions.

Each error names the file, the problem, and the recovery action. These checks do
not detect garbled glyphs, partial columns, flattened formulas, or incorrect reading
order. Inspect converted text before you trust the ranking. Accepted records keep
page and offset references in `source_provenance.extraction`.

#### Identify sittings and years

The pipeline stores each paper as a separate record and a separate report column:

- Models, sittings, and resits from the same year can coexist.
- Column labels use the filename parts that distinguish the papers, such as
  `2022 Lunes` and `2022 Martes`.
- The year comes from the filename or the paper text.
- An academic year such as `2021-2022` uses the later year, `2022`.
- `--year` overrides the detected year for one paper.

[ADR 0007](docs/adr/0007-one-record-per-paper-and-the-sitting-year.md) accepts a
stricter year-prefixed filename rule. The CLI does not yet enforce that decision;
the rules above describe current behavior.

### Course folders and providers

- `LLM_PROVIDER` selects Anthropic, DeepSeek, OpenAI, OpenRouter, or UnoRouter.
  Anthropic is the default. See the
  [provider setup](docs/development/workflow.md#optional-live-provider-setup).
- One course folder contains one exam's papers, state, and reports. State is never
  shared between course folders. See [ADR 0006](docs/adr/0006-course-folder-as-cli-argument.md).
- To create a course folder, follow the
  [new course setup](docs/guides/new-course-setup.md).

### Paper IDs and replacement

`--exam-id` accepts a filename ID such as `exam_2026_A`, not a path:

- A valid custom ID keeps its spelling, including internal spaces and Unicode.
- Without `--exam-id`, the pipeline uses the source filename without its extension
  and replaces spaces with underscores.
- To reprocess an older custom ID that converted spaces to underscores, use the
  stored underscore spelling.
- The pipeline rejects empty IDs, traversal, path separators, reserved device names,
  invalid filename characters, and trailing dots or spaces.
- The ID and `.json` extension must fit both a 255-byte UTF-8 filename and a
  255-unit UTF-16 filename.

Replacement follows these rules:

- The command skips an existing candidate or accepted record unless you use
  `--force`.
- If another source already owns an automatic ID, the pipeline adds a source-folder
  prefix.
- If all generated IDs are taken, choose a distinct `--exam-id`. `--force` does not
  bypass an automatic collision.
- An explicit ID selects that record even when the source moved to another path.
- With `--force`, the pipeline replaces only the candidate after a successful
  analysis. It does not change accepted records.

The storage layer protects course state:

- Record paths must stay inside the course's `parsed/` and `candidates/` directories.
- The pipeline rejects redirected state directories, file symlinks, and hard-linked
  records.
- An operating-system lock prevents two commands from updating one course at the
  same time.
- A transaction journal restores either the complete old state or the complete new
  state after an interrupted write.

See [course state and interruption recovery](docs/guides/course-state-recovery.md) for the
recovery rules and filesystem requirements.

## Repository map

```text
.
|-- pipeline/          application CLIs, package, runtime contracts, and tests
|-- scripts/           repository development tools and their tests
|-- docs/
|   |-- README.md      documentation index
|   |-- architecture.md
|   |-- glossary.md
|   |-- guides/        setup, usage, providers, and recovery
|   |-- development/   internal development and ticket workflow
|   |-- adr/           decisions, including SUPPRESSED/ history
|   `-- research/      maintained investigations and evidence
|-- tickets/           permanent backlog and generated status table
|-- Courses/           optional local course data; not included in a fresh clone
`-- .scratch/          ignored temporary local work
```

The [repository structure policy](docs/repository-structure.md) defines each
location, tracking rules, root exceptions, and how to maintain the layout.
Tool configuration stays in its required location.

The production CLI now delegates input handling, model access, evaluation, storage,
scoring, and report generation to `exam_roi` modules. [ADR 0008](docs/adr/0008-modular-pipeline-architecture.md)
explains the intended module boundaries. The current backlog is in
[Ticket status](tickets/TICKET_STATUS.md).

The [ticket workflow](docs/development/ticket-workflow.md) explains how to choose, update, and
verify project work. Ticket files are the source of truth, and the status table is
generated from them. Run `python scripts/check_tickets.py` to check the files and run
the ticket tests.

## More documentation

| Document                                                                      | Use it for                                                     |
| ----------------------------------------------------------------------------- | -------------------------------------------------------------- |
| [New course setup](docs/guides/new-course-setup.md)                            | Course folder conventions and the per-course workflow.         |
| [Evaluation contract 1.2.0](pipeline/exam_roi/contracts/evaluation-v1.2.0.md) | Required evidence, difficulty anchors, and ambiguity rules.    |
| [Independent review](docs/guides/independent-review.md)                     | Retained reviewer implementation, disabled in the MVP CLI.     |
| [Model request limits](docs/guides/model-request-limits.md)                 | Context and output token budgets for both model stages.        |
| [Course state recovery](docs/guides/course-state-recovery.md)                        | Locking, transaction recovery, and damaged-state handling.     |
| [Staged evaluation](docs/guides/staged-evaluation.md)                                | Capture, audit, approve, and replay model evaluation fixtures. |

## Studying with the output

This repo's scope ends at the ranked list above. It decides _what_ to study, not how. A separate
project, [`exam-prep-prompt`](https://github.com/tequers/exam-prep-prompt), reads this pipeline's
output and turns it into an actual study session with whatever LLM you have open. It's optional
and shares no code with this repo. The generated files are the only link between the projects.

## Course folder conventions

- **One course folder is the atomic state boundary.** Each holds one exam's past-paper corpus,
  taxonomy, and ROI sheet. Nothing is shared across folders, even for the same subject. See
  [`docs/glossary.md`](docs/glossary.md) and
  [`docs/adr/0001-course-exam-hierarchy.md`](docs/adr/0001-course-exam-hierarchy.md).
- **Exam folder names are `<type>_<date>`.** Examples include `final_26_08_2026`
  and `theory_20_08_2026`.
- **Grouping them as `Courses/<Course>/<Exam>/` is a convention, not a requirement.** The CLI
  accepts any course folder. This repository stores its own course folders under `Courses/`.
- **Course materials are never committed.** Lecture slides, exam papers, exercise sheets, and
  the pipeline's verbatim text extractions (`candidates/*.json` and `parsed/*.json`) are
  copyrighted or personal. See `.gitignore`. The pipeline reads them locally. The repository
  contains processing code and synthetic test fixtures.

See [`docs/adr/`](docs/adr/) for the reasoning behind these decisions, in particular
[ADR 0005](docs/adr/SUPPRESSED/0005-portfolio-cleanup-and-repo-split.md) for why the repo looks the way it
does today.

## License

Licensed under [PolyForm Noncommercial 1.0.0](LICENSE).
Copyright © 2026 Alberto Antequera Fernandez Palacios.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `docs/architecture.md` | Summarizes the available two-stage workflow and its limits. | Command availability, candidate acceptance, or module boundaries change. |
| `docs/glossary.md` | Uses Course, Exam, Topic, and Priority with their shared meanings. | Domain definitions or course isolation rules change. |
| `docs/guides/scoring-methodology.md` | Summarizes ranking arithmetic and evidence limits. | Formula, score interpretation, or aggregation rules change. |
| `docs/adr/0007-one-record-per-paper-and-the-sitting-year.md` | Describes current paper identity and year behavior beside the accepted naming decision. | The decision, its implementation status, or runtime identity rules change. |
| `docs/repository-structure.md` | Publishes a condensed repository map and tracking rules. | Maintained file locations or root exceptions change. |
| `docs/development/workflow.md` | Directs setup, offline checks, and approval before live analysis. | Setup commands, provider approval, or required checks change. |
| `pipeline/pipeline.py` | Documents commands, flags, exit codes, and candidate-only writes. | CLI arguments, outcomes, defaults, or acceptance behavior change. |
| `pipeline/exam_roi/inputs.py` | Documents input selection, extraction checks, and provenance. | Supported files, discovery order, exclusions, or text validation change. |
| `pipeline/exam_roi/identity.py` | Documents safe paper IDs and record paths. | ID validation, filename limits, or path guards change. |
| `pipeline/exam_roi/storage.py` | Summarizes locking, state validation, and recovery guarantees. | Locks, transactions, state versions, or recovery behavior change. |
| `pipeline/exam_roi/reports.py` | Describes report formats, fields, and paper labels. | Export schema, filenames, labels, or rendering behavior change. |
| `pipeline/requirements.txt` | Supplies the dependencies for documented installation. | Dependency lists, pins, or installation requirements change. |
| `docs/adr/0001-course-exam-hierarchy.md` | Applies the one-exam state boundary to course folder conventions. | Course hierarchy or sharing between exam types changes. |
| `docs/adr/0006-course-folder-as-cli-argument.md` | Documents the decided course-folder argument and independent destination. | Course selection or output-location policy changes. |
| `docs/adr/0008-modular-pipeline-architecture.md` | Summarizes the current division into focused pipeline modules. | Module boundaries or their implementation status change. |
| `docs/development/ticket-workflow.md` | Describes authoritative ticket records and the validation command. | Ticket authority, workflow entry points, or validation instructions change. |
| `docs/guides/course-state-recovery.md` | Summarizes storage protections and directs users to recovery procedures. | Lock, transaction, or recovery guarantees change. |
| `docs/guides/independent-review.md` | Summarizes the retained reviewer and disabled production integration. | Review availability or the meaning of review outcomes changes. |
| `pipeline/exam_roi/contracts/evaluation-v1.2.0.md` | Summarizes difficulty anchors, evidence requirements, and versioned judgments. | Active contract version, rubric, or evidence requirements change. |
| `LICENSE` | Displays the project license badge. | The license terms or declared license change. |
| `.gitignore` | Supports the policy that private course data and generated outputs stay out of Git. | Ignore rules or documented data-tracking boundaries change. |
<!-- doc-dependencies:end -->
