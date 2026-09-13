"""Ticket 04: a paper the pipeline cannot fully read never reaches a model."""

import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


PIPELINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPELINE))

from exam_roi.inputs import ExtractionError, extract_exam_text

with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}):
    app = importlib.import_module("pipeline")


def fake_pdf(*page_texts, fallback_texts=None):
    """A pypdf/pdfplumber pair whose pages return the given text."""

    def pages(texts):
        result = []
        for text in texts:
            page = MagicMock()
            page.extract_text.return_value = text
            result.append(page)
        return result

    pypdf = SimpleNamespace(
        PdfReader=MagicMock(return_value=SimpleNamespace(pages=pages(page_texts)))
    )
    reader = MagicMock()
    reader.__enter__.return_value = SimpleNamespace(pages=pages(fallback_texts or ()))
    reader.__exit__.return_value = False
    pdfplumber = SimpleNamespace(open=MagicMock(return_value=reader))
    return {"pypdf": pypdf, "pdfplumber": pdfplumber}


class TextFileExtractionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def write(self, name, data):
        path = self.folder / name
        path.write_bytes(data)
        return path

    def test_empty_and_whitespace_only_files_are_rejected(self):
        for name, data in [("empty.txt", b""), ("blank.txt", b"   \n\n\t  \n")]:
            with self.subTest(name=name):
                with self.assertRaises(ExtractionError) as raised:
                    extract_exam_text(self.write(name, data))
                self.assertEqual(raised.exception.kind, "empty_text")
                self.assertIn(name, raised.exception.reason)
                self.assertTrue(raised.exception.remedy)

    def test_invalid_encoding_is_reported_and_never_replaced(self):
        path = self.write("latin1.txt", "Pregunta 1: derivaci\xf3n".encode("latin-1"))
        with self.assertRaises(ExtractionError) as raised:
            extract_exam_text(path)
        error = raised.exception
        self.assertEqual(error.kind, "invalid_encoding")
        self.assertIn("utf-8", error.reason)
        self.assertIn("line 1", error.reason)
        self.assertNotIn("�", error.reason)
        self.assertIn("Re-save", error.remedy)

    def test_utf16_file_is_rejected_with_its_byte_order_mark_named(self):
        path = self.write("utf16.txt", "Question 1".encode("utf-16"))
        with self.assertRaises(ExtractionError) as raised:
            extract_exam_text(path)
        self.assertIn("UTF-16 LE byte-order mark", raised.exception.reason)

    def test_utf8_text_is_accepted_with_or_without_a_byte_order_mark(self):
        body = "Question 1\nExplain paging.\n"
        for name, data in [("plain.txt", body.encode("utf-8")),
                           ("bom.txt", b"\xef\xbb\xbf" + body.encode("utf-8"))]:
            with self.subTest(name=name):
                extracted = extract_exam_text(self.write(name, data))
                self.assertEqual(extracted.text, body)
                self.assertEqual(extracted.encoding, "utf-8")
                self.assertIsNone(extracted.page_count)
                self.assertEqual(len(extracted.segments), 1)
                self.assertEqual(extracted.segments[0].page, None)
                self.assertEqual(extracted.segments[0].char_end, len(body))

    def test_unsupported_file_types_are_rejected(self):
        with self.assertRaises(ExtractionError) as raised:
            extract_exam_text(self.write("paper.docx", b"PK\x03\x04"))
        self.assertEqual(raised.exception.kind, "unsupported_type")


