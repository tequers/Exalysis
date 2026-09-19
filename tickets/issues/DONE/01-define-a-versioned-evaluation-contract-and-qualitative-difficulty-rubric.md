# 01: Define a versioned evaluation contract and qualitative difficulty rubric

```json
{
  "schema_version": 1,
  "id": "01",
  "priority": "P1",
  "queue_order": 1,
  "areas": [
    "evaluation",
    "scoring"
  ],
  "depends_on": [],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/contracts/evaluation-v1.2.0.md",
    "pipeline/exam_roi/evaluation.py",
    "pipeline/tests/fixtures/difficulty-v1.json",
    "pipeline/tests/test_evaluation.py"
  ],
  "verification": null,
  "closure": {
    "reason": "implemented",
    "commit": null,
    "replacement": null,
    "reviewed_by": null,
    "evidence": [
      "Historical implementation and check evidence is preserved in this ticket body."
    ]
  }
}
```

**What to build:** Make every model judgment follow an explicit, auditable evaluation contract while retaining approximate difficulty and removing study-hour estimates.

- [x] Define difficulty as conceptual and reasoning complexity for representative topic questions, using background assumptions inferred from exam evidence alone; exclude study time, marks, frequency, and response format.
- [x] Anchor levels 1–6 respectively to direct recall, one-rule application, standard multi-step methods, combining concepts with method selection, unfamiliar transfer with interacting constraints, and sustained abstraction or synthesis. Provide reviewed examples, counterexamples, and boundary cases.
- [x] Define rules for question boundaries, optional questions, marks, topic granularity, multi-topic allocation, format, connection value, prerequisite references, and abstention under ambiguity.
- [x] Define how question-level evidence produces a topic-level score, how conflicting papers are reconciled, and when existing scores are reconsidered without overwriting explicit human overrides.
- [x] Require source evidence and concise rationales; distinguish extracted facts from estimates and uncertainty from confidence claims.
- [x] Version the contract and record its version in analyses; changing the rubric must not silently reinterpret previously accepted records.
- [x] Remove hour estimation from prompts and exports; tolerate but ignore legacy hour fields. Replace marks-per-hour claims with relative priority and reconcile the methodology with actual supported scoring.
- [x] Verify rubric boundary examples, old-record compatibility, and independence of difficulty from format.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Own the versioned rubric and qualitative rules as one authoritative contract. Introduce shared representations only as needed with validation; retain current CLI compatibility while removing hour estimates.

## Completion evidence

- Authoritative [contract 1.1.0](../../../pipeline/exam_roi/contracts/evaluation-v1.1.0.md)
  defines all qualitative rules, boundaries, cross-paper reconciliation, and
  reconsideration/override policy. The contract is injected into both model stages.
- Provider-independent [evaluation module](../../../pipeline/exam_roi/evaluation.py)
  validates evidence-backed new-topic judgments and computes ordinal summaries.
  New analyses and topic judgments record version and checksum. Existing scores
  retain their basis, including `legacy-unversioned`; rebuild never migrates them.
- The CLI keeps its invocation shape. New scoring sees full question evidence and
  background assumptions inferred from the paper. Human edits retain per-field provenance. Legacy
  duration fields are ignored, and JSON/XLSX exports omit duration estimates.
- README, glossary, and supported methodology now describe relative priority and
  the actual formula, format weights, paper weighting, and Tier 1 behavior.
- [Regression checks](../../../pipeline/tests/test_evaluation.py): 15 tests passed
  using the bundled Python runtime with openpyxl, including both CLI working
  directories, old-record preservation, export contents, evidence validation,
  abstention, overrides, ordinal aggregation, and format-independent score inputs.
  `git diff --check` passed.
- [Synthetic examples](../../../pipeline/tests/fixtures/difficulty-v1.json) cover
  all six anchors, five adjacent boundaries, and three format pairs. They were
  reviewed against the contract by the implementation author (an AI agent), and
  are explicitly marked as not human-reviewed. Independent human calibration and
  live model accuracy measurement remain ticket 9's work.

Scope follows the backlog: this ticket defines the complete evaluation contract
and implements its new-score representation, prompt integration, provenance, and
legacy/export changes. Full extraction/tagging validation, mark/optional-structure
checks, candidate isolation, and acceptance gating remain tickets 2, 3, and 8.
Automatic reconsideration proposals are not silently applied to stored scores.

Exams-only correction: no manual course prerequisite list is required or read.
New topic judgments infer background assumptions from exam questions and preserve
supporting quotes and reasons in `prerequisite_evidence`. Contract 1.1.0 records this
policy change; earlier contracts and stored judgments remain unchanged. Offline
checks cover scoring without a manual list, ignoring legacy manual configuration,
and rejecting missing or unresolvable assumption evidence.

Cumulative-analysis correction (contract 1.2.0): every paper now supplies independent
judgments for existing as well as new topics. The taxonomy is recomputed from current
paper evidence after each parse and on rebuild. Distinct supported dependencies
update both endpoints; expanded vocabulary triggers connection reviews of earlier
papers. Reparses replace evidence, conflicts remain visible, and explicit human
overrides take precedence over automatic estimates. Older records require an explicit
reparse rather than silent conversion. See the current methodology for details.
