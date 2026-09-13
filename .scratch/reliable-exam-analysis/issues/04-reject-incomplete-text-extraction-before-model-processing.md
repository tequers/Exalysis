# 04: Reject incomplete text extraction before model processing

**What to build:** Tell users when a paper needs input correction before any model request is made.

**Blocked by:** None (can start immediately).

**Status:** implemented (2026-09-12)

**Priority:** P1

- [x] Reject empty or whitespace-only extraction before a model call.
- [x] Identify textless PDF pages and require corrected input instead of silently discarding pages; do not claim this detects every extraction defect.
- [x] Report invalid text encoding rather than silently replacing characters, and document supported text input encoding.
- [x] Preserve available page or source-position references for later evidence checks.
- [x] Explain supported text-based inputs, OCR preparation, and that extracted exam text is sent to the configured provider.
- [x] Test empty files, fully textless and mixed PDFs, invalid encoding, and absence of model calls for rejected inputs.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Keep extraction and source evidence in the inputs module. Return explicit extraction outcomes; leave command presentation and process exit decisions to the CLI.


## Completion evidence

- New [inputs module](../../../pipeline/exam_roi/inputs.py) owns reading a paper and
  its source references. It raises `ExtractionError` (kind, reason, remedy) and
  never prints, exits, or calls a model; `pipeline.py` presents the outcome and
  keeps the exit decision, per [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md).
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
- README (["What it can read"](../../../README.md#what-it-can-read)), the CLI help
  screen, `add-exam --help`, and the pipeline docstring explain the supported
  inputs, OCR preparation, the detection limit, and that the extracted text is sent
  to the configured provider.
- [Regression checks](../../../pipeline/tests/test_input_extraction.py): 59 tests
  pass (`python -m unittest discover -s tests -t tests`), covering empty and
  whitespace-only files, fully textless and mixed PDFs, invalid encoding and
  byte-order marks, unsupported types, reader failures, preserved page references,
  and no model call for any rejected input. Three of them build a real PDF and run
  the installed reader — that is what caught a page with no `/Contents` being
  reported as a corrupt file instead of a textless page. `git diff --check` passed.

Not in scope: process exit codes for rejected inputs stay with ticket 15, and no
OCR or page rendering is performed anywhere in the pipeline.