class PdfExtractionTests(unittest.TestCase):
    def extract(self, modules, name="exam.pdf"):
        with patch.dict(sys.modules, modules):
            return extract_exam_text(Path(name), b"%PDF-test")

    def test_fully_textless_pdf_is_rejected_as_a_scan(self):
        with self.assertRaises(ExtractionError) as raised:
            self.extract(fake_pdf("", "  \n"))
        error = raised.exception
        self.assertEqual(error.kind, "textless_pages")
        self.assertIn("No page of exam.pdf has a text layer", error.reason)
        self.assertIn("ocrmypdf", error.remedy)

    def test_mixed_pdf_names_its_textless_pages_instead_of_dropping_them(self):
        with self.assertRaises(ExtractionError) as raised:
            self.extract(fake_pdf("Question 1", "", "Question 3", ""))
        error = raised.exception
        self.assertEqual(error.kind, "textless_pages")
        self.assertIn("2 of 4 page(s)", error.reason)
        self.assertIn("pages 2, 4", error.reason)
        # The check is not advertised as catching every extraction defect.
        self.assertIn("garbled, partial", error.remedy)

    def test_page_references_are_preserved_for_every_page(self):
        extracted = self.extract(fake_pdf("Question 1\nExplain paging.", "Question 2"))
        self.assertEqual(extracted.kind, "pdf_text_layer")
        self.assertEqual(extracted.page_count, 2)
        self.assertEqual(
            extracted.text,
            "[Page 1]\nQuestion 1\nExplain paging.\n\n[Page 2]\nQuestion 2")
        first, second = extracted.segments
        self.assertEqual((first.page, first.line_start, first.line_count), (1, 1, 3))
        self.assertEqual((second.page, second.line_start, second.line_count), (2, 5, 2))
        for segment in extracted.segments:
            self.assertEqual(
                extracted.text[segment.char_start:segment.char_end].splitlines()[0],
                f"[Page {segment.page}]")

    def test_uses_text_fallback_when_pypdf_returns_no_text(self):
        extracted = self.extract(
            fake_pdf("", fallback_texts=["Question 1\nExplain scheduling."]))
        self.assertEqual(extracted.text, "[Page 1]\nQuestion 1\nExplain scheduling.")
        self.assertEqual(extracted.kind, "pdf_text_layer_pdfminer_fallback")

    def test_fallback_rescues_a_page_the_primary_reader_missed(self):
        # Nobody should be told to OCR a paper the second text reader can read.
        extracted = self.extract(
            fake_pdf("Question 1", "", fallback_texts=["Question 1", "Question 2"]))
        self.assertEqual(extracted.page_count, 2)
        self.assertEqual(extracted.kind, "pdf_text_layer_pdfminer_fallback")

    def test_primary_reader_stands_when_the_fallback_reads_no_more_pages(self):
        # One reader's pages are taken whole: text is never stitched together from
        # both, so a paper each reader reads half of is still sent back for fixing.
        with self.assertRaises(ExtractionError) as raised:
            self.extract(fake_pdf("Question 1", "", fallback_texts=["", "Question 2"]))
        self.assertIn("page 2", raised.exception.reason)

    def test_fallback_that_also_finds_nothing_still_rejects_the_paper(self):
        with self.assertRaises(ExtractionError) as raised:
            self.extract(fake_pdf("", fallback_texts=[""]))
        self.assertEqual(raised.exception.kind, "textless_pages")

    def test_pdf_with_no_pages_is_rejected(self):
        with self.assertRaises(ExtractionError) as raised:
            self.extract(fake_pdf())
        self.assertEqual(raised.exception.kind, "empty_text")

    def test_unreadable_pdf_is_reported_rather_than_crashing(self):
        pypdf = SimpleNamespace(PdfReader=MagicMock(side_effect=ValueError("bad xref")))
        with self.assertRaises(ExtractionError) as raised:
            self.extract({"pypdf": pypdf})
        self.assertEqual(raised.exception.kind, "unreadable_pdf")
        self.assertIn("bad xref", raised.exception.reason)

    def test_missing_pdf_reader_asks_for_the_package_without_exiting(self):
        with patch.dict(sys.modules, {"pypdf": None}):
            with self.assertRaises(ExtractionError) as raised:
                extract_exam_text(Path("exam.pdf"), b"%PDF-test")
        self.assertEqual(raised.exception.kind, "reader_unavailable")
        self.assertIn("pip install pypdf", raised.exception.remedy)


