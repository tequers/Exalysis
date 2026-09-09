# Critique: Tutor v10 vs. Learning Science — and vs. its own ledgers

**Status: open.** Reviewed `tutor/TUTOR_SYSTEM_PROMPT_v10.md` (712 lines), `tutor/SKILL.md` (`/continue-study-session`, 229 lines), and both live Exam ledgers on **2026-08-17**.

Predecessors: `critique-tutor-learning-science.md` (v8) and `critique-tutor-v9-learning-science.md` (v9). **Neither is re-litigated here.** This starts from v10 as the baseline and asks one question: *what shipped, and what did the shipping change?*

Goal frame, unchanged and taken from the user: **effortless to start · honest without sugarcoating · engaging · makes you come back.** One command, zero decisions, then pure study.

---

## Timing note — read this before the plan

Two exams are live and close:

| Exam | Date | Days out | State |
|---|---|---:|---|
| Introduction to Quantum Computers | 2026-08-20 | **3** | 7/18 topics mastered · coverage 46.3% · 8 topics never opened |
| Computer Vision · final_26_08_2026 | 2026-08-26 | **9** | 8/10 mastered · banner claims 78.9% · **last retrieval 2026-06-29 — 49 days ago** |

**Nothing in the P1 plan below should be built before 2026-08-26.** Refactoring a tutor three days before an exam is the wrong trade at any effect size. The plan is therefore split: a §Triage section that is two manual actions this week, and the real work after the last exam.

---

## Source validation

Every empirical claim is tied to a primary source. Honest gaps, stated rather than papered over:

- **Bastani et al. (PNAS 2025)** — I retrieved the full text via PMC and confirmed the exact coefficients (below). **A published correction exists** (`10.1073/pnas.2518204122`); PNAS returned 403 and I could not read what it changes. Treat the numbers as from the original full text, not as post-correction verified.
- **Instruction Stacking Collapse (arXiv 2608.02639)** and **SEQUOR (arXiv 2605.06353)** — both are 2026 arXiv preprints, not peer-reviewed. I use them because they test the exact regime this system runs in (Claude-family models, stacked constraints, 50-turn conversations) and because their direction is corroborated by the older peer-reviewed primacy literature *and* by this project's own logs. The logs are the stronger evidence.
- **Kurnaz (2025) gamification meta-analysis** — K-12, 31 studies, high heterogeneity. I use it only to qualify a claim, not to overturn one.
- **Rawson & Dunlosky's "3 correct recalls, then relearn 3× spaced"** is their own prescription from a coherent programme of individual studies, several classroom-based. There is no meta-analysis of successive relearning specifically. Treat the *direction* as solid and the *number 3* as a sane default, not a constant.

---

## What v10 gets right — do not touch these

### 1. The retrieval-first gate is the single most valuable rule in the file

Bastani et al. ran ~1,000 students, grades 9–11, four 90-minute sessions, 2,848 observations, three arms. Precise results:

| Arm | During assisted practice | On the later unaided closed-book exam |
|---|---|---|
| Control (textbooks) | baseline 0.284 | baseline 0.321 |
| **GPT Base** (unguarded ChatGPT) | **+48%** (+0.137) | **−17%** (−0.054) |
| **GPT Tutor** (hints only, no solutions) | **+127%** (+0.361) | −0.004, indistinguishable from control |

The guardrail that removed the harm was, verbatim, *"provide hints rather than direct answers."* That is v10's hint ladder and its absolute gate from rung 1. This is not pedantry — it is the measured difference between a tutor that helps and one that actively damages unaided performance. **Whatever else changes, the gate stays absolute.**

Worth naming honestly: even GPT Tutor produced *no exam gain* over control. The gate prevents harm; it does not by itself produce benefit. The benefit has to come from spacing and criterion — which is exactly where W3 and W4 below say the system is weakest.

### 2. First contact is a textbook-correct resolution of a real tension

`[Problematic]` → hook → `[Probe]` (ungraded) → `[Worked example]` (faded, one step blanked) → `[Rung 1]`.

The pretesting effect is real: unsuccessful retrieval attempts before instruction improve later retention relative to equal-time restudy — but **the benefit depends on corrective feedback following the failed attempt**. v10 mandates exactly that (line 300: *"Feedback follows immediately — the pretesting benefit depends on it"*). Most designs that copy the pretest idea drop the conditional and lose the effect. The guardrail — *"if rung 1 can be answered by copying the worked example, you've written rung 1 wrong"* — is the other part everyone forgets.

### 3. Marks + explicit rubric + the no-fatal-error clause is near-optimal feedback design

Wisniewski, Zierer & Hattie (2020) — 435 studies, 994 effect sizes, N > 61,000 — found feedback averages **d = 0.48**, and that the dominant moderator is **how much information the feedback carries**. A bare PASS/FAIL is the low-information end. v10's `"84% — but the invariant is inverted, so that's a FAIL regardless of the score"` is about as information-rich as a single verdict gets: score, rubric, named missed step, and a judgement about whether the error propagates.

The detail that makes it work across a CS degree is that **"fatal" is adapter-relative** — an unjustified step in a proof, the wrong growth class in complexity, a broken invariant in code, the wrong mechanism in systems. That is a genuinely good piece of design and it is not in any textbook.

### 4. Task-directed tone, with the mechanism stated correctly

