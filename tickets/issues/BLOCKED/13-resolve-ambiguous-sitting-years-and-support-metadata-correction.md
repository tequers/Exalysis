# 13: Resolve ambiguous sitting years and support metadata correction

```json
{
  "schema_version": 1,
  "id": "13",
  "priority": "P2",
  "queue_order": 20,
  "areas": [
    "extraction",
    "storage"
  ],
  "depends_on": [
    "08",
    "11"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0007-one-record-per-paper-and-the-sitting-year.md",
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/inputs.py",
    "pipeline/exam_roi/storage.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Avoid treating historical dates in questions as sitting years and correct cached metadata without paid extraction.

- [ ] Use an explicit precedence policy for overrides, filename metadata, directory metadata, and paper evidence; do not accept arbitrary first-year mentions as authoritative.
- [ ] Leave unresolved or conflicting evidence undated and show the candidates and their sources.
- [ ] Document supported year bounds and academic-year conversion, including ambiguous ranges.
- [ ] Allow a sitting-year correction for an existing accepted paper without repeating extraction or changing its identity.
- [ ] Record metadata correction history and regenerate labels and reports consistently.
- [ ] Test history-question dates, conflicting filename/header years, academic-year ranges, undated papers, and cached corrections.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Keep evidence-based sitting resolution in inputs and commit corrections through the accepted-revision workflow.

## Dependency rollout finding, 2026-09-19

Ticket 32 found that accepted ADR 0007 requires YEAR_name filenames and prefix-only
year selection, while the current CLI still infers years and accepts --year.
The precedence policy proposed above also differs from that ADR. Before approving
implementation of this ticket, the owner must decide whether to enforce ADR 0007
or replace it with an explicitly approved policy. Preserve the current blockers;
this finding neither approves a different policy nor starts implementation.
