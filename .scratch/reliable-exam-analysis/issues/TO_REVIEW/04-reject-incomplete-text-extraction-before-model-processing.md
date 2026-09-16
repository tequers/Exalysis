# 04: Reject incomplete text extraction before model processing

```json
{
  "schema_version": 1,
  "id": "04",
  "priority": "P1",
  "queue_order": 2,
  "areas": [
    "extraction"
  ],
  "depends_on": [],
  "related_to": [],
  "references": [
    "README.md",
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/inputs.py",
    "pipeline/tests/test_input_extraction.py"
  ],
  "verification": {
    "commit": "b0dec34a18d51af266f73848c35c641fe353d10f",
    "checked_at": "2026-09-16T13:32:45+00:00",
    "criteria_digest": "6231c08091ac73063087042e0bdddf3a7664e7cd327251c42669addada84b65a",
    "checker": "Codex automated re-review",
    "result": "partially_resolved",
    "evidence": [
      "Independent Standards and Spec reviews found a PDF provenance bypass when extraction_kind is pdf_text_layer but page_count is absent, plus missing reverse-direction page-count and no-model-call regression cases. Focused tests: 51 passed. Full suite: 212 passed. add-exam --help and git diff --check passed."
    ],
    "provisional": true
  },
  "closure": null
}
```

**What to build:** Tell users when a paper needs input correction before any model request is made.

- [x] Reject empty or whitespace-only extraction before a model call.
- [ ] Identify textless PDF pages and require corrected input instead of silently discarding pages; do not claim this detects every extraction defect.
- [x] Report invalid text encoding rather than silently replacing characters, and document supported text input encoding.
- [ ] Preserve available page or source-position references for later evidence checks.
- [ ] Explain supported text-based inputs, OCR preparation, and that extracted exam text is sent to the configured provider.
- [ ] Test empty files, fully textless and mixed PDFs, invalid encoding, and absence of model calls for rejected inputs.

**Architecture:** Follow [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md). Keep extraction and source evidence in the inputs module. Return explicit extraction outcomes; leave command presentation and process exit decisions to the CLI.

## Completion evidence

- New [inputs module](../../../../pipeline/exam_roi/inputs.py) owns reading a paper and
  its source references. It raises `ExtractionError` (kind, reason, remedy) and
  never prints, exits, or calls a model; `pipeline.py` presents the outcome and
  keeps the exit decision, per [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md).
- Extraction runs before Stage 1, so a rejected paper costs no model request:
  empty or whitespace-only text, a PDF with no pages, an unopenable PDF, a missing
  PDF reader, an unsupported file type, and invalid encoding all raise first.
- Textless PDF pages are named (`2 of 4 page(s) ... (pages 2, 4)`) and the paper is
  refused rather than analysed with those pages dropped. Both the message and the
  docs state the limit: a page passes when it yields any text, so garbled, partial
  or out-of-order extraction is not detected. The pdfplumber text fallback now runs
  whenever any page came back empty, so a readable paper is not sent for OCR; one
  reader's pages are taken whole rather than stitched together.
- `.txt` papers are decoded as strict UTF-8 (a byte-order mark is accepted).
  An invalid byte is reported with its offset, line, column and value — and a
  UTF-16/32 mark is named — instead of being replaced with `�`. The supported
  encoding is documented in the README, the CLI help screen, and the module docstring.
- Page and offset references for every part of the analysed text are kept in
  `source_provenance.extraction` (`extraction_kind`, per-page `char_start`,
  `char_end`, `line_start`, `line_count`, and the check's stated limit).
  `_validate_extraction_provenance` in the evaluation module now requires them, so
  no candidate can be filed without a way back from a quote to its page.
- README (["What it can read"](../../../../README.md#what-it-can-read)), the CLI help
  screen, `add-exam --help`, and the pipeline docstring explain the supported
  inputs, OCR preparation, the detection limit, and that the extracted text is sent
  to the configured provider.
- [Regression checks](../../../../pipeline/tests/test_input_extraction.py): 59 tests
  pass (`python -m unittest discover -s tests -t tests`), covering empty and
  whitespace-only files, fully textless and mixed PDFs, invalid encoding and
  byte-order marks, unsupported types, reader failures, preserved page references,
  and no model call for any rejected input. Three of them build a real PDF and run
  the installed reader — that is what caught a page with no `/Contents` being
  reported as a corrupt file instead of a textless page. `git diff --check` passed.

Not in scope: process exit codes for rejected inputs stay with ticket 15, and no
OCR or page rendering is performed anywhere in the pipeline.

## Review findings

Automated re-review found one correctness gap and two regression-test gaps. No
human review is needed until they are fixed.

1. `pipeline/exam_roi/evaluation.py:409` decides whether provenance is paged only
   from the presence of `page_count`. A record with
   `extraction_kind="pdf_text_layer"`, no `page_count`, and one `whole file`
   segment passes validation. Bind PDF extraction kinds to required page metadata
   so a candidate cannot lose its page references. Add a regression test for this
   bypass.
2. The page-count disagreement regression covers only pypdf finding more pages
   than pdfplumber. Add the reverse case so a future one-sided comparison cannot
   silently accept either disagreement direction.
3. Add integration checks proving that fully textless PDFs and reader page-count
   disagreements stop before any model call, matching the existing checks for
   empty text, invalid encoding, and mixed PDFs.

The earlier fallback page-count fix and `add-exam --help` guidance now pass review.
The provenance range, order, and coverage checks work when `page_count` is present.

Verification during re-review: 51 focused tests and 212 full-suite tests passed in
UTF-8 mode; `add-exam --help` and `git diff --check` passed. A read-only probe
reproduced the missing-`page_count` provenance bypass.

Non-blocking standards notes: validation messages expose field names such as
`character_count`; the provenance validator tests would fit better in
`test_candidate_validation.py`; and synthetic provenance repeats the six-field
segment shape instead of sharing a constructor.