Kluger & DeNisi's finding is that feedback drawing attention to the *self* degrades performance — roughly a third of feedback interventions reduced it. v10 doesn't state this as politeness; it states the mechanism: *"the second set is harsher on me and less useful, because it moves attention from the task to my self-image."* Wisniewski et al. corroborate the direction — feedback shows higher impact on cognitive outcomes than on motivational ones, which is precisely why using feedback as a motivational instrument is a category error. v10 refuses to.

### 5. Confidence inferred rather than asked — better than what the v9 critique recommended

The v9 critique proposed an inline `low/ok/high` tag. v10's 2026-08-15 change went further: **infer it silently from hedging, commitment, and completeness; never ask.** That removes the turn cost *and* the irritation while preserving the hypercorrection routing, which is well-founded (high-confidence errors correct better than low-confidence ones when feedback is immediate, and don't return if a test follows). This was the right call and it beat the recommendation.

### 6. Refusing streaks and XP — right, with one footnote

The 2025 K-12 gamification meta-analysis (Kurnaz, *Psychology in the Schools*, 31 studies) reports **g = 0.654** on motivation overall — but with a larger effect on **extrinsic** motivation (g = 0.713) than **intrinsic** (g = 0.638), and high heterogeneity. That is not a refutation of v10's ban; it is a restatement of v10's own stated worry in the literature's vocabulary: gamification buys compliance faster than it buys internalisation, and over a months-long exam horizon that is the wrong trade.

The footnote: SDT does *not* condemn all feedback-shaped motivators. **Competence-contingent** information supports intrinsic motivation; **completion-contingent** rewards undermine it. The coverage banner is the first kind. v10 already draws exactly this line. Keep the ban; the section is correctly argued, not merely opinionated.

### 7. Discrimination sets scoped narrowly, and the ramp explicitly protected from interleaving

*"Never interleave the ramp itself. During acquisition, blocking is correct."* Correct, and unusually disciplined — most systems that discover interleaving apply it everywhere.

**Summary: the pedagogy is in good shape and is not the problem.** Nearly everything below is execution, state, or plumbing. That is a much better place to be — and it means the fixes are less prose and more mechanism.

---

## Weaknesses, ranked

### W1 — The prompt grew again, and its own ledgers show the back half is not firing

v10 is **712 lines**, up from v9's 665. The token-budget critique dated 2026-08-13 recommended a hard **20 KB ceiling** with mandatory eviction. That was four days ago. v10 shipped larger.

**The 2026 evidence is now much stronger than the IFScale result the v9 critique relied on:**

- **Instruction Stacking Collapse** (arXiv 2608.02639) stacks 24 verifier-checked instructions, 1–20 at a time, on **Claude Sonnet 4.6**, GPT-5-mini and Gemini 2.5 Flash. Follow rate falls **~96% → as low as 20%**, non-linearly. Critically, the failures are **not random forgetting — they are reproducible pairwise conflicts** (a single "output JSON" constraint is jointly unsatisfiable with nine others). Hold that finding; W2 is exactly this.
- **SEQUOR** (arXiv 2605.06353) measures the multi-turn case, which is what a study session is. Even with **one stable constraint**, accuracy declines **~26% across 50 turns**. With **three simultaneous constraints, 38%**. When constraints are introduced sequentially, **>40%**.
- Primacy/recency: instruction quality begins degrading measurably around 60–70% context fill, and middle-of-context attention degrades with distance from *both* ends.

A study session is 40–80 turns carrying several dozen standing constraints. This is the worst case in both benchmarks simultaneously.

**Now the local evidence, which is decisive.** The quantum ledger's top-level keys are:

```
['exam_date', 'target', 'coverage', 'next_session', 'session_log', 'topics']
```

v10's required schema is `course`, `exam`, `exam_date`, `topics`, `exam_coverage`, `review_queue`, `next_session`, `session_log`. So:

| v10 requirement | Stated at | What the quantum ledger shows |
|---|---|---|
| `course`, `exam` fields | L97–98 | **absent entirely** |
| `exam_coverage` | L106 | renamed to `coverage` |
| **`review_queue`** | L110, L564–566 | **the key does not exist** — yet the whole spaced-retrieval spine reads and writes it |
| `current_rung` | L103 | `null` on all 18 topics |
| `status` ∈ {locked, unlocked, struggling, mastered} | L102 | Hamiltonian Dynamics = `"in_progress"` — **not a legal value** |
| `confidence` "required, not optional" | L123 | absent from every 2026-08-14/15/16 attempt |
| implementation intention | close step 18 | `"intention": "not collected this session"` |

And the sharpest one — two attempts are logged as:

```json
{"result": "unverified", "note": "reconciled at study-run close — tutor session not separately logged",
 "source": "study-run-close"}
```

The ledger is being **reconstructed after the fact** because the in-session write never happened. That is W6(c) leaving a fingerprint in the data.

The Computer Vision ledger is worse on the same axis: **35 attempts, `marks` logged on 0, `confidence` on 0** — despite *"Grade in marks, then convert"* being one of the three hard rules.

**The pattern matches the benchmarks precisely.** Rules stated early and exercised *every turn* — the retrieval gate, question labels, the ramp — fire reliably. Rules in the back half that fire *once per session* — the schema, the close protocol, confidence — do not. This is the multiplier weakness: every other item in this document is a rule, and rules at line 560 of a 712-line prompt have a measured tendency not to fire.

---

### W2 — v10 and `SKILL.md` now issue directly contradictory orders about turn shape, and `SKILL.md`'s own arbitration clause hands the win to the wrong one

