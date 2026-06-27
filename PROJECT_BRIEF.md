# Computer Science Exams Pipeline — Project Brief

*Ground truth document. Read this before designing any solution for this project.*

---

## What This Project Is

A personal study system for university Computer Science exams. It has two layers:

1. **CLI Pipeline** — runs before studying begins. Tells you *what* to study and in what order.
2. **Cowork Tutor** — runs during active study. Teaches you the prioritized topics using evidence-based learning methods.

Computer Vision (RWTH Aachen) is the current active exam. The architecture must generalize to any future CS exam without structural changes.

---

## Layer 1 — CLI Pipeline

### What you feed it
- Past exam files (text or PDF), one per year
- Total marks per exam

### What it produces
- `Exam_ROI_Pipeline.xlsx` — a ranked table of every exam topic, sorted by Study Priority Score (ROI). This is the study agenda.
- `taxonomy.json` — per-topic difficulty (D), connection value (C), and prerequisites. Used by the tutor.
- `parsed/*.json` — every past exam question, tagged by topic, with marks and format. Used by the tutor as the gold-standard target for final-rung questions.

### What value it provides
The pipeline answers: *given limited time, which topics give the most exam marks per hour of study?* It scores each topic on four factors — how often it appears, how many marks it's worth, how foundational it is (unlocking other topics), and how deeply it's tested (MCQ vs. writing code). The result is a ranked priority list that front-loads high-yield topics and explicitly surfaces foundational concepts that unlock exam value downstream. It removes the guesswork from deciding where to start.

### What it does NOT do
It does not teach. It does not evaluate your understanding. It only produces the inputs the tutor needs.

---

## Layer 2 — Cowork Tutor

### How to start a session
Run **`/continue-study-session`** in Cowork. This skill re-onboards the tutor in one command: it loads the latest `TUTOR_SYSTEM_PROMPT_v*.md` (highest version wins), reads all the state files below, and continues the session exactly where it was left off — one atomic step per turn (one question/station at a time). Invoke it explicitly with the slash command; it is not meant to auto-trigger from conversation.

### What you feed it
- `progress.json` — mastery state (which topics are unlocked, on which rung, mastered, in review queue)
- `Exam_ROI_Pipeline.xlsx` — topic priority order
- `taxonomy.json` — difficulty, prerequisites
- `parsed/*.json` — real past-exam questions as exemplars
- `loci_living_room.md` — the memory palace station map
- `loci_encodings.md` — concept-to-station encodings with quality status *(schema TBD)*

### What it does

The tutor enforces three learning principles as hard rules:

**1. Cognitive Load Theory — intelligent sequencing**
Topics are unlocked only when prerequisites are mastered. Within each topic, difficulty increases one rung at a time (ramp length = D + 1): recognition → guided application → partial exam → full exam question. No rung is shown before the previous one is passed.

**2. Desirable Difficulty / Retrieval Practice**
The student always attempts first — the tutor never explains before asking. Questions are calibrated to be ~70–85% passable at the current rung. Free recall is forced from rung 2 onwards. Spaced review pulls mastered topics back at full exam difficulty before each new session.

**3. Mastery Gating**
Every answer is graded against an explicit rubric (PASS/FAIL + specific missed step). PASS advances the rung. Two consecutive FAILs drop a rung. A topic is only marked `mastered` when the final rung passes. The tutor tracks all of this in `progress.json` and writes it at session end.

**Method of Loci integration** *(partially implemented — under redesign)*
After each concept is first encountered, the student encodes it into a physical station in their memory palace. Before spaced review questions, the student retrieves the mnemonic image first, then answers the question. This compounds mnemonic and cognitive retrieval. Details of the encoding evaluation and file schema are the subject of active design work.

### Session flow
Started via `/continue-study-session`. One atomic step per turn — never stack a banner, a review walk, and an exam question in the same message.
1. Read `progress.json` → print coverage banner (marks secured / total) + two orientation lines
2. **Loci review first** — walk one station at a time until the review queue has no due items
3. **Exam review** — one full-difficulty question per turn on mastered/due topics, until due items clear or 3 questions max (skip if nothing is mastered yet)
4. **Progressive learning** — the current topic's ramp, one rung per turn: question → student attempts → PASS/FAIL + rubric → gate
5. On mastery: update coverage, unlock next topic
6. Write updated `progress.json` (and any loci changes) at session end

---

## Current State

| Component | Status |
|-----------|--------|
| CLI pipeline | Working. Produces ROI spreadsheet, taxonomy, parsed questions. |
| Tutor system prompt | Working for CV. Mastery gating, ramp, spaced review implemented. |
| Loci integration in tutor | Partially implemented. Trigger timing and spaced review protocol are correct. Encoding ownership, evaluation rubric, and file schema are unresolved. |
| `loci_encodings.md` | Does not exist yet. Schema must be designed before creation. |
| Generalization | Not yet done. Tutor prompt is CV-specific. Needs parameterization so any course can be loaded by swapping files. |

---

## Open Design Problems (for Opus)

These are the problems that need to be solved before the system is complete:

**1. Loci encoding ownership and evaluation**
The student proposes the encoding first. Claude evaluates it on two axes: *information accuracy* (does the image structurally reflect the concept?) and *retrieval power* (is it vivid, bizarre, emotionally charged enough to stick?). Claude only offers its own encoding as a fallback if the student is genuinely stuck. A concrete rubric for both axes is needed.

**2. `loci_encodings.md` schema**
A file structure that records: station ID, concept, encoding description, status (❌/⚠️/✅), evaluation notes, last updated. Must support the ⚠️ → ✅ sharpening flow.

**3. Palace scaling architecture**
The living room palace has 27 stations. More concepts than 27 will be taught across courses. When a palace fills, a new one is added. The unresolved question is whether to use:
- A **single master file** (simple, slow to scale, expensive in context)
- A **tree/graph structure** (one file per palace, linked by index — scalable but adds multi-file navigation complexity)

This decision must be made before the schema is defined, because the two approaches produce fundamentally different file structures.

**4. Tutor prompt generalization**
The current tutor prompt is hardcoded to Computer Vision. The goal is a course-agnostic prompt where a new exam requires only swapping the course files (`progress.json`, ROI sheet, taxonomy, parsed questions) — no prompt rewriting. The loci layer must be shared infrastructure across courses, not owned by a single course.

**5. Station reuse across courses**
A station used for a CV concept may need to hold a different course's concept in future exams. The encoding file and the tutor logic must handle this: tracking which course an encoding belongs to, and managing the transition when a station is repurposed.
