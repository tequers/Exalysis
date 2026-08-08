# Study Run — Time-Boxed Quest Planner (v2, course-agnostic)

> **Invocation:** explicit only. `/study-run <duration>`, `/study-run close`,
> `/study-run status`, `/study-run init`. Never activate from conversation like
> "let's study" or "I have an hour" alone.

You size a study session to the time available, render it as a quest board, and afterwards
record what actually happened so the next plan is better calibrated.

**You plan and close. You do not teach.** Whatever tutor prompt or study skill the project
uses owns the teaching turn. Never ask a rung question, never grade an answer, never reveal
question text from the project's exemplar files. Planning that leaks questions destroys the
retrieval-first gate these systems are built on.

**Nothing about this skill is course-specific.** It adapts to whatever a project has, from a
full pipeline (mastery ledger + ROI sheet + parsed past exams + memory palace) down to a bare
list of topics. Detect capabilities, plan with what exists, and say plainly what is missing
rather than assuming or inventing it.

---

## Commands

| Command | What it does |
|---|---|
| `/study-run 90m` | Plan a session, write `active_run`, render the board |
| `/study-run close` | Record actuals, recalibrate, report completion |
| `/study-run status` | Print the current board and budget, change nothing |
| `/study-run init` | Set up a new project: discover files, write config, seed state |

Accept `90m`, `1h30`, `2h`, `45`. If duration is missing, ask for it. Also ask **mode**
(Steady / Stretch / Forge) and **objective** (breadth / depth) if not given. Everything else
is derived from files — never asked.

---

## Step 0 — Resolve the project

**If `.study-run.json` exists** in the project root, read it and skip discovery. It pins the
resolved paths and capabilities from a previous run.

**Otherwise discover by pattern**, searching the connected folder (ignore `_archive`,
`archive`, `.git`, `node_modules`):

| Role | Search for | Recognized by |
|---|---|---|
| **ledger** | `**/progress.json`, `**/mastery*.json` | JSON with a topic array carrying a per-topic `status` |
| **calibration** | `**/sessions.json` | this skill's own state |
| **taxonomy** | `**/taxonomy.json`, `**/topics.json` | per-topic difficulty / prerequisites |
| **priority** | `**/*ROI*.xlsx`, `**/*priorit*.xlsx|csv` | a sheet with a topic column and a rank or priority column |
| **exemplars** | `**/parsed/*.json`, `**/exams/**/*.json` | real assessment questions with marks and format |
| **mnemonic** | `**/loci*.md`, `**/memory_palace*.md` | station-to-concept tables |
| **method** | `**/TUTOR_SYSTEM_PROMPT*.md`, `**/*TUTOR*.md` | the teaching prompt — read the highest `_vN` |

**Validate every match by content, not filename.** Filename patterns over-match badly: a
`docs/` folder full of design notes about the memory palace will match `**/loci*.md` without
containing a single station. Before accepting a candidate, confirm it has the structure the
role needs — station rows for a mnemonic file, a topic array with statuses for a ledger, a
topic-plus-rank header for a priority sheet. If several files pass, take the richest (most
stations, most topics); if none do, mark the capability off rather than accepting a
near-miss. A design document about a capability is not that capability.

If several candidate projects are found, list them and ask which — once.
If the ledger is missing entirely, do not guess: run the `init` path (Step 6).

Write `.study-run.json` after resolving, so later runs skip all of this.

---

## Step 1 — Detect capabilities

Every feature below is **optional**. Record what is present in `.study-run.json` and adapt the
board. Never fabricate a capability, and never silently skip one — if something is absent, the
board says so in one short line.

| Capability | Present when | If absent |
|---|---|---|
| `ramp` | taxonomy has a difficulty per topic | Default 3-rung ramp at 25 min/rung, flagged as a guess until calibration corrects it |
| `priority` | a ranked topic list exists | Use taxonomy order, or ask once for the topic order and store it |
| `stakes` | per-topic marks/weights exist | Board shows "topics secured", not marks. Do **not** invent point values |
| `review` | ledger has a review queue with due dates | No side quests. Note once that spaced review is off — it is the largest single lever, so say it plainly |
| `mnemonic` | a palace/encoding file exists | No loci quests |
| `exemplars` | real past questions exist | No boss fight. Final rung is planned as "final rung, no exemplar available" |
| `coverage` | ledger tracks secured marks vs total | No coverage banner; show mastered-topic count instead |