**This is new in v10 and it is the sharpest self-inflicted problem in the system.**

v10's entire changelog is about the turn contract:

> *"A topic opening is one message: `[Problematic]` → hook → `[Probe]`. Not three messages."*
> *"Mark the Lesson's end in one line and **start the next Lesson in the same message**."*

`SKILL.md`, under the heading **"The most important rule: be atomic"**:

> *"Every turn does exactly one thing, then stops and waits for the user. One question, one station, one prompt — never orientation plus a review walk plus an exam question in the same message."*
> *"If you catch yourself typing 'and then', that 'and then' is the next turn."*

These are not in tension. They are opposites. And `SKILL.md` Step 2 adjudicates against v10:

> *"The method prompt owns teaching. **This skill owns the session shell — startup order, the atomic rhythm**, and executing the board."*

The atomic rhythm is explicitly the skill's to own, and it forbids exactly what v10's headline fix mandates. Instruction Stacking Collapse's central finding is that degradation is driven by **structured, reproducible pairwise conflicts** rather than random drift. This is a textbook instance, sitting between the two documents that govern every session. Whichever way it resolves on a given turn, one document's fix silently dies — and there is no way to tell from the outside which one lost.

Secondary overlaps in the same two files: two planners with a precedence rule (`next_session` in `progress.json` vs `active_run` in `sessions.json`), two statements of the opening turn, two statements of the retrieval gate, two caps on exam questions per session.

---

### W3 — `mastered` is still awarded at peak performance, and the banner is still the entire motivation system

Unchanged from v9. A topic can go from `[Problematic]` to `mastered` in one sitting, minutes after first contact, and immediately book its marks into the banner — which v10 designates, in writing, as *"the motivation system."*

Soderstrom & Bjork (2015) is precisely about why this fails: **performance during acquisition is an unreliable index of learning**, and manipulations that boost immediate performance frequently *reduce* long-term retention. A same-session cold pass measures performance at the moment of maximum contextual support — same conversation, same vocabulary primed twenty minutes earlier, same worked example still on screen.

Rawson & Dunlosky's successive-relearning programme gives the constructive version, and one finding is directly load-bearing here: **pushing to a higher criterion *within* the first session does not persist** — subsequent spaced relearning overrides the benefit of initial overlearning. So the fix is not a stricter in-session bar. It is *more spaced passes*. v10 does session one and calls it mastery.

**The ledgers say something more nuanced than v9's critique did, and it deserves credit.** The quantum session log shows:

```
2026-08-14: 2 spaced reviews both FAILed and cost their topics' mastery
            (Tensor Products — tensor-order reversal, 74.5 marks; Quantum Measurement — omitted po…)
2026-08-16: Tensor Products and Quantum Measurement both re-mastered on spaced review
            (105 marks re-secured, coverage 123.0 → 228.0, 25.0% → 46.3%)
```

**The demotion path runs.** Delayed retrieval caught two inflated masteries, cost them honestly, and they were re-earned two days later. That is the system working, and it is a real improvement over anything the CV run produced.

What is still missing is a *distinction*: a topic that has survived one delayed retrieval and a topic that has never been retrieved since the day it was learned currently occupy the same status and count identically toward the banner. Computer Vision is the failure case — **78.9% secured, last retrieval 49 days ago, exam in 9 days.** That number is not a lie the system is telling the user; it is a lie the system is telling *itself*, and it then plans triage, ROI ordering, and review selection from it.

v10 already knows this. Its own difficulty controller says *"If I am passing everything first-try across a whole topic, that is **your** calibration failure, not evidence I'm a genius."* CV: 30 PASS / 5 FAIL, eight same-day masteries. The self-check exists and has never fired.

---

### W4 — Review scheduling has no throttle, no exam-proximity compression, and the reversion rule is a live landmine

v10's entire spaced-retrieval policy is *"Pull 1–2 items from `review_queue` at the start of a Lesson"* plus SM-2. Three problems.

**(a) Arithmetic.** CV's queue holds 8 items, every one due between 2026-06-30 and 2026-07-02 — **47 days overdue**. At 1–2 per Lesson with each cleared item re-entering the queue, it cannot drain. `/study-run`'s own documentation names this outcome — *"boards that are 100% review, session after session… the fastest way to abandon a system"* — and caps review at 50% of budget. **The tutor prompt has no equivalent rule, and the tutor is what actually runs.** CV's stored `next_session` reads *"clear the 3 oldest overdue items"* — three of eight, with the other five decaying. That is the board you don't come back to, and empirically, the user didn't.

**(b) The landmine, still present verbatim at L564–565.** *"Quiz me at full exam difficulty. If I fail, send that topic's final rung back to `unlocked`."* After a 49-day gap, failure is the expected outcome, not the exception. Run that rule honestly across CV's backlog and you revert most of 8 topics to `unlocked`, collapsing the banner from 78.9% toward single digits — **nine days before the exam.** Individually defensible, catastrophic in aggregate, and nothing in the prompt notices the difference between *forgot* and *never learned*.

**(c) Wrong scheduling curve for a dated exam.** Cepeda et al. (2008, N > 1,350) found the optimal inter-study gap is roughly **10–20% of the retention interval** — about 20% for delays of a few weeks, falling to ~5% at a year. Here the retention interval is *days to exam*: fixed, shrinking, and known. At 9 days out that implies **1–2 day gaps**, converging on daily review in the final week. Generic SM-2 ease-driven growth is tuned for indefinite retention and is simply the wrong curve. v10 clamps `next_due` to `exam_date − 1` but never **compresses**.

