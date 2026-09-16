# 06: Add an independent model review of candidate analyses

```json
{
  "schema_version": 1,
  "id": "06",
  "priority": "P1",
  "queue_order": 13,
  "areas": [
    "evaluation",
    "acceptance",
    "configuration"
  ],
  "depends_on": [
    "02",
    "03",
    "05"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/docs/independent-review.md",
    "pipeline/exam_roi/review.py",
    "pipeline/tests/test_independent_review.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Offer a configurable evidence-based review stage that challenges candidate analyses before acceptance.

- [x] Provide the reviewer with source evidence, the evaluation contract, and the candidate analysis; allow a separately configured model or provider.
- [x] Check extraction omissions, unsupported claims, mark allocation, topic consistency, and difficulty/connection rubric application.
- [x] Return structured findings with source evidence, severity, and an explicit disposition; model agreement alone must not establish correctness.
- [x] Do not silently rewrite candidates or let a reviewer approve its own corrections; review revised candidates through the configured workflow.
- [x] Bound correction attempts and send unresolved disagreements to a visible needs-review state.
- [x] Record reviewer model, contract version, findings, and whether review was enabled; reviewer failure cannot masquerade as a pass.
- [ ] Test correct candidates, seeded defects, disagreements, malformed reviews, unavailable reviewers, and retry exhaustion.

**Architecture:** Follow [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md). Consume candidate and contract representations through an evaluation interface. Keep reviewer results distinct from the acceptance decision and persistence commit.

Implementation and configuration: [independent review guide](../../../../pipeline/docs/independent-review.md). Offline tests cover review validation, provider failure, correction bounds, and candidate persistence. Ticket 03's deterministic mark checks remain a separate prerequisite and are not replaced by this model review.

## Review finding

`pipeline/tests/test_independent_review.py:36` builds the supposed correct candidate with only Q1, while the source fixture at line 19 contains Q1 and Q2. The clean path therefore tests a candidate with an extraction omission, and most seeded-defect cases contain that unrelated defect. Add a complete two-question candidate fixture, use it for the clean case, and derive each seeded defect from it.

The focused 16-test review suite and the combined 27-test review/configuration suite passed, but neither detects this fixture error.

After the automated test gap is fixed, this ticket still needs human review because offline tests cannot measure a live reviewer's judgment quality:

1. Process a known complete paper with a separately configured reviewer and `--review`. Expect six evidence-backed category results, a sensible overall disposition, and no automatic acceptance.
2. Compare every evidence quote with the source paper. Expect each quote to exist and support its rationale.
3. Repeat with known omissions, unsupported claims, wrong marks, topic inconsistencies, and wrong rubric scores. Expect every seeded defect to be reported and unresolved cases to have `candidate_status: needs-review`.
4. Compare accepted paper and taxonomy files before and after both runs. Expect no changes.
