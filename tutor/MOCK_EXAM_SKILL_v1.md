---
name: mock-exam
description: >-
  EXPLICIT-INVOCATION ONLY. Run only when the user types `/mock-exam` with a duration
  (e.g. `/mock-exam 60m`). Do NOT auto-trigger from "test me" or "give me a mock" — wait for
  the explicit slash command. Assembles a timed mock paper from real parsed exam questions
  and archetype variants, weighted toward the user's weakest archetypes, delivers it in one
  block under exam conditions, then grades the whole paper in one pass and reports a
  predicted score with a per-archetype breakdown. The dress rehearsal for exam-prep mode —
  run it once the queue is mostly drilled, not before. Course-agnostic.
---

> **Invocation:** explicit only — `/mock-exam 60m`, `/mock-exam 90m`, `/mock-exam full`.
> Never activate from "test me" alone.

# Mock Exam — the dress rehearsal

You build one timed paper, deliver it in a single message, shut up while it is taken, then grade the
whole thing at once and report a predicted score.

**This is not a drill session.** No playbooks, no hints, no per-question feedback, no coaching
mid-paper. The entire value is in the uninterrupted run: switching between question types under one
clock with nobody telling you whether the last one was right. `/start-session` is where you learn;
this is where you find out.

Governed by the highest-versioned `EXAM_PREP_PROMPT*.md` — same archetypes, same variant rules, same
write boundary.

---

## When to refuse

**If fewer than half the archetypes carrying marks are `exam_ready`, say so and offer a shorter
diagnostic instead** — one item per archetype, no timing, purely to rank what is weakest:

```
Only 3 of 14 archetypes are exam-ready — a full mock now measures how much you haven't drilled yet,
which you already know. Offering a 15-min diagnostic sweep instead: one item per archetype, ranked
output. Say "mock anyway" to override.
```

Accept the override immediately if given. It is the user's call, and there are legitimate reasons to
want the real thing early — but a mock run too soon returns a demoralising number that measures
schedule, not ability, and demoralising numbers in exam week are expensive.

`/mock-exam full` builds a full-length paper at the real exam's duration regardless of readiness.

---

## Step 1 — Resolve and load

Same resolution as `/start-session` — **choose the Exam first, then read that Course's own
`.study-run.json`**, then discovery by role. You need
`archetypes.json`, `parsed/*.json`, and the exam-prep method prompt. If `archetypes.json` is
missing, run the method prompt's mapping procedure silently first; this is not the moment to make
the user run another command.

Read `progress.json → exam_prep` for the coverage numbers. Read `topics[]` only to report `mastered`
alongside. Never write to either during the paper.

---

## Step 2 — Assemble the paper

**Marks first, questions second.** Target the real paper's mark distribution, not a fixed question
count:

```
target_marks = total_marks × (session_minutes / exam_minutes)
```

Then fill toward that target, drawing archetypes by weight:

| Archetype state | Weight | Why |
|---|---|---|
| `cold` (never drilled) | ×3 | Where the marks are actually being lost |
| has a live trap, `×2` or more | ×3 | The failure that keeps recurring under no pressure will recur under pressure |
| `drilled`, streak 1 | ×2 | Nearly there; the mock decides it |
| `exam_ready` | ×1 | Verification, and switching practice |
| `resolved` traps only | ×1 | Confirm the fix held |

**Every archetype carrying marks appears at least once** if the paper is long enough to hold it. A
mock that skips an archetype tells the user nothing about the one that might sink them.

**Prefer real exemplars the user has not seen.** Check `drills_seen`. When the unseen pool is empty,
use variants — and say so in the header, because "you have seen 4 of these 18 questions before" is
information the user needs to discount their own score by.

**Order the paper the way the real one is ordered** where the parsed files reveal an order — cheap
recognition items first, long derivations last, if that is what the papers do. Pacing is part of
what is being rehearsed, and a mock that front-loads the hardest question trains the wrong instinct.

---

## Step 3 — Deliver

**One message. The whole paper. Then silence.**

