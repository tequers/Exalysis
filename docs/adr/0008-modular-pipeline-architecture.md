# 0008: Use focused modules in the MVP pipeline

**Status:** accepted
**Date:** 2026-09-11
**Last updated:** 2026-09-18

## Decision

The MVP remains one command-line application. Its code is divided into focused
modules under `pipeline/exam_roi/`.

Each module owns one type of work. `pipeline/pipeline.py` coordinates those
modules and provides the command-line interface. This structure keeps the MVP
simple while preventing model calls, validation, storage, scoring, and report
generation from becoming one large block of code.

The MVP does not use microservices, plug-ins, or a general framework.

## Why the MVP is modular

The pipeline combines model-dependent analysis with deterministic operations
such as validation, scoring, file storage, and report generation. These parts
have different failure modes and testing needs.

Separating them makes it possible to:

- test deterministic rules without calling a model;
- replace or fake model clients in tests;
- change report formatting without changing analytical rules;
- protect course data behind one storage interface; and
- find the code responsible for a behavior quickly.

## Current modules and responsibilities

| Project area | Responsibility |
|---|---|
| `pipeline/pipeline.py` | Parses commands, loads startup configuration, defines model prompts, coordinates the workflow, and reports results and exit codes. |
| `pipeline/exam_roi/inputs.py` | Finds exam files, extracts supported text, and records where the extracted content came from. |
| `pipeline/exam_roi/identity.py` | Validates exam identifiers and creates safe, contained paths for exam records. |
| `pipeline/exam_roi/question_context.py` | Builds question groups and the source context used as evidence during analysis. |
| `pipeline/exam_roi/llm.py` | Provides model clients, provider adapters, request limits, batching, retries, and model-response errors. |
| `pipeline/exam_roi/evaluation.py` | Validates model output and evidence, then builds a candidate exam analysis. |
| `pipeline/exam_roi/contracts/` | Documents the versioned evaluation contract that model output must follow. |
| `pipeline/exam_roi/taxonomy.py` | Aggregates topic classifications while preserving human overrides. |
| `pipeline/exam_roi/scoring.py` | Calculates marks, rankings, tiers, and report data from explicit inputs. It does not call models or access files. |
| `pipeline/exam_roi/storage.py` | Owns course paths, snapshots, loading, locking, guarded writes, and recovery of interrupted writes. |
| `pipeline/exam_roi/reports.py` | Renders XLSX and JSON reports from supplied report data. It does not decide which analyses are accepted. |
| `pipeline/exam_roi/review.py` | Contains the independent review and correction loop. It is tested but disabled in the MVP command-line workflow. |
| `pipeline/staged_evaluation.py` | Runs staged evaluation separately from normal course processing. |

## How the modules work together

For exam analysis, `pipeline.py` coordinates input extraction, identity checks,
question context, model calls, evaluation, proposed taxonomy changes, and
storage. The result is saved as a candidate. The MVP does not automatically
promote that candidate to accepted course data.

For report rebuilding, `pipeline.py` loads accepted course data, applies the
scoring rules, and passes the result to the report writers.

The entry point decides the order of operations. The focused modules own the
rules and mechanics within each step.

## Current limits

- CLI handling, prompts, and workflow coordination still share `pipeline.py`.
- Independent model review exists, but the MVP CLI does not run it.
- Candidate acceptance is not implemented as a separate module.
- Only accepted records are used to build reports.

These limits describe the current MVP. Future changes can introduce new
boundaries when the product needs them, but they are not part of this decision.

See the [current architecture](../architecture.md) for detailed command and data
flows.

## Consequences

The repository contains more files than a single-file application, so developers
must follow module boundaries when making changes. In return, the pipeline has
clear ownership, focused tests, and smaller areas of change.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `pipeline/pipeline.py` | Coordinates the focused modules while retaining CLI, prompts, and workflow code. | Coordination absorbs domain logic or a responsibility moves between modules. |
| `pipeline/exam_roi/scoring.py` | Implements the decision that scoring has no model or filesystem access. | Scoring inputs, side effects, or module boundaries change. |
| `pipeline/exam_roi/storage.py` | Implements the single ownership boundary for guarded state and recovery. | Storage ownership or separation from acceptance policy changes. |
| `pipeline/exam_roi/reports.py` | Implements rendering from supplied data without acceptance decisions. | Report inputs, side effects, or responsibility boundaries change. |
| `pipeline/exam_roi/review.py` | Implements the retained review module described as disabled in the CLI. | Reviewer responsibilities or production integration change. |
| `pipeline/exam_roi/inputs.py` | Lists input discovery and extraction as a focused module responsibility. | Input responsibilities move or the module interface changes. |
| `pipeline/exam_roi/identity.py` | Lists safe exam IDs and contained paths as the identity responsibility. | Identity responsibilities move or the module interface changes. |
| `pipeline/exam_roi/question_context.py` | Lists evidence context and question groups as a focused responsibility. | Context responsibilities move or the module interface changes. |
| `pipeline/exam_roi/llm.py` | Lists model clients, budgets, batching, and retries as the model-access boundary. | Model-access responsibilities move or its interface changes. |
| `pipeline/exam_roi/evaluation.py` | Lists candidate construction and validation as the evaluation boundary. | Validation responsibilities move or the candidate interface changes. |
| `pipeline/exam_roi/taxonomy.py` | Lists cumulative topic summaries and protected overrides as the taxonomy boundary. | Aggregation responsibilities move or taxonomy inputs change. |
| `pipeline/staged_evaluation.py` | Separates evaluation execution from normal course processing. | Evaluation entry points or production integration boundaries change. |
| `pipeline/exam_roi/contracts/evaluation-v1.2.0.md` | Implements the listed versioned runtime-contract responsibility. | The active contract, its location, or the runtime-resource boundary changes. |
<!-- doc-dependencies:end -->
