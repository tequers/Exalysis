# One exam type per Course

**Status:** accepted. [ADR 0006](./0006-course-folder-as-cli-argument.md) makes the Course folder the pipeline's working folder.

## Context

A subject can use different exam types, such as separate theory and practical exams. Giving one Course several exam types would require another hierarchy level, rules for selecting the active type, and rules for keeping their state separate. The MVP does not need that complexity.

The pipeline still needs multiple past papers to calculate topic frequency and exam ROI. Those papers are different sittings of the same exam type, not different exam types.

## Decision

In the MVP, one Course folder contains papers for exactly one exam type. The Course folder is the atomic state boundary. It owns that exam type's past-paper corpus, `taxonomy.json`, candidate and parsed records, and reports.

The pipeline never combines state from separate Course folders. If a subject has another exam type, the user creates another Course folder, such as `OPERATING_SYSTEMS_EXAM_2`, and runs the pipeline there. Each folder remains independent even when both folders belong to the same subject.

## Consequences

The MVP needs no nested exam-type hierarchy or active-exam selection rule. Course setup and pipeline commands always refer to one folder and one exam type.

A future architecture decision may add multiple exam types to one Course. Until then, separate Course folders provide the same isolation without extra state or selection logic.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `pipeline/exam_roi/storage.py` | Isolated course storage implements the decided exam state boundary. | State becomes shared, split, or merged across course folders. |
<!-- doc-dependencies:end -->