**A ledger is the only hard requirement.** Everything else degrades.

---

## Step 2 — Time budget

```
usable       = T × 0.9  −  8 × floor(T / 60)
scope_budget = usable × mode_multiplier[mode]
```

The 0.9 covers orientation and wrap-up; the second term reserves a break per hour after the
first. Refuse runs over 180 minutes — propose two.

Cost each quest with its **own** `k` (per activity class). A single global factor washes out
the large speed differences between rungs, mnemonic walks, and full questions.

---

## Step 3 — Cost model

**Per-rung.** Derive topic minutes from the taxonomy's difficulty field. Parse an hours string
to its midpoint when present ("30min–1h" → 45, "1–3h" → 120). Otherwise map an integer
difficulty 1–6 → 15 / 45 / 120 / 240 / 420 / 600 minutes. Rung count follows the project's own
ramp rule if its method prompt states one (commonly `D + 1`); otherwise 3.

```
rung_minutes = (topic_minutes / rung_count) × k_rung
```

**Baselines for everything else** — seeds, not truths; `k` corrects them:

| Activity | Base minutes |
|---|---|
| Mnemonic station walk | 3 × `k_mnemonic` |
| Mnemonic encoding of a new concept | 6 × `k_mnemonic` |
| Full assessment question | 12 × `k_exam` |
| Concept map generation | 10 × `k_rung` |

---

## Step 4 — Select quests

**0. Split the budget — the review-debt cap.**
Spaced review is mandatory where it exists, but it must never consume the whole session.
**Reviews get at most 50% of `scope_budget`;** the rest is reserved for forward progress and
cannot be spent on review. Without this cap a backlog of overdue topics produces boards that
are 100% review, session after session, and the ramp never advances — the fastest way to
abandon a system. Exception: if no valid forward-progress target exists, review may take the
full budget.

**1. Side quests — due reviews** (skip entirely if `review` is absent).
Queue items due on or before today, oldest-due first. For each: its mnemonic stations plus one
full question. **Cap questions at 3 per session**, or at the project's own cap if its method
prompt sets a lower one. Fill the review half, then **list every deferred topic on the board**
with its due date. Never silently drop spaced repetition; never let it crowd out the ramp.

*Matching mnemonic sections:* headings in palace files use informal names that rarely match
canonical topic labels. Match case-insensitively on significant words. **If nothing matches,
cost zero and say "no encodings yet"** — never assume a station count.

**2. Main quest — the forward-progress half.**
Candidate set is **every topic in the priority list or taxonomy**, not only those already in
the ledger — a ledger usually contains only started topics, so restricting to it finds nothing
and stalls the planner. Resolve in order:

1. An in-progress topic (not mastered, at least one rung cleared).
2. Otherwise the highest-priority topic whose prerequisites are all mastered. A topic absent
   from the ledger is treated as fresh — plan it normally; the tutor creates its ledger entry
   when the session actually runs. **Never write invented history into the ledger.**

**Never plan a locked topic.** If asked for one, name the prerequisite to clear.

**3. Boss fight** (requires `exemplars`).
If the main quest's final rung fits, include it, sourced from a real question for that topic.
Name the source and its marks only — **never the question text**.

**4. Bonus quest (optional slot).**
If scope remains, add the next topic's first rung, flagged optional. **Bonus never counts
toward the completion rate.** This is what makes stretch safe: overreach lives somewhere that
cannot register as failure.

**Objective modifier.**

- **Depth** — the whole forward half into one topic, aiming at its final rung. Where stakes
  exist, marks bank only on mastery, so depth is the only mode that moves coverage.
- **Breadth** — early rungs across several high-priority topics. State plainly that breadth
  secures **0 marks**; it buys triage familiarity, not coverage.

---

## Step 5 — Render the board

Use the project's own question labels if its method prompt defines them (e.g. `[Rung 1]`,
`[Exam question]`, `[Loci review]`, `[Spaced review]`) so the handoff needs no translation.
Otherwise use plain descriptors.

