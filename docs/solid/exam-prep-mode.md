# Exam-Prep Mode — Usage Guide

The **fast mode**: drills recurring question archetypes to fluency under time pressure. It optimises marks per hour, not understanding.

It runs **alongside** the deep tutor and shares no state with it. Neither can corrupt the other. See `CONTEXT.md` for the Course/Exam/Topic vocabulary, and `docs/solid/new-course-setup.md` for getting past papers parsed in the first place — this guide assumes that is already done.

---

## Which mode do I want?

| | **Deep mode** | **Exam-prep mode** (this guide) |
|---|---|---|
| Commands | `/study-run`, `/continue-study-session` | `/start-session`, `/session-end`, `/mock-exam`, `/cheat-sheet` |
| Unit of work | Topic, climbed over `D+1` rungs | **Question archetype**, drilled to fluency |
| Goal | Understand it | Answer it correctly, in time |
| Success | `mastered` — unaided ≥90% on an exam-format question | `exam_ready` — 2 consecutive clean drills inside budget |
| Prerequisite locks | Enforced | **Ignored** |
| Governing prompt | `tutor/TUTOR_SYSTEM_PROMPT_v10.md` | `tutor/EXAM_PREP_PROMPT_v1.md` |
| Best when | Weeks out, want the subject | Days out, want the marks |

**Never run both in one sitting.** They use different pedagogy and will contradict each other.

> **`mastered` and `exam_ready` are different criteria and are never added together.**
> A topic mastered in deep mode still starts `cold` here. Staleness only discounts the *estimated drill time* (×0.70) — it never grants readiness. Two coverage numbers, permanently distinct.

---

## Daily use

### `/start-session 90m`

One shot. Resolves the project, sizes a queue to the time you have, and **starts drilling in the same message** — no plan to approve, no menu, no questions.

```
/start-session 90m        /start-session 45        /start-session 2h
```

What it does, in order: picks the Exam (nearest future `exam_date`) → loads `archetypes.json`, mining it first if absent → warm-up sweep → builds a queue sized to the time → drills.

Usable minutes are `T × 0.92 − 5 × floor(T / 60)` — it reserves overhead and a break per hour, so a "90m" session plans about 78 minutes of drilling.

Drills arrive in **sprint blocks of 3–5 questions against one clock**, not one at a time — you pace across a block the way you pace across a paper. A brand-new archetype's first drill always runs alone; mixing only starts once three or more are `exam_ready`, because switching cost between question types is real and examined.

**Answer a whole block in one message, with your elapsed time:**

```
[Sprint 3 · validity checks · 4 items · 3:00 total]
1. Is [1/√2, i/√2] a valid quantum state?
2. Is [[0,1],[1,0]] a valid unitary?
...

→  1 yes 2 yes 3 yes 4 no — 2:10
```

Omit the time and it grades normally, notes `time not reported`, and skips that block in calibration. It won't nag.

New archetypes open with a **cold shot**: one ungraded ~30-second attempt where *"I don't know"* is a fine answer. There is no Socratic deflection anywhere in this mode — if you're stuck, you get the playbook. A miss re-drills **immediately**, in the next sprint, not next session.

State is written after **every sprint**, so a crashed session loses at most one block.

### `/session-end 75`

Closes the session and persists everything. The number is the **actual** elapsed minutes.

```
/session-end 75       ← recalibrates the time model
/session-end          ← logs timing as "not_collected", skips recalibration entirely
```

Give the real number when you have it: it feeds `k_drill` (EWMA, α = 0.3, clamped to [0.4, 3.0]), which is how the queue-sizing gets less wrong over time. Omitting it is safe — it just skips calibration rather than guessing.

You get a six-line debrief — Drilled / Ready / Coverage / Pace / Stuck / Runway — then your full accumulated trap list.

### `/mock-exam 90m`

