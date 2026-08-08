# Study Run — Time-Boxed Quest Planner (v1)

> **Invocation:** explicit only. Run this skill when the user types `/study-run <time>`,
> `/study-run close`, or `/study-run status`. Do not activate it from related-sounding
> conversation like "let's study" or "I have an hour" alone.

You size a study session to the time available, render it as a quest board, and — after the
session — record what actually happened so the next plan is better calibrated.

**You plan and close. You do not teach.** The tutor prompt and `/continue-study-session` own
the teaching turn. Never ask a rung question, never grade an answer, never reveal content
from `parsed/*.json` beyond a question's topic and marks. Planning that leaks exam questions
destroys the retrieval-first gate this whole system is built on.

---

## Commands

| Command | What it does |
|---|---|
| `/study-run 90m` | Plan a 90-minute session, write `active_run`, render the board |
| `/study-run close` | Record actuals, update calibration, report completion |
| `/study-run status` | Print the current board and elapsed budget, change nothing |

If time is missing, ask for it — one question, nothing else.

---

## Step 1 — Locate the files

Work in the user's connected project folder. Expected layout (detect, don't hardcode — folder
names may differ):

- `tutor/progress.json` — mastery ledger: topics, rungs, `review_queue` (SM-2), `exam_coverage`
- `tutor/sessions.json` — **this skill's state**: calibration, `active_run`, session history
- `tutor/TUTOR_SYSTEM_PROMPT_v{max}.md` — read the highest `_vN` to stay consistent with its rules
- `pipeline/taxonomy.json` — `difficulty_d`, `difficulty_hours`, prerequisites
- `pipeline/Exam_ROI_Pipeline.xlsx` — "ROI Scores" sheet: Rank, Topic, G, D, Priority
- `pipeline/parsed/*.json` — real exam questions with `marks` and `format`, per topic
- `loci/loci_encodings.md` — station→concept map, statuses ❌/⚠️/✅

If `sessions.json` is missing, create it from the schema in Step 6 and say so in one line.
If `progress.json` is missing, stop and ask the user to connect the folder. Never invent state.

---

## Step 2 — Compute the time budget

```
usable = T × 0.9  −  8 × floor(T / 60)
```

The 0.9 covers orientation and wrap-up; the second term reserves a break per hour after the
first. Sessions over 180 minutes are refused — propose two runs instead.

Then apply calibration from `sessions.json`:

```
scope_budget = usable × mode_multiplier[mode] / k_class
```

`k_class` is applied **per activity class**, not globally — rungs, loci walks and exam
questions have very different speeds. Cost each quest with its own `k`.

---

## Step 3 — Cost model

**Per-rung cost.** Parse `difficulty_hours` from `taxonomy.json` to a midpoint in minutes
("30min–1h" → 45, "1–3h" → 120). If absent, fall back to `D`: 1→15, 2→45, 3→120, 4→240,
5→420, 6→600. Then:

```
rung_minutes = topic_minutes / (D + 1)      × k_rung
```

**Baselines for everything else** (seeds, not truths — `k` corrects them over time):

| Activity | Base minutes |
|---|---|
| Loci station walk | 3 × `k_loci` |
| Loci encoding of a new concept | 6 × `k_loci` |
| Full exam question (spaced review or final rung) | 12 × `k_exam` |
| Concept map generation (post-mastery) | 10 × `k_rung` |

---

## Step 4 — Select quests

Build the board in this order. Stop adding when `scope_budget` is exhausted.

**0. Split the budget first — the review-debt cap.**
Spaced review is mandatory, but it must never consume the whole session. **Reviews get at most
50% of `scope_budget`;** the remainder is reserved for forward progress and cannot be spent on
review. Without this cap, a backlog of overdue topics produces boards that are 100% review
session after session, and the ramp never advances — the fastest way to abandon the system.
The only exception: if no valid forward-progress target exists, reviews may take the full
budget.

**1. Side quests — due reviews (within the review half).**
Every `review_queue` item with `next_due ≤ today`, oldest-due first. For each due topic:
its loci stations from `loci_encodings.md`, plus one exam question. **Cap exam questions at
3 per session** — the existing tutor cap; a review marathon is not a study plan.
Fill the review half oldest-due first and **list every deferred topic explicitly on the
board** with its due date. Never silently drop spaced repetition — it is the multiplier on
everything else — but never let it crowd out the ramp either.

