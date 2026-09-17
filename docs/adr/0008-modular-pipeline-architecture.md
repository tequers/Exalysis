# 0008: Modularize the exam analysis pipeline incrementally

**Status at proposal:** proposed implementation direction; no module extraction had been implemented by this document.
**Date:** 2026-09-11

## Implementation update on 2026-09-17

The two-stage MVP now delegates input handling, identity checks, source context,
model requests, evaluation, taxonomy aggregation, scoring, storage, and report
rendering to `pipeline/exam_roi/`. Tickets 18 through 20 supplied the package,
report/scoring extraction, and explicit course/model configuration. Production
imports do not require credentials or configure console streams.

CLI dispatch, prompts, and workflow coordination still live in `pipeline.py`.
There are no separate `cli.py`, `workflow.py`, or `acceptance.py` modules. Candidates
do not enter accepted state; ticket 08's acceptance workflow remains pending.
The independent reviewer module exists and has offline tests, but the MVP CLI
disables that stage. Staged evaluation is a separate runner, and broader calibration
remains pending.

The [current architecture](../architecture.md) maps actual modules and command
behavior. The original context, proposed boundaries, and migration sequence below
remain as the decision's history. References there to the single-file application
and future extraction describe the 2026-09-11 proposal, not today's file layout.

## Context and scope

The current application is one CLI in one Python file. At the architecture review it contained 1,541 lines, 35 top-level functions, and two classes; its workbook writer occupied 310 lines. Size alone does not require a split. The reason is that model judgments, deterministic arithmetic, course state, persistence, and presentation currently share configuration and execution paths.

The approved reliability backlog adds versioned evaluation rules, candidate validation, independent review, accepted revisions, recoverable persistence, and calibration. These responsibilities need interfaces that can be tested independently. Preserve the course-folder contract in [ADR 0006](0006-course-folder-as-cli-argument.md) and the exam identity semantics in [ADR 0007](0007-one-record-per-paper-and-the-sitting-year.md).

This document describes a target and its tradeoffs. The repository's actual files remain the source of truth for implementation progress. Exact module names below are illustrative; changes to acceptance policy or scoring semantics require their own explicit decision.

## Proposed direction

Keep one Python application and the existing command entry point. Introduce a small internal package incrementally. Organize modules around behavior and invariants, rather than one file per function.

| Module responsibility | Interface and ownership |
|---|---|
| CLI | Parse arguments, configure console output, render outcomes, and select exit codes. |
| Workflow | Coordinate input, analysis, acceptance, storage, and export operations. Keep the sequence readable. |
| Inputs | Discover papers, extract text, and resolve sitting metadata with evidence. |
| Model calls | Use explicitly configured clients for requests and defined failures; support separate analyzer and reviewer instances. |
| Scoring | Aggregate marks and calculate rankings and tiers from explicit inputs. Return results without model calls, filesystem access, or printing. |
| Storage | Own course paths, identity, serialization, locks, and recoverable revision commits. |
| Reports | Render a supplied report snapshot to XLSX and JSON without deciding which analyses are accepted. |
| Domain data, introduced with validation | Represent questions, evidence, candidates, accepted revisions, and review findings consistently. |
| Evaluation, introduced with its tickets | Apply the versioned contract, deterministic checks, and structured model-review rules. |
| Acceptance, introduced with its ticket | Own permitted transitions and promotion/withdrawal policy. Only accepted revisions feed reporting. |

A possible package name is `exam_roi`, with `cli`, `workflow`, `inputs`, `llm`, `scoring`, `storage`, and `reports` modules. Introduce domain, evaluation, and acceptance modules as their behavior lands. Keep calibration fixtures and runners outside production processing.

## Interface rules

- Read environment configuration and configure output streams at startup. Reusable module imports must not terminate the process, require credentials, or reconfigure global streams.
- Pass a course context/storage instance and model clients explicitly. Separate course operations must not silently share mutable path state.
- Domain representations and pure rules must not depend on the CLI, provider SDKs, or workbook formatting.
- Keep cross-module imports directional: the workflow coordinates modules; shared data definitions and pure scoring remain independent of the workflow.
- The model-call module hides provider differences. The storage module hides persistence and recovery mechanics. Callers should not repeat their internal steps.
- Candidate creation must not mutate accepted taxonomy. Acceptance policy determines eligibility; storage commits the resulting revision using concurrency checks and recovery guarantees.
- Exports consume the same identified snapshot. They cannot make acceptance decisions or update canonical topic judgments.
- A file move alone does not satisfy modularization if hidden global state and implicit initialization order remain.

## Benefits and tradeoffs

Separating scoring enables fast deterministic tests. Separating model calls enables fake adapters and independently configured reviewers. Storage and acceptance interfaces make data-quality invariants visible. Reports can change without touching analytical rules. Focused ownership reduces conflicting edits between agents.

The costs are additional navigation, interface design, packaging/import risks, and refactoring effort. Excessive forwarding layers or one class per function would add complexity. Use a small interface that hides substantial behavior. Separate files do not automatically provide transaction safety, valid judgments, or safe parallel implementation.

The single-file design remains defensible for a small fixed workflow, but would increasingly couple the approved lifecycle and review features. A complete rewrite, multiple deployable applications, or a general plugin framework is not justified by this backlog.

## Migration and verification

1. Establish characterization checks for intended current behavior using synthetic papers and temporary course folders. Treat known defects as defects rather than permanent compatibility requirements.
2. Ticket 18 establishes the internal package and extracts report rendering while preserving the current CLI.
3. Ticket 19 extracts deterministic mark aggregation and ranking.
4. Ticket 20 introduces explicit course/model configuration and removes import side effects.
5. Existing validation and storage tickets introduce shared domain records and persistence guarantees.
6. Existing review and acceptance tickets introduce those policies and their lifecycle.

Tickets 19 and 20 can proceed after 18 where ownership allows. They both affect the remaining entry file, so coordinate overlapping edits and integrate one at a time if necessary.

Keep relocation and behavioral changes in separate commits where practical. Compare semantic export contents, not byte-for-byte XLSX archives. Verify command invocation from the repository root and the existing pipeline working directory.

The refactoring tickets preserve current externally supported behavior except import-side-effect removal explicitly assigned to ticket 20. They must not silently change the ROI formula, apply new difficulty judgments, or migrate accepted course data.

## Effect on the backlog

[Ticket status](../../.scratch/reliable-exam-analysis/TICKET_STATUS.md) lists the work, its current state, and its unresolved blockers.

- Existing IDs 01–17 remain stable.
- New tickets 18–20 cover bounded preparatory refactoring.
- Ticket 02 depends on 20 for explicit dependencies.
- Ticket 03 depends on 19 for the shared arithmetic implementation.
- Ticket 07 depends on 20 for explicit course state.
- Ticket 17 depends on 19 for pure ranking.
- Reports work in 16 and provider work in 05 inherit the relevant prerequisites through their existing chains.
- Other fixes can proceed without waiting for every extraction. Code overlap still requires coordination even when the dependency graph permits parallel work.
- Create reviewed rubric examples during 01; complete the evaluation harness in 09. Its blockers do not postpone reference-example preparation.

Refactor only what an interface or ticket needs. A ticket is complete through demonstrated behavior, not through achieving a prescribed number of files.
