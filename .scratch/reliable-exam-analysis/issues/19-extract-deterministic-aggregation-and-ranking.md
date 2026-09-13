# 19: Extract deterministic aggregation and ranking

**What to build:** Make mark aggregation and ROI ranking directly testable without model calls, storage, or CLI setup.

**Blocked by:** 18: Extract report rendering behind a stable package interface.

**Status:** ready-for-agent

**Priority:** P2

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md); preserve behavior while establishing the interface described here.

- [ ] Separate deterministic aggregation from topic tagging and new-topic model scoring; pass questions, assignments, and score inputs explicitly.
- [ ] Extract ranking and Tier 1 calculation from command handling into pure functions returning a report representation.
- [ ] Preserve existing intended arithmetic, precision, ordering, and presentation data until the corresponding behavioral tickets change them.
- [ ] Require no credentials, environment configuration, file access, console output, or monkeypatching of model calls to exercise the scoring interface.
- [ ] Keep command-level loading and export orchestration outside the scoring module.
- [ ] Test representative mixed-format and multi-paper examples against hand-calculated expectations, and verify inputs are not mutated.
- [ ] Keep one arithmetic implementation shared by rebuild and future merge/validation workflows; document legacy fallback behavior for correction by its assigned ticket.
