# Computer Science Exams Pipeline — Project Brief

*Ground truth document. Read this before designing any solution for this project.*

*Last updated 2026-08-08, for `TUTOR_SYSTEM_PROMPT_v9`.*

---

## What This Project Is

A personal study system for university Computer Science exams. It has two layers:

1. **CLI Pipeline** — runs before studying begins. Tells you *what* to study and in what order.
2. **Cowork Tutor** — runs during active study. Teaches you the prioritized topics using evidence-based learning methods.

Computer Vision (RWTH Aachen), exam `final_26_08_2026`, is the current active Exam. **The architecture is course-agnostic**: a new course requires creating a folder and running the pipeline — no prompt rewriting. See `CONTEXT.md` for the Course / Exam / Topic / Lesson vocabulary and `docs/adr/` for the decisions behind the structure.

### The design goal, stated plainly

**The student types one command and studies. Nothing else.** They should never have to decide what to work on, where they left off, or what comes next. Planning is the system's job; learning is the student's. Every design decision below is subordinate to that, with one exception: **accuracy is never traded for comfort** — verdicts are literal, feedback is specific, and nothing is sugarcoated.

---

## Layer 1 — CLI Pipeline

### What you feed it
- Past exam files (text or PDF), one per year
- Total marks per exam

### What it produces
Inside `Courses/<Course>/<Exam>/`:
- `Exam_ROI_Pipeline.xlsx` — a ranked table of every exam topic, sorted by Study Priority Score (ROI). This is the study agenda.
- `taxonomy.json` — per-topic difficulty (D), connection value (C), and prerequisites. Used by the tutor for sequencing and for identifying confusable topic pairs.
- `parsed/*.json` — every past exam question, tagged by topic, with marks and `format`. Used by the tutor as the gold-standard target for final-rung questions **and** as the evidence for which discipline adapter a topic needs.

### What value it provides
The pipeline answers: *given limited time, which topics give the most exam marks per hour of study?* It scores each topic on four factors — how often it appears, how many marks it's worth, how foundational it is (unlocking other topics), and how deeply it's tested (MCQ vs. writing code). The result is a ranked priority list that front-loads high-yield topics and explicitly surfaces foundational concepts that unlock exam value downstream. It removes the guesswork from deciding where to start.

### What it does NOT do
It does not teach. It does not evaluate your understanding. It only produces the inputs the tutor needs.

### Active-Exam resolution
Commands auto-detect the Exam when exactly one exists anywhere under `Courses/`, and require explicit `--course` / `--exam` the moment a second one does — ambiguity is never silently guessed. See `docs/adr/0003-active-exam-resolution.md`.

---

## Layer 2 — Cowork Tutor

### How to start a session
Run **`/continue-study-session`** in Cowork. The skill loads the latest `TUTOR_SYSTEM_PROMPT_v*.md` (highest version wins, `_archive/` ignored), reads the active Exam's state files, and resumes exactly where the last session ended. Invoke it explicitly; it is not meant to auto-trigger from conversation.

**From v9, a session opens in three lines and goes straight into a question:**

```
📊 Computer Vision · final_26_08_2026 — 138/175 marks secured (79%) · 18 days to exam
Today: 3 overdue review items, then open Support Vector Machines. ~35 min.

[Spaced review] …
```

Path resolution, ledger reads, ROI ranking and topic selection all happen **silently**. The tutor announces a decision; it never stages a deliberation in front of the student. Exactly two questions may be asked before teaching starts: which Exam (only when several exist) and the exam date (only when unset).

### What you feed it
Per Exam, under `Courses/<Course>/<Exam>/`:
- `progress.json` — the mastery ledger: rung state, attempts with confidence, coverage, review queue, and the `next_session` plan
- `Exam_ROI_Pipeline.xlsx` — topic priority order
- `taxonomy.json` — difficulty, prerequisites, connections
- `parsed/*.json` — real past-exam questions as exemplars
- `PROJECT_NOTES.md` — per-Exam quirks that override defaults

Global and optional:
- `loci/` — memory palace files. **An optional add-on. The system is complete without it.**

### What it does

The tutor enforces three learning principles as hard rules:

