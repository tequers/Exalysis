"""
Render a supplied ranked-topic snapshot to XLSX and JSON.

Per docs/adr/0008-modular-pipeline-architecture.md, this module owns report
rendering only: `write_xlsx` and `write_json` take an explicit destination
path and an already-built snapshot (ranked topic rows, the exam list, and the
taxonomy dict) and write them out. They must NOT:
  - read course-folder globals (COURSE_FOLDER, OUTPUT_XLSX, OUTPUT_JSON, ...);
    every path this module writes to is passed in by the caller;
  - decide which analyses are accepted, aggregate marks, rank topics, or assign
    tiers. The workflow selects accepted records and exam_roi.scoring builds the
    report snapshot;
  - call a model or reach a provider;
  - mutate taxonomy, or any other input it is given.

This module owns short, disambiguated exam labels. Format arithmetic now lives
in exam_roi.scoring and remains re-exported here for compatibility.

Importing this module must not require credentials, terminate the process,
or reconfigure global streams — it only defines functions and constants.
"""

import json
import re
from datetime import datetime

from .evaluation import LEGACY_VERSION, difficulty_version
from .scoring import weighted_fmt


def _id_tokens(exam_id: str) -> list:
    return [t for t in re.split(r"[_\-\s]+", exam_id) if t]


# A local copy of pipeline.py's EARLIEST_YEAR. This value only bounds the
# heuristic that recognizes a bare year inside an exam ID label.
_EARLIEST_YEAR = 1990


def _is_year_token(token: str) -> bool:
    return (token.isdigit() and len(token) == 4
            and _EARLIEST_YEAR <= int(token) <= datetime.now().year + 1)


def exam_labels(exam_list: list) -> dict:
    """Return short, distinct report labels keyed by exam ID."""
    by_year = {}
    for exam in exam_list:
        by_year.setdefault(exam.get("year"), []).append(exam)

    labels = {}
    for year, group in by_year.items():
        head = str(year) if year else "?"
        if len(group) == 1:
            labels[group[0]["exam_id"]] = head
            continue

        token_lists = [_id_tokens(e["exam_id"]) for e in group]
        shortest = min(len(tokens) for tokens in token_lists)

        n_pre = 0
        while (n_pre < shortest - 1
               and len({tokens[n_pre].lower() for tokens in token_lists}) == 1):
            n_pre += 1
        n_suf = 0
        while (n_pre + n_suf < shortest - 1
               and len({tokens[-1 - n_suf].lower() for tokens in token_lists}) == 1):
            n_suf += 1

        for exam, tokens in zip(group, token_lists):
            rest = tokens[n_pre:len(tokens) - n_suf] or tokens[-1:]
            rest = [token for token in rest if not _is_year_token(token)] or rest
            suffix = " ".join(rest)
            if len(suffix) > 14:
                suffix = suffix[:13] + "…"
            labels[exam["exam_id"]] = f"{head} {suffix}"
    return labels


# ── JSON writer ────────────────────────────────────────────────────────────────

def write_json(rows: list, destination) -> None:
    """
    Write the ranked topic list as a flat JSON array — the machine-readable twin of the
    .xlsx. Same rows, same sort order (priority desc), no formatting concerns: this is what
    a script, or an LLM reading the exam folder directly, should parse instead of the sheet.
    Each element: topic, Freq, G_Marks, Conn, Diff, Fmt, priority, rank, tier, appearances,
    prerequisites, per_exam (per-exam presence/marks breakdown).

    destination : path to write the JSON file to (caller-supplied — see the module
                  docstring; this function never reads a course-folder global).
    """
    destination.write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


# ── Excel writer ───────────────────────────────────────────────────────────────

