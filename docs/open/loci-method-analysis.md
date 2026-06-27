# Loci Method Integration — Critical Analysis

## Original Report

> Current model, the AI is not adapted to correctly manage the loci method and structure. Claude advances to new concepts without making sure the user has encoded the newly learned concepts correctly.
>
> It would be helpful if Claude asks the user how is the encoding, and then evaluate it — "it's too vague because of the association relies on …" / "this encoding is incorrect because the oven doesn't really represent the concept of y" — indicating whether the analogies/metaphors really match or not the concepts behind, and whether they will stick in memory or they're too abstract or dull.
>
> Maybe evaluate the user encoding based on:
> - **Information accuracy** — how much does the metaphor align with the underlying concept
> - **Retrieval power** — how easy or hard is it to maintain and retrieve the knowledge long term (how emotional the encoding is, how vivid, bizarre, how well it sticks in the user memory)
>
> Keep a loci encoding file where Claude keeps track of the user encodings in the places. Lets Claude review the user encodings and it's also useful for the user to review and retrieve information if needed.
>
> Claude should not tell the user directly an encoding for a concept, the user should go and think first, then Claude reviews and indicates how to improve the encoding if needed, if the user can't truly think of anything then Claude gives a possible "bizarre" encoding.

---

## Critical Analysis

### 1. Strong Points

The core behavioral problem is identified precisely: *"Claude advances to new concepts without making sure the user has encoded the newly learned concepts correctly."* This is a real and specific failure mode, not a vague complaint. It gives a clear behavioral target to change.

The two-axis evaluation framework — **Information accuracy** and **Retrieval power** — is genuinely well-conceived. These dimensions are distinct, non-redundant, and map onto real cognitive science (semantic accuracy vs. mnemonic potency). Most learning tools conflate these or ignore the second entirely.

The pedagogical stance of *"the user should go and think first, then Claude reviews"* is the right instinct. It prevents learned helplessness and preserves the encoding effort that makes the method actually work. This isn't just a preference — it's load-bearing for the whole method's effectiveness.

---

### 2. Weak Points

**"Retrieval power" is undefined operationally.** The report lists proxies — *"how emotional the encoding is, how vivid, bizarre, how well it sticks"* — but gives Claude no rubric for actually scoring this. What distinguishes a 6/10 encoding from a 4/10? Without criteria, Claude's feedback will be inconsistent across sessions.

**The loci encoding file is underspecified.** It's described as a place where "Claude keeps track of user encodings in the places" but the structure is never stated. What fields does it have? Is it per-palace, per-concept, per-session? Does it store Claude's evaluation score alongside the encoding? Without a schema, this risks becoming a flat text dump that's hard to query or review.

**"If the user can't truly think of anything" is a fuzzy trigger.** How many attempts? After how long? Does Claude prompt a second try before offering one? The boundary between "user is stuck" and "user hasn't tried hard enough" is undefined, and Claude will likely err toward offering encodings too early, undermining the stated goal.

**The phrase "bizarre encoding"** appears only once, attributed to Claude's fallback output, but the retrieval power criteria already list "bizarre" as a positive quality. This creates an implicit tension: Claude should reward bizarreness in user encodings, but also produce bizarre ones on demand. The report doesn't address whether Claude-generated encodings risk anchoring the user's memory to Claude's imagery rather than their own.

---

### 3. Potential Pitfalls

**Evaluation subjectivity will produce inconsistent feedback.** Whether *"the oven doesn't really represent the concept of y"* is a bad encoding depends on the concept. Without grounding each judgment in the underlying concept's defining properties, Claude's accuracy assessments will vary arbitrarily between sessions and topics.

**The encoding file becomes stale quickly.** Memory palaces are personal and evolve — users revise encodings, forget old ones, repurpose locations. If the file doesn't have a mechanism for versioning or marking encodings as revised/abandoned, it will diverge from the user's actual mental model and become misleading rather than helpful.

**Interruption frequency is unaddressed.** If Claude checks encoding after every concept, the session becomes interrogative and slow. If it checks too rarely, the original problem (advancing without confirmation) persists. The report identifies the problem but doesn't propose a cadence, which is where the UX will actually break.

**No handling of multi-stage encoding.** Some concepts are too abstract for a single image. Users may encode a concept across two or three connected loci. The report assumes a 1:1 concept-to-encoding mapping, which won't hold for dense technical material.

---

### 4. Problem Framing Check

