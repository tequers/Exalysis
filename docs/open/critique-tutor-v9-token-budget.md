# Critique — tutor v9 context budget and the "consistent instructions" question

**Date:** 2026-08-13
**Scope:** `tutor/TUTOR_SYSTEM_PROMPT_v9.md`, `tutor/SKILL.md` (continue-study-session), `tutor/STUDY_RUN_SKILL_v3.md`, synced skill descriptions, per-Exam state files.
**Measured against:** `Courses/Introduction_to_quantum_computers` (the exam with the fullest state).

Token figures are `bytes / 4`, which is within a few percent for English markdown and JSON.

---

## 1. The question that started this

Two questions were asked:

1. What should go into Cowork's *consistent instructions* (the project custom-instructions field) for learning sessions?
2. Is the tutor system prompt too long?

They turn out to be the same question, because `TUTOR_SYSTEM_PROMPT_v9.md` line 3 says:

> *Paste into a Cowork project's custom instructions, or send as the first message each session.*

That instruction is **wrong now and should be removed from the file.** At v1 (5,988 bytes) it was reasonable advice. At v9 it would put **13,969 tokens into every message of every chat in the project** — including chats about `pipeline.py`, chats about the ROI spreadsheet, and chats that have nothing to do with studying. It would also bust the project's prompt cache on every edit to the prompt, which at this rate of iteration is weekly.

The custom-instructions field should hold a **router**, not a method. The method belongs where it already is: a file that `/continue-study-session` loads on demand.

---

## 2. Measured: what a study session actually costs

Cold start of `/continue-study-session` on the quantum exam, before the first question is asked:

| Loaded | Tokens | When |
|---|---:|---|
| Synced skill descriptions (17 skills) | **2,935** | every message, every session, always |
| `tutor/SKILL.md` (continue-study-session) | 2,929 | on invocation |
| `TUTOR_SYSTEM_PROMPT_v9.md` | **13,969** | on invocation, read in full |
| `tutor/progress.json` | 5,651 | on invocation |
| `tutor/sessions.json` | 2,102 | on invocation |
| `final_20_08_2026/taxonomy.json` | 1,482 | on invocation |
| `glossaries/quantum_computing_glossary.md` | 3,284 | on invocation |
| `.study-run.json` | 203 | on invocation |
| **Subtotal before the first question** | **~32,555** | |
| `parsed/Practice_E-test_1.json` (if pulled whole) | +9,075 | lazily, per topic |
| `STUDY_RUN_SKILL` if planning in the same chat | +4,633 | on `/study-run` |
| **Realistic worst case** | **~46,000** | |

### Verdict on cost

**Token *cost* is not the problem.** 14k tokens read once per session, then served from a cached prefix at ~10%, is cheap relative to a 90-minute session of questions, answers and grading. Anyone optimising this to save money is optimising the wrong variable.

**Context *occupancy* is the problem.** ~32k tokens are resident for the entire session and never released. As the conversation grows past 60–80 turns, the tutor prompt's 50 sections compete for attention with 30k+ tokens of live dialogue. This is the mechanism behind "the tutor goes soft late in a session": not forgetting, but dilution.

---

## 3. The growth curve

| Version | Bytes | Δ |
|---|---:|---:|
| `TUTOR_SYSTEM_PROMPT.md` | 5,988 | — |
| v2 | 12,361 | +106% |
| v3 | 14,548 | +18% |
| v4 | 18,865 | +30% |
| v5 | 23,208 | +23% |
| v6 | 28,317 | +22% |
| v7 | 33,399 | +18% |
| v8 | 43,069 | +29% |
| **v9** | **58,654** | **+36%** |

**9.8× in nine versions, and every single step is positive.** Nothing has ever been removed. Each critique cycle adds a section; none evicts one. Left alone, v12 is ~110KB.

This is the finding that matters more than any individual number. The prompt has no eviction mechanism, so the question is not "is v9 too long" but "what stops v14 from being 200KB."

---

## 4. Section-by-section: what must be resident, what must not

Full outline of v9, classified by whether it changes behaviour on *every* turn.

### Tier 1 — core contract (must be resident, ~5,100 tok)

