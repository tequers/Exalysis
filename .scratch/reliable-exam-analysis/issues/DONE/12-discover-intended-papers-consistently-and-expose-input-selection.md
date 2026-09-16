# 12: Discover intended papers consistently and expose input selection

```json
{
  "schema_version": 1,
  "id": "12",
  "priority": "P2",
  "queue_order": 4,
  "areas": [
    "extraction",
    "configuration"
  ],
  "depends_on": [],
  "related_to": [],
  "references": [
    "README.md",
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/inputs.py",
    "pipeline/tests/test_input_selection.py"
  ],
  "verification": null,
  "closure": {
    "reason": "implemented",
    "commit": null,
    "replacement": null,
    "reviewed_by": "Historical standards and specification reviews; reviewer identity unavailable",
    "evidence": [
      "Ticket body records separate standards and specification reviews with no actionable findings."
    ]
  }
}
```

**What to build:** Make default input discovery include both supported paper locations and show exactly what will be analyzed.

- [x] Combine matching papers in the course root and its exams subfolder, deduplicating resolved inputs.
- [x] Preserve explicit recursive-search behavior and exclude pipeline-managed candidate and accepted output directories.
- [x] Document relative-input-path precedence and make the selected resolved files visible before processing.
- [x] Explain that matching TXT/PDF files are treated as papers and provide a documented way to select or exclude unrelated material.
- [x] Test mixed root/subfolder inputs, explicit files plus folders, duplicates, recursive discovery, and ambiguous relative filenames.

**Architecture:** Follow [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md). Keep file selection in inputs with explicit course context. This fix can land before extraction; coordinate later relocation.

Implementation: `exam_roi.inputs.collect_exam_files` takes an explicit course directory, combines both default locations, and returns resolved unique files. The CLI lists all selected paths before processing and supports `add-exam --dry-run`. README documents selection, exclusions, and working-directory precedence.

Validation: 15 offline selection tests cover the acceptance criteria, managed-directory aliases, Windows directory links and recursive loops, two independent course contexts, and dry runs from both supported working directories. The full suite passes with the bundled Python runtime. Separate standards and specification reviews found no actionable issues.
