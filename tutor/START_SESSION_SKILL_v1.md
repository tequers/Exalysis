---
name: start-session
description: >-
  EXPLICIT-INVOCATION ONLY. Run only when the user types `/start-session` with a duration
  (e.g. `/start-session 90m`). Do NOT auto-trigger from phrases like "let's study", "I have
  an hour", or "quiz me" — wait for the explicit slash command. One-shot exam-prep session:
  resolves the project, mines the parsed past papers into question archetypes if that hasn't
  been done, sizes a drill queue to the time available, and starts drilling in the same
  message. Governed by EXAM_PREP_PROMPT_v1.md — pattern recognition and timed execution, not
  deep understanding. Course-agnostic. This is the fast mode; `/continue-study-session` is
  the deep one, and they are never run together.
---

> **Invocation:** explicit only — `/start-session 90m`, `/start-session 45`, `/start-session 2h`.
> Never activate from conversation alone.

# Start Session — one-shot exam-prep drill session

You resolve, plan, and **teach**, in that order, in one message. The user types one command with a
duration and the next thing they see is a question.

**This is the exam-prep mode.** It optimises marks per hour by drilling recurring question
archetypes to fluency under time. It does not build deep understanding, and it is not supposed to.
The deep path is `/study-run` + `/continue-study-session`, and it is untouched by this skill.

---

## The rule that outranks the rest: zero decisions before drilling

The user has already made the only decision this skill needs — how long they have. Everything else
is derived from files. **Do not ask about mode, objective, topic, difficulty, or readiness.** Do not
render a plan and wait for approval. Do not open with a menu.

The one question you may ask, once ever per exam, is the exam's duration in minutes — and only
because per-question time budgets are arithmetic that needs it. Ask it inline, in one line, and
proceed in the same message with a 90-minute default if they don't answer.

Every question you ask before the first drill is a minute of an exam-week evening spent not
drilling.

---

## Step 1 — Resolve the project

**Pick the Exam first, then read that Course's cache. Never the other way round.**

A repo can hold several Courses, and a `.study-run.json` belonging to a *different* Course is
worse than no cache at all: it resolves cleanly, validates cleanly, and silently drills the wrong
subject. So:

1. **Find the candidate Exams** — every `Courses/<Course>/<Exam>/` folder holding `parsed/*.json`
   with real questions in it.
2. **Choose one** by the rule below (nearest future `exam_date`).
3. **Only now** look for `.study-run.json`, and only inside that Exam's own Course folder. If its
   `exam_prep` block points at paths under a different Course, discard it and discover by role.

**If that Course's `.study-run.json` exists and matches**, read it and stop searching — it is
shared with `/study-run` and already carries content-validated paths. Only re-resolve a path that
no longer exists. A missing cache is normal, not an error; some Courses deliberately have none.

**Otherwise discover by role**, ignoring `_archive`, `archive`, `.git`, `node_modules`,
`_to_delete`:

| Role | Search for | Recognized by |
|---|---|---|
| **exemplars** | `**/parsed/*.json` | real exam questions with `q_id`, `text`, `format`, `marks` |
| **archetypes** | `**/archetypes.json` | this mode's own map |
| **ledger** | `**/progress.json`, `**/mastery*.json` | JSON with a topic array carrying per-topic `status` |
| **method** | `**/EXAM_PREP_PROMPT*.md` | this mode's governing prompt — take the highest `_vN` |
| **priority** | `**/*ROI*.xlsx`, `**/*priorit*` | a topic column plus a rank or priority column |
| **taxonomy** | `**/taxonomy.json` | per-topic difficulty — read for names only |
| **glossary** | `**/*glossar*.md` | notation and answer-format conventions |

**Validate by content, not filename.** A design document about past papers is not a set of past
papers. Open each candidate and confirm it has the structure the role needs before accepting it.

**If several Exams resolve** (multiple `Courses/<Course>/<Exam>/` folders with parsed papers), pick
the one whose `exam_date` is nearest in the future and say which in one clause. Only ask if two
share a date. Deep mode asks; this mode picks, because the nearest exam is almost always the answer
and being wrong costs one word of correction.

Write the resolved paths back to `.study-run.json` **in the chosen Exam's own Course folder**,
under an `exam_prep` key. Create the file if it does not exist. Do not disturb the keys
`/study-run` owns, and never write exam-prep paths into another Course's cache.

---

## Step 2 — Hard requirement check

**No `parsed/*.json` with questions in it → this mode cannot run.** Say so in one line, name what
was missing, point at the alternative, and stop:

```
No parsed past papers found under this Exam — exam-prep mode has nothing to mine.
Run the pipeline's parse stage first, or use /continue-study-session for the deep ramp.
```

Do not improvise a queue from the syllabus, the lecture PDF, or the taxonomy. Archetypes that don't
come from real papers are guesses about the examiner, and drilling a guess to fluency is worse than
not drilling.

---

## Step 3 — Load the method prompt

Load the highest-versioned `EXAM_PREP_PROMPT*.md` **in full** and adopt it as your governing
instructions — its loop, its sprint rules, its feedback format, its write boundary, its tone.

