# Exam ROI Pipeline

A CLI that reads a course's past exam papers and ranks its topics by exam ROI — how many marks
per hour of study each one is worth. This glossary covers the pipeline's own vocabulary only.

A companion project, [`exam-prep-prompt`](https://github.com/tequers/exam-prep-prompt), reads
this pipeline's output to drill recurring question patterns to fluency; it's a separate repo with
its own glossary (Archetype, Playbook, `exam_ready`, Trap) since it shares no code with the
pipeline.

## Language

**Course**:
A university subject (e.g. "Computer Vision", "Operating Systems"). Purely an organizational grouping in `Courses/<Course>/` — it owns no taxonomy, priority, or progress state of its own.
_Avoid_: using "exam" to mean the course as a whole (older docs say "Exam: Computer Vision (RWTH Aachen)" — that's naming the Course, not an Exam).

**Exam**:
A specific examination within a Course, e.g. Computer Vision's one exam, or Operating Systems' Practical exam vs its Theory exam. The atomic, fully independent unit of study state: each Exam owns its own past-paper corpus, `taxonomy.json`, `parsed/` exemplars, and ROI spreadsheet. Nothing is shared or merged across Exams, even within the same Course — a topic tested in two Exams gets scored independently in each.
_Avoid_: conflating with Course; avoid "subject" or "module" for this term.

**Topic**:
A single examinable concept within an Exam's taxonomy (e.g. "Edge Detection"), scored on difficulty (Diff), connection value (Conn), and tagged with prerequisites. Lives in that Exam's `taxonomy.json` — not shared across Exams.

**Priority Score (ROI)**:
`100 × (Freq × G_Marks × Conn) / (Diff × Fmt)` — the ranking that answers "which topic gives the most exam marks per hour of study," computed per Exam from that Exam's own `Freq`/`G_Marks`/`Fmt` (from its past papers) and `Conn`/`Diff` (from its own taxonomy). The pipeline's final output.