def write_xlsx(rows: list, exam_list: list, taxonomy: dict, destination) -> None:
    """
    rows      : list of topic dicts, sorted by priority desc, each containing:
                topic, Freq, G_Marks, Conn, Diff, Fmt, priority, rank, tier,
                prerequisites, per_exam={exam_id: {present, mark_fraction, fmt_score}}
    exam_list : list of exam dicts sorted by year
    taxonomy  : full taxonomy dict (for Taxonomy sheet)
    destination : path to save the workbook to (caller-supplied — see the module
                  docstring; this function never reads a course-folder global).
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.formatting.rule import ColorScaleRule, FormulaRule
    from openpyxl.utils import get_column_letter as gcl

    wb = Workbook()

    # ── Micro-helpers ──
    P = dict(
        dk_blue="1F4E79", md_blue="2E75B6", lt_blue="BDD7EE", pale="DEEAF1",
        frm="E2EFDA",   frm2="EBF5EB",
        audit="FFF8EE", audit2="FEF3E2",
        tier1="C6EFCE",
        white="FFFFFF",  gray="F2F2F2",  gray2="EDEDED",
        brown="7B3F00",  dk_gray="4A4A4A",
    )
    def fn(sz=10, bold=False, color="000000", italic=False):
        return Font(name="Arial", size=sz, bold=bold, color=color, italic=italic)
    def fl(h): return PatternFill("solid", fgColor=h)
    def al(h="left", v="center", w=True):
        return Alignment(horizontal=h, vertical=v, wrap_text=w)
    def bd(color="C0C0C0"):
        s = Side(style="thin", color=color)
        return Border(left=s, right=s, top=s, bottom=s)

    exam_ids = [e["exam_id"] for e in exam_list]

    # ── Column definitions ──
    # (header, width, data_key, group)
    # data_key is either a string (row field) or (exam_id, field) tuple for per-exam cols
    FIXED = [
        ("Rank",       7,  "rank",     "scores"),
        ("Tier",      13,  "tier",     "scores"),
        ("Topic",     32,  "topic",    "scores"),
        ("Freq\n(0–1)",    9,  "Freq",     "scores"),
        ("G_Marks\n(0–1)", 9,  "G_Marks",  "scores"),
        ("Conn\n(1–3)",    8,  "Conn",     "scores"),
        ("Diff\n(1–6)",    8,  "Diff",     "scores"),
        ("Fmt\n(avg)",     9,  "Fmt",      "scores"),
        ("Priority",  12,  "priority", "scores"),
    ]
    labels    = exam_labels(exam_list)
    EXAM_COLS = []
    for eid in exam_ids:
        lb = labels.get(eid, eid)
        EXAM_COLS += [
            (f"{lb}\n✓",      8,  (eid, "present"),       "audit"),
            (f"{lb}\nmarks%", 10, (eid, "mark_fraction"),  "audit"),
            (f"{lb}\nFmt",     8, (eid, "fmt_score"),      "audit"),
        ]
    TAIL = [
        ("Diff contract", 22, "difficulty_contract_version", "taxonomy"),
        ("Prerequisites", 34, "prerequisites", "taxonomy"),
        ("Review notes", 32, "review_notes", "taxonomy"),
    ]

    ALL = FIXED + EXAM_COLS + TAIL
    NF = len(FIXED)
    NE = len(EXAM_COLS)

    for i, (_, w, _, _) in enumerate(ALL):
        wb.active.column_dimensions[gcl(i + 1)].width = w

    # ════════════════════════════
    #  Sheet 1: ROI Scores
    # ════════════════════════════
    ws = wb.active
    ws.title = "ROI Scores"
    ws.sheet_view.showGridLines = False

    n_topics = len(rows)
    n_exams  = len(exam_list)
    tier1_n  = sum(1 for r in rows if r["tier"])

    # Row 1: title
    ws.row_dimensions[1].height = 28
    ws.merge_cells(f"A1:{gcl(len(ALL))}1")
    c = ws["A1"]
    c.value = (
        f"Exam ROI Analysis  ·  {n_topics} topics  ·  {n_exams} exam{'s' if n_exams != 1 else ''}"
        f"  ·  {tier1_n} Tier 1  ·  Priority = 100 × (Freq × G_Marks × Conn) / (Diff × Fmt)"
    )
    c.font = fn(12, bold=True, color=P["white"])
    c.fill = fl(P["dk_blue"])
    c.alignment = al("left", "center")

    # Row 2: group headers
    ws.row_dimensions[2].height = 18
    GROUP_BG = {"scores": P["md_blue"], "audit": P["brown"], "taxonomy": P["dk_gray"]}
    spans = [
        (1,       NF,          "SCORES",          P["md_blue"]),
        (NF+1,    NF+NE,       "PER-EXAM AUDIT",  P["brown"]),
        (NF+NE+1, len(ALL),    "TAXONOMY",        P["dk_gray"]),
    ]
    for start, end, label, bg in spans:
        if start > end:
            continue
        ws.merge_cells(f"{gcl(start)}2:{gcl(end)}2")
        c = ws[f"{gcl(start)}2"]
        c.value     = label
        c.font      = fn(9, bold=True, color=P["white"])
        c.fill      = fl(bg)
        c.alignment = al("center", "center")
        c.border    = bd()

    # Row 3: column headers
    ws.row_dimensions[3].height = 50
    ws.freeze_panes = "D4"
    for i, (hdr, _, _, grp) in enumerate(ALL):
        c = ws[f"{gcl(i+1)}3"]
        c.value     = hdr
        c.font      = fn(9, bold=True, color=P["white"])
        c.fill      = fl(GROUP_BG[grp])
        c.alignment = al("center", "center", w=True)
        c.border    = bd()

    # Data rows
    last_row = 3 + n_topics
    for ri, row in enumerate(rows):
        r   = ri + 4
        alt = ri % 2 == 0
        ws.row_dimensions[r].height = 18

        for ci, (_, _, key, grp) in enumerate(ALL):
            c = ws[f"{gcl(ci+1)}{r}"]
            c.font   = fn(10)
            c.border = bd(color="DDDDDD")

            # Background by group
            if grp == "scores":
                c.fill = fl(P["frm2"] if alt else P["frm"])
            elif grp == "audit":
                c.fill = fl(P["audit2"] if alt else P["audit"])
            else:
                c.fill = fl(P["gray2"] if alt else P["white"])

            # Value & number format
            if isinstance(key, tuple):
                eid, field = key
                val = row["per_exam"][eid][field]
                c.value     = val
                c.alignment = al("center", "center")
                if field == "mark_fraction" and val:
                    c.number_format = "0.0%"
                elif field == "fmt_score":
                    c.number_format = "0.0"
            else:
                val = row.get(key, "")
                c.value = val

                if key == "topic":
                    c.font      = fn(10, bold=True)
                    c.fill      = fl(P["gray2"] if alt else P["white"])
                    c.alignment = al("left", "center", w=False)
                elif key == "tier":
                    c.alignment = al("center", "center")
                    if val == "★ Tier 1":
                        c.font = fn(10, bold=True, color="166534")
                elif key == "rank":
                    c.alignment = al("center", "center")
                elif key == "priority":
                    c.number_format = "0.00"
                    c.alignment     = al("center", "center")
                elif key in ("Freq", "G_Marks"):
                    c.number_format = "0.00"
                    c.alignment     = al("center", "center")
                elif key in ("Conn", "Diff"):
                    c.alignment = al("center", "center")
                elif key == "Fmt":
                    c.number_format = "0.0"
                    c.alignment     = al("center", "center")
                else:
                    c.alignment = al("left", "center")

    # Conditional formatting
    if rows:
        data_range  = f"A4:{gcl(len(ALL))}{last_row}"
        tier_col    = gcl(next(i+1 for i, (_, _, k, _) in enumerate(ALL) if k == "tier"))
        pri_col     = gcl(next(i+1 for i, (_, _, k, _) in enumerate(ALL) if k == "priority"))

        ws.conditional_formatting.add(
            data_range,
            FormulaRule(
                formula=[f'${tier_col}4="★ Tier 1"'],
                fill=PatternFill("solid", fgColor=P["tier1"]),
            ),
        )
        ws.conditional_formatting.add(
            f"{pri_col}4:{pri_col}{last_row}",
            ColorScaleRule(
                start_type="min",       start_color="FF9999",
                mid_type="percentile",  mid_value=50, mid_color="FFFF99",
                end_type="max",         end_color="63BE7B",
            ),
        )

    # ════════════════════════════
    #  Sheet 2: Taxonomy
    # ════════════════════════════
    ws2 = wb.create_sheet("Taxonomy")
    ws2.sheet_view.showGridLines = False

    ws2.row_dimensions[1].height = 28
    ws2.merge_cells("A1:G1")
    c = ws2["A1"]
    c.value     = "Topic Taxonomy  —  correct scores with edit-topic or taxonomy.json, then rebuild"
    c.font      = fn(12, bold=True, color=P["white"])
    c.fill      = fl(P["dk_blue"])
    c.alignment = al("left", "center")

    TAX_HDRS   = ["Topic", "Diff (1–6)", "Diff contract", "Conn (1–3)", "First seen", "Appearances", "Prerequisites"]
    TAX_WIDTHS = [32, 9, 22, 9, 16, 14, 42]
    for i, (h, w) in enumerate(zip(TAX_HDRS, TAX_WIDTHS)):
        ws2.column_dimensions[gcl(i+1)].width = w
        c = ws2[f"{gcl(i+1)}2"]
        c.value     = h
        c.font      = fn(10, bold=True, color=P["white"])
        c.fill      = fl(P["md_blue"])
        c.alignment = al("center", "center")
        c.border    = bd()
    ws2.row_dimensions[2].height = 22

    # exam_list is already every parsed exam (cmd_rebuild loaded them) — no re-read.
    appearances_map: dict[str, int] = {}
    for exam in exam_list:
        for t in exam.get("per_topic", {}):
            appearances_map[t] = appearances_map.get(t, 0) + 1

    for ri, (tname, tdata) in enumerate(sorted(taxonomy["topics"].items())):
        r   = ri + 3
        alt = ri % 2 == 0
        bg  = P["gray2"] if alt else P["white"]
        YLW = "FFF2CC"

        vals = [
            (tname,                                "left",   bg),
            (tdata.get("Diff", ""),                "center", YLW),
            (difficulty_version(tdata),             "center", bg),
            (tdata.get("Conn", ""),                "center", YLW),
            (tdata.get("first_seen", ""),          "center", bg),
            (appearances_map.get(tname, 0),        "center", bg),
            (", ".join(tdata.get("prerequisites", [])), "left", bg),
        ]
        for ci, (val, align, bg_c) in enumerate(vals):
            c = ws2[f"{gcl(ci+1)}{r}"]
            c.value     = val
            c.font      = fn(10)
            c.fill      = fl(bg_c)
            c.alignment = al(align, "center")
            c.border    = bd(color="DDDDDD")
        ws2.row_dimensions[r].height = 18

    # ════════════════════════════
    #  Sheet 3: Exam Log
    # ════════════════════════════
    ws3 = wb.create_sheet("Exam Log")
    ws3.sheet_view.showGridLines = False

    ws3.row_dimensions[1].height = 28
    ws3.merge_cells("A1:H1")
    c = ws3["A1"]
    c.value     = "Exam Log  —  one row per processed exam"
    c.font      = fn(12, bold=True, color=P["white"])
    c.fill      = fl(P["dk_blue"])
    c.alignment = al("left", "center")

    LOG_HDRS   = ["Exam ID", "Year", "Sheet label", "Total Marks", "Topics Found",
                  "Source File", "Processed At", "Analysis contract"]
    LOG_WIDTHS = [28, 11, 16, 13, 14, 32, 22, 22]
    for i, (h, w) in enumerate(zip(LOG_HDRS, LOG_WIDTHS)):
        ws3.column_dimensions[gcl(i+1)].width = w
        c = ws3[f"{gcl(i+1)}2"]
        c.value     = h
        c.font      = fn(10, bold=True, color=P["white"])
        c.fill      = fl(P["md_blue"])
        c.alignment = al("center", "center")
        c.border    = bd()
    ws3.row_dimensions[2].height = 22

    for ri, exam in enumerate(exam_list):
        r   = ri + 3
        bg  = P["gray2"] if ri % 2 == 0 else P["white"]
        processed = exam.get("processed_at", "")
        if processed:
            processed = processed[:10]
        for ci, (val, align) in enumerate([
            (exam["exam_id"],                              "left"),
            (exam.get("year_label") or exam.get("year", ""), "center"),
            (labels.get(exam["exam_id"], ""),              "center"),
            (exam.get("total_marks", ""),                  "center"),
            (len(exam.get("per_topic", {})),       "center"),
            (exam.get("source_file", ""),          "left"),
            (processed,                            "center"),
            (exam.get("evaluation_contract_version", LEGACY_VERSION), "center"),
        ]):
            c = ws3[f"{gcl(ci+1)}{r}"]
            c.value     = val
            c.font      = fn(10)
            c.fill      = fl(bg)
            c.alignment = al(align, "center")
            c.border    = bd(color="DDDDDD")
        ws3.row_dimensions[r].height = 18

    wb.save(str(destination))