def minimal_pdf(*page_texts):
    """A real PDF whose pages carry the given text; "" makes a page with no content.

    Hand-built so the readers themselves are exercised: a mocked page cannot fail
    the way a real one does (a page with no /Contents makes pypdf raise rather
    than return no text).
    """
    objects, kids, next_id = [], [], 3
    for text in page_texts:
        if text:
            stream = b"BT /F1 24 Tf 72 700 Td (" + text.encode("ascii") + b") Tj ET"
            objects.append((next_id, b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                            b"/Contents %d 0 R /Resources << /Font << /F1 1 0 R >> >> >>"
                            % (next_id + 1)))
            objects.append((next_id + 1, b"<< /Length %d >>\nstream\n" % len(stream)
                            + stream + b"\nendstream"))
            kids.append(next_id)
            next_id += 2
        else:
            objects.append((next_id, b"<< /Type /Page /Parent 2 0 R "
                                     b"/MediaBox [0 0 612 792] >>"))
            kids.append(next_id)
            next_id += 1
    objects = [
        (1, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
        (2, b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % k for k in kids)
            + b"] /Count %d >>" % len(kids)),
        *objects,
        (next_id, b"<< /Type /Catalog /Pages 2 0 R >>"),
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), {}
    for number, body in objects:
        offsets[number] = len(out)
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    start = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offsets[n] for n, _ in objects)
    out += (b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
            % (len(objects) + 1, next_id, start))
    return bytes(out)


@unittest.skipUnless(importlib.util.find_spec("pypdf"), "pypdf is not installed")
class RealPdfReaderTests(unittest.TestCase):
    """The same checks against the real reader, which fails in ways a mock cannot."""

    def test_real_pdf_with_text_on_every_page_is_accepted_with_page_references(self):
        extracted = extract_exam_text(
            Path("real.pdf"), minimal_pdf("Question 1", "Question 2"))
        self.assertEqual(extracted.page_count, 2)
        self.assertIn("[Page 1]", extracted.text)
        self.assertIn("Question 2", extracted.text)
        self.assertEqual([segment.page for segment in extracted.segments], [1, 2])

    def test_real_pdf_with_a_contentless_page_is_reported_as_textless_not_corrupt(self):
        with self.assertRaises(ExtractionError) as raised:
            extract_exam_text(Path("real.pdf"), minimal_pdf("Question 1", ""))
        self.assertEqual(raised.exception.kind, "textless_pages")
        self.assertIn("page 2", raised.exception.reason)

    def test_bytes_that_are_not_a_pdf_are_reported_as_unreadable(self):
        with self.assertRaises(ExtractionError) as raised:
            extract_exam_text(Path("real.pdf"), b"not a pdf at all")
        self.assertEqual(raised.exception.kind, "unreadable_pdf")