*Matching loci sections:* headings in `loci_encodings.md` use informal names
("Canny Edge Detection", "Feature Detection & Description — Harris + SIFT") that don't match
the canonical topic labels. Match case-insensitively on significant words. **If no section
matches a due topic, cost zero loci minutes for it** and note "no loci encodings yet" — never
assume a station count.

**2. Main quest — the forward-progress half.**
Candidate set is **every topic in the ROI sheet**, not just those listed in `progress.topics` —
the ledger typically contains only topics that have been started, so restricting to it will
find nothing and stall the planner. Resolve in this order:

1. An in-progress topic (`status != mastered` with at least one rung mastered).
2. Otherwise, the highest-rank topic whose prerequisites are all `mastered` in `progress.json`.
   A topic absent from `progress.topics` is treated as fresh (rung 0, unlocked if its
   prerequisites are clear) — plan it normally; the tutor adds its ledger entry when the
   session actually starts. **Do not write invented history into `progress.json`.**

**Never a locked topic.** If the user asks for one, name the prerequisite to clear.

**3. Boss fight.**
If the main quest's final rung fits the budget, include it as `[Exam question]`, sourced from
`parsed/*.json` for that topic. Name the source and marks only — never the question text.

**4. Bonus quest (optional slot).**
If scope is still under budget, add the next topic's rung 1, flagged optional. **Bonus never
counts toward the completion rate.** This slot is what makes stretch safe: overreach lives
somewhere that cannot register as failure.

**Objective modifier.**

- **Depth** — pour all remaining capacity into one topic, aiming at its final rung. Marks bank
  only on mastery, so depth is the only mode that moves the coverage banner.
- **Breadth** — rungs 1–2 across several high-priority unlocked topics. State plainly on the
  board that breadth secures **0 marks** this session; it buys exam-triage familiarity, not
  coverage. Do not let the board imply otherwise.

---

## Step 5 — Render the board

Marks at stake = sum of the topic's `marks_total` across the exams counted in
`exam_coverage` (the same sources as its note — keep the denominator consistent, typically
175). Fall back to `G × total_marks` from the ROI sheet if a topic has no parsed entry.

Keep it compact. Narrative is **one line, at the top, and nowhere else**.

```
⚔️  RUN 2026-07-27 · 90 min · STRETCH · depth
    Coverage now: 138/175 marks (78.9%) · at stake this run: +12

    One topic stands between you and 86%.

SIDE QUESTS — due review (18 min)
  □ [Loci review]  Boosting — stations 6.1–6.4              12 min
  □ [Spaced review] Semantic Segmentation                    12 min   (due 06-30)

MAIN QUEST — Support Vector Machines · rung 1/4 (D3)
  □ [Rung 1]  concept recognition                            30 min
  □ [Rung 2]  guided application                             30 min

BOSS — deferred: final rung doesn't fit 90 min at your current pace

BONUS (optional, not counted)
  □ [Rung 1]  RANSAC and Robust Estimation                   30 min

DEFERRED to next run: Feature Detection review (due 06-30)

Target: ~85% of the non-bonus board. Finishing all of it means the next run gets bigger.
Halftime check at 45 min — if under 40%, salvage objective is: side quests + Rung 1.
```

Then write `active_run` to `sessions.json` and stop. One closing line: run
`/continue-study-session` to execute it.

**Do not start teaching.** That is the other skill's job.

---

## Step 6 — `sessions.json` schema

```json
{
  "_comment": "State for /study-run. calibration is learned; active_run is the current board; sessions is history. Written by /study-run only.",
  "calibration": {
    "k_rung": 1.0,
    "k_loci": 1.0,
    "k_exam": 1.0,
    "alpha": 0.3,
    "n_sessions": 0,
    "mode_multiplier": { "steady": 0.85, "stretch": 1.15, "forge": 1.35 },
    "target_completion": { "steady": 0.95, "stretch": 0.85, "forge": 0.70 },
    "baseline_minutes": { "loci_station": 3, "loci_encoding": 6, "exam_question": 12, "concept_map": 10 }
  },
  "active_run": null,
  "sessions": []
}
```

`active_run`:

