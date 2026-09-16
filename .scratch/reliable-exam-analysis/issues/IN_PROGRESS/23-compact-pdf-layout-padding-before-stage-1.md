# 23: Compact PDF layout padding before Stage 1

```json
{
  "schema_version": 1,
  "id": "23",
  "priority": "P1",
  "queue_order": 23,
  "areas": [
    "extraction",
    "configuration"
  ],
  "depends_on": [
    "20"
  ],
  "related_to": [
    "12"
  ],
  "references": [
    "pipeline/exam_roi/inputs.py",
    "pipeline/tests/test_input_extraction.py",
    "pipeline/tests/test_request_limits.py"
  ],
  "verification": {
    "commit": "610be3086bc519642f399023ef8408e67835fab0",
    "checked_at": "2026-09-16T19:27:01+00:00",
    "criteria_digest": "84cb1179d42d3329ec38e63423e7e7bd616f40d6c0c1651aff8cdad940d8d731",
    "checker": "Codex",
    "result": "still_valid",
    "evidence": [
      "Offline reproduction extracted 202,815 characters from the 14-page 2024 Modelo A PDF, produced one complete source unit, and raised the reported 253,235-token RequestLimitError before any model call. Horizontal whitespace compaction reduced the unchanged complete request estimate to 110,159 tokens."
    ],
    "provisional": false
  },
  "closure": null
}
```

**What to build:** Remove horizontal padding inserted by PDF layout extraction before Stage 1 request sizing, while preserving page boundaries, line boundaries, and readable separation between words.

- [ ] Collapse runs of horizontal whitespace in extracted PDF lines.
- [ ] Preserve line and page boundaries used by source provenance.
- [ ] Keep UTF-8 text-file contents unchanged.
- [ ] Add an offline regression test that reproduces the oversized layout-padding request.
- [ ] Confirm the 2024 Modelo A Stage 1 request fits the existing 128k configured context without discarding content.

**Architecture:** Normalize reader-generated PDF layout padding in the input module. Do not weaken request-limit checks, truncate source text, add OCR, or change question-boundary rules.

## Evidence and history

Created after the 2024 Modelo A PDF produced a deterministic `RequestLimitError`: 202,815 extracted characters became an estimated 253,235-token Stage 1 request. The model was not called. Collapsing reader-generated horizontal padding reduced the same complete request estimate to 110,159 tokens.
