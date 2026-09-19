# 07: Make course-state updates recoverable and serialize writers

```json
{
  "schema_version": 1,
  "id": "07",
  "priority": "P1",
  "queue_order": 10,
  "areas": [
    "storage",
    "reports"
  ],
  "depends_on": [
    "20"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "docs/guides/course-state-recovery.md",
    "pipeline/exam_roi/storage.py",
    "pipeline/tests/test_storage.py"
  ],
  "verification": null,
  "closure": {
    "reason": "implemented",
    "commit": null,
    "replacement": null,
    "reviewed_by": null,
    "evidence": [
      "Historical completion claim and scope are preserved in this ticket body."
    ]
  }
}
```

**What to build:** Protect saved course records from interruptions, corrupt files, and concurrent commands.

- [ ] Prevent concurrent writers to the same course and give actionable lock-contention diagnostics.
- [ ] Use atomic replacement and a documented recoverable commit strategy for related paper and taxonomy updates.
- [ ] Detect corrupt or incompatible saved records and report their identity without silently discarding or overwriting them.
- [ ] Define interruption recovery and safe stale-lock handling; preserve the last committed state until a new commit succeeds.
- [ ] Keep export failures distinguishable from accepted-state failures.
- [ ] Test controlled interruption at each commit boundary, concurrent writers, corrupt records, and successful recovery.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Make course persistence a module with explicit context and a small commit/load interface. Own locks, serialization, and interruption recovery inside it.
