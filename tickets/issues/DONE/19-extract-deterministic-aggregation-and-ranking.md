# 19: Extract deterministic aggregation and ranking

```json
{
  "schema_version": 1,
  "id": "19",
  "priority": "P2",
  "queue_order": 7,
  "areas": [
    "scoring",
    "reports"
  ],
  "depends_on": [
    "18"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/scoring.py",
    "pipeline/tests/test_scoring.py"
  ],
  "verification": null,
  "closure": {
    "reason": "implemented",
    "commit": null,
    "replacement": null,
    "reviewed_by": "Codex specification and standards review",
    "evidence": [
      "The scoring module contains pure aggregation and ranking functions with explicit inputs and no provider, storage, environment, or console dependencies.",
      "The command layer loads state and exports the returned report; it does not own the arithmetic.",
      "Five focused scoring tests passed, including hand-calculated mixed-format and multi-paper cases, stable ordering, Tier 1 rounding, legacy fallbacks, and input non-mutation.",
      "The report-rendering integration tests cover the same ranked representation used by rebuild.",
      "No human review is required because the outputs are deterministic and directly asserted by automated tests."
    ]
  }
}
```

**What to build:** Make mark aggregation and ROI ranking directly testable without model calls, storage, or CLI setup.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md); preserve behavior while establishing the interface described here.

- [x] Separate deterministic aggregation from topic tagging and new-topic model scoring; pass questions, assignments, and score inputs explicitly.
- [x] Extract ranking and Tier 1 calculation from command handling into pure functions returning a report representation.
- [x] Preserve existing intended arithmetic, precision, ordering, and presentation data until the corresponding behavioral tickets change them.
- [x] Require no credentials, environment configuration, file access, console output, or monkeypatching of model calls to exercise the scoring interface.
- [x] Keep command-level loading and export orchestration outside the scoring module.
- [x] Test representative mixed-format and multi-paper examples against hand-calculated expectations, and verify inputs are not mutated.
- [x] Keep one arithmetic implementation shared by rebuild and future merge/validation workflows; document legacy fallback behavior for correction by its assigned ticket.
