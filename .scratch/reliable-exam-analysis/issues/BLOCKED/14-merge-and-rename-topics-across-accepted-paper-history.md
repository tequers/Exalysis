# 14: Merge and rename topics across accepted paper history

```json
{
  "schema_version": 1,
  "id": "14",
  "priority": "P2",
  "queue_order": 17,
  "areas": [
    "evaluation",
    "scoring",
    "storage"
  ],
  "depends_on": [
    "02",
    "08"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/scoring.py",
    "pipeline/exam_roi/taxonomy.py",
    "pipeline/tests/test_cumulative_taxonomy.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Provide one consistent operation for consolidating topic labels without losing marks or historical evidence.

- [ ] Update taxonomy, question tags, aggregates, and prerequisite references together through the accepted-state workflow.
- [ ] Recompute contributions when a question previously used both merged labels; conserve marks and avoid duplicate topic assignment.
- [ ] Require an explicit resolution for conflicting difficulty, connection scores, and human overrides.
- [ ] Preserve revision history and source evidence; handle pending candidates referencing old names explicitly.
- [ ] After rebuild, show only the resulting canonical labels and do not silently assign fallback scores to orphaned historical labels.
- [ ] Test renames, multi-label merges, score conflicts, prerequisite references, rollback, and mark conservation.

**Architecture:** Follow [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md). Coordinate topic transformations through the workflow, recompute using shared scoring, and commit consistent revisions through storage.
