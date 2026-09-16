# 16: Make exports consistent and clarify supported overrides

```json
{
  "schema_version": 1,
  "id": "16",
  "priority": "P2",
  "queue_order": 18,
  "areas": [
    "reports",
    "storage"
  ],
  "depends_on": [
    "07",
    "08"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/reports.py",
    "pipeline/tests/test_report_rendering.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Generate traceable outputs from accepted state without suggesting spreadsheet edits are persisted overrides.

- [ ] Remove workbook wording that advertises editable overrides unless an actual import workflow is implemented; direct users to supported score-editing commands.
- [ ] Build XLSX and ranked JSON from the same accepted-state snapshot and identify their generation or revision.
- [ ] Handle locked workbooks and interrupted export replacement without silently presenting mismatched outputs as current.
- [ ] Identify stale exports and provide a rebuild path that does not require new model calls.
- [ ] Verify override behavior, matching exported rankings, pending-paper visibility, locked-workbook recovery, and consistent rebuilds.

**Architecture:** Follow [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md). Consume one accepted-state snapshot through the reports interface. Coordinate export recovery without reading or mutating analytical state inside rendering.