The good news on the fix: **abandoning SM-2's expanding schedule costs nothing measurable.** Latimier et al. (2021) found expanding vs. uniform intervals differ by **g = 0.034, non-significant**. The expanding curve was never buying anything here.

---

### W5 — Nothing in the system measures itself against the actual exam

Every number v10 produces is generated by the model that taught the material, graded against a rubric it wrote, on a question it chose, one topic at a time, untimed, mid-conversation, immediately after teaching. The `[Exam question]` uses real exemplars — good — but it is not the criterion task.

The real exam is cumulative, timed, closed-book, and mixes topics without labelling them. Dunlosky et al. (2013) rate **practice testing** and **distributed practice** as the only two of ten assessed techniques earning *high* utility, partly for generality across criterion tasks. A cumulative timed past paper is both at once, in the criterion format. `parsed/` is already full of real past papers, so assembling one is nearly free.

v10's *"under 4 days out: review and past-paper exemplars only"* is not a graded, timed, cumulative sitting — and four days is too late to *discover* that 78.9% was 55%. **This is the only intervention that could catch W3 before the exam does.**

---

### W6 — The one-command promise is 90% built and not wired; the user's proposed feature already exists

The stated ideal — sit down, type `/continue-study-session`, study — is v10's own prime directive. Three seams break it.

**(a) Two planners.** `next_session` (progress.json, tutor-owned) vs `active_run` (sessions.json, `/study-run`-owned), arbitrated by `SKILL.md` Step 4. Two authorities for "what am I studying today."

**(b) Second command, partially fixed.** Quantum's `sessions.json` now shows **8 sessions logged** with real calibration (`k_rung: 0.759`, `n_sessions: 8`) — so `/study-run close` *is* being run there, and the v9 critique's "0/8 closes" claim no longer holds for quantum. **Computer Vision's still reads 0 sessions.** The step gets taken on the course being actively studied and not otherwise.

**(c) Nothing survives a mid-session exit, and that is the common exit.** All persistence lives in close steps 16–19. Sessions end with a closed laptop, not a ceremony. The `"result": "unverified", "source": "study-run-close"` entries are that failure, recorded in the data.

**On the user's proposal — "have the tutor create one lesson, then create the next based on performance on that one":** this is already the design, in three places. The Lesson is a bounded unit (*"never plan more than one Lesson ahead out loud — the next Lesson depends on how this one went; that's the point"*), `next_session` carries it forward, and the difficulty controller adjusts within it. **It is not a missing feature. It is a feature that doesn't persist**, because the block that carries it is written in a close protocol that often doesn't run. The fix is P7, not new pedagogy.

---

### W7 — One supportive thing is missing, and it would not be sugarcoating

v10 correctly bans praise inflation, effort commentary, and manufactured urgency. It has no line for **naming difficulty as a property of the method rather than a verdict on the learner**.

Bjork's desirable-difficulties framing — retrieval that feels hard is the condition under which durable encoding happens, and fluency during study is the misleading signal — is *true*, *task-directed* (so it survives the Kluger & DeNisi constraint), and about to become load-bearing: the fixes below will produce several deliberately unpleasant sessions.

Saying *"that should have felt hard — retrieval at this spacing is where the encoding happens, and it's why it'll still be there in two weeks"* is not softening a verdict. It is an accurate statement about the measurement, and it is the difference between a hard session reading as *progress* and reading as *evidence you're behind*.

---

### W8 (mechanical) — State hygiene, unchanged since the v9 critique

- Quantum's ledger is at `Courses/Introduction_to_quantum_computers/tutor/progress.json`, **outside its Exam folder**, violating v10 L68 (*"All study state lives inside the Exam folder"*). v10's own resolver would not find it by the documented rule.
- `.study-run.json` sits at **Course level**, not project root where both skills look.
- Two live Exams means the multi-Exam disambiguation question fires **every single session** — permitted, but it is a decision at the exact moment the contract promises none. The information needed to answer it (nearest exam date) is in the ledgers.

---

## Triage — this week only, before either exam

Not the plan. Two manual actions, roughly 40 minutes total, that do not touch any prompt.

**T1 — Neutralise the reversion landmine by hand, today (2 minutes).** Before the next CV session, edit L564–565 of v10 so a first post-gap review failure demotes to a re-review at 1 day rather than resetting the ramp. One honest CV review session under the current rule wipes the banner nine days out. This is a one-line edit, not a refactor.

**T2 — Run one cumulative timed mock per exam, manually, now.** Assemble a section from `parsed/*.json`, closed-book, timed, graded against the real mark scheme, no hints. Quantum first — it is three days out with 8 of 18 topics never opened, and the difference between "revise everything" and "revise these four" is worth an hour. Then CV, which is the more important case: 78.9% claimed with 49 days of no retrieval is a number nobody should walk into an exam trusting.

- **Why now, despite the timing note:** T2 is not a system change, it is the highest-value *study activity* available under Dunlosky's ranking, and it is the only thing that can tell you where you actually stand while there is still time to act.
- **Argument against:** a bad mock three days out is demoralising. **Response:** a bad exam is worse, and at 3 days the mock's ROI-reordering output is still actionable. Report it flat, no padding.

---

## The plan — after 2026-08-26

Ordered by expected value against the stated goals. Each argues both sides, because three of these are genuine trade-offs.