The dress rehearsal. A full timed paper assembled from real past questions and variants, weighted toward your weakest archetypes, delivered in one block, then graded in one pass with a predicted score.

**It will refuse if fewer than half your mark-carrying archetypes are `exam_ready`**, and offer a diagnostic instead. Say **"mock anyway"** to override. Run it once the queue is mostly drilled — a mock taken cold measures nothing you didn't already know.

Mock results **can break** an `exam_ready` streak but never **set** one.

### `/cheat-sheet`

Builds the content of a permitted handwritten aid from your playbooks and the traps you personally kept hitting — ranked by marks at risk, cut to fit.

```
/cheat-sheet          /cheat-sheet a5          /cheat-sheet "2 sides"
```

**It checks the rules first.** If `exam_format` says no aids, it refuses and offers a revision list. If conditions aren't recorded, it asks once rather than guessing. It outputs **text to copy by hand, never a print-ready page** — handing over a formatted sheet invites a disqualification.

The value is that it's *earned*: a page of what actually cost you marks, not a page of what looked important. Run it after your last drill session, not before.

---

## What each file does

### Shared across every course — `tutor/`

| File | Role |
|---|---|
| `EXAM_PREP_PROMPT_v1.md` | **The method.** Governs how this mode drills, grades, and decides. Edit here to change behaviour everywhere. |
| `START_SESSION_SKILL_v1.md` etc. | Source of truth for the four skills. |
| `*-v1.skill` | Zip bundles for uploading to Cowork. |
| `../.claude/skills/<name>/SKILL.md` | Installed copies — what Claude Code actually loads. |

> **Three copies exist per skill** (source `.md`, `.skill` bundle, installed `SKILL.md`). Edit the source, then resync all three, or your fix silently won't take effect.

The prompt has **no "TUTOR" in its filename on purpose** — deep-mode skills glob `**/*TUTOR*.md` for their prompt, and a collision would make `/continue-study-session` load the wrong method.

### Per Exam — `Courses/<Course>/<Exam>/`

| File | Written by | Role |
|---|---|---|
| `archetypes_map.py` | You / Claude | **Judgement layer.** Which question belongs to which archetype, plus the playbooks. **Contains no arithmetic.** |
| `archetypes_postprocess.py` | You / Claude | **Arithmetic layer.** Computes every number, validates, writes `archetypes.json`. |
| `archetypes.json` | the script | **Generated — never hand-edit.** The archetype map plus live drill state. |
| `progress.json → exam_prep` | `/session-end` | Rolled-up readiness, session history, calibration. |
| `parsed/*.json` | the pipeline | The real exam questions everything is mined from. |
| `syllabus.json` | You / Claude | The **current** topic list from the slides. Separates the form layer from the content layer — see below. |
| `../.study-run.json` | `/start-session` | Resolved-paths cache under an `exam_prep` key. |

**The map/postprocess split is the important part.** Judgement is the part a person must make; arithmetic is the part a person gets wrong. On the quantum-computing exam the time budgets were hand-derived and were wrong three times running, because a hand-typed number has nothing checking it. The script asserts every question is mapped, no marks leak, and the summed budgets land within 10% of the exam length.

**To change anything about archetypes: edit `archetypes_map.py`, then re-run.**

```bash
cd "Courses/<Course>/<Exam>" && python archetypes_postprocess.py
```

It fails loudly on an unmapped question, an archetype with no playbook, or a playbook with no questions.

---

## What the system needs from you

### Required — it cannot run without these

1. **Parsed past papers** at `Courses/<Course>/<Exam>/parsed/*.json`, each question carrying `q_id`, `text`, `marks`, `format`, `topics`.

   No parsed papers, no mode. `/start-session` stops and says so rather than improvising a queue from the syllabus — archetypes that don't come from real papers are guesses about the examiner, and drilling a guess to fluency is worse than not drilling.

2. **`exam_date`** in `progress.json`. This is how the right Exam gets picked when the repo holds several.

