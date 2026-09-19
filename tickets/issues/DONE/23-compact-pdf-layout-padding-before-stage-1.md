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
    "commit": "c2e7b5f0990f991883375d4116359d021c26c335",
    "checked_at": "2026-09-16T19:30:46+00:00",
    "criteria_digest": "84cb1179d42d3329ec38e63423e7e7bd616f40d6c0c1651aff8cdad940d8d731",
    "checker": "Codex",
    "result": "already_resolved",
    "evidence": [
      "At commit c2e7b5f, the real 2024 Modelo A PDF fits the unchanged 128,000-token Stage 1 context at an estimated 110,159 tokens. All 221 pipeline tests and 35 ticket checks passed offline; no model call was used for verification."
    ],
    "provisional": false
  },
  "closure": {
    "reason": "implemented",
    "commit": "c2e7b5f0990f991883375d4116359d021c26c335",
    "replacement": null,
    "reviewed_by": "Codex automated verification",
    "evidence": [
      "The real 2024 Modelo A request now fits at 110,159 of 128,000 configured tokens; 221 pipeline tests and 35 ticket checks passed."
    ]
  }
}
```

**What to build:** Remove horizontal padding inserted by PDF layout extraction before Stage 1 request sizing, while preserving page boundaries, line boundaries, and readable separation between words.

- [x] Collapse runs of horizontal whitespace in extracted PDF lines.
- [x] Preserve line and page boundaries used by source provenance.
- [x] Keep UTF-8 text-file contents unchanged.
- [x] Add an offline regression test that reproduces the oversized layout-padding request.
- [x] Confirm the 2024 Modelo A Stage 1 request fits the existing 128k configured context without discarding content.

**Architecture:** Normalize reader-generated PDF layout padding in the input module. Do not weaken request-limit checks, truncate source text, add OCR, or change question-boundary rules.

## Evidence and history

Created after the 2024 Modelo A PDF produced a deterministic `RequestLimitError`: 202,815 extracted characters became an estimated 253,235-token Stage 1 request. The model was not called. Collapsing reader-generated horizontal padding reduced the same complete request estimate to 110,159 tokens.

Implementation collapses horizontal whitespace on each PDF text-layer line before the page blocks and provenance offsets are assembled. It does not alter UTF-8 text-file extraction, page boundaries, line boundaries, request-limit enforcement, or question splitting.

Offline verification on the real 14-page 2024 Modelo A PDF produced 59,739 normalized characters and an estimated 110,159-token complete Stage 1 request under the existing 128,000-token context. The 33 input-extraction tests, 26 request-limit tests, and all 221 pipeline tests passed.