Detect the version, never hardcode it:

```bash
ls "<project>"/**/EXAM_PREP_PROMPT*.md \
  | awk '{n=$0; v=0; if (match($0,/_v([0-9]+)\.md$/,m)) v=m[1]; print v"\t"n}' \
  | sort -n | tail -1 | cut -f2
```

**Never load `TUTOR_SYSTEM_PROMPT*.md` in this mode.** The two prompts contradict each other
deliberately — one gates retrieval absolutely, the other refuses to gate at all; one sends a single
question per turn, the other sends blocks. Loading both produces a tutor that stonewalls and rushes
in the same message.

Division of authority: **the method prompt owns the teaching** (playbooks, drills, sprints, grading,
exam-ready). **This skill owns the session shell** — resolution, mapping, the time budget, the
queue, and the handoff to `/session-end`.

---

## Step 4 — Map, if needed

Run the method prompt's Part 3 mapping procedure when **either**:

- `archetypes.json` does not exist, or
- any file in `parsed/` is newer than `archetypes.json`'s `mapped_at`.

Otherwise load the existing map and skip this entirely.

Mapping is **silent and unattended**. Do not narrate the clustering, do not show intermediate
groupings, do not ask the user to confirm the archetypes. Report the result as one line and keep
going:

```
Mapped 14 archetypes from 2 papers · 492 marks.
```

**Re-mapping preserves state.** When a map already exists and is being refreshed, carry every
archetype's `state`, `streak`, `best_time_s`, `drills_seen` and accumulated `traps` across by `id`.
A new paper appearing must never reset the user's drilled progress — and the accumulated traps are
the most expensive thing in the file to rebuild.

If `exam_minutes` is unknown, this is where the one permitted question goes.

---

## Step 5 — Size the session

```
usable  = T × 0.92 − 5 × floor(T / 60)
```

The 0.92 covers the opening and the wrap line; the second term reserves a short break per hour after
the first. Drill sessions are denser than ramp sessions, so the reserves are smaller than
`/study-run`'s — but they are not zero, and 180 minutes is still the hard ceiling. Refuse more,
propose two.

**Estimate each archetype's drill cost:**

```
drill_minutes = (cold_shot? 1 : 0) + 2 + (instances_needed × budget_s × k_drill / 60)
```

where `instances_needed` is 2 for a fresh archetype (the streak length), 4 if it has a live trap
logged against it, and 1 for a warm-up sweep item. The flat `+2` is the playbook. `k_drill` comes
from `progress.json → exam_prep.calibration`, defaulting to 1.0.

**Build the queue:**

1. **Warm-up sweep** — 3–5 drills from `exam_ready` archetypes, oldest-seen first, plus any
   high-confidence miss carried over. Skip on the very first session. Cap at 8% of usable time.
2. **The rest, by `marks_at_stake ÷ drill_minutes`, descending** — with the method prompt's
   dependency rule applied: if an archetype's `uses` names an undrilled move, its archetype is
   pulled in front.
3. **Cut at the budget.** Everything below the line is deferred, and the deferred list is named on
   one line so the user can see what Thursday will cost.

**Never plan more than the budget holds.** An over-full queue produces a session that ends in the
middle of an archetype with a streak of 1 — which banks nothing at all.

---

## Step 6 — Open and go

**One message.** Mapping line (if it ran), two lines of position, one line of plan, then the first
move.

```
Mapped 14 archetypes from 2 papers · 492 marks.
Exam-ready 0/492 · mastered 228/492 · exam in 3 days.
90 min → validity checks (4 archetypes, 28 marks), then amplitude→probability, then BV fill-the-boxes.
Deferred: tensor 3-factor, QFT matrix, Grover iteration.

[Cold shot · ungraded · ~30s] Is [1/√2, i/√2] a valid quantum state? "I don't know" is a fine answer.
```

Then run the method prompt's loop, one sprint per turn, until the user stops or runs `/session-end`.

**Both coverage numbers, always, and never merged.** `exam-ready` is what this mode has built;
`mastered` is what deep mode built. A single blended number would be the most misleading thing on
the screen.

---

## Step 7 — Persist as you go

Write `archetypes.json` **after every sprint**, not at session end: state, streak, best time, drills
seen, and any newly logged trap.

Exam-week sessions end unclean — the window closes, the context runs out, it's 1am. A skill that
persists only at the end loses the whole evening when that happens, and the accumulated traps are
not reconstructible.

**Do not write `progress.json` during the session.** `/session-end` writes the `exam_prep` roll-up
in one transaction. Nothing else in `progress.json` is ever written by this mode — not `status`, not
`rung`, not `marks_secured`, not `coverage`, not any topic's `review_queue`.

Hand off in one line and stop:

```
Run /session-end 75 to log this.
```

---

## What this skill is NOT

It is not `/continue-study-session` — that one loads v10, climbs rungs, and gates mastery. It is not
`/study-run` — that one plans and hands off rather than teaching. It does not write the debrief;
`/session-end` does. And it does not build understanding: it builds the reflex of seeing a question,
recognising its type, and executing a known flow inside the time the paper allows.
