# 05: Preserve question context and respect model request limits

**What to build:** Analyze long papers and questions without silently deleting the context needed for reliable judgments.

**Blocked by:** 02: Apply the evaluation contract and validate candidate analyses.

**Status:** implemented and reviewed

**Priority:** P1

- [x] Remove unconditional 500-character question truncation; retain task-bearing context and source evidence across tagging and scoring.
- [x] Supply relevant question evidence, the course baseline, and rubric context when estimating topic difficulty.
- [x] Make model context and output limits explicit and configurable; check extraction, tagging, and new-topic scoring requests before dispatch.
- [x] Split oversized work with stable question identity and validate merged coverage, including questions spanning chunk boundaries.
- [x] Treat truncation as incomplete output, with bounded recovery or actionable failure rather than accepting partial JSON.
- [x] Test long introductions with decisive text at the end, oversized papers, large topic sets, and truncated responses without live API calls.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Use explicitly injected model clients and request limits. Keep provider mechanics separate from exam interpretation and preserve evidence across requests.


## Implementation and verification

- Added explicit model clients and per-stage input/output budget checks in `pipeline/exam_roi/llm.py`.
- Preserved complete question text and original source context, including page continuations and explicit question references.
- Added bounded batch splitting and validated extraction, tag, and score coverage before merging.
- Rejected truncated or malformed responses without saving partial candidates.
- Self-review corrected cross-question context and injected-client provenance. No remaining actionable findings in this change.
- Verification: all 85 offline tests pass, including 26 new request-limit/context tests. `git diff --check` passes.

[Configuration, supported boundaries, and limitations](../../../pipeline/docs/model-request-limits.md).