```
MOCK · 60 min · 18 questions · 108 marks
4 of these are real past-paper questions you have already seen — discount accordingly.
Start your timer. Answer everything in one reply; number your answers. No feedback until you're done.

1.  [1 mk] Is [1/√2, i/√2] a valid quantum state?
2.  [1 mk] Is [[0,1],[1,0]] a valid unitary?
…
17. [6 mk] For a balanced f, complete: Σ_x (−1)^f(x) = ? and P(measure 0ⁿ) = ?
18. [12 mk] …
```

Rules while the paper is out:

- **No hints. No clarifications on content.** A genuine ambiguity in the question wording gets a
  one-line clarification of the *wording* only. If the user asks whether their approach is right,
  the answer is "grade at the end" and nothing else.
- **No check-ins.** Do not ask how it's going. Do not send a halfway message.
- **If the user stops early**, grade what exists and mark the paper `partial` — do not extend the
  clock, and do not pretend the unanswered questions were unattempted for lack of time if they say
  otherwise.

---

## Step 4 — Grade in one pass

The whole paper at once. Per question: marks awarded out of marks available, and for anything not
full marks, **the playbook step that broke** and the trap name — one line each, no rubric recitals.

Then the report:

```
MOCK RESULT · 17 Aug · 60 min · finished in 54:00

Score       81 / 108 (75%)
By archetype
  ✓ validity checks         12/12   avg 38s (budget 45s)
  ✓ amplitude→probability   16/18   one modulus slip
  ✗ BV fill-the-boxes        8/24   phase-sign step broke in 3 of 4
  ✗ tensor 3-factor          9/20   order reversed on both
  ✓ measurement             36/34 … (etc.)

Pace        finished 6 min early · 3 questions ran >2× budget (all BV)
Predicted   ~75% on the real paper, ±8 — from 18 questions, so read it loosely
Costliest   BV fill-the-boxes: 16 marks lost, one recurring step. Highest-value hour available.

NEW TRAPS
  ×1  BV: forgot the (−1)^f(x) phase survives the second Hadamard   (17 Aug)
```

**State the confidence interval and the sample size.** An 18-question mock predicting a percentage
to the point is false precision, and the user will make scheduling decisions from this number.

**"Costliest" is the actionable line** — the single archetype where the most marks were lost per
minute of repair available. Name it, and name the specific step.

---

## Step 5 — Write

- **`archetypes.json`** — log every mock question against its archetype in `drills_seen`, append new
  traps with today's date, and update `best_time_s` where beaten. **Mock results do not set
  `exam_ready`**: exam-ready is a streak built under drill conditions, and one correct answer inside
  a paper is not two consecutive clean ones. A mock *may* break a streak, though — an archetype that
  was exam-ready and failed here drops to `drilled`, streak 0, with the trap logged. Passing is
  earned; failing counts.
- **`progress.json → exam_prep.sessions`** — one entry with `"type": "mock"`, the score, the
  duration, and the archetype breakdown. Recompute `exam_ready_marks` after any streak break.
- **Never** `topics[]`, `status`, `rung`, `marks_secured`, `coverage`, or any topic's `review_queue`.
  A mock score is not mastery, and this mode never claims it is.

Close on one line: `Run /start-session 60m to repair BV fill-the-boxes — 16 marks, one step.`

---

## Guardrails

- **Never reveal the paper's answers before it is submitted**, including by hinting at difficulty,
  correcting a numbering question with content, or reacting to an answer in progress.
- **Never inflate.** Grade to the exemplars' real standard. A generous mock is worse than no mock:
  it is a false readiness signal bought at the cost of an hour.
- **Never build a mock from invented archetypes.** Same rule as everywhere in this mode — every
  question traces to a real parsed stem, format, mark value and reasoning depth.
- **A predicted score is a prediction, not a promise.** Always with an interval, always with the
  sample size, never as a single confident number.
- **One mock per day, maximum.** Two in a day is time spent measuring rather than repairing, and the
  second one measures fatigue.

---

## What this skill is NOT

It is not `/start-session` — no playbooks, no sprints, no coaching. It is not `/session-end` — it
writes its own result and does not print the running debrief or the full trap list. And it is not a
mastery check: it measures whether the drilled patterns survive contact with a clock and a mixed
paper, which is the last thing worth knowing before the real one.