### P1 — Move state-writing out of the prompt and into a tool *(fixes W1; unblocks W3, W4, W6)*

Add `pipeline/ledger.py` with a verb CLI the tutor calls instead of hand-editing JSON:

```
ledger resolve                              → active exam, paths, capability flags (one JSON blob)
ledger open                                 → banner + next_session + due reviews, computed
ledger attempt --topic T --rung 2 --result PASS --marks 7/8 --confidence high --note "…"
ledger master --topic T                     → status, coverage w/ dedup, review scheduling, unlock
ledger review --topic T --result FAIL       → schedule update, exam-date clamp, compression
ledger close --next-topic T --why "…" --est 30 --intention "Tue 09:00 library"
ledger check                                → schema + invariant validation, non-zero exit on drift
```

Then **delete the corresponding ~150 lines of schema prose from v10** and replace them with the verb list.

- **Why:** it is the only fix that addresses W1 structurally rather than by asking the model to try harder. `--confidence` becomes a *required argument*: the failure mode changes from "silently omitted on every attempt" to "the command errors out." Coverage de-duplication, interval arithmetic and the exam-date clamp become code that is right every time rather than prose re-derived at turn 40 — which SEQUOR says is exactly when it stops being re-derived. `ledger check` would have caught all six schema violations in the quantum ledger, including `"in_progress"` and the missing `review_queue`.
- **Why it serves the UX goal:** `ledger open` collapses v10's entire silent step 1 — resolve, read ledger, read notes, read taxonomy, read exemplars, read ROI, compute banner — into one call that cannot half-fail. Session start gets faster and cheaper.
- **Argument against:** v10's header says it can be pasted into Cowork with nothing but file access, and a Python dependency breaks that. **Response:** keep the prose schema as an appendix labelled *"fallback when no tooling is available"*, and have the prompt prefer the CLI when `pipeline/ledger.py` exists. Every session in the logs happened in Claude Code, which is the path that gets the reliable version.
- **Argument against #2:** more moving parts to maintain. **Response:** `ledger check` in a pre-commit hook is the answer. Nothing validates the ledgers today and both are already malformed — one has drifted to a schema the prompt cannot read.
- **Cost:** ~250 lines of Python, one afternoon.

**Recommendation: implement. Highest leverage item here.**

---

### P2 — Resolve the v10 ↔ `SKILL.md` conflict by deleting the overlap, not by adding an arbitration rule *(fixes W2)*

`SKILL.md` shrinks to bootstrap only: resolve the project, load the highest-versioned method prompt, read state, hand off. **Delete its "be atomic" section, its opening-turn spec, its retrieval-gate restatement, and its question caps.** The turn contract then exists in exactly one file.

Then reconcile the underlying question honestly, because both documents are half right:

- **Framing components never terminate a turn** (v10 is right — a `[Problematic]` with no question attached is a dead turn).
- **Two graded questions never share a turn** (`SKILL.md` is right — stacking retrieval demands means the second is answered carelessly).

Both survive as one rule: *a message may contain any amount of framing but exactly one thing to respond to, and must contain one.*

- **Why:** Instruction Stacking Collapse shows degradation is driven by reproducible pairwise conflicts, not random drift. This is the cleanest identified conflict in the system, it sits between the two documents that govern every session, and no arbitration clause can fix it — a clause that says "the skill owns the rhythm" only guarantees that v10's headline fix is the one that dies.
- **Argument against:** `SKILL.md` needs *some* rhythm rule or a fresh session has no shape before the method prompt loads. **Response:** it has one — "load the method prompt and adopt it as your system prompt" is Step 2. The shape arrives with the prompt. Nothing needs to be said twice.
- **Argument against #2:** deleting from a working skill risks regression. **Response:** it is not working. The conflict is live today and resolves nondeterministically.
- **Cost:** ~90 lines deleted, an hour of care.

**Recommendation: implement, in the same commit as P3.**

---

### P3 — Split v10 into a resident core plus `tutor/reference/`, and enforce the ceiling *(fixes W1)*

The 2026-08-13 token-budget critique already specified this and it was not adopted; v10 grew instead. Target: **resident core ≤ 250 lines**, with everything situational in `tutor/reference/<topic>.md`, each referenced from the core by one line naming its trigger.

Move out: folder structure, active-Exam resolution, path resolution, file schemas (or delete under P1), graceful degradation, first-contact detail, the full adapter table, the hypercorrection routing table, narrative framing, the problematic's structure (already duplicated in `PROBLEMATIC_SKILL_v2.md` — keep the skill, cut the prompt section to two lines), visual artifacts, concept maps, coverage math, **and the entire loci add-on** (913 tokens describing a feature that is off).

Keep resident: persona, prime directive, vocabulary, the three hard rules, question labels, the turn contract, the Lesson, the difficulty controller, the session protocol, write ownership, tone. Repeat the three hard rules verbatim at the bottom — primacy *and* recency, ~80 tokens, the cheapest available defence against the 26–40% multi-turn decay SEQUOR measures.

Add to whatever governs prompt revisions:

> `TUTOR_SYSTEM_PROMPT_v{N}.md` has a hard ceiling of 20 KB. A change that would exceed it must evict or relocate something to `tutor/reference/` **in the same commit**.