**1. Cognitive Load Theory — intelligent sequencing**
Topics unlock only when prerequisites are mastered. Within each topic, difficulty increases one rung at a time (ramp length = D + 1): recognition → guided application → partial exam → full exam question. No rung is shown before the previous one is passed.

**2. Desirable Difficulty / Retrieval Practice**
The student always attempts first — the tutor never explains before asking, and never reveals an answer no matter how much the student stalls. Free recall is forced from rung 2 onwards. Spaced review pulls mastered topics back at full exam difficulty.

**3. Mastery Gating**
Every answer is graded in **marks against an explicit rubric**, then converted to PASS/FAIL: **≥85% and no fatal conceptual error** for rungs, **≥90%** for the final rung. A fatal error (wrong invariant, inverted inequality, wrong complexity class, broken proof step) fails the answer *at any score* — the no-fatal-error clause, not the percentage, is what protects rigour. Two consecutive FAILs drop a rung. A topic is `mastered` only when the final rung passes cold and unaided.

### The four mechanisms that make it work in practice

**First contact — teaching a topic the student has no schema for.**
A new topic opens `[Problematic]` → relevance hook → `[Probe]` → `[Worked example]` → `[Rung 1]`. The problematic states the *problem* the topic solves, bounded so it never leaks the mechanism. The probe is one cold question that is **ungraded and ungated** ("I don't know" is a complete answer) — attempting retrieval before instruction improves later retention even when the attempt fails. The worked example is a canonical instance with one step blanked. Only then does the retrieval-first gate switch on, and it is absolute from that point.

**Discipline adapters — one system, many exam shapes.**
A proof course's exam question is a proof; an OS course's is a trace; a databases course's is a query. The tutor picks an adapter **per topic** from the `format` field on that topic's exemplars — code-writing, proof/formal, algorithmic/complexity, systems/conceptual, or quantitative — which fixes the intermediate rung type, the final-rung format, and what counts as a *fatal* error in that discipline. Exemplars always win over assumptions about the subject.

**Confidence and hypercorrection.**
Before every verdict the student states one word: `low` / `ok` / `high`. A **high-confidence wrong answer is the highest-value moment in the system** — it is corrected explicitly and then re-tested within the same session, because such errors are corrected best and do not return when a test follows the feedback. A low-confidence right answer is not treated as mastery. Periodically the tutor reports calibration honestly: *"you said `high` six times and got three right."*

**The Lesson — a bounded unit.**
A Lesson is due review + one topic advanced 1–3 rungs + any mastery event, with its size stated up front and an explicit end ("that's the lesson — another, or stop here?"). Unbounded tasks are harder to start than bounded ones. The **next** Lesson is chosen from how this one went and written into the ledger's `next_session` block at session close — which is what lets the following session open in three lines.

### Motivation model

**Used:** competence made visible (the coverage banner, marks secured, mastery events, days remaining), and an implementation intention at session close — *"when and where is the next one?"* — which is the best-evidenced intervention for the specific failure of never getting started.

**Deliberately never used:** streaks, points, XP, badges, or any reward for showing up. Completion-contingent rewards measurably undermine intrinsic motivation, and over a months-long exam horizon that trade is bad. Also banned: commentary on the student's effort, discipline or character. The tutor's wit targets the work — the mistake, the reasoning, the missed step — never the person, because self-directed feedback is the documented way feedback stops working.

### Session flow
1. Resolve the Exam, read state, **execute `next_session`** — all silent. Print banner + one "Today" line.
2. Due spaced review (0–2 items, full exam difficulty).
3. New topic → first contact. Continuing topic → resume at `current_rung`.
4. Run the ramp: labelled question → attempt → confidence → marks + rubric + verdict → gate. Apply the difficulty controller.
5. Final rung cold and unaided; boss-check only after a failed first attempt.
6. On mastery: concept map (text) → discrimination set if a confusable neighbour is mastered → update coverage → unlock next.
7. End the Lesson explicitly and offer another.
8. On stop: write the ledger, **write `next_session`**, ask for the implementation intention.

---

## Current State

