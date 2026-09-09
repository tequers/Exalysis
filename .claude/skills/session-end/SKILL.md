---
name: session-end
description: >-
  EXPLICIT-INVOCATION ONLY. Run only when the user types `/session-end`, optionally with the
  actual elapsed minutes (e.g. `/session-end 75`). Do NOT auto-trigger from "I'm done" or
  "that's it for today" — wait for the explicit slash command. Closes an exam-prep drill
  session: persists archetype state, rolls up exam-ready marks into progress.json's exam_prep
  block, recalibrates the drill-time estimate, and prints a short debrief ending in the
  user's accumulated trap list. Writes only exam-prep state — never mastery, rungs, or
  marks_secured, which belong to the deep-mode tutor. Course-agnostic.
---

> **Invocation:** explicit only — `/session-end`, or `/session-end 75` with actual minutes.
> Never activate from "I'm done" alone.

# Session End — persist, recalibrate, debrief

You are the write transaction and the readout for an exam-prep session. Everything the session
learned that isn't already on disk gets written here, and then the user gets six short lines and
their trap list.

**You do not teach, grade, or drill.** If the user answers a question in the same message as
`/session-end`, grade nothing — close the session and say the drill didn't count.

---

## The argument

`/session-end 75` — the number is **actual elapsed minutes**, and it is optional.

**If it is omitted, do not guess and do not ask twice.** Ask once, in the batched question of Step 2,
and if it still isn't given, mark the session `timing: "not_collected"` and **skip recalibration
entirely**. A `k_drill` nudged from an invented total launders a guess into the estimator, and every
later session inherits it. A `k` left alone is simply a `k` that hasn't learned yet.

---

## Step 1 — Read what happened

1. **`archetypes.json`** — the session's real record. `/start-session` persists after every sprint,
   so this is usually complete. Diff it against its state at session start where you can: which
   archetypes changed `state`, which streaks moved, which traps were appended with today's date.
2. **The conversation**, if the close runs in the same one as the session. This is the accurate
   source for drill counts, clean counts, and per-sprint elapsed times. Prefer it over asking.
3. **`progress.json → exam_prep`** — the existing roll-up, to extend rather than overwrite.

**If `archetypes.json` shows no activity dated today and the conversation has no drills**, say so in
one line and write nothing:

```
No drills recorded today — nothing to log. archetypes.json last changed 16 Aug.
```

Writing an empty session into the history makes the trend line lie.

---

## Step 2 — One batched question, or none at all

Ask **at most one message** containing **at most three things**, and only what you genuinely cannot
read:

- elapsed minutes, if not passed as the argument;
- whether the session was interrupted (it changes whether it counts toward calibration);
- for any archetype whose state moved without a matching drill record, whether it actually happened.

**State back what you already know rather than asking about it.** `12 archetypes drilled, 4 went
exam-ready` is a sentence, not a question.

**Never ask about correctness, marks, or how it felt.** The drill record already holds correctness,
and a self-reported "I think I got most of them" is exactly the kind of data this system must not
write. Never ask more than one message; a close that turns into an interrogation is a close the user
stops running, and an unrun close means the state is simply lost.

---

## Step 3 — Write the state

### `archetypes.json`

Flush anything the live session left unwritten: `state`, `streak`, `best_time_s`, `drills_seen`,
`traps[]` with dates and repeat counts. Idempotent — if it is already there, leave it alone. Never
re-append a trap that is already logged for today.

### `progress.json → exam_prep`

**This key and nothing else in the file.**

```json
"exam_prep": {
  "mode_version": "EXAM_PREP_PROMPT_v1",
  "exam_ready_marks": 156.0,
  "total_marks": 492.0,
  "sessions": [
    { "date": "2026-08-17", "minutes": 75, "timing": "collected", "interrupted": false,
      "drills": 42, "clean": 34, "archetypes_ready": ["validity-check-quantum-state",
      "validity-check-unitary", "amplitude-to-probability"], "pace_ratio": 0.83,
      "traps_logged": 3 }
  ],
  "calibration": { "k_drill": 0.97, "alpha": 0.3, "n_sessions": 1 }
}
```

- `exam_ready_marks` = **recomputed** as the sum of `marks_at_stake` over archetypes in state
  `exam_ready`. Never incremented blind, so a re-map or a lost streak corrects it downward honestly.
- `pace_ratio` = actual ÷ budgeted across timed sprints. Below 1.0 is under budget.
- Append to `sessions`; never rewrite a past entry.

### What you must never write

`topics[]`, `status`, `rung`, `marks_secured`, `coverage`, `attempts[]`, `next_session`,
`session_log`, or any topic's `review_queue`.

Those belong to `TUTOR_SYSTEM_PROMPT_v10.md` and to `/study-run close`. A drill streak is evidence
that the user can execute a pattern under time — it is **not** evidence of the unaided exam-format
derivation that `mastered` records, and writing it there would inflate a coverage number the user
makes real decisions from. **Unlike `/study-run close`, this skill never reconciles the deep ledger.
If deep-mode work happened today too, say in one line that `/study-run close` still needs running.**