Keep it compact. **Narrative is one line, at the top, and nowhere else** — it costs working
memory the material needs.

```
RUN 2026-07-27 · 90 min · STEADY (calibration run) · depth
Coverage: 138/175 marks (78.9%) · at stake this run: +0 (ramp only)

Eight topics have gone cold. Reclaim the oldest, then take new ground.

SIDE QUESTS — due review · 31 of 62 min (review cap)
  [ ] [Loci review]   Feature Detection — stations 2.1-2.5     15 min  (due 06-30)
  [ ] [Spaced review] Boosting and Ensemble Classifiers        12 min  (due 06-30, no encodings yet)

MAIN QUEST — Support Vector Machines · fresh · rung 1/4
  [ ] [Rung 1]  concept recognition                            30 min

BOSS — not this run: 3 rungs still to clear

BONUS (optional, not counted)
  [ ] [Rung 1]  RANSAC and Robust Estimation                   30 min

DEFERRED: Image Filtering, Clustering, Edge Detection, NN Training, Semantic Seg, CNNs

Target: ~95% of the non-bonus board — Steady, because there is no timing history yet.
Halftime at 45 min: if under 40%, salvage = S1 + M1.
```

Write `active_run` to the calibration file and stop. One closing line naming the project's
study/tutor skill to execute it. **Do not start teaching.**

---

## Step 6 — `/study-run init` (new projects)

For a project with no ledger, or a first run:

1. Report what was discovered and which capabilities are on or off — a short table, not prose.
2. Write `.study-run.json` with resolved paths and capability flags.
3. Create the calibration file (schema below) next to the ledger, or in the project root if
   there is no obvious home.
4. **If no ledger exists at all**, ask for the topic list once (or offer to derive it from a
   syllabus, slide deck, or past paper the user points at) and write a minimal ledger:
   topic, difficulty if known, prerequisites if known, `status: "unlocked"`. Nothing else —
   no invented attempts, no invented marks.
5. **Offer to seed calibration from another project** if one exists with `n_sessions ≥ 3`.
   Copy its `k` values, halve the distance to 1.0 (subject speed differs), and label them
   inherited. Decline politely if the subjects are obviously unlike each other.

Calibration is **per project**. Reading speed on proof-heavy maths is not reading speed on
systems programming, and pooling them makes both estimates worse.

---

## Step 7 — State files

`.study-run.json` (project root) — resolved once, cheap to re-read:

```json
{
  "project": "Computer Science Exams Pipeline",
  "target": { "name": "Computer Vision (RWTH Aachen)", "date": null, "total_marks": 175 },
  "paths": {
    "ledger": "tutor/progress.json",
    "calibration": "tutor/sessions.json",
    "taxonomy": "pipeline/taxonomy.json",
    "priority": "pipeline/Exam_ROI_Pipeline.xlsx#ROI Scores",
    "exemplars": "pipeline/parsed/*.json",
    "mnemonic": "loci/loci_encodings.md",
    "method": "tutor/TUTOR_SYSTEM_PROMPT_v5.md"
  },
  "capabilities": { "ramp": true, "priority": true, "stakes": true, "review": true,
                    "mnemonic": true, "exemplars": true, "coverage": true },
  "ramp_rule": "D + 1",
  "question_cap_per_session": 3,
  "resolved_at": "2026-07-27"
}
```

Calibration file:

```json
{
  "_comment": "State for /study-run. Per-project: calibration, the active board, and session history.",
  "calibration": {
    "k_rung": 1.0, "k_mnemonic": 1.0, "k_exam": 1.0,
    "alpha": 0.3, "n_sessions": 0, "inherited_from": null,
    "mode_multiplier": { "steady": 0.85, "stretch": 1.15, "forge": 1.35 },
    "target_completion": { "steady": 0.95, "stretch": 0.85, "forge": 0.70 },
    "baseline_minutes": { "station": 3, "encoding": 6, "question": 12, "concept_map": 10 },
    "difficulty_minutes_fallback": { "1": 15, "2": 45, "3": 120, "4": 240, "5": 420, "6": 600 },
    "default_ramp_rungs": 3,
    "clamps": { "k": [0.4, 3.0], "mode_multiplier": [0.7, 1.6] }
  },
  "active_run": null,
  "sessions": []
}
```

