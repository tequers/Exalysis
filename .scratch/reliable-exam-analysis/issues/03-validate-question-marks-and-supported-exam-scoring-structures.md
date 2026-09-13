# 03: Validate question marks and supported exam scoring structures

**What to build:** Prevent unknown marks, inconsistent totals, or optional-question structures from producing misleading topic shares.

**Blocked by:** 02: Apply the evaluation contract and validate candidate analyses; 19: Extract deterministic aggregation and ranking.

**Status:** ready-for-agent

**Priority:** P1

- [ ] Reject missing, negative, non-finite, and otherwise invalid marks under the contract; distinguish legitimate zero-mark content from missing data.
- [ ] Require a positive available total and reconcile allocated marks against it using an explicit numeric tolerance; do not invent a 100-mark denominator.
- [ ] Ensure parent questions and subquestions are not counted twice.
- [ ] Detect optional sections, alternatives, and bonus questions; explicitly reject unsupported structures with correction instructions instead of treating every question as compulsory.
- [ ] Apply and document equal allocation across a question's distinct topic labels while conserving total marks.
- [ ] Clarify that a total-marks override does not supply missing question marks and how a batch-wide override behaves.
- [ ] Test complete, partially unmarked, entirely unmarked, fractional-mark, overlapping, optional-section, and contradictory-total papers.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Apply mark rules through the shared deterministic aggregation implementation; model prompts must not become a second arithmetic implementation.