---

## Step 4 — Recalibrate

Only when `timing: "collected"` and the session was not interrupted:

```
k_drill = (1 − 0.3) · k_drill + 0.3 · (actual_minutes / estimated_minutes)
```

Clamp to `[0.4, 3.0]`. One nudge per session. This corrects *planning* estimates only — never the
exam's own per-question budgets, which come from the paper's clock and are not negotiable.

Interrupted sessions are recorded and excluded: they measure the evening, not the estimate.

---

## Step 5 — The debrief

Six lines, then the traps. No score, no praise, no encouragement padding. The user reads this to
decide what to change tomorrow.

| Line | Reports | Source |
|---|---|---|
| **Drilled** | archetypes touched · drills · clean rate | archetypes diff |
| **Ready** | archetypes that reached exam-ready this session, and the marks they carry | state changes |
| **Coverage** | exam-ready marks and % · mastered marks and %, side by side | recomputed + ledger read |
| **Pace** | actual vs budgeted, and the `k_drill` that moved | timed sprints |
| **Stuck** | archetypes drilled but still not ready, and what is blocking each | streak < 2 |
| **Runway** | days to exam · marks still cold · whether the remaining queue fits the days left | arithmetic |

**Runway is the line that matters.** It is the only place the user finds out that the plan does not
fit before the exam finds out for them. Compute it plainly — remaining archetype drill-minutes
against remaining study days at the observed session length — and if it doesn't fit, say which
archetypes to cut, by lowest marks-per-minute. Do not soften it.

Then the trap list — the point of the whole exercise:

```
YOUR TRAPS — 8 live, sorted by repeat count
  ×3  complex modulus: |a+bi|² = a²+b², not (a+bi)²          (14, 16, 17 Aug)
  ×2  stochastic matrices: columns sum to 1, not rows        (16, 17 Aug)
  ×2  measurement questions: post-measurement state omitted   (14, 17 Aug)
  ×1  tensor order reversal on 3-factor products              (17 Aug)
```

Print **every** live trap, not a sample, sorted by repeat count then recency. This list is the
artifact the user reads on exam morning, and a trap seen three times is the single most valuable
line in the system. A trap goes quiet after two consecutive clean sessions on its archetype — mark
it `resolved` with the date rather than deleting it, so a re-emergence is visible as a re-emergence.

### Format

```
DEBRIEF · 17 Aug · 75 min
Drilled   9 archetypes · 42 drills · 34 clean (81%)
Ready     3 → exam-ready: validity/state, validity/unitary, amplitude→probability (+28 marks)
Coverage  exam-ready 156/492 (32%) · mastered 228/492 (46%)
Pace      0.83 of budget — consistently under (k_drill 1.00 → 0.97)
Stuck     BV fill-the-boxes, streak 1 — the phase-sign step breaks every second attempt
Runway    3 days · 336 marks cold · queue needs ~5.5h, you have ~9h. Fits.

YOUR TRAPS — 4 live, sorted by repeat count
  ×3  complex modulus: |a+bi|² = a²+b², not (a+bi)²          (14, 16, 17 Aug)
  ×2  stochastic matrices: columns sum to 1, not rows        (16, 17 Aug)
  …

Tomorrow opens on BV fill-the-boxes — it's the only thing standing between you and 24 marks.
```

When data is thin the lines shrink rather than get padded:

```
DEBRIEF · 17 Aug · 40 min
Drilled   2 archetypes · 9 drills · 7 clean
Ready     none yet — both at streak 1
Coverage  exam-ready 0/492 · mastered 228/492 (46%)
Pace      not collected — calibration skipped this session
Stuck     —
Runway    3 days · 492 marks cold · first session, estimates are still seeds

YOUR TRAPS — 1 live
  ×1  complex modulus: |a+bi|² = a²+b², not (a+bi)²          (17 Aug)
```

---

## Guardrails

- **Report behaviour, never character.** "34 of 42 clean" is a fact to act on. "You were sloppy
  tonight" is a label that makes the debrief something to avoid running.
- **Never manufacture a pattern.** One closing line, only if something real is there. Otherwise stop
  after the traps.
- **Never write a plan as history.** Only drills that happened get logged.
- **Never fabricate elapsed time.** Missing timing is recorded as missing.
- **Watch for clean rate rising while pace collapses** — that is the user slowing down to stay
  correct, which reads as improvement and isn't. Say it directly if it holds across three sessions.
- **Watch for the inverse too:** pace improving while clean rate falls is rushing, and it is the
  specific failure this mode is most prone to. Same rule — name it after three sessions.

---

## What this skill is NOT

It is not `/study-run close` — that one reconciles the deep mastery ledger, and this one must never
touch it. It does not teach, grade, or drill. And it does not judge the session: it records what
happened, prints the traps, and says whether the remaining plan fits the days left.