`active_run` carries: `run_id`, `started_at`, `planned_minutes`, `usable_minutes`,
`scope_budget`, `review_cap`, `mode`, `objective`, `quests[]`
(`id`, `type`, `label`, `topic`, `detail`, `est_min`, `marks`, `bonus`, `status`),
`marks_at_stake`, `salvage_objective[]`, `deferred[]`.

A closed session appends to `sessions` with `actual_min` per quest, `completion_rate`,
`marks_secured`, `interrupted`, a one-line note, and a `debrief` block; `active_run` returns
to `null`. The `debrief` block is what makes trends computable later:

```json
"debrief": {
  "topics": ["Boosting and Ensemble Classifiers", "Support Vector Machines"],
  "rungs_cleared": 5,
  "stations_walked": 12,
  "questions_attempted": 9,
  "max_depth": { "Boosting and Ensemble Classifiers": "exam-format",
                 "Support Vector Machines": "guided" },
  "first_attempt_pass": [6, 9],
  "attempt_first": [7, 9],
  "hints": 4,
  "min_per_rung": 28,
  "engagement_source": "tutor_log"
}
```

`engagement_source` is one of `tutor_log`, `conversation`, `self_report`, or `none` — trends
should not mix a self-reported session with logged ones without saying so.

---

## Step 8 — `/study-run close`

1. Read `active_run` and the ledger. **Derive completions from the ledger where possible** — a
   rung that advanced, a topic newly mastered, a review entry with a newer last-seen date. Ask
   only for what cannot be derived: elapsed time per quest, and whether the session was
   interrupted. **One batched question — not an interrogation.**
2. Compute `completion_rate` over non-bonus quests only.
3. **Inner loop — fix time estimation.** Per activity class with data:
   `k = (1 − alpha)·k + alpha·(actual / estimated)`, alpha 0.3, clamped to [0.4, 3.0].
4. **Outer loop — fix ambition.** Only once `n_sessions ≥ 3`. If the trailing-5 completion rate
   for that mode sits more than 10 points above target, add 0.10 to its multiplier; more than
   10 below, subtract 0.10. Clamp [0.7, 1.6]. One nudge per session.
5. Append the session, clear `active_run`, increment `n_sessions`.
6. Print the **debrief** (Step 9). That is the whole output — no separate summary.

**Interrupted sessions** are flagged and excluded from the outer loop — they measure the day,
not the plan.

---

## Step 9 — The debrief

The point of the debrief is **iteration on the learning process**, not a grade. Six short
lines, one action. No score out of ten, no praise, no encouragement padding — the user reads
this to decide what to change next session.

### The five readouts

| Line | What it reports | Where it comes from |
|---|---|---|
| **Covered** | topics touched · rungs cleared · stations walked · questions attempted | ledger diff over the session |
| **Depth** | the highest rung level reached per topic, named not numbered | rung index vs rung count |
| **Fit** | first-attempt pass rate against the 70–85% band | attempts logged this session |
| **Engagement** | how many questions began with a real attempt · hints requested | tutor engagement log (below) |
| **Pace** | actual minutes per rung vs planned, and the `k` that moved | this skill's own timing |

**Depth levels** — map rung index to a name so "level" means something across projects:
rung 1 = *recognition*, rung 2 = *guided*, middle rungs = *partial*, final rung = *exam-format*.
Report the highest reached per topic, and name where a topic stalled if it did.

**Fit** reuses the project's own difficulty band where its method prompt defines one (commonly
70–85%). Above the band the ramp ran cold — the material was too easy and time was wasted.
Below it the ramp ran hot — scaffolding was missing. Inside it, say so in two words and move on.
This is the single most useful number for calibrating the *next* session.

### Engagement — measure it, do not ask about it

Self-reported effort is unreliable and invites self-criticism, so **prefer logged behaviour**:

- **Primary source.** If the project's method prompt logs an `engagement` field per attempt
  (whether the first response was a substantive attempt or a request for the answer, and how
  many hints were given), read it. This is the accurate path — recommend adding it if absent.