- **Why:** the growth curve is 5,988 B → 40 KB over ten versions with **every single step positive and nothing ever removed**. Without a ceiling, v13 is back where v10 is now. The primacy evidence says the rules being dropped are exactly the ones in the back half, and that is where the ledger failures are concentrated.
- **Argument against:** reordering a carefully argued prompt risks breaking a subtle dependency, and no-op edits to working prompts are how good prompts rot. **Response:** do it after P1 lands, in one pass, with the three critique docs as the check. And note the asymmetry — this is not a rewrite, it is a *move*; every rule still exists, it just arrives when it applies.
- **Argument against #2:** duplicating the hard rules top and bottom is redundant. **Response:** deliberate. Redundancy is the cheapest known mitigation for constraint-count degradation.

**Recommendation: implement, after P1.**

---

### P4 — Split `mastered` into `passed` → `retained`, and make the banner tell the truth *(fixes W3)*

**(a) Two-stage mastery.**
- `passed` — cleared the cold `[Exam question]`. Awarded exactly as today: same moment, same unlock of the next topic, same concept map. **Nothing about the ramp changes.**
- `retained` — cleared **one further spaced retrieval on a later calendar day** at exam difficulty. Only then do the marks count as secured.
- Two spaced confirmations when the exam is > 21 days out; one when closer. Rawson & Dunlosky prescribe three relearnings — but their own finding, that criterion pushed *within* a session doesn't carry, argues for spending a limited budget on more spaced passes rather than a stricter bar.

**(b) The banner splits.**

```
📊 Computer Vision · final_26_08_2026 — 71/175 retained (41%) · 67 provisional · 9 days to exam
```

- **Why:** the number *is* the motivation system, and SDT says competence support only works if the competence signal is credible. A 78.9% you privately suspect is inflated has already stopped motivating — 49 days of not returning is roughly what that looks like. It also converts W4's backlog from a chore into the mechanism that moves the headline number: **review becomes the thing that banks marks**, which is precisely the incentive you want in the final fortnight. The quantum log already demonstrates the mechanic working (`coverage 123.0 → 228.0` on a review day); this just makes it the rule.
- **Argument against — and it is real:** the number drops overnight. **Response:** it is also the single most useful fact available, and the alternative is discovering it in the exam hall. Frame it once, explicitly, as recalibration rather than loss — *"nothing was taken away; 67 marks are unconfirmed because they haven't been retrieved since June"* — and let the first three sessions convert provisional → retained so it moves back up fast. That recovery is a credible competence signal in a way the original number is not.
- **Argument against #2:** delayed mastery could stall forward progress. **Response:** unlocking still happens at `passed`, so the ramp is never blocked. Only *coverage accounting* waits.

**Recommendation: implement, and do the recalibration out loud rather than silently.**

---

### P5 — Deadline-anchored review: proportional budget, triage pass, graded demotion, compressed intervals *(fixes W4)*

Four rules replacing *"pull 1–2 items"*:

1. **Proportional budget, both ends.** Review takes **at most 50%** of a Lesson and **at least one item** whenever anything is due. Mirrors `/study-run`'s existing cap so the two stop disagreeing, and guarantees forward progress always exists.
2. **Queue-collapse triage.** When > 4 items are overdue, do not walk them one at a time. Run one **mixed rapid-recall pass** — one core question per topic, 3–4 topics in a block, unlabelled as to which is which — and reschedule each from its result. This is the one context where interleaving's evidence is strongest (genuinely confusable, all decayed), and it produces triage data on the whole backlog in one Lesson rather than four.
3. **Graded demotion, never silent reversion.** First failure after a gap → `retained` drops to `passed`, requeue at 1 day. Only a **second** consecutive failure demotes to `unlocked` and reopens the ramp. One failure after six weeks measures the gap, not the knowledge; only the second attempt separates forgetting from never-having-learned.
4. **Compress toward the deadline.** Multiply the computed interval by `min(1, days_remaining / 30)` before the clamp. Cepeda's 10–20% ratio against a shrinking retention interval implies 1–2 day gaps in the final week regardless of what ease says.

- **Why:** W4 is the mechanism that ended the CV run — a board that is 100% overdue review is the board you don't come back to, which is exactly the user's stated failure mode. And rule 3 is a live hazard sitting in the prompt right now.
- **Argument against:** rule 2 trades depth for coverage, and rapid recall is a weaker retrieval event than a full exam question. **Response:** accepted deliberately. Against a cold backlog and a short horizon, knowing *which four of eight topics decayed* is worth more than one deep pass on one of them. Follow the triage with full exam questions on the failures only.
- **Argument against #2:** rule 4 abandons SM-2. **Response:** it abandons nothing of value — expanding vs. uniform schedules differ by g = 0.034, non-significant (Latimier et al. 2021). SM-2's curve is tuned for indefinite retention; the retention interval here is a known date.

**Recommendation: implement. Rule 3 is urgent independently — see T1.**

---

### P6 — Add a Mock Exam unit *(fixes W5)*

A bounded unit alongside the Lesson: **one timed, closed-book, cumulative section assembled from `parsed/*.json`**, graded against the real mark scheme, no hints, no scaffolding, no narrative wrapper.

- **Trigger:** ~14 days and ~5 days out, and on demand.
- **Output is authoritative.** Per-topic marks **overwrite** the coverage estimate for the topics covered; failures re-rank ROI for the remaining days.
- Report flat: marks per section, the three biggest losses, one line on what changes.