The stated problem — Claude not checking encoding correctness — is real, but it may be a symptom of a deeper issue: **the pipeline has no concept of encoding state at all.** The current pipeline likely treats loci as an output format rather than a cognitive process that needs to be validated and stored. The report correctly identifies the behavioral fix, but frames it as a feature addition ("Claude should ask") when it may require a structural change (encoding state as a first-class object in the session model). If the root problem is architectural, patching Claude's conversation behavior without the encoding file and evaluation rubric will produce superficial compliance — Claude asks the question, the user answers, and nothing is actually retained or evaluated consistently.

---

### Overall Verdict

This is a well-motivated analysis with a clear behavioral target and a genuinely useful evaluation framework in embryonic form. The two-axis model and the "user-first, Claude-fallback" pedagogy are solid foundations. However, the report is not yet ready to move to implementation — it has three specification gaps that would immediately cause ambiguity in practice: the retrieval power rubric lacks criteria, the encoding file lacks a schema, and the "user is stuck" trigger lacks a decision rule. These aren't minor details; they're the pieces Claude would need to behave consistently across sessions. The analysis correctly identifies the problem and points at the right solution space, but it needs one more pass to harden the specs before any implementation work begins.

---

## Update — TUTOR_SYSTEM_PROMPT.md Integration Review
*Added after reviewing the existing tutor system prompt*

The tutor prompt already contains a `## Method of Loci integration` section. This changes the picture significantly: several gaps identified above have been partially addressed, but new gaps have been introduced.

### What the prompt gets right

The trigger point is well-defined: loci encoding is checked *after rung 1 pass or first explanation*, and consolidation happens *after topic mastery*. This solves the cadence problem — it ties encoding to the mastery gate, so it never interrupts mid-ramp and never gets skipped.

The status system (❌ / ⚠️ / ✅) in `loci_encodings.md` gives the encoding file a lightweight state machine. This is a practical schema skeleton.

The spaced review protocol (*"Walk to station [X.Y]. What do you see?"*) is the strongest feature: it forces mnemonic retrieval before cognitive retrieval, which is exactly how the method should compound with retrieval practice.

The encoding quality guidance is explicit and correct: *"bizarre, violent, sexual, funny, or emotionally extreme"* — this is precisely what memory science supports and the original report only gestured at.

### What remains unresolved

**Claude proposes the encoding; the user confirms or refines.** This is the inverse of the original design intent — *"the user should go and think first."* The prompt has Claude leading with a proposed image, which risks anchoring the user's memory to Claude's imagery. The original report identified this risk explicitly; the prompt ignores it.

**"Confirm or refine" is not an evaluation.** The prompt says Claude should *propose* an encoding and ask the user to confirm or refine it. It does not say Claude should evaluate the user's encoding for information accuracy or retrieval power. The two-axis rubric from the original report is entirely absent.

**`loci_encodings.md` schema is still unspecified.** The status symbols exist but the file structure — what fields surround each entry, how concepts are linked to stations, whether scores are stored — is not defined anywhere. The prompt references the file as if it exists but provides no template.

**The ⚠️ status has no resolution path.** The prompt says *"keep ⚠️ until they confirm"* but gives no instruction for what Claude should do differently to move an encoding from ⚠️ to ✅. It will stay ⚠️ indefinitely without a sharpening protocol.

**No handling of station exhaustion.** The living room palace has 27 stations. The CV exam has far more concepts than 27. The prompt has no rule for what happens when the palace fills up — whether to chain palaces, reuse stations, or flag the capacity issue.

---

## Decisions & Open Architecture Questions
*Added after user review*

### Resolved

**Encoding ownership: user-first.** Confirmed. The user proposes the encoding first. Claude evaluates it on both axes and gives specific feedback. Claude only provides its own encoding as a fallback after the user genuinely cannot produce one.

### Open — Palace Scaling Architecture

When a palace fills up, a new one must be added. This raises a structural decision for the encoding file system:

**Option A — Single master file**
All palaces and all encodings in one file (`loci_encodings.md`). Simple to read, simple for Claude to scan. Drawback: grows unbounded with each new exam topic and each new palace. At scale (multiple subjects, 5+ palaces), the file becomes slow to navigate and expensive to pass in context.

**Option B — Tree or graph structure**
Each palace is its own file. A master index links them, possibly with semantic metadata (which topic cluster lives in which palace). Palaces can be connected by concept relationships, not just sequential order. More scalable. Drawback: Claude must navigate multiple files per session; cross-palace retrieval (e.g., a concept that relates to two topics in different palaces) requires graph traversal logic that is complex to implement reliably in a prompt.

**The core trade-off:** master file is fast to build and query but brittle at scale. Graph structure is architecturally correct but adds implementation complexity that could introduce failure modes in the prompt logic.

**This decision needs to be made before `loci_encodings.md` is created**, because the schema depends on it — a flat file and a node-based graph have fundamentally different entry structures.