| Component | Status |
|-----------|--------|
| CLI pipeline | **Working.** Produces ROI spreadsheet, taxonomy, parsed questions. Multi-course aware. |
| Course/Exam hierarchy | **Done.** `Courses/<Course>/<Exam>/` is the atomic state boundary (ADR 0001), with auto-detect/explicit resolution (ADR 0003). |
| Tutor system prompt | **Working and course-agnostic** (`TUTOR_SYSTEM_PROMPT_v9`). Mastery gating, ramp, first contact, discipline adapters, spaced review, confidence routing, bounded Lessons. |
| Zero-decision session start | **Done in v9.** `next_session` written at session close, executed at session open. |
| Generalization | **Done.** A new course needs a folder and a pipeline run — no prompt edits. See `docs/solid/new-course-setup.md`. |
| Loci integration | **Decoupled by design.** Optional add-on, off by default, never gates mastery. Files exist (`loci_living_room.md`, `loci_encodings.md`) and the Living Room palace is near full. |
| Learning-science review | **Done.** Nine weaknesses identified and fixed in v9; rationale recorded in `docs/open/critique-tutor-learning-science.md`. |

---

## Resolved design problems

*Original numbering preserved — `docs/adr/0002` references these numbers.*

**1. Loci encoding ownership and evaluation** — **Resolved in principle.** The student encodes first; the tutor evaluates on two axes (*information accuracy*: does the image structurally reflect the concept's defining properties; *retrieval power*: anchored to the station object, physical, emotionally charged, vivid, specific) and only supplies a fallback image when the student is genuinely stuck. Implemented in the v9 add-on section. *Remaining:* the axes are stated as criteria, not as a numeric rubric — see `docs/open/loci-method-analysis.md`. Low priority now that the layer is optional.

**2. `loci_encodings.md` schema** — **Resolved.** The file exists and records station, concept, image, status (❌/⚠️/✅), accuracy note, retrieval-power note, owning Course/Exam, and date.

**3. Palace scaling architecture** — **Resolved: one file per palace.** A new physical room gets its own `loci_<room>.md`, indexed rather than merged into a master file — a palace *is* a room, so the file shape matches the domain. See ADR 0002.

**4. Tutor prompt generalization** — **Resolved.** v8 replaced hardcoded course details with the Course/Exam folder contract; v9 added per-topic discipline adapters so the prompt fits proof, systems, algorithmic and code-writing courses, not just vision-shaped ones.

**5. Station reuse across courses** — **Resolved.** Loci stays one shared resource across all Courses and Exams; each encoding is tagged with its owning Course/Exam so a station becomes identifiable as repurposable once that Exam is done. The concrete retirement workflow is deliberately left undesigned until a second course exists to design it against. See ADR 0002.

---

## Open problems

Genuinely open, in priority order:

1. **Second-course validation.** Everything is course-agnostic *by construction* but has only ever run against one Exam. The first real second course is the test of the folder contract, the adapters, and station contention.
2. **v9 field validation.** First contact, the 85%-plus-no-fatal-error bar, confidence routing and the `next_session` handoff are all argued from the literature but unobserved in this system. Watch for: probes that leak into rung 1, the calibration line landing as nagging, and `next_session` going stale when a session ends abruptly.
3. **Loci retirement workflow** — undesigned on purpose (see #5 above); needs a finished course to design against.
4. **Concept-map and connection tooling** — see `docs/open/critique-mindmap-graph-connections.md` and `docs/open/solution-research-*.md`. The discrimination-set mechanism in v9 covers part of what these were reaching for; the rest is unresolved.
5. **The `.skill` bundle** is a zip whose internal `SKILL.md` may name a prompt version; it needs unpacking to verify against v9.

---

## Where to read next

| You want | Read |
|---|---|
| Vocabulary and domain model | `CONTEXT.md` |
| Repo layout and conventions | `README.md` |
| Why the structure is this way | `docs/adr/` |
| How to add a course | `docs/solid/new-course-setup.md` |
| Why the tutor's rules are what they are | `docs/open/critique-tutor-learning-science.md` |
| The tutor itself | `tutor/TUTOR_SYSTEM_PROMPT_v9.md` |
