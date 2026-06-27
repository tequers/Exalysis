# Loci System — File Analysis Brief
*For Claude Opus: solution design input*

---

## Context

This project uses the **Method of Loci** to study for Computer Science exams (Computer Vision, RWTH Aachen). Three files are now in play:

1. `loci_living_room.md` — a 27-station memory palace (the spatial layer)
2. `loci-method-analysis.md` — design analysis of how Claude should manage loci encoding
3. `TUTOR_SYSTEM_PROMPT.md` — the active tutor prompt; already contains a `Method of Loci integration` section

The goal is to integrate the loci method effectively into the tutor system prompt. The analysis below reflects the current state of all three files.

---

## What Already Works (in TUTOR_SYSTEM_PROMPT.md)

The tutor prompt has a loci section with several strong design decisions:

- **Trigger timing is solved**: encoding check fires after rung 1 pass or first explanation; consolidation fires after topic mastery. Loci never interrupts mid-ramp.
- **Spaced review protocol**: before each review question, Claude prompts *"Walk to station [X.Y — object name]. What do you see?"* — mnemonic retrieval before cognitive retrieval. This is the right compounding mechanism.
- **Status tracking**: `loci_encodings.md` uses ❌ / ⚠️ / ✅ per encoding — a lightweight state machine.
- **Quality guidance**: the prompt explicitly calls for *"bizarre, violent, sexual, funny, or emotionally extreme"* images. Correct, and more specific than the original design report.

---

## What Is Still Broken

| Gap | Description |
|-----|-------------|
| **User-first pedagogy inverted** | The prompt has Claude propose an encoding, then ask the user to confirm/refine. The original design intent was user proposes first, Claude evaluates. Claude-led encoding risks anchoring the user's memory to Claude's imagery instead of their own. |
| **No encoding evaluation** | The prompt says "confirm or refine" — it does not instruct Claude to evaluate accuracy or retrieval power. The two-axis rubric (Information accuracy / Retrieval power) from the design report is entirely absent. |
| **`loci_encodings.md` has no schema** | The file is referenced as if it exists, but its structure is never defined. No template for fields, no example entry. Claude will produce inconsistent formats across sessions. |
| **⚠️ has no resolution path** | The prompt marks weak encodings ⚠️ but gives no instruction for how to sharpen them. They will stay ⚠️ indefinitely. |
| **Station exhaustion unaddressed** | The living room palace has 27 stations. The CV exam has more concepts than 27. No rule exists for what happens when the palace is full. |
| **Retrieval power rubric missing** | No criteria for what makes an encoding strong vs. weak on vividness, emotionality, or bizarreness. Claude's feedback will be inconsistent without it. |

---

## Resolved Decision

**Encoding ownership: user-first.** The user proposes the encoding. Claude evaluates it on both axes and gives specific feedback. Claude only offers its own encoding as a fallback after the user genuinely cannot produce one. The current tutor prompt inverts this — it must be corrected.

---

## What Needs to Be Designed

1. **Decide the encoding ownership model** — user-first (propose, then Claude evaluates) vs. Claude-first (Claude proposes, user refines). Define the fallback: after how many failed user attempts does Claude step in?
2. **`loci_encodings.md` schema** — a concrete file template with fields: station ID, concept, encoding description, status (❌/⚠️/✅), information accuracy note, retrieval power note, last updated
3. **Retrieval power rubric** — concrete criteria Claude uses to score an encoding's mnemonic strength (e.g., involves physical action, emotionally charged, anchored to the specific station object, concept properties are structurally reflected)
4. **⚠️ sharpening protocol** — what specific questions or prompts does Claude use to move an encoding from ⚠️ to ✅?
5. **Palace scaling architecture** — when station 27 is reached, a new palace is added. The open decision is how to structure the encoding file system across multiple palaces:

   - **Option A — Single master file**: all palaces in one `loci_encodings.md`. Simple, fast to query. Scales poorly — grows unbounded and becomes expensive to pass in context across sessions.
   - **Option B — Tree/graph structure**: each palace is its own file; a master index links them with semantic metadata (which topic cluster lives where). Architecturally correct for long-term use. Adds complexity: Claude must navigate multiple files, and cross-palace concept relationships require graph traversal logic that is hard to make reliable in a prompt.

   **This must be decided before creating `loci_encodings.md`** — the schema is fundamentally different depending on the choice.

6. **Integration into session protocol** — exact placement of loci steps within the existing 5-step session flow in the tutor prompt, without bloating session length

---

## Generalization Requirement — Critical Priority

The Computer Vision exam is the **current use case and working example**, not the target scope. The goal is a general loci integration solution reusable across any university exam course with no per-course reconfiguration.

This is the highest-priority design constraint. Any solution that hardcodes CV-specific logic (topic names, file references like `Exam_ROI_Pipeline.xlsx`, parsed CV questions) is a prototype, not the deliverable.

### What "general" means in practice

- The tutor system prompt structure (mastery gating, ramp, spaced review) should be course-agnostic — course-specific files (`progress.json`, ROI sheet, taxonomy, parsed questions) are injected as parameters, not baked in
- The loci integration layer must work regardless of subject matter — the encoding evaluation criteria (information accuracy, retrieval power) apply equally to OS scheduling algorithms, linear algebra, or computer networks
- Palace management (station catalogue, encoding file, scaling architecture) must be reusable across courses without rebuilding from scratch — the user's living room palace should be available to any course, not owned by CV
- The encoding file schema must accommodate multi-course use: a station may hold a CV concept today and a different course's concept in a future exam cycle

### Key design questions for Opus

- How does the tutor prompt get parameterized so a new course requires only swapping course files, not rewriting the prompt?
- Should palaces be course-scoped (one palace per course) or concept-scoped (stations assigned by concept type, reused across courses)? The latter risks interference between courses sharing the same stations.
- How does the encoding file track which course a station's encoding belongs to, and handle station reuse when a prior course's encoding is no longer needed?
- What is the minimum viable spec for a new course onboarding — what files does a user need to prepare before the tutor can run?

---

## Goal

A course-agnostic tutor system where: any exam course can be loaded by providing a small set of structured files, the loci layer is shared infrastructure across courses, the user encodes concepts themselves with Claude evaluation, and all encodings are tracked in a scalable file structure. Computer Vision is the reference implementation; the next exam should require no architectural changes.
