# 02: Apply the evaluation contract and validate candidate analyses

```json
{
  "schema_version": 1,
  "id": "02",
  "priority": "P1",
  "queue_order": 9,
  "areas": [
    "evaluation",
    "storage"
  ],
  "depends_on": [
    "01",
    "20"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
    "pipeline/exam_roi/evaluation.py",
    "pipeline/tests/test_candidate_validation.py",
    "pipeline/tests/test_cumulative_taxonomy.py"
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

**What to build:** Produce traceable candidate analyses that cannot silently accept malformed, incomplete, or unsupported model output.

- [x] Apply one evaluation-contract version consistently through extraction, tagging, and scoring, with evidence references and judgment rationales preserved.
- [x] Validate response structure, unique question IDs, allowed formats, finite numeric values, Diff 1–6, Conn 1–3, and prerequisite-reference structure.
- [x] Require every extracted question to have one or two distinct topic labels; reject unexpected IDs, missing scores, wrong types, and incomplete coverage.
- [x] Flag uncertainty and request correction or review instead of substituting undocumented scores or empty tags.
- [x] Keep candidate paper records and proposed taxonomy changes separate from accepted course state.
- [x] Record source and model provenance sufficient to trace a candidate back to its input and processing configuration.
- [x] Test malformed JSON, valid JSON with invalid semantics, missing tags, duplicate IDs, invalid scores, and unchanged accepted state on rejection.

**Architecture:** Follow [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md). Own candidate/evidence representations and validation at an explicit interface. Keep candidate results separate from accepted storage and share the contract with scoring and review.
