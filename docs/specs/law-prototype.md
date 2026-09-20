# LAW prototype export agreement

Approved by the owner on 2026-09-19 in the LAW portfolio conversation. Ticket 33 implements this agreement.

## Problem and intended result

The existing `add-exam` command saves candidates. `rebuild` reads accepted papers only, and there is no acceptance command. A new course therefore cannot produce the requested Excel and ranked agent JSON through the current two-stage workflow.

Add `add-exam --prototype --total-marks N` for compulsory-question papers with one known total. After successful analysis, export all current candidates in that course to `prototype/Exam_ROI_Pipeline.xlsx` and `prototype/Exam_ROI_Pipeline.json`. Candidate analyses remain unreviewed. Do not promote them or change accepted papers, the canonical taxonomy, or accepted reports.

Add `rebuild --prototype` to regenerate both files from candidates without model configuration or requests. Aggregate a temporary taxonomy from those candidates. Reuse its topic names when processing later papers in prototype mode. Forced replacement retracts the previous contribution of that paper.

## Extraction and scoring

In prototype mode, clarify Stage 1 instructions for spaced question numbers such as `0 1`, page furniture, complete scenarios, and questions with one shared mark allocation. Keep an unsplit question when its tasks share a single printed total. Use the existing `explain_derive` format for analytical essays. Preserve the default prompt and its historical replay evidence.

Prototype mode requires a finite positive explicit paper total. Before Stage 2, require finite nonnegative marks on every extracted question and require their sum to match that total. Saved candidates must meet the same rule before export. This limited check does not implement optional questions, marking schemes, or general score reconciliation from ticket 03.

Keep the existing one-or-two-topic assignments, equal mark shares, difficulty judgments, and ranking formula. Document these approximations rather than inventing finer mark allocations.

For the MVP, Stage 2 may list `prerequisites` or `unlocks` without duplicating every relationship in `connection_edges`. Missing matching edges do not reject or prevent saving a candidate. `Conn` must remain an integer from 1 through 3, but it does not have to match the number of listed `unlocks`. Any supplied edge must still pass structural and citation validation, and the temporary taxonomy derives relationships and its connection score only from validated edges.

In prototype mode, Stage 2 evidence quotes are advisory. Preserve a supplied string even when it is not a verbatim source substring, and normalize a missing or null quote to an empty string. Quote absence or mismatch must not prevent candidate storage, Excel generation, JSON generation, or offline rebuild. Question IDs, topic references, rationales, score ranges, and the remaining evidence structure stay validated. Non-prototype analysis keeps strict verbatim quote validation.

## Acceptance and failure cases

- A synthetic full command with injected model responses saves candidates and generates matching Excel and JSON rankings with visible unreviewed status and a shared generation identifier.
- The workbook retains the existing ROI Scores, Taxonomy, and Exam Log views. The JSON remains a ranked array with prototype metadata on each row.
- Rebuilding uses saved candidates without AI calls. It fails clearly when there are no candidates or incompatible saved candidates.
- In a batch, failed papers are named and produce a nonzero exit. Successful candidates survive. Automatic export waits for a successful batch; the user may explicitly rebuild the saved subset.
- Export rendering completes before either destination is replaced. Ordinary replacement failures attempt rollback and preserve candidates. Interrupted or failed exports can be rebuilt without another analysis. A shared generation identifier exposes mismatched files after a process interruption.
- Offline tests cover mark mismatch before Stage 2, missing totals before model configuration, forced replacement, later-paper topic reuse, report consistency, and export recovery.
- The owner runs the actual LAW paper and checks question coverage, marks, topics, and presentation before publishing selected results. The expected June 2025 example has 11 questions and 100 marks.

## Exclusions

No live or paid model calls, OCR, acceptance/reviewer implementation, scoring redesign, automatic publication, real-paper fixtures, or README revision. A successful offline test is not evidence of a successful live provider run. Only one LAW paper is currently present; additional comparable papers improve frequency estimates but are not a prerequisite for a first export.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `pipeline/pipeline.py` | Specifies opt-in commands and extraction behavior. | Command flags, validation timing, or prompt behavior change. |
| `pipeline/exam_roi/reports.py` | Reuses the workbook and ranked JSON formats. | Output fields, sheets, or labels change. |
| `pipeline/exam_roi/prototype.py` | Implements candidate selection, mark checks, and export recovery. | Prototype behavior changes. |
| `pipeline/tests/test_prototype.py` | Verifies the approved behavior offline. | Test coverage or acceptance criteria change. |
<!-- doc-dependencies:end -->
