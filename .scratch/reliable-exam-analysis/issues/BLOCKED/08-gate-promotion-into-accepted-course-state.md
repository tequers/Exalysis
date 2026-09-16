# 08: Gate promotion into accepted course state

```json
{
  "schema_version": 1,
  "id": "08",
  "priority": "P1",
  "queue_order": 14,
  "areas": [
    "acceptance",
    "storage",
    "reports"
  ],
  "depends_on": [
    "02",
    "03",
    "06",
    "07"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/evaluation.py",
    "pipeline/exam_roi/storage.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Ensure only accepted analyses influence the shared taxonomy and ROI report.

- [ ] Represent provisional, needs-review, accepted, and rejected states with explicit permitted transitions.
- [ ] Require deterministic validation before acceptance; when model review is enabled, require its disposition to be resolved under a documented acceptance policy.
- [ ] Do not interpret a disabled reviewer as a passed reviewer; record the acceptance route and reason.
- [ ] Exclude pending and rejected candidates and their proposed taxonomy changes from report inputs.
- [ ] Preserve the previous accepted revision when reprocessing fails or produces an unresolved candidate.
- [ ] Record revision history, provenance, acceptance reasons, and support correction, rejection, and withdrawal through a user-accessible workflow.
- [ ] Show pending, excluded, and withdrawn paper counts so incomplete corpus coverage is visible.
- [ ] Handle legacy records explicitly as legacy/unreviewed rather than claiming they passed new checks; document a migration/review route.
- [ ] Test that a rejected candidate cannot change shared topic scores or the report and that accepted promotion is recoverable.

**Architecture:** Follow [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md). Own acceptance transitions and decisions in one module. Delegate durable commits to storage; preserve accepted-revision invariants across that seam.
