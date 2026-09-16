# 21: Prototype staged GPT evaluation and fixture replay

```json
{
  "schema_version": 1,
  "id": "21",
  "priority": "P1",
  "queue_order": 21,
  "areas": [
    "evaluation",
    "extraction",
    "configuration"
  ],
  "depends_on": [
    "20"
  ],
  "related_to": [],
  "references": [
    "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
    "pipeline/exam_roi/evaluation.py",
    "pipeline/exam_roi/llm.py",
    "pipeline/exam_roi/review.py",
    "Courses/SISTEMAS_OPERATIVOS/evaluations/2026_Enero/2026_Enero-case.reviewed.json",
    "Courses/SISTEMAS_OPERATIVOS/evaluations/2026_Enero/review-summary.md"
  ],
  "verification": null,
  "closure": {
    "reason": "implemented",
    "commit": null,
    "replacement": null,
    "reviewed_by": "Project owner human review and Codex independent review",
    "evidence": [
      "The focused staged-evaluation suite passed all 15 tests; the implementation review also recorded a 206-test full-suite pass.",
      "Astra processed only the January 2026 Sistemas Operativos exam through independent and chained Stage 1 and Stage 2 runs.",
      "Offline audit replay reproduced every captured result and failure with zero replay errors and no network or provider call.",
      "Human review confirmed five top-level questions, Q3b as a file-system task, Q5a as both processes and memory with memory primary, and Q3 as mainly write/prove/justify.",
      "The failed Astra capture remains unapproved because it split the paper into 14 questions. The human-reviewed five-question case is stored separately and is not model-authored reference truth.",
      "The current schema divides marks equally among a question's topics, so it cannot encode memory as more important than processes within Q5a. This limitation is recorded in the review summary for later calibration work."
    ]
  }
}
```

**What to build:** Create an explicitly invoked evaluation workflow that uses GPT sub-agents to exercise the real Stage 1 and Stage 2 instructions, then turns reviewed outputs into deterministic fixtures for the normal automated test suite.

- [x] Run Stage 1 with the same evaluation contract and prompt used by the pipeline. Give the GPT sub-agent the source exam text and capture output in the validated parsed-question structure.
- [x] Run Stage 2 independently with a frozen, validated Stage 1 result and taxonomy. Capture topic assignments, evidence, difficulty judgments, uncertainties, and proposed topic names in the candidate-analysis structure.
- [x] Exercise one representative exam through both stages in sequence so the test detects data lost or changed between extraction and topic evaluation.
- [x] Record the source input, model identifier, prompt or contract version, generation date, and human-review status with each captured result. Model output must not become reference truth until a person approves it.
- [x] Add deterministic fixture replay through the existing injected extraction and analysis clients. The regular test suite must run without credentials, network access, or a live model.
- [x] Compare exact facts and invariants separately from judgment fields. Check question coverage, marks, evidence quotes, schema validity, and locally computed values exactly; use documented accepted values or tolerances for topic and difficulty judgments.
- [x] Keep live GPT evaluation opt-in and outside the default test run. Report stage failures separately so a valid Stage 2 result cannot hide a Stage 1 regression.
- [x] Document how an approved GPT fixture can later be run as a small GLM provider smoke test without changing the reference result.

**Architecture:** Use the separate `extraction_client` and `analysis_client` seam established by Ticket 20. The GPT sub-agent workflow produces evaluation evidence and reviewed fixtures; it does not replace production model adapters or deterministic tests. Feed the resulting fixtures and lessons into Ticket 09's full calibration harness.
