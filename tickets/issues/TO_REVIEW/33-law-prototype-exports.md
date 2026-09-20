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
    "pipeline/exam_roi/reports.py",
    "pipeline/exam_roi/prototype.py",
    "pipeline/tests/test_prototype.py",
    "docs/guides/run-law-prototype.md",
    "docs/guides/prototype-output-format.md"
  ],
  "verification": {
    "commit": "ad5f3a60c1fcd05040105422ac6cf6fb362864b6",
    "checked_at": "2026-09-20T17:10:54+00:00",
    "criteria_digest": "40143fad9075da976e59ce5dae63635d1ae09ca5ec3585d749082fc846d08ccd",
    "checker": "/root/review_prototype",
    "result": "still_valid",
    "evidence": [
      "Independent review confirmed the UnoRouter environment variable names, relative exams/ resolution, and prototype output paths match the implementation. The README now also tells readers to supply the ignored LAW PDFs. All 245 offline pipeline tests pass; ticket and documentation checks pass."
    ],
    "provisional": false
  },
  "closure": null
}
```

**What to build:** The approved prototype export path in the linked specification.

- [x] Run Stage 1 and Stage 2, save candidates, and export a matching unreviewed Excel and agent JSON pair with an explicit prototype option.
- [x] Rebuild prototype reports from saved candidates without model calls or acceptance.
- [x] Clarify extraction of spaced question numbers, answer-space pages, and shared mark allocations. Reconcile compulsory-question marks before Stage 2.
- [x] Document the output format and exact LAW run commands. Verify offline with synthetic model responses and export failure recovery.
- [x] Obtain independent review and leave actual model output and publication selection for the owner.

## Agreement

The owner approved these three changes with "yes" on 2026-09-19 in the LAW portfolio conversation. See the specification for boundaries and acceptance evidence. This is a separate prototype path, not completion of tickets 03, 08, or 16. No live model calls, OCR, private exam tracking, or README revision is authorized here.

The owner additionally approved relaxing Stage 2 dependency completeness for the MVP on 2026-09-19. A candidate must no longer be rejected when `prerequisites` or `unlocks` lack matching `connection_edges`; supplied edges remain validated and only validated edges contribute to the temporary taxonomy.

On 2026-09-20, the owner also approved removing the requirement that `Conn` match the count of listed `unlocks`. Stage 2 still requires an integer `Conn` from 1 through 3; the temporary taxonomy recomputes its connection score from validated edges.

The owner then approved advisory Stage 2 evidence quotes for prototype mode. Missing, null, empty, or non-verbatim quotes must not block candidate storage or the Excel and agent JSON exports. Supplied strings are retained, missing values are normalized to empty strings, and ordinary non-prototype analysis remains strict.

On 2026-09-20, the owner approved a small README section that explains the real
three-exam LAW prototype to recruiters, links its run and output guides, and leaves
a clearly labeled placeholder for a future screenshot or GIF.

The owner then approved documenting the exact UnoRouter PowerShell configuration,
LAW command, relative-path behavior, and generated output paths used for that run.

## Delivery and verification

Implemented on `codex/33-law-prototype-exports`, based on `origin/codex/mvp-two-stage` at `d386546e3ef952a732c930ed5bc79058fe8236b6`.

Commands ran from the repository root with `PYTHONIOENCODING=utf-8`:

- `python -m unittest discover -s pipeline/tests -p 'test_prototype.py' -v`: 11 tests passed.
- `python -m unittest discover -s pipeline/tests -p 'test_*.py'`: 242 tests passed. The invalid-PDF, missing-live-approval, and rejected-capture messages are expected negative-test output. The first full run caught changed historical replay prompts; restricting the new wording to prototype mode fixed that regression without changing captured evidence.
- `python scripts/check_tickets.py`: 76 tooling tests passed, 33 ticket records valid, zero errors. Six existing unreviewed-closure warnings remain for tickets 01, 02, 05, 07, 10, and 18.
- `git diff --check` and `git diff --cached --check`: passed. Git also warns about the inaccessible global ignore file and LF-to-CRLF conversion; these are environment notices, not hidden test failures.
- `python scripts/doc_dependencies.py check`: complete and valid, 29 owners and 182 relationships.
- `python scripts/doc_dependencies.py build` and `python scripts/doc_dependencies.py check --against-artifacts .scratch/doc-dependencies`: passed.
- `python scripts/doc_dependencies.py discover --file docs/guides/run-law-prototype.md`, repeated for the output-format guide and specification: valid. Unresolved references are generated course paths, the ignored `.env`, and command text. These are not tracked dependency targets. The requirements file is covered through the linked development workflow. An earlier attempt to run discovery on Python code was rejected because discovery accepts document owners; it was rerun on these documents.
- A dry run against the owner's LAW course selected only `exams/2025_june.pdf`, with no model configuration or AI calls. `rebuild --help` exposes the offline prototype option.
- The approved Stage 2 relaxation is covered by `test_missing_edge_evidence_does_not_reject_mvp_candidate`: unmatched prerequisite and unlock lists remain in the candidate, do not block processing, and do not create unsupported taxonomy edges. The cumulative-taxonomy and prototype suites each pass 11 tests; the full suite still passes 242 tests.
- The approved `Conn` relaxation is covered by `test_scores_accept_conn_that_does_not_match_unlock_count`. Candidate-validation tests pass 12 tests, cumulative-taxonomy and prototype tests each pass 11 tests, and the full suite passes 243 tests without live model calls.
- Advisory quotes are covered at each Stage 2 evidence location and through candidate storage, Excel/JSON export, and offline rebuild. Candidate-validation tests pass 13 tests, prototype tests pass 12 tests, CLI outcome tests pass 13 tests, and the full suite passes 245 tests without live model calls.

The independent read-only reviewer `/root/review_prototype` passed the final code and documentation against the agreement. Its initial finding, inconsistent saved topic totals, is fixed and covered by a regression test. It independently reran all 11 prototype tests. It also reviewed the Stage 2 relaxations and confirmed supplied edges remain validated, unsupported labels do not enter the aggregated taxonomy, advisory quotes propagate through storage and rebuild, and the normal path remains strict. No remaining actionable findings were reported.

Documentation now links the prototype implementation to its specification, glossary, architecture, run guide, and format reference. Existing default-workflow, reviewer, storage, and provider documentation remains applicable. After separate owner approval, the README now includes a concise, recruiter-facing example from the three-exam LAW run. The local dependency maps were refreshed; no generated maps or course artifacts are committed.

## Required owner review

1. Run the analysis command in `docs/guides/run-law-prototype.md` using the configured provider. Expect a saved candidate and two output paths under `LAW_1/prototype/`.
2. Compare `candidates/2025_june.json` with the paper. Expect Q1 through Q11 once each and marks `1, 1, 1, 1, 1, 5, 5, 10, 15, 30, 30`, totaling 100.
3. Open both prototype reports. Confirm matching generation IDs and rankings, readable sheets, and sensible topic assignments for Q10 and Q11 before selecting portfolio material.

The live run is complete; subject-matter review of its content remains pending. No
model accuracy is claimed from offline tests alone.
