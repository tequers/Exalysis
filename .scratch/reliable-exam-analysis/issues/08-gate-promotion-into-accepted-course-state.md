# 08: Gate promotion into accepted course state

**What to build:** Ensure only accepted analyses influence the shared taxonomy and ROI report.

**Blocked by:** 02: Apply the evaluation contract and validate candidate analyses; 03: Validate question marks and supported exam scoring structures; 06: Add an independent model review of candidate analyses; 07: Make course-state updates recoverable and serialize writers.

**Status:** ready-for-agent

**Priority:** P1

- [ ] Represent provisional, needs-review, accepted, and rejected states with explicit permitted transitions.
- [ ] Require deterministic validation before acceptance; when model review is enabled, require its disposition to be resolved under a documented acceptance policy.
- [ ] Do not interpret a disabled reviewer as a passed reviewer; record the acceptance route and reason.
- [ ] Exclude pending and rejected candidates and their proposed taxonomy changes from report inputs.
- [ ] Preserve the previous accepted revision when reprocessing fails or produces an unresolved candidate.
- [ ] Record revision history, provenance, acceptance reasons, and support correction, rejection, and withdrawal through a user-accessible workflow.
- [ ] Show pending, excluded, and withdrawn paper counts so incomplete corpus coverage is visible.
- [ ] Handle legacy records explicitly as legacy/unreviewed rather than claiming they passed new checks; document a migration/review route.
- [ ] Test that a rejected candidate cannot change shared topic scores or the report and that accepted promotion is recoverable.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Own acceptance transitions and decisions in one module. Delegate durable commits to storage; preserve accepted-revision invariants across that seam.
