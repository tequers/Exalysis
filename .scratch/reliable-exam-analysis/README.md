# Reliable exam analysis: ticket index

The architecture rationale and proposed module ownership live in [ADR 0008](../../docs/adr/0008-modular-pipeline-architecture.md). Each ticket owns its acceptance criteria and blocking edges. Keep IDs stable: execute dependencies, not filename order.

Tickets 18–20 add preparatory refactoring; 01–17 retain their original scope with architecture notes. Ticket 01 now owns a small `exam_roi` evaluation package; the broader module split remains planned. Keep these documents with the code in version control so worktrees can read them.

| ID | Ticket | Blocked by |
|---|---|---|
| 01 | [Define a versioned evaluation contract and qualitative difficulty rubric](issues/01-define-a-versioned-evaluation-contract-and-qualitative-difficulty-rubric.md) | None |
| 02 | [Apply the evaluation contract and validate candidate analyses](issues/02-apply-the-evaluation-contract-and-validate-candidate-analyses.md) | 01, 20 |
| 03 | [Validate question marks and supported exam scoring structures](issues/03-validate-question-marks-and-supported-exam-scoring-structures.md) | 02, 19 |
| 04 | [Reject incomplete text extraction before model processing](issues/04-reject-incomplete-text-extraction-before-model-processing.md) | None |
| 05 | [Preserve question context and respect model request limits](issues/05-preserve-question-context-and-respect-model-request-limits.md) | 02 |
| 06 | [Add an independent model review of candidate analyses](issues/06-add-an-independent-model-review-of-candidate-analyses.md) | 02, 03, 05 |
| 07 | [Make course-state updates recoverable and serialize writers](issues/07-make-course-state-updates-recoverable-and-serialize-writers.md) | 20 |
| 08 | [Gate promotion into accepted course state](issues/08-gate-promotion-into-accepted-course-state.md) | 02, 03, 06, 07 |
| 09 | [Calibrate extraction and judgments against reviewed reference examples](issues/09-calibrate-extraction-and-judgments-against-reviewed-reference-examples.md) | 01, 02, 06, 08 |
| 10 | [Constrain exam IDs to the intended state directory](issues/10-constrain-exam-ids-to-the-intended-state-directory.md) | None |
| 11 | [Make paper identity portable and detect stale cached inputs](issues/11-make-paper-identity-portable-and-detect-stale-cached-inputs.md) | 08, 10 |
| 12 | [Discover intended papers consistently and expose input selection](issues/12-discover-intended-papers-consistently-and-expose-input-selection.md) | None |
| 13 | [Resolve ambiguous sitting years and support metadata correction](issues/13-resolve-ambiguous-sitting-years-and-support-metadata-correction.md) | 08, 11 |
| 14 | [Merge and rename topics across accepted paper history](issues/14-merge-and-rename-topics-across-accepted-paper-history.md) | 02, 08 |
| 15 | [Return reliable CLI outcomes and actionable recovery instructions](issues/15-return-reliable-cli-outcomes-and-actionable-recovery-instructions.md) | None |
| 16 | [Make exports consistent and clarify supported overrides](issues/16-make-exports-consistent-and-clarify-supported-overrides.md) | 07, 08 |
| 17 | [Specify and verify the ranking and Tier 1 contract](issues/17-specify-and-verify-the-ranking-and-tier-1-contract.md) | 01, 03, 08, 19 |
| 18 | [Extract report rendering behind a stable package interface](issues/18-extract-report-rendering-behind-a-stable-package-interface.md) | None |
| 19 | [Extract deterministic aggregation and ranking](issues/19-extract-deterministic-aggregation-and-ranking.md) | 18 |
| 20 | [Make course and model configuration explicit](issues/20-make-course-and-model-configuration-explicit.md) | 18 |

One valid dependency order: 01, 04, 10, 12, 15, 18, 19, 20, 02, 07, 03, 05, 06, 08, 09, 11, 14, 16, 17, 13.

Tickets with no blockers: 01, 04, 10, 12, 15, 18. Dependency readiness does not imply safe simultaneous edits; coordinate shared-file ownership.

Refresh this index when ticket titles or blocking edges change. Status and completion evidence belong in the individual tickets.
