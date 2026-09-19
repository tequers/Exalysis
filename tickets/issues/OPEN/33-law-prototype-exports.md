# 33: Export an unreviewed LAW prototype after two-stage analysis

```json
{
  "schema_version": 1,
  "id": "33",
  "priority": "P1",
  "queue_order": 33,
  "areas": [
    "extraction",
    "reports",
    "documentation"
  ],
  "depends_on": [],
  "related_to": [
    "03",
    "08",
    "16"
  ],
  "references": [
    "docs/specs/law-prototype.md",
    "pipeline/pipeline.py",
    "pipeline/exam_roi/reports.py"
  ],
  "verification": {
    "commit": "d386546e3ef952a732c930ed5bc79058fe8236b6",
    "checked_at": "2026-09-19T14:34:36+00:00",
    "criteria_digest": "40143fad9075da976e59ce5dae63635d1ae09ca5ec3585d749082fc846d08ccd",
    "checker": "Codex",
    "result": "still_valid",
    "evidence": [
      "At d386546, add-exam saves candidates only and rebuild excludes them. LAW_1 contains one PDF and no accepted records. Owner approved an explicit prototype export path on 2026-09-19."
    ],
    "provisional": true
  },
  "closure": null
}
```

**What to build:** The approved prototype export path in the linked specification.

- [ ] Run Stage 1 and Stage 2, save candidates, and export a matching unreviewed Excel and agent JSON pair with an explicit prototype option.
- [ ] Rebuild prototype reports from saved candidates without model calls or acceptance.
- [ ] Clarify extraction of spaced question numbers, answer-space pages, and shared mark allocations. Reconcile compulsory-question marks before Stage 2.
- [ ] Document the output format and exact LAW run commands. Verify offline with synthetic model responses and export failure recovery.
- [ ] Obtain independent review and leave actual model output and publication selection for the owner.

## Agreement

The owner approved these three changes with "yes" on 2026-09-19 in the LAW portfolio conversation. See the specification for boundaries and acceptance evidence. This is a separate prototype path, not completion of tickets 03, 08, or 16. No live model calls, OCR, private exam tracking, or README revision is authorized here.
