# Current architecture

This describes the checked-out two-stage MVP after the September 2026 branch
consolidation. The [contributor guide](../CONTRIBUTING.md) explains how to obtain
the appropriate branch and run its offline checks. [ADR 0008](adr/0008-modular-pipeline-architecture.md)
records the modularization direction and progress. The
[glossary](../CONTEXT.md) defines Course, Exam, and Topic.

## Two stages produce a candidate

The production entry point is [pipeline.py](../pipeline/pipeline.py). It owns CLI
dispatch, startup configuration, model prompts, and workflow coordination.
Its `process_exam_file` function coordinates these steps:

1. Resolve selected TXT/PDF inputs, exam identity, and course storage. Validate the
   text extraction before a model request. Inputs must be UTF-8 text or PDFs where
   every page yields text. There is no OCR. A text layer alone does not prove that
   extraction preserved formulas or reading order.
2. Stage 1 extracts complete questions, retained shared context, printed marks,
   response formats, and the sitting year. Python validates the response.
3. Stage 2 assigns topic names and supplies qualitative judgments with evidence.
   It includes tagging and topic-scoring requests, possibly split into batches.
   Python validates coverage and evidence and computes mark totals, fractions,
   format distributions, and other deterministic values.
4. Build a candidate with source and model provenance and the versioned
   [evaluation contract](../pipeline/exam_roi/contracts/evaluation-v1.2.0.md).
   Calculate proposed taxonomy changes in memory using the accepted snapshot plus
   this candidate. Ambiguity can leave the candidate marked `needs-review`.
5. Commit `candidates/EXAM_ID.json` through `CourseStore`. Accepted papers,
   `taxonomy.json`, and ranked outputs remain unchanged. The MVP records independent
   review as disabled. It rejects `--review` and nonzero `--review-corrections`.

Two model stages do not mean exactly two network requests. Batching and retries
can add requests. The [limits guide](../pipeline/docs/model-request-limits.md)
describes budgeting. With `--dry-run`, input selection stops before analysis and
requires no model configuration.

```text
TXT/PDF -> text extraction -> Stage 1 -> validation -> Stage 2 -> validation
  -> candidate plus proposed taxonomy -> candidates/EXAM_ID.json

parsed/*.json plus taxonomy.json -> rebuild -> taxonomy aggregation and ranking
  -> Exam_ROI_Pipeline.xlsx and Exam_ROI_Pipeline.json
```

There is currently no CLI transition between those two paths. Ticket 08 owns the
pending acceptance workflow. Copying a candidate into `parsed/` is not a documented
substitute for that policy.

## Accepted records produce reports

`rebuild` loads accepted papers from `parsed/` and the current taxonomy. It
recomputes taxonomy summaries from compatible stored evidence, preserves human
overrides, and commits taxonomy changes when needed. Pure scoring produces one
report snapshot, which the report writers render as Excel and JSON. This path
makes no model calls and does not inspect candidates as accepted evidence.

With no accepted papers, `rebuild` returns successfully without creating a new
report. `status` shows accepted-paper and taxonomy counts and report existence;
it does not certify that a report is current. `edit-topic` changes difficulty or
connection overrides for an existing accepted taxonomy topic and then rebuilds.
It does not create topics from candidate proposals.

`add-exam --force` replaces a successfully reprocessed candidate, even when an
accepted record with that ID exists. It neither replaces that accepted record nor
converts older accepted evidence. Contract versions retain their original meaning.

## Production modules

| Module | Responsibility |
|---|---|
| [pipeline.py](../pipeline/pipeline.py) | CLI parsing, console output and exit codes, configuration at startup, prompts, analysis orchestration, and command workflows. |
| [inputs.py](../pipeline/exam_roi/inputs.py) | File discovery, text/PDF extraction, input diagnostics, and extraction provenance. |
| [identity.py](../pipeline/exam_roi/identity.py) | Exam ID validation and contained record paths. |
| [question_context.py](../pipeline/exam_roi/question_context.py) | Shared source context, question groups, and evidence text used in stage requests and checks. |
| [llm.py](../pipeline/exam_roi/llm.py) | Explicit model clients, provider adapters, token budgets, batching, transport retries, and response failures. |
| [evaluation.py](../pipeline/exam_roi/evaluation.py) | Contract metadata, response and evidence validation, and candidate construction and classification. |
| [taxonomy.py](../pipeline/exam_roi/taxonomy.py) | Deterministic aggregation of compatible paper judgments and preservation of human overrides. |
| [scoring.py](../pipeline/exam_roi/scoring.py) | Pure per-paper arithmetic, ranking, tiers, and report data. |
| [storage.py](../pipeline/exam_roi/storage.py) | Course paths and snapshots, record loading, locks, guarded writes, and transaction recovery. |
| [reports.py](../pipeline/exam_roi/reports.py) | Excel/JSON rendering and paper labels from supplied report data. |
| [review.py](../pipeline/exam_roi/review.py) | Retained independent reviewer and correction loop, tested through injected clients but disabled in the MVP CLI. |

The CLI passes course paths and model clients explicitly. Reusable imports do not
need credentials or terminate the process. Scoring has no provider or storage
dependency. Storage does not decide whether a candidate is eligible for acceptance,
and report writers do not promote records. CLI and workflow code still share
`pipeline.py`; there are no separate `cli.py`, `workflow.py`, or `acceptance.py`
modules in this checkout.

Each course folder is an independent state boundary. A course lock serializes
commands that use `CourseStore`; its journal recovers interrupted state commits.
Bad or incompatible saved records stop processing rather than disappearing from
the calculation. Generated reports can be recreated with `rebuild`; follow the
[state recovery guide](course-state-recovery.md) for lock and record errors.

## Offline evidence and evaluation

[Pipeline tests](../pipeline/tests/) cover input handling, candidates, explicit
configuration, storage recovery, scoring, reports, and CLI outcomes. They use
temporary folders and injected clients. Reviewer tests establish protocol behavior,
not a live model's accuracy.

[staged_evaluation.py](../pipeline/staged_evaluation.py) is a separate evaluation
CLI. It captures or replays the production extraction and analysis functions with
synthetic cases. A human must approve reference evidence before it becomes a
trusted replay reference. The checked-in Astra capture remains unapproved evidence
with documented representation disagreements. See [staged evaluation](staged-evaluation.md).

[Ticket tooling](ticket-workflow.md) is separate from course processing. It uses
standard-library scripts and authoritative Markdown ticket records, then generates
the shared status table. It does not analyze papers or call providers.

## Pending work

The [backlog](../.scratch/reliable-exam-analysis/TICKET_STATUS.md) is the authority
for current ticket states. In this MVP, candidate acceptance, withdrawal, and the
associated CLI lifecycle from ticket 08 remain pending. Independent model review
exists as a tested module but is unavailable in normal CLI processing. Broader
calibration in ticket 09 remains pending; prototype captures do not settle it.

The additional architecture boundaries proposed in ADR 0008 are a direction, not
an inventory of modules already present. New acceptance policy, scoring changes,
and provider changes require their own reviewed work. OCR remains outside the MVP.