### Required, asked once — the exam's duration

**Every time budget is derived from it.** Getting it wrong scales every drill clock. Set it in `archetypes_postprocess.py`:

```python
EXAM_MINUTES = 90
BUDGET_PAPER = "2023_Exam"   # the one genuine sitting
```

then re-run — budgets rescale, no re-mining needed.

> **Pick `BUDGET_PAPER` carefully: one real sitting, never a sum.** Practice sets, task compilations, and mock papers make excellent archetype sources and terrible clocks. Summing them inflates the denominator and makes every budget too fast.

### Strongly wanted — the *current* syllabus (`syllabus.json`)

Past papers tell you two different things with two different shelf-lives, and conflating them is the biggest single risk in this mode:

| | Anchored on | Shelf-life |
|---|---|---|
| **Form** — how questions are asked and marked (`answer_shape`, `trigger`, `budget_s`, "marks = distinct scorable statements", the generic traps) | past papers | **long** — exam style rarely changes |
| **Content** — which topics appear and what they're worth (`marks_at_stake`, `roi`, `must_cover`, the topic-specific `steps`) | past papers | **short** — a syllabus can turn over in a few years |

**If staff say the course content has changed, the content layer is stale but the form layer is not.** `syllabus.json` holds the current topic list so the two can be tracked apart. Each topic is `current`, `unverified`, `dropped`, or `new`.

Two rules keep it honest:

- **`unverified` carries full weight.** Assuming a topic is gone is as unfounded as assuming it stays. Nothing is down-weighted on speculation — it's flagged, and the postprocess emits a standing warning while the file is a stub.
- **Blind spots are the real danger.** Curricula usually drift by *adding*. A syllabus topic with **no archetype** is marks nothing in the queue drills — far worse than a mis-weighted old archetype. `blind_spots` is computed as soon as the file is filled in; while it's a stub it reports *"not checked"*, never *"none"*.

**Exercise sheets are a second source, and often the better one.** Even when they are programming tasks, their prose carries conceptual questions in the exam's own voice - *"Which network has more parameters?"*, *"Why do we use addition instead of concatenation?"* - and sometimes worked answers. Mine the markdown, not the code. On this course the exercises were the ONLY source revealing that Vision Transformers are taught; neither the past papers nor the slide summaries mentioned them.

When slides and exercises disagree, the examinable set is their **union**. Exercises are the practical subset, so absence from them is weak evidence; absence from the slides is stronger.

Filling it in needs only the slide deck's table of contents: set each topic's status, add anything the slides cover that no past paper did, re-run.

### Strongly wanted — the exam's conditions

Recorded in `archetypes.json → exam_format`: aids permitted, calculator, open/closed book, whether heavy calculation is avoided.

**If unknown, record it as unknown** rather than assuming. `/cheat-sheet` then asks instead of guessing. This is worth an email to course staff — on the quantum exam it turned out to permit a handwritten A4 sheet, which changed what was worth drilling.

### Wanted, but gathered automatically

Your **actual elapsed minutes** at `/session-end`, and your **traps** — the named failure modes that accumulate per archetype as you drill. Traps are the highest-value content the system produces: they become the cheat sheet and the final-review list.

---

## Setting this up for a new Exam

Assumes past papers are already parsed (`docs/solid/new-course-setup.md`).

1. **Read the questions.** Cluster them into archetypes — a recurring *stem + format + solution flow*. Expect roughly one archetype per 5–8 marks.
2. **Write `archetypes_map.py`**: the `(exam_id, q_id) → archetype` table and a playbook each. Judgement only.
3. **Copy `archetypes_postprocess.py`** from a sibling Exam; set `EXAM_MINUTES` and `BUDGET_PAPER`.
4. **Run it** until it passes clean.
5. **Create `Courses/<Course>/.study-run.json`** with an `exam_prep` key. *(Optional — `/start-session` discovers by role without it, and writes it on first run.)*
6. **`/start-session 60m`.**

