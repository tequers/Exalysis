# 18: Extract report rendering behind a stable package interface

```json
{
  "schema_version": 1,
  "id": "18",
  "priority": "P2",
  "queue_order": 6,
  "areas": [
    "reports"
  ],
  "depends_on": [],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/reports.py",
    "pipeline/tests/test_report_rendering.py"
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

**What to build:** Create the first internal package seam while preserving the existing CLI and semantic exports.

**Architecture:** Follow [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md); preserve behavior while establishing the interface described here.

- [x] Establish characterization checks for intended CLI and report behavior using synthetic course data and isolated temporary output.
- [x] Keep the current script invocation working from both the repository root and the pipeline working directory.
- [x] Move XLSX and ranked JSON rendering into one reports module with explicit destinations and a supplied snapshot; retain orchestration outside rendering.
- [x] Keep current score values, order, worksheet content, and public output shape unchanged; document known defects rather than making them new permanent requirements.
- [x] Rendering must not read course globals, decide acceptance, call a model, or mutate taxonomy.
- [x] Verify semantic workbook cells and JSON data rather than binary workbook identity; separate relocation from functional fixes.
- [x] Record the initial package interface and verify imports without adding a framework or speculative module hierarchy.