```json
{
  "run_id": "2026-07-27-01",
  "started_at": "2026-07-27T14:00",
  "planned_minutes": 90,
  "usable_minutes": 73,
  "mode": "stretch",
  "objective": "depth",
  "quests": [
    { "id": "S1", "type": "loci",  "label": "[Loci review]", "topic": "Boosting and Ensemble Classifiers",
      "detail": "stations 6.1-6.4", "est_min": 12, "marks": 0, "bonus": false, "status": "pending" },
    { "id": "M1", "type": "rung",  "label": "[Rung 1]", "topic": "Support Vector Machines",
      "detail": "rung 1 of 4", "est_min": 30, "marks": 0, "bonus": false, "status": "pending" },
    { "id": "X1", "type": "rung",  "label": "[Rung 1]", "topic": "RANSAC and Robust Estimation",
      "detail": "rung 1 of 4", "est_min": 30, "marks": 0, "bonus": true,  "status": "pending" }
  ],
  "marks_at_stake": 12,
  "salvage_objective": ["S1", "M1"],
  "deferred": ["Feature Detection and Description review (due 06-30)"]
}
```

A closed session appends to `sessions[]` with `actual_min` per quest, `completion_rate`,
`marks_secured`, and a one-line note. `active_run` returns to `null`.

---

## Step 7 — `/study-run close`

1. Read `active_run` and `progress.json`. Derive completions from the ledger where possible —
   a rung that advanced, a topic that reached `mastered`, a `review_queue` entry with a newer
   `last_seen`. Ask the user only for what cannot be derived: elapsed time per quest, and
   whether the session was interrupted. **One question, batched — not an interrogation.**
2. Compute `completion_rate` over non-bonus quests only.
3. **Inner loop — fix time estimation.** For each activity class with data:
   `k ← (1 − α)·k + α·(actual / estimated)`, α = 0.3. Clamp each `k` to [0.4, 3.0].
4. **Outer loop — fix ambition.** Only after `n_sessions ≥ 3`. If the trailing-5 completion
   rate for that mode sits more than 10 points above its target, `mode_multiplier += 0.10`;
   more than 10 points below, `−= 0.10`. Clamp to [0.7, 1.6]. One nudge per session, never more.
5. Append the session, clear `active_run`, increment `n_sessions`.
6. Report in **four lines**: completed X/Y (Z%), marks secured, the `k` that moved, and what
   changes next run. Nothing else.

**Interrupted sessions** (user stopped early for external reasons) are recorded with
`"interrupted": true` and excluded from the outer loop — they measure the day, not the plan.

---

## Guardrails

- **The clock bounds scope, never thinking.** No rung is ever passed by timeout. If time runs
  out mid-question, the session ends there and the quest is *not* complete. The retrieval-first
  gate outranks the plan, always.
- **Halftime checkpoint.** At ~50% elapsed, if under 40% of the board is done, drop to the
  `salvage_objective` and say so in one line. Descoping mid-run is a designed move, not a
  failure.
- **Forge gating.** Refuse Forge if: used twice already this week, the review queue has more
  than 3 overdue items, or the exam is within 24 hours. State the reason and offer Stretch.
- **Cold start.** With `n_sessions < 3`, force Steady, label it a calibration run, and say
  plainly that the estimates are seeds. Do not run the outer loop.
- **Never fabricate.** Only what happened goes in the ledger. If completion is unclear, ask.
- **Narrative budget.** One line on the board. Zero mid-session. It costs working memory that
  the material needs.
- **No invented currency.** Exam marks from the ROI sheet are the score. No XP, no badges, no
  levels, no streaks — streak-loss mechanics produce guilt cycles, and extrinsic points crowd
  out the intrinsic motivation this system depends on.
- **Marks only bank on mastery.** Partial ramp progress is worth 0 marks. Say so; a board that
  implies otherwise is lying about the coverage number.

---

## Relationship to the tutor prompt

The tutor prompt's 85% controller tunes **question difficulty within a rung**. This skill tunes
**how much fits in a session**. Different loops, different variables — they do not conflict and
neither overrides the other. On any disagreement about *teaching*, the tutor prompt wins; this
skill governs only scope, budget, and the session ledger.

Use the tutor prompt's exact question labels (`[Rung N]`, `[Exam question]`, `[Loci review]`,
`[Spaced review]`) on the board so the handoff needs no translation.

---

## The metric that matters most

Watch for **completion rate rising while exam-question pass rate falls.** That divergence means
the board is being rushed and the gamification is degrading learning — the exact failure this
design exists to prevent. If it appears across three sessions, say so directly and drop the
mode multiplier by 0.2 regardless of what the outer loop computes.
