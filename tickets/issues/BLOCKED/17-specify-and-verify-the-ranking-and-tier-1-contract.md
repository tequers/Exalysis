# 17: Specify and verify the ranking and Tier 1 contract

```json
{
  "schema_version": 1,
  "id": "17",
  "priority": "P2",
  "queue_order": 19,
  "areas": [
    "scoring",
    "reports"
  ],
  "depends_on": [
    "01",
    "03",
    "08",
    "19"
  ],
  "related_to": [],
  "references": [
    "README.md",
    "docs/adr/0008-modular-pipeline-architecture.md",
    "docs/guides/scoring-methodology.md",
    "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
    "pipeline/exam_roi/scoring.py",
    "pipeline/tests/test_scoring.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Make ranking assumptions transparent and verify that accepted evidence produces reproducible relative priorities.

- [ ] Document equal paper weighting, uneven sampling implications, duplicate-policy interaction, and absence of recency weighting.
- [ ] Specify mark-weighting within a paper and equal averaging of paper-level format scores across appearances, with a numerical example.
- [ ] Clarify the role of descriptive prerequisites versus independently estimated connection value and how the approved difficulty contract avoids format double-counting.
- [ ] Define missing-score behavior consistently with acceptance validation; do not silently invent accepted scores.
- [ ] Define Tier 1 as a rank-based selection, including rounding and tie behavior; do not present zero-priority topics as high-yield.
- [ ] Add deterministic fixtures for absent topics, multiple papers per year, unequal mark totals, mixed formats, tied scores, and zero values.
- [ ] Reconcile README, methodology, command help, and export labels; describe unsupported graph/recency features as unimplemented rather than operational.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Make pure scoring the single implementation of ranking and tiers. Keep policy documentation aligned with that implementation and the approved rubric.
