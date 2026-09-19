# Exam ROI Pipeline

A CLI that reads a course's past exam papers and ranks its topics by exam ROI — relative study priority from observed exam value and qualitative judgments. This glossary covers the pipeline's own vocabulary only.

A companion project, [`exam-prep-prompt`](https://github.com/tequers/exam-prep-prompt), reads
this pipeline's output to drill recurring question patterns to fluency; it's a separate repo with
its own glossary (Archetype, Playbook, `exam_ready`, Trap) since it shares no code with the
pipeline.

## Language

**Course folder**:
The folder named first on every `pipeline.py` command (`python pipeline.py COURSE_FOLDER COMMAND …`), holding one Exam's past papers, `taxonomy.json`, `parsed/` and ranked output. It *is* the Exam as far as the CLI is concerned — created on first use, updated in place after that, and never merged with another folder. Any path on disk works; this repo keeps its own under `Courses/<Course>/<Exam>/`.

**Course**:
A university subject (e.g. "Computer Vision", "Operating Systems"). Purely an organizational grouping in `Courses/<Course>/` — it owns no taxonomy, priority, or progress state of its own.
_Avoid_: using "exam" to mean the course as a whole (older docs say "Exam: Computer Vision (RWTH Aachen)" — that's naming the Course, not an Exam).

**Exam**:
A specific examination within a Course, e.g. Computer Vision's one exam, or Operating Systems' Practical exam vs its Theory exam. The atomic, fully independent unit of study state: each Exam owns its own past-paper corpus, `taxonomy.json`, `parsed/` exemplars, and ROI spreadsheet. Nothing is shared or merged across Exams, even within the same Course — a topic tested in two Exams gets scored independently in each.
_Avoid_: conflating with Course; avoid "subject" or "module" for this term.

**Topic**:
A single examinable concept within an Exam's taxonomy (e.g. "Edge Detection"), scored on difficulty (Diff), connection value (Conn), and tagged with prerequisites. Lives in that Exam's `taxonomy.json` — not shared across Exams.

**Priority Score (ROI)**:
`100 × (Freq × G_Marks × Conn) / (Diff × Fmt)` — a relative ranking heuristic, computed per Exam from that Exam's own `Freq`/`G_Marks`/`Fmt` (from its past papers) and `Conn`/`Diff` (from its own taxonomy). The pipeline's final output.


**Evaluation contract**:
The versioned rules in [evaluation-v1.2.0.md](../pipeline/exam_roi/contracts/evaluation-v1.2.0.md).
Diff means conceptual and reasoning complexity under background assumptions inferred from exam evidence (1–6),
independent of marks, frequency, response format, or study duration. Each new analysis
records its contract version; old scores retain their original meaning, reported as
`legacy-unversioned` when no version exists. Conn measures supported direct downstream
usefulness (1–3); Fmt is a separate response-mode weight. Neither Priority nor Diff is
a calibrated prediction. Human overrides are preserved per field.

**Assumed prerequisites**:
Background knowledge inferred from the exam questions for each new topic, with source
quotes and reasons in `prerequisite_evidence`. No manual course prerequisite list is
used. These assumptions describe what the paper appears to expect, not verified
course entry requirements or the student's current knowledge.

**Paper judgment and taxonomy summary**:
Each candidate stores independent model observations in `topic_judgments` and
proposes a taxonomy summary without changing accepted state. On `rebuild`, the
taxonomy combines compatible evidence from accepted records in `parsed/`.
Dependency edges are counted once per distinct dependent topic, with citations
from supporting papers. Human overrides take precedence over `model_estimate`.
Reprocessing an older record creates a candidate; promotion into accepted state
remains pending in ticket 08. See the [current architecture](architecture.md).

**Prototype report**:
A study-priority report built from unreviewed candidate analyses. It uses their
observed topics and estimated scores without declaring the papers accepted.
Its rankings and topic mark shares remain estimates for the owner to inspect.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `docs/adr/0001-course-exam-hierarchy.md` | Defines Course and Exam around the accepted independent state boundary. | Course hierarchy or sharing between exam types changes. |
| `pipeline/exam_roi/contracts/evaluation-v1.2.0.md` | Defines evaluation, difficulty, connectivity, and evidence terms. | Contract meanings, scales, or provenance requirements change. |
| `pipeline/exam_roi/scoring.py` | Defines Priority using the implemented formula. | Ranking arithmetic or metric interpretation changes. |
| `pipeline/exam_roi/taxonomy.py` | Describes paper judgments, cumulative summaries, and human overrides. | Evidence aggregation or override semantics change. |
| `pipeline/exam_roi/prototype.py` | Defines the unreviewed report boundary. | Candidate selection or acceptance meaning changes. |
<!-- doc-dependencies:end -->
