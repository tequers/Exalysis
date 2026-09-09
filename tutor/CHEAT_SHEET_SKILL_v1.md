---
name: cheat-sheet
description: >-
  EXPLICIT-INVOCATION ONLY. Run only when the user types `/cheat-sheet`. Do NOT auto-trigger
  from "make me a summary" or "what should I memorise" — wait for the explicit slash command.
  Builds the content for a permitted handwritten exam aid (typically one side of A4) out of
  the archetype playbooks and the user's own accumulated traps, ranked by marks at stake and
  cut to fit the stated size limit. Outputs text to copy out by hand, never a printable
  artifact. Refuses to include anything the exam's stated conditions forbid. Course-agnostic.
---

> **Invocation:** explicit only — `/cheat-sheet`, or `/cheat-sheet a5` / `/cheat-sheet "2 sides"`
> to override the size. Never activate from "summarise this" alone.

# Cheat Sheet — the permitted aid, earned rather than copied

You turn everything the drill sessions learned into the content of a handwritten exam aid: the
playbooks that produce marks, and the traps the user has personally and repeatedly fallen into.

**The value is that it is earned.** A cheat sheet copied from lecture notes is a page of things
that looked important. This one is a page of things that actually cost the user marks, measured
across real drills. That difference is the whole reason this skill exists.

---

## Step 0 — Check the rules before writing a word

Read `exam_format` in `archetypes.json` (or the project's notes file if that is where the
conditions live).

**If the conditions are recorded and permit an aid**, obey their exact limit — one side, two
sides, A4, A5, handwritten, printed, formula sheet already provided.

**If the conditions are recorded and forbid an aid**, say so and stop:

```
The recorded exam conditions forbid notes of any kind. Not building a sheet.
The same content is available as a revision list — say "revision list" if you want it.
```

**If the conditions are not recorded at all**, do not guess. Ask once what is permitted, build
to that answer, and write it into `exam_format` so the next run knows.

**Never produce content that the conditions forbid.** If printed material is banned, you output
text for the user to copy by hand and you say so explicitly — you do not produce a formatted,
print-ready page, because a printed sheet is a disqualification risk and handing one over
invites exactly that mistake.

---

## Step 1 — Rank what earns a place

Every line competes for space. Rank candidates by **marks at stake × how likely you are to lose
them**, which is not the same as marks alone:

| Candidate | Include when | Priority |
|---|---|---|
| **A trap that has fired ≥2 times** | always — this is the highest-value content on the page | 1 |
| **A playbook's steps** | the archetype is `cold` or `drilled` (streak < 2) and carries real marks | 2 |
| **A trap that fired once**, recently | space remains after 1 and 2 | 3 |
| **A playbook for an `exam_ready` archetype** | only its *traps*, never its steps | 4 |
| **Anything never drilled** | never | — |

**Drop what the user can already do.** An archetype at `exam_ready` with a clean streak does not
need its recipe on the page; it needs at most its trap line. Space spent on solved problems is
space stolen from unsolved ones, and this is the most common way these sheets get wasted.

**Drop anything the user has not drilled.** An unfamiliar formula on a cheat sheet costs the
seconds it takes to discover you don't understand it, and those seconds come out of a question
you could have answered.

**Never pad to fill the page.** A three-quarters-full sheet of things that matter beats a full
one padded with definitions.

---

## Step 2 — Compress

The constraint is physical: a person has to write this out by hand and then read it under time
pressure at a computer.

- **Traps become imperatives.** Not "students often forget that stochastic matrices have columns
  summing to one" but `stochastic: COLUMNS sum to 1`.
- **Playbooks become numbered steps, verbs only.** Strip every explanation. The user drilled
  these; the line is a pointer to a memory, not a teaching text.
- **Keep notation exactly as the exam uses it**, per the project's glossary. A cheat sheet in
  private notation is a translation exercise mid-exam.
- **Formulas over prose, always**, where the material has formulas.
- **Group by trigger, not by topic.** The sheet is read by someone who has just seen a question
  and is asking "which of my recipes is this?" — so the left-hand column is what they can see on
  screen, not what the lecture called it.

Target roughly **35–45 lines** for one handwritten side of A4, and say which estimate you used.
If the content exceeds it, cut by rank and **report what was cut**, so the user can overrule.

---

## Step 3 — Output

Plain text, in copy order, with the rank cut marked. Something like:

```
CHEAT SHEET — one side A4, handwritten. ~41 lines. Copy this out by hand.
Ranked by marks at risk. Everything below the line was cut for space.

── TRAPS (fired more than once — read these first) ──────────────
complex modulus      |a+bi|² = a²+b²   NOT (a+bi)²        ×3
stochastic matrix    COLUMNS sum to 1, not rows            ×2
measurement          ALWAYS write the post-measurement state ×2
tensor               order matters; A⊗B ≠ B⊗A              ×2

── RECIPES (by what you see on screen) ──────────────────────────
vector + "valid quantum state?"   |a_i|² → sum → =1?
matrix + "valid unitary?"         U†U = I  († = transpose AND conjugate)
H + state + "total energy"        ⟨ψ|Hψ⟩   (conjugate the bra)
…

── CUT FOR SPACE (say the word to swap any of these in) ─────────
shor-order-finding recipe   — 18 mk, but staff said heavy calculation is avoided
qec-threshold recipe        — 10 mk, heavy arithmetic
```

Close on the two things that matter:

```
Handwrite this — a printed sheet is not permitted and copying it out is one more retrieval pass.
Not on here on purpose: 6 archetypes you're already exam-ready on. You don't need notes for those.
```

---

## Step 4 — Write

Write the generated content to a file next to the archetypes (`cheat_sheet.md`), so it survives
the conversation and can be regenerated and diffed as more drills land.

**Do not write to `progress.json`.** This skill produces an artifact; it does not change state.
Nothing about generating a cheat sheet means an archetype was drilled.

---

## Guardrails

- **Never invent content.** Every line traces to a playbook or a logged trap. If the sheet looks
  thin, that is a true report on how much has been drilled — say so rather than filling it.
- **Never include forbidden material**, and never format it as print-ready where handwriting is
  required.
- **Never present it as a substitute for drilling.** A sheet built on Wednesday from three
  drilled archetypes is a sheet for a mostly-undrilled exam, and saying so is more useful than
  the sheet.
- **Regenerate rather than patch.** Run it again after the last session; the ranking will have
  moved and the traps will be more honest.

---

## What this skill is NOT

It is not a revision summary of the course — it contains only what has been drilled and only
what has cost marks. It does not teach, drill, or grade. And it does not decide what is allowed:
the exam's stated conditions do, and where those are unrecorded it asks rather than assuming.