- **Why:** it is the only measurement in the system not produced by the model that taught the material, and it is the ground truth for the number P4 is about. Practice testing and distributed practice are Dunlosky's two highest-utility techniques and a cumulative timed paper is both, in the criterion format. The past papers are already parsed.
- **Argument against:** it costs a session and can be demoralising. **Response:** that is the argument for T−14 rather than T−4 — there is still time to act. Let it *replace* a Lesson rather than supplement one, so it adds no net load.
- **Argument against #2:** overlaps the boss-check. **Response:** the boss-check is per-topic and mid-conversation. This is cumulative, timed and mixed — a different measurement of a different thing.

**Recommendation: implement.**

---

### P7 — One command: fold planning and closing into `/continue-study-session`, and persist incrementally *(fixes W6 — the headline UX requirement)*

**(a) Collapse the invocation surface to one.** `/continue-study-session` becomes the only command typed. It calls the planner internally, silently, before the banner, and runs the close automatically when the Lesson ends. `/study-run` survives as an explicit override for *"I have exactly 90 minutes and want to see the board"* — a power-user entry point, not part of the loop.

**(b) Persist after every graded answer, not at close.** `ledger attempt` writes immediately; `ledger master` writes immediately; **`next_session` is recomputed after every rung**, so it is always current. Closing stops being an event that must happen and becomes a state that is already true.

**(c) Keep exactly one thing at the end:** the implementation intention. Gollwitzer & Sheeran report d = 0.65 overall and **d = 0.61 specifically for failures to get started** — the best-evidenced intervention in the system for the exact problem the user described. One line, asked once, never nagged.

- **Why:** this is the item that most directly matches what was asked for. It also makes the *actual* exit path — closing the laptop — a first-class case instead of data loss, which is what the two `"unverified"` reconciliation records in the quantum ledger are. And it makes the user's "one lesson, then the next from performance" idea reliable: that loop already exists in the design; incremental persistence is what makes it survive to the next session.
- **Argument against:** merging planner and tutor loses a clean separation of concerns, and `/study-run`'s calibration loop is genuinely well-designed — quantum's `k_rung: 0.759` over 8 sessions is real data. **Response:** keep every bit of that logic, drop the second invocation. The planner becomes a function the tutor calls rather than a peer skill with a precedence contract. Nothing in the cost model changes — it just needs to be *called*, which on CV it never was.
- **Argument against #2:** auto-closing risks writing a session record when you meant to continue. **Response:** incremental writes make the close a no-op summary rather than a commit point. There is no state to lose because none was ever held.

**Recommendation: implement.**

---

### P8 — One line normalising difficulty *(fixes W7)*

Add to § *Tone*, under the non-negotiables: **difficulty may be named as a property of the method, never as a property of the learner.**

- Permitted: *"that should have felt hard — retrieval at this spacing is where the encoding happens, and it's why it'll still be there in two weeks."*
- Still banned: anything about effort, character, consistency, or gaps between sessions.

- **Why:** true (Bjork), task-directed (survives Kluger & DeNisi), and load-bearing for the several deliberately unpleasant sessions P4 and P5 will produce. Without it, *"your retained score is 41%"* reads as a verdict on the person rather than a measurement of the schedule.
- **Argument against:** it is one step from the encouragement padding the prompt correctly bans. **Response:** bound it explicitly — a statement about the *method*, never the *learner*, never attached to a verdict. The same boundary § *Tone* already draws for errors, applied to difficulty.
- **Cost:** three lines.

**Recommendation: implement, tightly scoped.**

---

### P9 — State hygiene *(fixes W8)*

Mechanical, ~20 minutes. Move `Courses/Introduction_to_quantum_computers/tutor/{progress,sessions}.json` into `final_20_08_2026/`; move `.study-run.json` to project root; add `ledger check` to a pre-commit hook. Change multi-Exam disambiguation from "always ask" to **"default to the nearest exam date, name it in the banner, let the escape hatch redirect."**

- **Why:** each produces one confusing session, and the disambiguation question fires every session against a contract that promises zero decisions.
- **Argument against:** defaulting could silently pick the wrong exam. **Response:** the banner names Course and Exam on line 1 — v10 already says that naming exists precisely as the check — and redirecting costs one sentence.

**Recommendation: do it first; it is free.**

---

## Summary

| # | Weakness | Fix | Priority | Evidence | Verdict |
|---|---|---|---|---|---|
| W2 | v10 and `SKILL.md` give opposite orders on turn shape | Delete the overlap; one turn rule | **P0** | Instruction Stacking Collapse + the two files | **Implement** |
| W1 | 712 lines; ledger drifted to an unreadable schema | Ledger CLI + core/reference split + ceiling | **P0** | SEQUOR, ISC 2026 + **both ledgers** | **Implement** |
| W4 | Queue 47 days overdue; reversion landmine; wrong curve | Proportional budget · triage · graded demotion · compression | **P0** | Cepeda 2008; Latimier 2021 + CV queue | **Implement**; rule 3 urgent |
| W3 | `mastered` = same-session performance; 78.9% after 49 idle days | `passed` → `retained`; split banner | **P0** | Soderstrom & Bjork; Rawson & Dunlosky | **Implement**, recalibrate openly |
| W6 | Two planners; nothing survives a mid-session exit | One command · incremental persistence | **P0** | Design + the `"unverified"` records | **Implement** |
| W5 | No cumulative, timed, externally-anchored measurement | Mock Exam unit at T−14 and T−5 | P1 | Dunlosky et al. 2013 | **Implement**; run one manually now |
| W7 | No honest normalisation of difficulty | One bounded line in § *Tone* | P2 | Bjork | **Implement**, tightly scoped |
| W8 | Ledger outside its Exam folder; `.study-run.json` misplaced | Hygiene pass + `ledger check` | P2 | Contract violations | **Do first** |