| Section | Tok |
|---|---:|
| Header: persona, prime directive | ~350 (after trimming, see §5) |
| Vocabulary | 264 |
| Hard rule 1 — Cognitive load | 281 |
| Hard rule 2 — Retrieval practice | 398 |
| Hard rule 3 — Mastery gating | 899 |
| Question labeling | 603 |
| The Lesson | 285 |
| Difficulty controller | 412 |
| Session protocol — opening / running / closing | 920 |
| Write ownership | 169 |
| Tone | 503 |
| **Total** | **~5,084** |

### Tier 2 — situational reference (load on trigger, ~8,900 tok)

| Section | Tok | Trigger |
|---|---:|---|
| Expected folder structure | 551 | only when `.study-run.json` is absent |
| Active-Exam resolution | 242 | only when `.study-run.json` is absent |
| Path resolution | 203 | only when `.study-run.json` is absent |
| File schemas (progress / next_session / parsed / taxonomy / ROI) | 765 | at session close, when writing state |
| Graceful degradation | 287 | only when a file is missing |
| First contact + guardrails | 694 | only when opening a *new* topic |
| Discipline adapters (all disciplines) | 858 | load only the one adapter in play (~200) |
| Confidence + hypercorrection loop | 464 | only after a high-confidence error |
| Narrative framing | 458 | situational |
| Problem-first framing (the problematic) | 718 | **delete — see §4.1** |
| Teaching delivery | 299 | arguably tier 1 |
| Discrimination sets | 349 | only for confusable pairs |
| Visual artifacts | 341 | only at consolidation |
| Post-mastery concept map | 243 | only at mastery |
| Spaced retrieval | 268 | at review scheduling |
| Coverage tracking | 341 | at open/close |
| Motivation | 372 | situational |
| **Method of loci (5 subsections)** | **913** | **only when `loci/` exists** |

### 4.1 Three duplications worth deleting outright

**The problematic — 718 tokens, maintained in three places.** `TUTOR_SYSTEM_PROMPT_v9.md § Problem-first framing` and the synced `/problematic` skill have the same section headings in the same order: *the hard boundary (requirement never mechanism)* · *structure, 150–250 words, in this order* · *solution chains — start at the right failure* · *grounding*. `tutor/PROBLEMATIC_SKILL_v1.md` (7,251 B) is a third copy. **Keep the skill, cut the prompt section to two lines** ("open every new topic with a `[Problematic]`; the `/problematic` skill defines the form"). Saves 718 tok/session and removes a two-way drift risk.

**The loci add-on — 913 tokens for a feature the prompt itself calls "OPTIONAL ADD-ON (off by default)".** `.study-run.json` for the quantum exam already records `"mnemonic": false` and `"paths.mnemonic": null`. So 913 tokens describing palace activation, encoding flow and bookkeeping are loaded into a session that has resolved, in writing, that there is no palace. **Move to `tutor/reference/loci.md`, gated on `capabilities.mnemonic`.**

**Resolution prose vs. the resolver — ~1,000 tokens.** `.study-run.json` already contains resolved paths and capability flags, and `tutor/SKILL.md` Step 1 says to trust it and stop searching. When it is present, *Expected folder structure* + *Active-Exam resolution* + *Path resolution* (996 tok) are describing work that has already been done and cached. **Move to `tutor/reference/bootstrap.md`, read only when `.study-run.json` is missing.**

### 4.2 The session-protocol overlap

`TUTOR_SYSTEM_PROMPT_v9 § Session protocol` (920 tok) and `tutor/SKILL.md` Steps 5–7 (opening turn, atomic rhythm, persist state) govern the same three moments. The skill already carries a *Division of authority* clause to adjudicate — that clause exists because the overlap is real, not because it was designed. Symptomatic, not fatal: worth collapsing when v10 is written, giving the shell to the skill and the teaching to the prompt, with no restatement in either direction.

---

## 5. Proposed changes

### 5.1 Project custom instructions — a router (~250 tok)

Paste into the project's custom-instructions field. Deliberately excludes the teaching method and anything that changes weekly, because edits here bust the prompt cache for every chat in the project.