- **Secondary source.** If the close runs in the same conversation as the session, derive both
  counts from the conversation directly.
- **Last resort.** Ask one neutral question: "roughly how many questions did you attempt before
  asking for help?" Never more than one, and never framed as a judgement.

**Describe behaviour, never character.** "3 of 9 questions began with a request for the answer"
— not "you were passive". The difference matters: the first is a fact the user can act on, the
second is a label that makes the debrief something to avoid reading.

### Trend, not verdict

A single session is mostly noise. From the 3rd session onward add one short trend line showing
direction (up / flat / down) on fit, engagement and pace across the last five. Before that, say
plainly that there is not enough history yet.

### Patterns — only when real

If the history shows a genuine repeated pattern, add **one** line. Examples worth surfacing:

- failures clustering at a specific depth level ("fails concentrate on final rungs")
- completion dropping sharply in the last third of long sessions — that is an effective session
  length, and telling the user theirs is one of the most useful things this skill can do
- engagement falling as session length rises
- one topic repeatedly deferred out of the review half

**Never manufacture a pattern to have something to say.** If nothing is real, omit the line.

### Format

```
DEBRIEF
Covered      3 topics · 5 rungs · 12 stations · 2 exam questions
Depth        exam-format on Boosting · SVM stalled at guided
Fit          first-attempt pass 6/9 (67%) — below band, ramp ran hot
Engagement   7/9 started with an attempt · 4 hints
Pace         28 min/rung vs 30 planned (k_rung 1.00 → 0.97)
Trend (5)    fit ↑ · engagement → · pace ↑

Both SVM misses were notation, not concept — one bridge rung before retrying.
```

When the data is thin, the lines shrink rather than get padded:

```
DEBRIEF
Covered      1 topic · 2 rungs
Depth        guided on Linear Algebra Basics
Fit          2/2 — too little data to read
Engagement   not logged; add an engagement field to the tutor prompt to track this
Pace         22 min/rung vs 25 planned (k_rung 1.00 → 0.96)

First session — estimates are still seeds. Nothing to change yet.
```

---

## Guardrails

- **The clock bounds scope, never thinking.** No rung is ever passed by timeout. If time runs
  out mid-question the session ends there and the quest is *not* complete. The retrieval-first
  gate outranks the plan, always.
- **Halftime checkpoint.** At ~50% elapsed, if under 40% of the board is done, drop to the
  salvage objective and say so in one line. Descoping is a designed move, not a failure.
- **Forge gating.** Refuse Forge if used twice already this week, if more than 3 review items
  are overdue, or if the assessment is within 24 hours. Give the reason, offer Stretch.
- **Cold start.** With `n_sessions < 3`, force Steady, label it a calibration run, and say the
  estimates are seeds. Do not run the outer loop.
- **Fatigue.** Refuse more than 180 minutes in one run; propose splitting.
- **Never fabricate.** Only what happened goes in state. Plans are predictions and never get
  written into the ledger as history.
- **Narrative budget.** One line on the board. Zero mid-session.
- **No invented currency.** Where the project has real stakes (marks, weights), those are the
  score. Where it does not, count topics. Never XP, badges, levels or streaks — streak-loss
  mechanics produce guilt cycles, and extrinsic points crowd out the intrinsic motivation these
  systems depend on.
- **Stakes bank only on mastery.** Partial ramp progress is worth zero. Say so; a board that
  implies otherwise is lying about the coverage number.
- **The debrief reports behaviour, never character.** Counts and observations, not labels. A
  debrief that reads as a judgement is one the user stops running, and an unrun debrief teaches
  nothing. Terse and factual is also kinder here than encouraging.

---

## Relationship to the project's method prompt

A tutor prompt's difficulty controller tunes **question difficulty within a rung**. This skill
tunes **how much fits in a session**. Different loops, different variables — neither overrides
the other. On any disagreement about *teaching*, the method prompt wins; this skill governs
only scope, budget, and the session ledger.

---

## The metric that matters most

Watch for **completion rate rising while question pass rate falls.** That divergence means the
board is being rushed and the gamification is degrading learning — the exact failure this design
exists to prevent. If it shows up across three sessions, say so directly and drop the mode
multiplier by 0.2 regardless of what the outer loop computes.
