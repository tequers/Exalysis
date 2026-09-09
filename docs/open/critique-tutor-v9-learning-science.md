# Critique: Tutor v9 vs. Learning Science (and vs. its own logs)

**Status: open.** Reviewed `tutor/TUTOR_SYSTEM_PROMPT_v9.md`, `tutor/SKILL.md` (`/continue-study-session`), and `tutor/STUDY_RUN_SKILL_v2.md` on 2026-08-11.

Companion to `critique-tutor-learning-science.md`, which reviewed v8 and whose P0/P1/P2 items all shipped in v9. **That doc is not re-litigated here.** Its conclusions still hold; this one starts from v9 as the baseline.

**What is different about this review:** the v8 critique was argued purely from literature. This one also reads the two live ledgers — `Courses/Computer Vision/final_26_08_2026/progress.json` (7 sessions, 35 attempts, Jun 23–29) and `Courses/Introduction_to_quantum_computers/tutor/progress.json` (v9's **first real run**, today). Several weaknesses below are not predictions. They are already in the data.

Goal frame, unchanged: **effortless to start · honest without sugarcoating · engaging · makes the user return.** One command, zero decisions, then pure study.

---

## Source validation note

Every empirical claim below is tied to a primary paper (meta-analysis or original study), listed in *Sources*. Honest gaps, stated up front rather than papered over:

- **Kestin et al. (2025)** — I have the abstract, the Harvard Gazette write-up, and the preprint PDF listing, not the full published *Scientific Reports* text. The headline ("more than twice the learning gain in less time vs. active learning, N = 194, within-subject crossover") is consistent across all three, but I have not verified the effect size myself. I use it only as *directional* support that a well-constrained LLM tutor works — which is a claim this project has already bet on regardless.
- **IFScale / "How many instructions can LLMs follow at once?" (arXiv 2507.11538)** — the fetched PDF gave me the qualitative findings (monotonic degradation from 10→500 instructions; clear primacy bias toward earlier instructions) but not clean per-count accuracy numbers. So W1 below rests on *direction plus your own logs*, not on a retrieved accuracy curve. The logs are the stronger evidence anyway.
- **Rawson & Dunlosky** — the prescriptive "3 correct recalls, then relearn 3× at widely spaced intervals" is their own stated recommendation. There is no meta-analysis of successive relearning specifically; it is a coherent programme of individual studies, several classroom-based. Treat the *direction* as solid and the *number 3* as a reasonable default, not a constant of nature.

Where the evidence is genuinely mixed I say so.

---

## What v9 gets right (do not touch these)

Everything the v8 critique praised survived, and v9 added four things worth naming:

1. **First contact is now correct.** `[Problematic]` → hook → `[Probe]` (ungraded) → `[Worked example]` (faded) → `[Rung 1]` is a textbook-accurate resolution of the pretesting/worked-example tension. The guardrails against it becoming a loophole ("if rung 1 can be answered by copying the worked example, you wrote rung 1 wrong") are the part most designs forget.

2. **The no-fatal-conceptual-error clause is better than the percentage it accompanies.** `"84% — but the invariant is inverted, so that's a FAIL regardless"` is a genuinely superior grading primitive to any threshold. It is also adapter-relative (§ *Discipline adapters* fixes what "fatal" means per family), which is the detail that makes it work across proof / trace / code / prose.

3. **The retrieval-first gate is the single most important rule in the file, and the external evidence for it got stronger this year.** Bastani et al. (PNAS 2025) ran ~1,000 high-school students: unguarded GPT-4 access improved performance *during practice by 48%* and then **reduced unaided exam grades by 17%** versus never having access. A guardrailed tutor version — hints only, no full solutions — eliminated the harm. That is the exact failure mode this prompt's gate exists to prevent, now measured. The gate is not pedantry; it is the difference between the two arms of that experiment.

4. **The motivation section is right in an unfashionable way.** Refusing streaks/XP and betting entirely on visible competence is correct per the SDT and Deci et al. evidence, and most systems get this wrong. **But it depends completely on the competence signal being true** — which is exactly what W2 is about.

5. **Task-directed tone, adapters, discrimination sets, the escape hatch** — all shipped as specified, all still well-founded.

The pedagogy is in good shape. **Almost every problem below is an execution, state, or plumbing problem, not a teaching-theory problem.** That is a much better place to be, and it changes what the fixes look like: less prose, more mechanism.

---

## Weaknesses, ranked

### W1 — The rules are not being executed, and the prompt's own size is the likeliest cause *(biggest — it gates everything else)*

v9 is **665 lines / 58 KB of hard rules**. `/continue-study-session` adds another 229 lines that also claim governing authority over the session shell. That is ~900 lines of simultaneous constraints held across a multi-hour, many-turn conversation.

**Direct evidence from v9's first real run** (quantum, today, 7 attempts):

| v9 requirement | Where stated | What the ledger shows |
|---|---|---|
| `confidence` is "**required, not optional**" / "**mandatory**" | L119, L329, step 10 | `"confidence": "not_collected"` on **5 of 7 attempts** |
| `course`, `exam` fields | L93–94 schema | both `null` |
| `session_log` one-liner | close step 16 | `null` |
| `review_queue` with SM-2 fields on mastery | L519, step 13 | `null` — **two topics were mastered today and neither was scheduled** |
| `next_session` block, "**not optional**" | L588, step 17 | `null` |
| `current_rung` | L99 schema | `null` |

Six required behaviours, all skipped, on the run that was supposed to demonstrate them. And note *where they live in the file*: the confidence rule at L329, the close protocol at L584–590 — the back half. The IFScale work finds instruction-following degrades non-linearly with constraint count and shows a **primacy bias: earlier instructions are followed, later ones are dropped first**. Your losses are concentrated exactly where that predicts.

The Computer Vision ledger shows the same thing under v8: 35 attempts, **`note` present on 3, `marks` on 0, `confidence` on 0**.

This is the biggest weakness because it is a multiplier. Every other item in this document is a rule, and rules at line 500 of a 665-line prompt have a measured tendency not to fire. **Fixing the pedagogy without fixing execution buys nothing.**

---

### W2 — `mastered` is awarded at peak performance, in the same sitting as first contact. The coverage banner is therefore not measuring what it claims

This is the pedagogical headline.

v9 marks a topic `mastered` the moment it clears one cold `[Exam question]` — potentially minutes after the `[Problematic]` that introduced it. Then `exam_coverage` books the marks, the banner prints them, and **that number is the entire motivation system** (§ *Motivation*: "the coverage banner… **is** the motivation system").

Soderstrom & Bjork's (2015) integrative review is precisely about why this fails: **performance during acquisition is an unreliable index of learning**, and manipulations that boost immediate performance frequently *reduce* long-term retention. A same-session cold pass measures performance at the moment of maximum contextual support — same conversation, same worked example, same vocabulary primed twenty minutes earlier.

Rawson & Dunlosky's successive-relearning programme gives the constructive version: durability comes from **retrieval to criterion repeated across multiple spaced sessions**, and — the sharp finding — pushing to a *higher* criterion within the first session does **not** persist across relearning sessions. Their prescription is ~3 correct recalls initially, then relearning ~3 times at widely spaced intervals. **v9 does session one and calls it mastery.**

**What your ledger says.** Computer Vision, right now:

- `mastered_total_marks: 138 / 175` → **the banner reads 78.9% secured.**
- 8 of 10 topics mastered. **Every one reached mastery on the same calendar day it was opened** (Image Filtering rungs 1–3 all on 2026-06-23; Feature Detection, 4 rungs, same day).
- 30 PASS / 5 FAIL across all attempts.
- **Last retrieval on any topic: 2026-06-29 — 43 days ago.** Exam is 2026-08-26, 15 days out.

"78.9% secured" is a claim about knowledge in August derived from performance in June that was never once confirmed at a delay. The number is not a lie the system is telling *you* — it is a lie the system is telling *itself*, and it then plans from it. Under-14-days triage, ROI ranking, and what to review next are all computed off a quantity that has never been validated at a delay.

And it is reproducing: quantum, today, two topics from `[Problematic]` to `mastered` in one sitting, with **no review queue written** — so there is no mechanism by which they will ever be re-tested.

The irony is that v9 already knows this. Its difficulty controller says *"If I am passing everything first-try across a whole topic, that is **your** calibration failure, not evidence I'm a genius."* Thirty passes, five fails, eight same-day masteries. The self-check exists and has never fired.

---

### W3 — Review debt has no throttle, and the one rule that handles review failure is a landmine

v9's spaced retrieval is: *"Pull 1–2 items from `review_queue` at the start of a Lesson."* A fixed small cap with no concept of overdue-ness, no triage, and no divergence check.

With SM-2 intervals starting at 1–3 days and 8 topics in queue, arrival outruns service almost immediately. Your CV queue: **8 items, every one due 2026-06-30 to 07-02, all ~6 weeks overdue.** At 1–2 per Lesson, with each cleared item re-entering, the queue never drains. `/study-run`'s own doc names this exact outcome — *"boards that are 100% review, session after session… the fastest way to abandon a system"* — and caps review at 50% of budget. **The tutor prompt has no equivalent rule**, and the tutor is what actually runs.

The stored `next_session` (planned 2026-08-08) reads: *"Review-heavy: clear the 3 oldest overdue items, then open Support Vector Machines."* Three of eight, with the other five decaying further. That is the board you don't come back to — and empirically, you didn't.

**The landmine.** § *Spaced retrieval*: *"Pull 1–2 items… at **full exam difficulty**. If I fail, send that topic's final rung back to `unlocked`."* After a 6-week gap, failure is the expected outcome, not the exception. Run that rule honestly across the backlog and you revert most of 8 topics to `unlocked`, collapsing the banner from 78.9% toward single digits — **15 days before the exam.** The rule is individually defensible and catastrophic in aggregate, and nothing in the prompt notices the difference.

There is also a **spacing-schedule mismatch**. Cepeda et al. (2008, N > 1,350) found the optimal study gap is roughly **10–20% of the retention interval** (20–40% for a 1-week delay, 5–10% at a year). Your retention interval is fixed and short — days to exam. At 15 days out that implies gaps of ~2–3 days, converging on daily review in the final week. Generic SM-2 ease/interval growth is tuned for indefinite retention and is the wrong curve for a dated exam. v9 clamps `next_due` to `exam_date − 1` but never *compresses* the schedule as the date approaches.

---

### W4 — The one-command promise is broken at three seams, and the most common exit path is unhandled

Your stated ideal: sit down, type `/continue-study-session`, study. v9's prime directive says the same. Three things prevent it.

**(a) Two planners, two state files, one precedence rule you have to remember.** v9 writes `next_session` into `progress.json`; `/study-run` writes `active_run` into `sessions.json`; `SKILL.md` Step 4 arbitrates ("if `active_run` is non-null, that is the plan — do not re-plan"). Correct as engineering, but it means "what am I studying today" has two possible authorities and a tie-break.

**(b) The second command is never run.** v9 closes with *"Run `/study-run close` to log this session."* Across **8 real sessions on two courses**, both `sessions.json` files read `"n_sessions": 0, "sessions": []`. Quantum still has a non-null `active_run` left open. So the entire calibration loop — `k_rung`, mode multipliers, throughput, the debrief, and the `~30 min` estimate v9's Lesson line depends on — has **zero data after eight sessions**. A step that requires a second deliberate invocation after the work is done does not get taken. That is not a discipline failure; it is a design prediction that has now been confirmed eight times.

**(c) Nothing survives a mid-session exit — the common case.** All persistence is in close steps 16–19. Sessions do not end with a ceremony; they end with a closed laptop. When that happens: no ledger write, no `next_session`, no review scheduling. The next session then re-derives everything, which is precisely the state the zero-decision contract was built to eliminate. CV's last session (2026-06-29, one attempt logged) ended with a queue full of "due tomorrow" and no `next_session` at all.

Gollwitzer & Sheeran's implementation intentions (d = 0.65 overall, **d = 0.61 for failures to get started**) are shipped in v9 step 18 — but step 18 is inside the close protocol that doesn't run. `next_session.intention` is empty in both ledgers.

---

### W5 — Nothing in the system measures itself against the actual exam

Every number v9 produces is generated by the same model that taught the material, graded against a rubric it wrote, in a conversation where it chose the question. The `[Exam question]` uses real exemplars — good — but it is still administered mid-conversation, untimed, one topic at a time, immediately after teaching.

The real exam is cumulative, timed, closed-book, and mixes topics without telling you which is which. Dunlosky et al. (2013) rate **practice testing** and **distributed practice** as the only two techniques earning a *high* utility rating out of ten assessed — and part of the reason is generality across criterion tasks. A cumulative timed past paper is both techniques at once, in the criterion format.

v9's exam-date clamp says *"Under 4 days out: review and past-paper exemplars only."* Four days is too late to *discover* that 78.9% was 55%, and "exemplars only" is not the same as a graded, timed, cumulative sitting. **There is no Mock Exam unit anywhere in the system**, and `parsed/` is full of real past papers that would make one nearly free to assemble.

This is the only intervention that could have caught W2 before the exam did.

---

### W6 — Confidence costs a full extra turn per graded question, which is why it gets skipped

v9 L329: *"After every graded answer, **before you reveal the verdict**, ask for one word."* Combined with `SKILL.md`'s atomic rule (one thing per turn, "if you catch yourself typing *and then*, that *and then* is the next turn"), each graded question becomes: ask → answer → **ask confidence → answer confidence** → verdict. Five turns per rung, ~25 per Lesson, with the extra pair adding no thinking — pure latency between an answer and the feedback that makes it useful.

The tutor skipped it 5/7 times today. I'd read that as the model resolving a real conflict between two rules in the file, not as random non-compliance.

The signal itself is worth keeping — the hypercorrection routing is well-founded (Butterfield & Metcalfe; high-confidence errors correct better and don't return when a test follows). It's the *turn structure* that is wrong.

---

### W7 — State hygiene: the layout contract is already violated, and there are two copies of the prompt

Small, mechanical, but each one produces a confusing session:

- **Quantum's ledger is outside its Exam folder.** `Courses/Introduction_to_quantum_computers/tutor/progress.json`, while `final_20_08_2026/` holds the taxonomy, exemplars and ROI sheet. v9 L64: *"All study state lives inside the Exam folder."* Its own resolver would not find this by the documented rule.
- **`.study-run.json` is at Course level**, not project root where both skills look for it — and its `"method": null` and `"date": null` despite the exam being **9 days out**.
- **Two byte-identical copies of `TUTOR_SYSTEM_PROMPT_v9.md`** (`tutor/` and `Courses/Introduction_to_quantum_computers/tutor/`). Identical today; the highest-`_vN` resolver will pick arbitrarily once they diverge.
- **Two live Exams 9 and 15 days apart** means v9's multi-Exam disambiguation question fires every single session — a permitted question, but still a decision at the exact moment the contract promises none.

---

### W8 (minor) — One supportive thing that is missing and would not be sugarcoating

v9 correctly bans praise inflation, effort commentary, and manufactured urgency. What it has no line for is **normalising difficulty as a signal rather than a verdict**. Bjork's desirable-difficulties framing — retrieval that feels hard is the condition under which durable encoding happens; fluency during study is the misleading signal — is *true*, *task-directed*, and load-bearing for someone about to spend three sessions failing overdue review items under W3's fix.

Saying "this is supposed to feel worse than rereading, and the feeling is not the score" is not softening a verdict. It's an accurate statement about the measurement, and it is the difference between a hard session reading as *progress* and reading as *evidence you're behind*.

---

## Plan

Ordered by expected value against the stated goals. Each item argues **for and against**, because two of these are genuine trade-offs.

---

### P0-1 — Move state-writing out of the prompt and into a tool *(fixes W1; unblocks W2, W3, W4)*

Add `pipeline/ledger.py` with a small verb CLI the tutor calls instead of hand-editing JSON:

```
ledger resolve                         → active exam, paths, capability flags (one JSON blob)
ledger open                            → banner + next_session + due reviews, computed
ledger attempt --topic T --rung 2 --result PASS --marks 7/8 --confidence high --note "..."
ledger master --topic T                → status, coverage w/ dedup, review scheduling, unlock
ledger review --topic T --result FAIL  → SM-2 update, exam-date clamp, compression
ledger close --next-topic T --why "..." --est 30 --intention "Tue 09:00 library"
ledger check                           → schema + invariant validation, non-zero exit on drift
```

Then **delete the corresponding ~150 lines of schema prose from v9** and replace them with the verb list. The prompt stops describing a data format and starts naming six commands.

- **Why:** this is the only fix that addresses W1 structurally rather than by asking the model to try harder. `--confidence` becomes a *required argument* — the failure mode changes from "silently omitted" to "command errors out". Coverage de-duplication, SM-2 arithmetic, and the exam-date clamp become code that is right every time instead of prose the model re-derives at turn 40. It also shrinks the prompt, which is the W1 intervention that has the most evidence behind it.
- **Why it serves the UX goal:** `ledger open` collapses v9's entire silent step-1 (resolve → read ledger → read notes → read taxonomy → read exemplars → read ROI → compute banner) into one call. Session start gets faster and cheaper, and cannot half-fail.
- **Argument against:** v9 is explicitly designed to be pasted into Cowork with nothing but file access, and a Python dependency breaks that. **Response:** keep the prose schema as an appendix labelled *"fallback when no tooling is available"* and have the prompt prefer the CLI when `pipeline/ledger.py` exists. The Claude Code path — which is where all 8 logged sessions actually happened — gets the reliable version.
- **Second argument against:** more moving parts to maintain. **Response:** `ledger check` is the answer; run it as a pre-commit hook. Right now nothing validates the ledgers and both are already malformed.
- **Cost:** ~250 lines of Python, one afternoon. Highest leverage item in this document.

**Recommendation: implement.**

---

### P0-2 — Split `mastered` into `passed` → `retained`, and make the banner tell the truth *(fixes W2)*

Two coupled changes:

**(a) Two-stage mastery.**
- `passed` — cleared the cold `[Exam question]`. Awarded exactly as today, in-session. The mastery *moment* is unchanged: same celebration, same unlock of the next topic, same concept map.
- `retained` — cleared **one further spaced retrieval on a later calendar day** at exam difficulty. Only then does the topic count as secured.
- Reaching `retained` requires 2 spaced confirmations when the exam is >21 days out, 1 when it's closer. Rawson & Dunlosky's prescription is 3 relearnings; with 15 days and 10 topics that is not affordable, and their own finding — that criterion pushed *within* a session doesn't carry — argues for spending the budget on more spaced passes rather than a stricter bar.

**(b) The banner splits.**

```
📊 Computer Vision · final_26_08_2026 — 71/175 retained (41%) · 67 provisional · 15 days to exam
```

- **Why:** it makes the number honest, and the number *is* the motivation system. SDT says competence is the strongest driver of self-sustaining motivation — but competence support only works if the signal is credible. A 78.9% you privately suspect is inflated has already stopped motivating you; that is roughly what 43 days of not returning looks like. It also converts W3's backlog from a chore into the mechanism that moves the headline number — **review becomes the thing that banks marks**, which is exactly the incentive you want in the last two weeks.
- **Why it's cheap:** it is a status enum and one banner line. The scheduling machinery already exists.
- **Argument against — and it's real:** the number drops from 78.9% to ~41% overnight, 15 days out. That is a demoralising thing to do to someone in the final stretch. **Response:** it is also the single most useful piece of information available to you right now, and the alternative is discovering it on 2026-08-26. Frame it once, explicitly, as a recalibration rather than a loss — *"nothing was taken away; 67 marks are unconfirmed because they haven't been retrieved since June"* — and make the first three sessions convert provisional → retained, so the number moves up fast. It should recover most of the way within a week of actual review, and *that* recovery is a credible competence signal in a way the original 78.9% is not.
- **Argument against #2:** delayed mastery could stall forward progress if everything sits in `passed`. **Response:** unlocking still happens at `passed`, so the ramp is never blocked. Only *coverage accounting* waits.

**Recommendation: implement, and do the recalibration explicitly rather than silently.**

---

### P0-3 — Review budget as a proportion, queue-collapse triage, and no auto-reversion *(fixes W3)*

Three rules, replacing v9's *"pull 1–2 items"*:

1. **Proportional budget, both ends.** Review takes **at most 50%** of a Lesson and **at least one item** whenever anything is due. Mirrors `/study-run`'s cap so the two skills stop disagreeing; guarantees forward progress always exists.
2. **Queue-collapse triage.** When >4 items are overdue, do **not** walk them one at a time. Run one **mixed rapid-recall pass** — one core question per topic, 3–4 topics in a single block, unlabelled as to which topic each belongs to. Reschedule each from its result. This is the one context where interleaving's evidence is strongest (genuinely confusable, all decayed), it costs a fraction of full exam questions, and it produces triage data on the whole backlog in one Lesson rather than four.
3. **Graded review failure, never silent reversion.** Replace *"if I fail, send the final rung back to `unlocked`"* with: **first failure after a gap → `retained` drops to `passed`, requeue at 1 day.** Only a **second** consecutive failure demotes to `unlocked` and reopens the ramp. Rationale: one failure after six weeks measures the gap, not the knowledge — the distinction between forgetting and never-having-learned matters, and only the second attempt separates them.
4. **Compress intervals near the exam.** Multiply SM-2's computed interval by `min(1, days_remaining / 30)` before the clamp. Cepeda's ratio implies ~10–20% of the retention interval; with 15 days left that's 2–3 day gaps regardless of what ease says.

- **Why:** W3 is the mechanism that ended the last run, and rule 3 is a live hazard sitting in the current prompt — one honest review session could wipe the banner today.
- **Argument against:** rule 2 sacrifices depth for coverage, and a rapid-recall pass is a weaker retrieval event than a full exam question. **Response:** accepted deliberately. Against a 6-week-cold backlog and a 15-day horizon, knowing *which four of eight topics actually decayed* is worth more than one deep pass on one of them. Follow the triage pass with full exam questions on the failures only.
- **Argument against #2:** rule 3 could let a genuinely lost topic keep counting. **Response:** it doesn't — it drops to `passed`, which under P0-2 means it stops counting toward the retained number immediately. The demotion is real; only the *ramp reset* is deferred.

**Recommendation: implement. Rule 3 is urgent regardless of the rest.**

---

### P0-4 — One command: fold planning and closing into `/continue-study-session`, and persist incrementally *(fixes W4 — your headline requirement)*

**(a) Collapse the invocation surface to one.** `/continue-study-session` becomes the only command you type. It calls the planner logic internally (silently, before the banner) and runs the close automatically when the Lesson ends. `/study-run` stays as an explicit override for *"I have exactly 90 minutes and want to see the board"* — a power-user entry point, not part of the normal loop.

**(b) Persist after every graded answer, not at close.** `ledger attempt` (P0-1) writes immediately; `ledger master` writes immediately; `next_session` is **recomputed after every rung**, so it is always current. Closing stops being an event that must happen and becomes a state that is already true.

**(c) Keep exactly one thing at the end:** the implementation intention. One line, asked once. It has the best evidence in the system for the specific problem of restarting (d = 0.61), and it is the only close step that genuinely requires you.

- **Why:** eight sessions, zero closes, is not ambiguous. Any step requiring a deliberate second invocation after the work is finished will not be taken, and everything downstream of it — calibration, throughput estimates, the `~30 min` Lesson line, the debrief — is dead as a result. Incremental persistence also makes the *actual* exit path (closing the laptop) a first-class case rather than data loss.
- **Argument against:** merging planner and tutor loses a clean separation of concerns, and `/study-run`'s calibration loop is genuinely well-designed. **Response:** keep the logic, drop the second invocation. The planner becomes a function the tutor calls, not a peer skill with a precedence contract. Nothing in the cost model or the `k`-update loop needs to change — it just needs to be *called*, which today it never is.
- **Argument against #2:** auto-closing risks writing a session record when you meant to keep going. **Response:** incremental writes make the close a no-op summary rather than a commit point. There is no state to lose because it was never held.

**Recommendation: implement. This is the item that most directly matches what you asked for.**

---

### P0-5 — Restructure v9 for primacy: hard rules first, reference material last *(fixes W1, complements P0-1)*

Not a rewrite — a reordering plus a cut:

1. **New first section: ~12 numbered non-negotiables**, ~40 lines, before anything else. Retrieval-first gate · label every question · confidence with every answer · one atomic step per turn · grade in marks + rubric + fatal-error check · never invent exam format · write state after every answer · wit targets the work · never mark retained without a spaced pass · never plan out loud · escape hatch · no streaks.
2. **Everything currently in Part 1 (schemas, path resolution, degradation table) moves to an appendix** or disappears into `ledger resolve` (P0-1). It is reference data the model needs *once*, at startup, not a constraint it must hold for 40 turns.
3. **Merge the overlap with `SKILL.md`.** Both define session startup, atomicity, and file resolution. Two documents claiming authority over the same behaviour is a coin flip. `SKILL.md` should shrink to: invoke, resolve, load v9, hand off.

Target: **v9 under 350 lines, `SKILL.md` under 80.**

- **Why:** primacy bias is the documented failure pattern, and your losses match it exactly — the rules that were dropped today are at L119, L329, and L584–590. Moving them to L20 is free.
- **Argument against:** reordering a prompt this carefully argued risks breaking a subtle dependency, and no-op edits to working prompts are how good prompts rot. **Response:** do it *after* P0-1 and P0-2 land, in one pass, with the rationale docs as the check. The v8 critique explicitly noted the right direction is *shorter*; v9 grew instead.
- **Argument against #2:** duplicating rules at the top and in detail below is redundant. **Response:** deliberate. Redundancy is the cheapest known mitigation for constraint-count degradation, and unlike prose length it costs nothing at inference time.

**Recommendation: implement, after P0-1 and P0-2.**

---

### P1-6 — Fold confidence into the answer *(fixes W6)*

Change the rule from *"ask for confidence in a separate turn"* to: **every graded question ends with `— tag your answer low / ok / high.`** The verdict follows the answer directly. If the tag is missing, record `not_collected` and move on — never spend a turn chasing it.

- **Why:** removes two turns per graded question with **zero measurement loss** — it is still a retrospective judgment made after seeing the question and before seeing the verdict, which is exactly what hypercorrection routing requires. It also resolves the real conflict with the atomicity rule that is currently causing the model to drop it 5 times in 7.
- **Argument against:** an inline tag may get less deliberation than one asked for on its own. **Response:** plausible, and worth accepting — a slightly noisier signal collected 100% of the time beats a clean signal collected 29% of the time.
- **Cost:** two lines.

**Recommendation: implement. Cheapest item here.**

---

### P1-7 — Add a Mock Exam unit *(fixes W5)*

A new bounded unit alongside the Lesson: **one timed, closed-book, cumulative section assembled from `parsed/*.json`**, graded against the real mark scheme, no hints, no scaffolding, no narrative wrapper.

- **Trigger:** at ~14 days and ~5 days out, and on demand.
- **Output is authoritative.** The mock's per-topic marks **overwrite** the coverage estimate for the topics it covers, and its failures re-rank the ROI ordering for the remaining days.
- Report it flat: marks per section, the three biggest losses, one line on what changes. No encouragement padding.

- **Why:** it is the only measurement in the system not produced by the same model that taught the material, and it is the ground truth for the number W2 is about. Practice testing and distributed practice are the two highest-utility techniques in Dunlosky's assessment, and a cumulative timed paper is both, in the criterion format. You already own the past papers.
- **Argument against:** it costs a full session and can be demoralising 14 days out. **Response:** that is the point of doing it at 14 days rather than 4 — there is still time to act on it. Frame it as instrumentation, and let it *replace* rather than supplement a Lesson so it doesn't add net load.
- **Argument against #2:** overlaps with the boss-check. **Response:** the boss-check is per-topic and mid-conversation. This is cumulative, timed, and mixed — a different measurement.

**Recommendation: implement — and given CV sits 15 days out with 43 days of no retrieval, consider running one manually this week regardless of whether the rest ships.**

---

### P2-8 — State hygiene pass *(fixes W7)*

Mechanical, ~15 minutes: move `Courses/Introduction_to_quantum_computers/tutor/progress.json` and `sessions.json` into `final_20_08_2026/`; delete the duplicate `TUTOR_SYSTEM_PROMPT_v9.md`; move `.study-run.json` to project root and fill `method` and `date`; add `ledger check` to a pre-commit hook. Change multi-Exam disambiguation from "always ask" to **"default to the nearest exam date, name it in the banner, and let the escape hatch redirect"** — the information is in the ledgers, so it is not one of the two genuinely unanswerable questions.

- **Why:** each of these produces one confusing session, and the duplicate prompt is a silent-divergence bug waiting to happen.
- **Argument against:** defaulting to nearest-exam-date could silently pick the wrong course. **Response:** the banner names Course and Exam on line 1 — v9 already says that naming exists precisely as your check — and redirecting costs one sentence.

**Recommendation: implement. Do it first, it's free.**

---

### P2-9 — One line normalising difficulty *(fixes W8)*

Add to § *Tone*, under the non-negotiables: **difficulty may be named as a property of the method, never as a property of me.** Permitted: *"that should have felt hard — retrieval at this spacing is where the encoding actually happens, and it's why it'll still be there in two weeks."* Still banned: anything about effort, character, consistency, or gaps between sessions.

- **Why:** it is true (Bjork), task-directed (survives the Kluger & DeNisi constraint), and load-bearing for the several deliberately unpleasant sessions P0-2 and P0-3 are about to produce. Without it, "your retained score is 41%" reads as a verdict on you rather than a measurement of the schedule.
- **Argument against:** it's one step from encouragement padding, which the prompt correctly bans. **Response:** bound it explicitly — a statement about the *method*, never about the *learner*, and never attached to a verdict. Same boundary the tone section already draws, applied to difficulty instead of to error.

**Recommendation: implement, tightly scoped.**

---

## Summary table

| # | Weakness | Fix | Priority | Evidence | Verdict |
|---|---|---|---|---|---|
| W1 | 665-line prompt; 6 required behaviours skipped on first run | Ledger CLI + prompt restructure for primacy | **P0** | Strong (IFScale) + **your logs** | **Implement** |
| W2 | `mastered` = same-session performance; banner reads 78.9% after 43 days idle | `passed` → `retained`; split banner | **P0** | Strong (Soderstrom & Bjork; Rawson & Dunlosky) | **Implement**, recalibrate openly |
| W3 | Review debt unthrottled; auto-reversion landmine | Proportional cap · triage pass · graded demotion · interval compression | **P0** | Strong (Cepeda) + your queue | **Implement**; rule 3 urgent |
| W4 | Two commands, 0/8 closes run, nothing survives a mid-session exit | One command · incremental persistence | **P0** | Design + **8/8 confirmations** | **Implement** |
| W5 | No cumulative, timed, self-authored-free measurement | Mock Exam unit at T−14 and T−5 | P1 | Strong (Dunlosky et al.) | **Implement**; run one manually now |
| W6 | Confidence costs 2 turns; skipped 5/7 | Inline tag on the answer | P1 | Design; resolves a rule conflict | **Implement** (2 lines) |
| W7 | Ledger outside Exam folder; duplicate prompt; `.study-run.json` misplaced | Hygiene pass + `ledger check` | P2 | N/A — contract violations | **Implement first** |
| W8 | No honest normalisation of difficulty | One bounded line in *Tone* | P2 | Strong (Bjork) | **Implement**, tightly scoped |

**Net effect on the prompt: substantially shorter.** P0-1 and P0-5 remove ~250 lines; P0-2, P0-3, P1-6, P1-7, P2-9 add ~60. That direction was right in the v8 critique and is more right now — the pedagogy is sound and the failures are executional, so the correct move is less prose and more mechanism.

**One thing that is not on this list:** nothing here weakens the retrieval-first gate. Bastani et al. is the strongest external result to appear since v8 was written, and it says the gate is the difference between a tutor that helps and one that measurably harms. Whatever else changes, it stays absolute from rung 1.

---

## Sources

- Soderstrom & Bjork (2015), *Learning Versus Performance: An Integrative Review*, Perspectives on Psychological Science 10(2), 176–199 — https://journals.sagepub.com/doi/abs/10.1177/1745691615569000 · PDF: https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/11/soderstorm_ra_learningvsperformance.pdf
- Rawson & Dunlosky (2022), *Successive Relearning: An Underexplored but Potent Technique for Obtaining and Maintaining Knowledge*, Current Directions in Psychological Science — https://www.semanticscholar.org/paper/5308ee62b2524668cec30f70849c7ef6f1ca8c06
- Rawson & Dunlosky (2013), *The Power of Successive Relearning: Improving Performance on Course Exams and Long-Term Retention*, JEP: Applied — https://www.researchgate.net/publication/258845409
- Rawson & Dunlosky (2016), *Effects of successive relearning on recall: Does relearning override the effects of initial learning criterion?* — https://pubmed.ncbi.nlm.nih.gov/27027887/
- Cepeda, Vul, Rohrer, Wixted & Pashler (2008), *Spacing Effects in Learning: A Temporal Ridgeline of Optimal Retention*, Psychological Science 19, 1095–1102 — https://laplab.ucsd.edu/articles/Cepeda%20et%20al%202008_psychsci.pdf
- Dunlosky, Rawson, Marsh, Nathan & Willingham (2013), *Improving Students' Learning With Effective Learning Techniques*, Psychological Science in the Public Interest 14(1), 4–58 — https://journals.sagepub.com/doi/abs/10.1177/1529100612453266
- Bastani, Bastani, Sungu, Ge, Kabakcı & Mariman (2025), *Generative AI without guardrails can harm learning: Evidence from high school mathematics*, PNAS — https://www.pnas.org/doi/10.1073/pnas.2422633122 · https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/
- Kestin et al. (2025), *AI Tutoring Outperforms Active Learning*, Scientific Reports — https://projects.panickssery.com/docs/kestin-2024-ai_tutoring_harvard_physics.pdf · https://news.harvard.edu/gazette/story/2024/09/professor-tailored-ai-tutor-to-physics-course-engagement-doubled/
- Jaroslawicz et al. (2025), *How Many Instructions Can LLMs Follow At Once?* (IFScale), arXiv:2507.11538 — https://arxiv.org/pdf/2507.11538
- Carried over from the v8 critique — VanLehn (2011); Kluger & DeNisi (1996); Butterfield & Metcalfe; Gollwitzer & Sheeran (2006); Deci, Koestner & Ryan (1999); SDT need-support meta-analyses. See `critique-tutor-learning-science.md`.
