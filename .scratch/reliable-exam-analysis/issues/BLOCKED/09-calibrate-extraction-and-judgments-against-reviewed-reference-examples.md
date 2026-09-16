# 09: Calibrate extraction and judgments against reviewed reference examples

```json
{
  "schema_version": 1,
  "id": "09",
  "priority": "P1",
  "queue_order": 15,
  "areas": [
    "evaluation",
    "extraction",
    "acceptance"
  ],
  "depends_on": [
    "01",
    "02",
    "06",
    "08"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
    "pipeline/tests/fixtures/difficulty-v1.json"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Measure reliability and reviewer usefulness before promoting rubric, prompt, or model changes.

- [ ] Create a small human-reviewed reference set spanning subjects, formats, ambiguous marks, optional structures, and difficulty boundary cases; label unreviewed examples clearly.
- [ ] Separate deterministic scoring invariants from human judgment tolerances and record reference rationales.
- [ ] Measure extraction completeness, mark accuracy, topic consistency, and difficulty agreement; repeat runs to measure stability.
- [ ] Compare processing with and without review, including missed defects, false alarms, latency, and model-call cost where available.
- [ ] Define acceptance thresholds before evaluating candidate changes and keep calibration examples distinct from held-out checks.
- [ ] Produce a reproducible evaluation summary identifying contract, prompt, and model versions; failures prevent calling a change validated.
- [ ] Use deterministic fixtures for automated checks and an explicitly invoked live evaluation path; never auto-label model output as reference truth.

**Architecture:** Follow [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md). Keep reference fixtures and evaluation runners separate from production workflow. Begin example preparation during 01; reserve this ticket for the complete measurement harness.