**Net effect on the prompt: substantially shorter.** P1 and P3 remove ~350 lines; P2 removes ~90 from `SKILL.md`; P4, P5, P6, P8 add ~70. The v8 critique said the right direction was shorter, the v9 critique repeated it, the token-budget critique set a number — and the prompt has grown at every step. **The pedagogy is sound and the failures are executional, which means the correct move is less prose and more mechanism.**

**One thing that is not on this list:** nothing here weakens the retrieval-first gate. Bastani et al. is the strongest external result in this literature and it says the gate is the difference between a tutor that helps and one that measurably harms unaided performance. It stays absolute from rung 1.

---

## Sources

**Learning science**

- Soderstrom & Bjork (2015), *Learning Versus Performance: An Integrative Review*, Perspectives on Psychological Science 10(2), 176–199 — https://journals.sagepub.com/doi/abs/10.1177/1745691615569000
- Rawson & Dunlosky (2022), *Successive Relearning: An Underexplored but Potent Technique*, Current Directions in Psychological Science — https://journals.sagepub.com/doi/full/10.1177/09637214221100484
- Rawson & Dunlosky (2013), *The Power of Successive Relearning: Improving Performance on Course Exams and Long-Term Retention*, JEP: Applied — https://www.researchgate.net/publication/258845409
- Rawson & Dunlosky (2016), *Does relearning override the effects of initial learning criterion?* — https://pubmed.ncbi.nlm.nih.gov/27027887/
- Cepeda, Vul, Rohrer, Wixted & Pashler (2008), *Spacing Effects in Learning: A Temporal Ridgeline of Optimal Retention*, Psychological Science 19, 1095–1102 — https://laplab.ucsd.edu/articles/Cepeda%20et%20al%202008_psychsci.pdf
- Cepeda et al. (2006), *Distributed Practice in Verbal Recall Tasks: A Review and Quantitative Synthesis* — https://augmentingcognition.com/assets/Cepeda2006.pdf
- Latimier, Peyre & Ramus (2021), *A Meta-Analytic Review of the Benefit of Spacing out Retrieval Practice Episodes*, Educational Psychology Review — http://www.lscp.net/persons/ramus/docs/EPR20.pdf
- Dunlosky, Rawson, Marsh, Nathan & Willingham (2013), *Improving Students' Learning With Effective Learning Techniques*, Psychological Science in the Public Interest 14(1), 4–58 — https://journals.sagepub.com/doi/abs/10.1177/1529100612453266
- Wisniewski, Zierer & Hattie (2020), *The Power of Feedback Revisited: A Meta-Analysis of Educational Feedback Research*, Frontiers in Psychology 10, 3087 — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6987456/
- Richland, Kornell & Kao (2009), *The Pretesting Effect: Do Unsuccessful Retrieval Attempts Enhance Learning?* — https://learninglab.uchicago.edu/Pre-Testing_files/RichlandKornellKao.pdf
- Marin-Garcia et al. (2025), *The Pretesting Effect: Exploring the Impact of Feedback and Final Test Timing*, Journal of Cognition — https://pmc.ncbi.nlm.nih.gov/articles/PMC12292081/
- Kurnaz (2025), *A Meta-Analysis of Gamification's Impact on Student Motivation in K-12 Education*, Psychology in the Schools — https://onlinelibrary.wiley.com/doi/10.1002/pits.70056

**AI tutoring**

- Bastani, Bastani, Sungu, Ge, Kabakcı & Mariman (2025), *Generative AI without guardrails can harm learning: Evidence from high school mathematics*, PNAS — https://www.pnas.org/doi/10.1073/pnas.2422633122 · full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/ · **correction (unread, 403):** https://www.pnas.org/doi/10.1073/pnas.2518204122
- Kestin et al. (2025), *AI Tutoring Outperforms Active Learning*, Scientific Reports — https://projects.panickssery.com/docs/kestin-2024-ai_tutoring_harvard_physics.pdf
- *Do intelligent tutoring systems benefit K-12 students? A meta-analysis* (2025), arXiv:2511.04997 — https://arxiv.org/abs/2511.04997
- Ma, Adesope, Nesbit & Liu (2014), *Intelligent Tutoring Systems and Learning Outcomes: A Meta-Analysis*, JEP — https://www.apa.org/pubs/journals/features/edu-a0037123.pdf

**LLM instruction-following (preprints — see Source validation)**

- *Instruction Stacking Collapse: A Benchmark and the Capability-Dependent Value of Prompt Compilation* (2026), arXiv:2608.02639 — https://arxiv.org/abs/2608.02639
- *SEQUOR: A Multi-Turn Benchmark for Realistic Constraint Following* (2026), arXiv:2605.06353 — https://arxiv.org/pdf/2605.06353
- Jaroslawicz et al. (2025), *How Many Instructions Can LLMs Follow At Once?* (IFScale), arXiv:2507.11538 — https://arxiv.org/pdf/2507.11538

**Carried over from earlier critiques:** VanLehn (2011); Kluger & DeNisi (1996); Butterfield & Metcalfe; Gollwitzer & Sheeran (2006); Deci, Koestner & Ryan (1999); Sweller & Cooper; Renkl; Kulik et al.; Rohrer; Brunmair & Richter (2019). See `critique-tutor-learning-science.md` and `critique-tutor-v9-learning-science.md`.
