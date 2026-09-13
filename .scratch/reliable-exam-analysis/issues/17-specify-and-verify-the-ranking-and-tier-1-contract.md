# 17: Specify and verify the ranking and Tier 1 contract

**What to build:** Make ranking assumptions transparent and verify that accepted evidence produces reproducible relative priorities.

**Blocked by:** 01: Define a versioned evaluation contract and qualitative difficulty rubric; 03: Validate question marks and supported exam scoring structures; 08: Gate promotion into accepted course state; 19: Extract deterministic aggregation and ranking.

**Status:** ready-for-agent

**Priority:** P2

- [ ] Document equal paper weighting, uneven sampling implications, duplicate-policy interaction, and absence of recency weighting.
- [ ] Specify mark-weighting within a paper and equal averaging of paper-level format scores across appearances, with a numerical example.
- [ ] Clarify the role of descriptive prerequisites versus independently estimated connection value and how the approved difficulty contract avoids format double-counting.
- [ ] Define missing-score behavior consistently with acceptance validation; do not silently invent accepted scores.
- [ ] Define Tier 1 as a rank-based selection, including rounding and tie behavior; do not present zero-priority topics as high-yield.
- [ ] Add deterministic fixtures for absent topics, multiple papers per year, unequal mark totals, mixed formats, tied scores, and zero values.
- [ ] Reconcile README, methodology, command help, and export labels; describe unsupported graph/recency features as unimplemented rather than operational.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Make pure scoring the single implementation of ranking and tiers. Keep policy documentation aligned with that implementation and the approved rubric.
