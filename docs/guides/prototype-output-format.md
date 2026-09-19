# Prototype Excel and agent JSON format

`add-exam --prototype` and `rebuild --prototype` export every saved candidate in the selected course. Both files describe the same ranked snapshot:

- `prototype/Exam_ROI_Pipeline.xlsx`
- `prototype/Exam_ROI_Pipeline.json`

Both outputs are unreviewed estimates. The Excel banner and each JSON row contain the same generation ID. A successful rebuild replaces both files and assigns a new ID. Matching IDs identify one export operation, not a reviewed or current analysis.

## Excel workbook

The layout follows the existing reference workbook, with three sheets in this order.

| Sheet | Content |
|---|---|
| ROI Scores | One row per topic, ordered by descending study priority. Includes per-paper audit columns and review notes. |
| Taxonomy | Alphabetical topic list, difficulty, connection score, first-seen paper, appearance count, and prerequisites. Includes canonical seed topics when present. |
| Exam Log | One row per candidate paper, with ID, year, short label, total marks, topic count, source filename, processing date, and analysis contract. |

Each sheet begins with an `UNREVIEWED PROTOTYPE` banner and the generation ID. The ROI sheet freezes headers and the first three columns. Green highlights identify Tier 1 topics, and priority cells use a color scale. Workbook cells are exported values. Editing a cell does not update the JSON or saved analysis.

The ROI columns are:

| Column | Meaning |
|---|---|
| Rank, Tier, Topic | Rank, optional Tier 1 label, and canonical topic name. |
| Freq | Number of papers containing the topic divided by the number of candidate papers. |
| G_Marks | Mean share of available marks, calculated only across papers containing the topic. |
| Conn | Connection score on the existing 1 to 3 scale. |
| Diff | Qualitative difficulty on the existing 1 to 6 scale. |
| Fmt | Mean response-format score across papers containing the topic. |
| Priority | `100 * Freq * G_Marks * Conn / (Diff * Fmt)`. Uses unrounded inputs before the exported rounding. |
| Paper label: presence, marks%, Fmt | Three columns per paper: presence as 0 or 1, share of that paper's marks, and response-format score. |
| Diff contract, Prerequisites, Review notes | Evaluation version, prerequisite names, and provisional or conflicting-evidence notes. |

## Agent JSON

The file is UTF-8 JSON containing an array of topic objects in the same order as ROI Scores. There is no outer wrapper. Existing ranking fields retain their names.

| Fields | Representation |
|---|---|
| `topic`, `rank`, `tier`, `priority` | Topic name, integer rank, tier label or empty string, and numerical priority. |
| `Freq`, `G_Marks`, `Conn`, `Diff`, `Fmt`, `appearances` | The same metrics shown in Excel, plus the number of papers containing this topic. |
| `per_exam` | Object keyed by paper ID. Entries contain `year`, `label`, `present`, `mark_fraction`, `marks_total`, `fmt_score`, and `evaluation_contract_version`. |
| `prerequisites` | Comma-separated display text, matching the workbook. |
| `evaluation_contract_version`, `difficulty_contract_version` | Versions that define the scoring meanings. |
| `model_estimate`, `human_overrides`, `connection_evidence`, `contributing_exam_ids`, `review_notes` | Supporting estimates, applied overrides, citations, paper IDs, and review notes. |
| `report_status` | Always `unreviewed-prototype`. |
| `generation_id` | A 32-character identifier shared by every row and all workbook banners. |

This is a study-priority summary for an agent. Full question text, topic assignments, and extraction/model provenance remain in `candidates/PAPER_ID.json`. The ranked JSON does not contain the full exam questions.

## Interpretation limits

Each question receives one or two topics. Its marks are split equally between those topics, so a 30-mark scenario with two topics contributes 15 marks to each. This is an estimate, not an allocation from a marking scheme.

The format score is 1 for multiple choice, 2 for short answers or analytical explanations, and 3 for code or proof tasks. Analytical LAW essays use `explain_derive`, the existing explanation category. The pipeline does not assess student answers or predict a grade.

With one paper, every reported topic has frequency 1. More comparable papers make frequency useful. Taxonomy and difficulty remain provisional. A correct 100-mark sum does not prove that all 11 questions were extracted correctly; the owner must compare them with the paper.

Prototype reports use candidates only. Accepted records and accepted reports remain separate. Existing canonical topic names and overrides seed the temporary taxonomy; later candidates supply the prototype evidence. A forced reanalysis replaces that candidate's previous contribution. Spreadsheet edits are not imported, and `edit-topic` applies only to topics already in the canonical taxonomy.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `pipeline/exam_roi/prototype.py` | Defines report selection, status, generation IDs, and destinations. | Candidate scope or export metadata changes. |
| `pipeline/exam_roi/reports.py` | Defines sheets, columns, formatting, and JSON serialization. | Export presentation or schema changes. |
| `pipeline/exam_roi/scoring.py` | Defines ranking arithmetic and output fields. | Metrics, types, ordering, or tiers change. |
| `docs/specs/law-prototype.md` | Implements the approved export agreement. | Prototype scope or acceptance criteria change. |
<!-- doc-dependencies:end -->
