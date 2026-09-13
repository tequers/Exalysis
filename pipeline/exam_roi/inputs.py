"""Turn a source paper into text with its page references; no CLI, provider, or course paths.

Text is read, never rendered: a PDF is accepted only when every page carries an
extractable text layer. That check answers one question — did this page yield any
text — and nothing more. Garbled glyphs, half-read columns, dropped figures,
formulas flattened into noise, and text extracted out of reading order all pass
it. It is a floor under the model's input, not a guarantee that the input is
faithful.

Callers decide how to present the outcome: every failure here raises
ExtractionError with a reason and a remedy, and nothing in this module prints,
exits, or calls a model.
"""

import codecs
from dataclasses import dataclass
from io import BytesIO
import re

SUPPORTED_SUFFIXES = (".txt", ".pdf")
TEXT_ENCODING = "utf-8"

#: What the completeness check does and does not cover, for messages and docs.
DETECTION_LIMIT = (
    "A page counts as readable when it yields any text at all; garbled, partial "
    "or out-of-order extraction is not detected."
)

_BYTE_ORDER_MARKS = (
    (codecs.BOM_UTF32_LE, "UTF-32 LE"),
    (codecs.BOM_UTF32_BE, "UTF-32 BE"),
    (codecs.BOM_UTF16_LE, "UTF-16 LE"),
    (codecs.BOM_UTF16_BE, "UTF-16 BE"),
)


class ExtractionError(ValueError):
    """A source paper cannot be turned into text complete enough to analyse.

    `kind` names the defect for callers that branch on it; `reason` states what is
    wrong with this file, and `remedy` what the person holding it must change.
    """

    def __init__(self, kind, reason, remedy):
        self.kind = kind
        self.reason = reason
        self.remedy = remedy
        super().__init__(f"{reason} {remedy}")


@dataclass(frozen=True)
class TextSegment:
    """Where one page (or a whole text file) sits in the extracted text.

    Offsets cover the block as it was handed to the model, `[Page N]` header
    included, so a later evidence check can map a quote back to its page.
    """

    label: str
    page: object          # 1-based page number, or None for a source without pages
    char_start: int
    char_end: int
    line_start: int
    line_count: int

    def as_dict(self):
        return {"label": self.label, "page": self.page,
                "char_start": self.char_start, "char_end": self.char_end,
                "line_start": self.line_start, "line_count": self.line_count}


@dataclass(frozen=True)
class ExtractedText:
    """Accepted text, how it was read, and where each part of it came from."""

    text: str
    segments: tuple
    kind: str
    page_count: object    # pages read, or None for a source without pages
    encoding: object      # text-file encoding, or None for a PDF

    def summary(self):
        """One line naming what was read, for a run log."""
        if self.page_count is not None:
            return f"{self.page_count} page(s) of text from the PDF text layer"
        lines = self.segments[0].line_count if self.segments else 0
        return f"{len(self.text)} characters of {self.encoding} text over {lines} line(s)"

    def provenance(self):
        """The source references worth keeping next to the saved analysis."""
        record = {
            "extraction_kind": self.kind,
            "character_count": len(self.text),
            "completeness_check": "every page produced text",
            "completeness_check_limit": DETECTION_LIMIT,
            "segments": [segment.as_dict() for segment in self.segments],
        }
        if self.page_count is not None:
            record["page_count"] = self.page_count
        if self.encoding is not None:
            record["text_encoding"] = self.encoding
        return record


def extract_exam_text(path, source_bytes=None):
    """Read one paper, or say why it cannot be read. Returns an ExtractedText.

    Raises ExtractionError for an unsupported file type, an unreadable or textless
    PDF, text that is not valid UTF-8, and text that holds no characters — every
    case where sending the file on would mean analysing a paper the model never
    fully saw.
    """
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ExtractionError(
            "unsupported_type",
            f"{path.name} is a {suffix or 'no-suffix'} file, and only "
            f"{' and '.join(SUPPORTED_SUFFIXES)} papers can be read.",
            "Supply the paper as a .pdf with a text layer, or as a UTF-8 .txt file.",
        )

    if source_bytes is None:
        source_bytes = path.read_bytes()

    if suffix == ".pdf":
        return _extract_pdf(path, source_bytes)
    return _extract_text_file(path, source_bytes)


def _extract_text_file(path, source_bytes):
    text = _decode_utf8(path, source_bytes)
    if not text.strip():
        raise ExtractionError(
            "empty_text",
            f"{path.name} holds no text.",
            "Put the paper's questions in the file, or point add-exam at the right file.",
        )
    body, segments = _assemble([(None, text)])
    return ExtractedText(text=body, segments=segments, kind="utf8_text_file",
                         page_count=None, encoding=TEXT_ENCODING)


def _decode_utf8(path, source_bytes):
    """Decode strictly: a byte that is not UTF-8 is reported, never replaced.

    Replacing it would hand the model a paper with silent holes in it, and every
    later quote check would compare against characters the paper never contained.
    """
    try:
        return source_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        line = source_bytes[:exc.start].count(b"\n") + 1
        column = exc.start - source_bytes.rfind(b"\n", 0, exc.start)
        offending = source_bytes[exc.start:exc.end].hex(" ")
        hint = ""
        for bom, name in _BYTE_ORDER_MARKS:
            if source_bytes.startswith(bom):
                hint = f" The file starts with a {name} byte-order mark."
                break
        raise ExtractionError(
            "invalid_encoding",
            f"{path.name} is not {TEXT_ENCODING} text: byte {exc.start} "
            f"(line {line}, column {column}, 0x{offending}) is not valid "
            f"{TEXT_ENCODING}.{hint}",
            f"Re-save the file as {TEXT_ENCODING} and run add-exam again. "
            f"{TEXT_ENCODING} is the only supported encoding for .txt papers; "
            "a byte-order mark is accepted.",
        ) from None