class RejectedInputMakesNoModelCallTests(unittest.TestCase):
    """The whole point of the ticket: rejection happens before any request."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        app.setup_course_folder(Path(self.tmp.name))

    def process(self, name, data):
        path = Path(self.tmp.name) / name
        path.write_bytes(data)
        no_calls = MagicMock(side_effect=AssertionError("a model was called"))
        with patch.object(app, "call_llm", no_calls), \
             patch.object(app, "_client", no_calls):
            with self.assertRaises(ExtractionError) as raised:
                app.process_exam_file(path, force=True)
        no_calls.assert_not_called()
        return raised.exception

    def test_empty_paper_is_rejected_before_stage_1_and_saves_nothing(self):
        error = self.process("empty_2026.txt", b"\n \n")
        self.assertEqual(error.kind, "empty_text")
        self.assertEqual(list(app.CANDIDATES_DIR.glob("*.json")), [])
        self.assertEqual(list(app.PARSED_DIR.glob("*.json")), [])

    def test_bad_encoding_is_rejected_before_stage_1(self):
        self.assertEqual(
            self.process("latin_2026.txt", b"Pregunta \xf3").kind, "invalid_encoding")

    def test_scanned_pdf_is_rejected_before_stage_1(self):
        path = Path(self.tmp.name) / "scan_2026.pdf"
        path.write_bytes(b"%PDF-test")
        no_calls = MagicMock(side_effect=AssertionError("a model was called"))
        with patch.dict(sys.modules, fake_pdf("Question 1", "")), \
             patch.object(app, "call_llm", no_calls), \
             patch.object(app, "_client", no_calls):
            with self.assertRaises(ExtractionError) as raised:
                app.process_exam_file(path, force=True)
        self.assertEqual(raised.exception.kind, "textless_pages")
        no_calls.assert_not_called()
        self.assertEqual(list(app.CANDIDATES_DIR.glob("*.json")), [])

    def test_add_exam_reports_the_problem_and_the_fix_for_each_rejected_file(self):
        for name, data in [("empty_2026.txt", b" "), ("latin_2026.txt", b"\xf3")]:
            (Path(self.tmp.name) / name).write_bytes(data)
        args = SimpleNamespace(paths=[], recursive=False, year=None, total_marks=None,
                               exam_id=None, force=True)
        no_calls = MagicMock(side_effect=AssertionError("a model was called"))
        with patch.object(app, "call_llm", no_calls), \
             patch.object(app, "_client", no_calls), \
             patch("builtins.print") as printed:
            app.cmd_add_exam(args)
        log = "\n".join(str(call.args[0]) for call in printed.call_args_list if call.args)
        no_calls.assert_not_called()
        self.assertIn("empty_2026.txt holds no text", log)
        self.assertIn("is not utf-8 text", log)
        self.assertIn("Re-save the file as utf-8", log)
        self.assertIn("2 failed", log)


class AcceptedInputProvenanceTests(unittest.TestCase):
    def test_saved_candidate_keeps_the_page_references_and_the_check_limit(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        app.setup_course_folder(Path(tmp.name))
        paper = Path(tmp.name) / "paper_2026.txt"
        paper.write_text("Question 1\nSolve the two equations.\n", encoding="utf-8")

        question = {"q_id": "Q1", "text": "Solve the two equations.",
                    "marks": 10, "format": "short_answer"}
        tag = {"topics": ["Equations"], "quote": "Solve the two equations.",
               "rationale": "The cited task directly tests this topic.", "uncertainties": []}
        scores = {"Equations": {
            "question_difficulty": [{
                "q_id": "Q1", "level": 3, "quote": "Solve the two equations.",
                "rationale": "This follows a standard multi-step method.",
                "uncertainties": []}],
            "difficulty_rationale": "The question requires a standard sequence of steps.",
            "assumed_prerequisites": [], "prerequisite_evidence": [],
            "Conn": 1, "connection_rationale": "No direct downstream use is supported.",
            "connection_evidence": [{"q_id": "Q1", "quote": "Solve the two equations."}],
            "connection_edges": [], "unlocks": [], "prerequisites": [], "uncertainties": [],
        }}

        with patch.object(app, "stage1_extract", return_value=([question], 2026)), \
             patch.object(app, "_stage2_tag", return_value=({"Q1": tag}, ["Equations"])), \
             patch.object(app, "call_llm", return_value=json.dumps(scores)):
            app.process_exam_file(paper, force=True)

        candidate = json.loads(
            (app.CANDIDATES_DIR / "paper_2026.json").read_text(encoding="utf-8"))
        extraction = candidate["source_provenance"]["extraction"]
        self.assertEqual(extraction["extraction_kind"], "utf8_text_file")
        self.assertEqual(extraction["text_encoding"], "utf-8")
        self.assertEqual(extraction["segments"][0]["line_start"], 1)
        self.assertIn("garbled", extraction["completeness_check_limit"])


if __name__ == "__main__":
    unittest.main()