### Adapting the playbook to the exam's character

A playbook has `trigger`, `why` (**one sentence** of causal intuition — not a derivation), `answer_shape`, `steps`, `traps`, `budget_s`.

**How much each field matters depends on what the exam asks for**, and getting this wrong is the main way a port underperforms:

- **Computational exam** (compute-a-number): `steps` is a calculation recipe and carries the value. `why` matters least here.
- **Verbal exam** (`explain_derive` dominant): the marks count **distinct scorable statements**, so `answer_shape` becomes load-bearing — *"2 methods × (1 advantage + 1 disadvantage)"*. And `why` becomes essential, because the question literally asks it; a recipe alone will quietly underperform.

Check the mix before writing playbooks:

```python
import json, collections
qs = json.load(open('parsed/<paper>.json', encoding='utf-8'))['questions']
m = collections.Counter()
for q in qs: m[q['format']] += q['marks']
print(m, 'mean marks/question:', sum(q['marks'] for q in qs)/len(qs))
```

**Two structural rules worth carrying over:**

- **Recall archetypes** (*"list the steps of X"*) put the answer **shape** in the playbook and cycle content through instances — no single step list covers Canny and k-Means at once.
- **Derivation archetypes** put the **actual derivation** in the playbook, because there is only one and it is the whole value.

### The ROI trap

The queue orders by `marks_at_stake ÷ estimated_drill_minutes`. That is right for a time-constrained queue and **wrong at the extremes**: long derivations cost the most minutes per mark, so pure ROI buries them — even when they're guaranteed marks on the real paper.

Fix it with a floor, not by abandoning ROI:

```python
MUST_COVER_REAL_MARKS = 5      # >= this many marks in the genuine sitting -> front tier
```

On the CV exam this rescued two derivations worth 13 of the paper's 94 marks from ranks 28 and 30 of 33.

---

## Gotchas

**Exam resolution picks the nearest *future* `exam_date`.** Once an exam passes, that course drops out automatically.

**`.study-run.json` is read *after* the Exam is chosen, never before.** A cache belonging to a different Course resolves cleanly, validates cleanly, and silently drills the wrong subject — so the cache is only consulted inside the chosen Exam's own Course folder. A missing cache is normal.

**Figure-dependent archetypes.** Parsed JSON carries text, not images, so questions referencing a diagram are flagged `figure_dependent: true`. Drills regenerate a textual matrix instead — workable, but those variants won't look identical to the paper.

**This mode never writes deep-mode state.** Not `topics[]`, `status`, `rung`, `marks_secured`, `coverage`, `attempts[]`, `next_session`, `session_log`, or any topic's `review_queue`. It writes `archetypes.json` and `progress.json → exam_prep`, and nothing else. You can run it on a course mid-ramp without disturbing the ramp.

**Skills don't appear in Cowork automatically.** `.claude/skills/` works in Claude Code only; Cowork needs the `.skill` bundles uploaded through its UI. And the bundles deliberately **don't** contain `EXAM_PREP_PROMPT_v1.md` — each skill resolves it from the connected folder by glob. Uploading the bundles is necessary but not sufficient: **the repo folder must also be connected**, or they load, find no method prompt, and stop.

---

## Live example — Computer Vision, `final_26_08_2026`

```
33 archetypes · 105/105 questions · 220/220 marks mapped
budget basis: 2023_Exam alone — 94 marks / 47 q / 90 min → 57.4 s per mark
budget validation drift: −1.1%
must-cover tier: 5 archetypes, 41 of 94 real-paper marks (44%), ~46 min
total to exam_ready on everything: 191 min
```

A verbal exam — 58% of marks `explain_derive`, 2.0 marks per question — so its mode-level rule is **marks = number of things you must write**, and its playbooks lean on `answer_shape` and `why`.

See that Exam's `PROJECT_NOTES.md` for its full decision record and open questions.