def _extract_pdf(path, source_bytes):
    pypdf = _import_reader("pypdf")
    try:
        reader = pypdf.PdfReader(BytesIO(source_bytes))
        pages = _read_pdf_pages(reader.pages, layout=True)
    except Exception as exc:                     # any pypdf parse failure
        raise ExtractionError(
            "unreadable_pdf",
            f"{path.name} could not be opened as a PDF: {exc}",
            "Check the file is a complete, uncorrupted PDF, or export the paper again.",
        ) from None

    kind = "pdf_text_layer"
    # Some PDFs have a valid text layer but broken cross-reference pointers. pypdf
    # can open those files yet return no text, while pdfminer (through pdfplumber)
    # can still read the embedded characters. Ask it whenever any page came back
    # empty, so nobody is told to OCR a paper that is already readable. The
    # fallback stays text-only: no rendering or OCR is involved here.
    if pages and not all(text.strip() for _, text in pages):
        fallback = _pdfplumber_pages(source_bytes)
        if _readable(fallback) > _readable(pages):
            pages, kind = fallback, "pdf_text_layer_pdfminer_fallback"

    if not pages:
        raise ExtractionError(
            "empty_text",
            f"{path.name} holds no pages.",
            "Supply the complete paper as a PDF with a text layer, or as a UTF-8 .txt file.",
        )

    textless = [number for number, text in pages if not text.strip()]
    if textless:
        raise ExtractionError(
            "textless_pages",
            _textless_reason(path, textless, len(pages)),
            "Run OCR over the paper (for example `ocrmypdf in.pdf out.pdf`) and add the "
            "result, or supply the paper as a UTF-8 .txt file. A genuinely blank page "
            f"has to be removed from the file first. {DETECTION_LIMIT}",
        )

    body, segments = _assemble(pages)
    return ExtractedText(text=body, segments=segments, kind=kind,
                         page_count=len(pages), encoding=None)


def _readable(pages):
    """How many of these pages produced text — the only measure used to pick a reader."""
    return sum(1 for _, text in pages if text.strip())


def _textless_reason(path, textless, total):
    listed = ", ".join(str(number) for number in textless[:10])
    if len(textless) > 10:
        listed += f", … (+{len(textless) - 10} more)"
    if len(textless) == total:
        return (f"No page of {path.name} has a text layer — all {total} page(s) are "
                f"images or blank, so the paper cannot be read as text.")
    label = "page" if len(textless) == 1 else "pages"
    return (f"{len(textless)} of {total} page(s) in {path.name} have no text layer "
            f"({label} {listed}); reading it would drop those questions.")


def _import_reader(module_name):
    try:
        return __import__(module_name)
    except ImportError:
        raise ExtractionError(
            "reader_unavailable",
            f"Reading a PDF needs the {module_name} package, which is not installed.",
            f"Install it with `pip install {module_name}`, or supply the paper as a "
            "UTF-8 .txt file.",
        ) from None


def _read_pdf_pages(pdf_pages, *, layout):
    """Every page as (number, text) — textless pages included, so they can be reported."""
    return [(number, _normalize(_page_text(page, layout)))
            for number, page in enumerate(pdf_pages, 1)]


def _page_text(page, layout):
    """This page's text, or "" when the reader cannot produce any.

    A page with no content at all makes pypdf raise rather than return nothing.
    Either way the page yielded no text, which the textless-page check reports as
    such — a page nobody can read must not be confused with a corrupt file.
    """
    try:
        return page.extract_text(extraction_mode="layout") if layout else page.extract_text()
    except TypeError:                            # older readers take no extraction_mode
        pass
    except Exception:
        return ""
    try:
        return page.extract_text()
    except Exception:
        return ""


def _normalize(text):
    # Layout mode pads every line to preserve columns; that padding carries no
    # information and is pure prompt weight in Stage 1.
    text = "\n".join(line.rstrip() for line in (text or "").splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip("\n")


def _pdfplumber_pages(source_bytes):
    try:
        import pdfplumber
    except ImportError:
        return []
    try:
        with pdfplumber.open(BytesIO(source_bytes)) as reader:
            return _read_pdf_pages(reader.pages, layout=False)
    except Exception:                            # the primary reader's outcome stands
        return []


def _assemble(blocks):
    """Join (page, text) blocks into one string, recording where each one landed."""
    parts, segments = [], []
    offset, line = 0, 1
    for index, (page, text) in enumerate(blocks):
        block = text if page is None else f"[Page {page}]\n{text}"
        if index:
            offset += 2                          # the blank line between blocks
            line += 2
        segments.append(TextSegment(
            label="whole file" if page is None else f"Page {page}",
            page=page,
            char_start=offset,
            char_end=offset + len(block),
            line_start=line,
            line_count=block.count("\n") + 1,
        ))
        parts.append(block)
        offset += len(block)
        line += block.count("\n")
    return "\n\n".join(parts), tuple(segments)