```markdown
## Working in this project

Two kinds of work happen here: building the pipeline (pipeline/pipeline.py, taxonomy.json,
the ROI spreadsheet — see CONTEXT.md and README.md), and studying against the ranked topics.
Read the request, pick one, don't blend them.

### When the user is learning

- Sessions run through the skills, never ad hoc: `/study-run <duration>` plans,
  `/continue-study-session` teaches, `/study-run close` logs. If they ask to study
  without a slash command, name the command — don't improvise a session.
- Skills are explicit-invocation only. Never auto-trigger from conversational phrasing.
- `tutor/TUTOR_SYSTEM_PROMPT_v{highest}.md` is the governing authority on teaching.
  Your defaults do not outrank it. Load it via the skill — never inline it here.
- Retrieval before explanation — including outside a formal session. If they ask about
  a topic they're studying, ask what they remember first. Explaining something they
  could have retrieved is the exact failure this project exists to prevent.
- One thing per message. One question, then stop and wait.
- State files record only what happened. Never write a plan as history; never estimate
  a number you could read. Vocabulary is fixed by CONTEXT.md.
```

### 5.2 Split v9 into a core + `tutor/reference/`

Target for `TUTOR_SYSTEM_PROMPT_v10.md`: **~5,000 tokens** (20KB), containing exactly the Tier 1 table above. Everything in Tier 2 moves to `tutor/reference/<topic>.md`, each referenced from the core by one line stating its trigger:

```markdown
- Opening a new topic → read `tutor/reference/first-contact.md` first.
- High-confidence error → read `tutor/reference/hypercorrection.md`.
- Writing state at close → read `tutor/reference/schemas.md`.
```

**Expected: 13,969 → ~5,100 resident, a 64% reduction, with no capability removed** — every rule still exists, it just arrives when it applies. A typical session pulls 2–3 reference files (~1,200 tok), so realistic total is ~6,300 vs 13,969.

Two structural additions while rewriting:

- **Drive tier-2 loading off `.study-run.json` capability flags.** `mnemonic: false` → never read `loci.md`. `exemplars: true` → `question-shapes.md` is in play. The resolver already computes this; nothing else uses it.
- **Bracket the hard rules.** Put the three hard rules as a compact block at the *top* and repeat them verbatim at the *bottom* of the core file. Primacy and recency are the cheapest available defence against late-session drift, at ~80 tokens.

### 5.3 Trim the header

The v9 header is ~853 tok, of which the *design basis* citation paragraph and the nine-bullet *changes from v8* changelog are ~500. Neither changes behaviour. **Move both to `docs/adr/0004-tutor-v9-rationale.md`.** Provenance matters and should be kept — it just should not be resident during teaching.

### 5.4 Trim always-on skill descriptions

~2,935 tokens of skill descriptions ride in **every message of every session in this workspace**, studying or not. Five skills are explicit-invocation-only, where description text buys nothing because triggering is manual:

| Skill | Tok | Could be |
|---|---:|---:|
| `study-run` | 258 | ~25 |
| `concept-story` | 259 | 259 (auto-triggers — leave) |
| `continue-study-session` | 239 | ~25 |
| `problematic` | 180 | ~25 |
| `bizarre-analogy` | 153 | ~25 |

Cutting the four slash-only ones to a single line ("EXPLICIT-INVOCATION ONLY. Runs on `/x`.") saves **~780 tokens on every message you ever send**, which over a long session outweighs anything recoverable from the tutor prompt itself.

### 5.5 Add a size ceiling to the versioning ritual

The accretion curve is the root cause; every other fix here is treating a symptom. Add to whatever governs prompt revisions:

> `TUTOR_SYSTEM_PROMPT_v{N}.md` has a hard ceiling of 20KB. A change that would exceed it must
> evict or relocate something to `tutor/reference/` in the same commit. Reference files have no
> ceiling — the constraint is on what is resident during teaching, not on total documented method.

Without this, v10 lands at 5,000 tokens and v13 is back at 14,000.

---

## 6. Priority order

| # | Change | Saves | Effort |
|---|---|---:|---|
| 1 | Delete "paste into custom instructions" from the prompt header; add the §5.1 router | prevents 14k×every-message | minutes |
| 2 | Trim 4 slash-only skill descriptions | ~780 tok / message | minutes |
| 3 | Move loci (913) + problematic (718) + header changelog (500) out | ~2,130 tok / session | ~1 hour |
| 4 | Full Tier 1 / Tier 2 split into v10 | ~8,900 tok / session | half a day |
| 5 | Capability-flag-driven reference loading | correctness, not tokens | with #4 |
| 6 | 20KB ceiling in the revision ritual | prevents recurrence | minutes |

Items 1, 2 and 6 are worth doing today and cost almost nothing. Item 4 is the real work and should wait until after the 20/08 exam.
