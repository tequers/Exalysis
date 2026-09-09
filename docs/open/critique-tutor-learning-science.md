# Critique: Tutor Prompt vs. Learning Science

**Status: implemented in `tutor/TUTOR_SYSTEM_PROMPT_v9.md` (2026-08-08).** Every P0 and P1 item shipped. W5 (loci) went *further* than the P2 recommendation — the add-on was fully decoupled rather than merely retargeted, on the instruction that nothing in the system may depend on it. This doc is kept as the **rationale record** for v9: it holds the argument and the evidence; the prompt holds the implementation. Do not re-litigate a v9 rule without reading the matching section here first.

Reviewed: `tutor/_archive/TUTOR_SYSTEM_PROMPT_v8.md` (2026-08-08).
Goal frame: the system should be **effortless to start**, **honest without sugarcoating**, **engaging**, and should make the user *return*. The user should never have to decide what to study.

---

## Source validation note

Claims below are tied to primary literature (meta-analyses and the original papers) rather than blog summaries, with two honest gaps:

- **Kulik, Kulik & Bangert-Drowns (1990)** — I could retrieve the abstract (108 controlled evaluations; positive effects on exam performance; **stronger effects on weaker students**; effect size varies with *stringency of the mastery criterion*) but **not** the per-criterion-level numbers. So the recommendation to lower the PASS bar rests on the *direction* the literature supports plus the incoherence argument in W2, **not** on a retrieved 80%-vs-95% comparison. Flagging that rather than inventing a number.
- **Wilson et al. (2019)** — the Nature Communications page is behind an IdP redirect; the derivation details come from the bioRxiv preprint and the abstract. The scope limitation (binary classification, gradient-descent learners, Gaussian error assumption) is stated in the paper's own framing and is not disputed.

Where evidence is genuinely mixed (interleaving) or weak (method of loci), the doc says so instead of overclaiming.

---

## Strongest points — keep these, they are well-founded

**1. The backbone is the right one.** Retrieval practice → mastery gate → spaced review is the highest-confidence stack in the whole field. VanLehn's (2011) review puts intelligent tutoring at **d ≈ 0.76** against human tutoring's **d ≈ 0.79** — i.e. a well-built step-based tutor is roughly as effective as a human one, and far more available. The design is aiming at a real, documented effect, not a folk theory.

**2. The interaction granularity is already optimal — this is the prompt's quietest strength.** VanLehn's central finding is the **interaction plateau**: step-based and substep-based tutoring perform about equally, and both match human tutoring. The prompt operates at exactly step granularity (one rung, one answer, one rubric, one verdict). *This is a reason to stop adding machinery, not to add more.* Most of my recommendations below therefore **remove or simplify** rather than extend.

**3. Marks-based rubric grading is textbook-correct feedback design.** Kluger & DeNisi's meta-analysis (131 experiments, 607 effect sizes, 23,663 observations; mean **d = 0.41**) found feedback works when it is **task-focused** — and `5/8 — 3 marks lost on the normalisation step` is precisely task-focused, specific, and actionable.

**4. "No empty praise" is not just taste — it is supported.** The same meta-analysis found **38% of feedback interventions *decreased* performance**, with the mechanism being attention shifted from the task to the self. Generic praise is self-directed feedback. Banning it is correct.

**5. Problem-first framing (`[Problematic]`) is the best original idea in the prompt.** It creates an interpretive need before the answer exists, which is the same mechanism behind the **pretesting effect** (Richland, Kornell & Kao, 2009: posttest performance was better after a pretest *even when analysis was restricted to items the learner failed to retrieve*). The requirement/mechanism boundary is a genuinely clever piece of prompt engineering — it gets the motivational benefit without leaking the answer.

**6. Exemplar-derived final rungs.** Practising in the exam's actual format is transfer-appropriate processing. Refusing to invent an exam style is the right call and should never be relaxed.

**7. The coverage banner satisfies the competence need.** The SDT meta-analysis of 144 studies / 79,000+ students found **competence is the strongest predictor of self-determined motivation**, ahead of autonomy and relatedness. Visible, credible progress toward a real exam is the correct motivational lever — and it is already built.

---

## Weaknesses, ranked

### W1 — The retrieval-first gate is applied at first contact, where the evidence points the other way *(biggest)*

The gate says: **no explanation, no worked step, nothing above an L1 hint until the user has attempted.** At rung 1 of a brand-new topic, the user has just read a 150–250 word problematic that deliberately withholds the mechanism — and is then asked to produce it.

This collides with the **worked example effect** (Sweller & Cooper): novices who study worked examples outperform novices made to solve equivalent problems, because unguided problem-solving on unfamiliar material spends working memory on search rather than on schema construction. The **expertise reversal effect** (Kalyuga et al.) is the precise boundary condition: worked examples help low-knowledge learners and lose value — even reverse — as knowledge grows. The prompt has this backwards: it is *most* restrictive exactly where the learner is *least* equipped.

The pretesting literature is the counter-argument, and it is real — but note its shape: pretest items were **immediately followed by the instructional text**, and the 2025 *Journal of Cognition* follow-up finds **feedback is essential to the effect** (immediate beat delayed, though delayed still worked). A pretest is a short probe followed by teaching. The prompt instead makes the failed attempt a *gate* the learner must pass, with a "two consecutive FAILs at rung 1 → stop the ramp" floor that will fire routinely on hard first contact.

**These are reconcilable, and the resolution is a distinction the prompt currently lacks: a pretest is not a rung.**

### W2 — The 95% PASS bar is miscalibrated and makes the 85% controller nearly unimplementable

The prompt asks the tutor to author questions such that P(user scores ≥95%) ∈ [0.70, 0.85]. The prompt is admirably explicit that these are different quantities — but that does not make the target *authorable*. No question-writer, human or model, can steer a 95%-threshold exceedance probability into a 15-point band. In practice this collapses into vibes wearing a lab coat.

Separately, the 85% rule's provenance is narrower than the prompt implies: Wilson et al. derive **≈15.87% optimal error** for **gradient-descent learners on binary classification tasks under a Gaussian noise assumption**, with perceptual learning as the human analogue. Extending it to marks-graded exam answers is an analogy, not a result.

And 95% is stringent by mastery-learning standards. Kulik et al. found effect size varies with criterion stringency and that gains concentrate in **weaker students** — the population most likely to be ground down by a 95% bar with a two-strike drop rule.

### W3 — The tone rules invite the exact feedback failure Kluger & DeNisi identified

"Roast me for the mistake" is fine. "**Needle me when I stall**" and "sharp-tongued, a little relentless" are not the same thing — they are **person-directed**. FIT's mechanism for the 38% of interventions that *hurt* performance is attention diverted from task to self, and that is true for negative self-directed feedback as much as for praise.

This matters more than usual here because the user explicitly wants **no sugarcoating**. The good news: honesty and person-directed jabs are separable, and the evidence says keep the first, drop the second. Nothing about "your normalisation step is wrong and it cost you 3 marks" is soft.

### W4 — The ramp is pure blocked practice; nothing ever forces discrimination between topics

A topic is climbed to mastery in one sitting, then revisited only as isolated review-queue items. Nothing ever asks *"which of these methods applies here, and why not the other one?"* — which is the dominant failure mode in real CS exams and the specific thing **interleaving** trains.

Being honest about the evidence: Rohrer's studies show interleaving benefits at 1-day and 30-day delays (one study tripled test scores while *lowering* practice scores), but Brunmair & Richter's meta-analysis finds a **small** effect with **strong heterogeneity**, a full-year classroom RCT found small non-significant gains, and the benefit depends on **category confusability**. So: not a universal upgrade — a targeted one, aimed at confusable topic clusters, which the taxonomy's `connections` field already identifies.

### W5 — The loci layer is over-weighted for the material it is applied to

It is labelled "core retention mechanism, not optional" and consumes a large share of session time (encode → dual-axis evaluation → sharpen → consolidate at mastery → walk before every review).

The 2025 *British Journal of Psychology* systematic review and meta-analysis of the method of loci rates the evidence base **low to very low quality, mainly due to high risk of bias**, and finds it strongest for **recall in adults** — list-like, arbitrary, order-dependent material. Evidence for conceptual understanding and **transfer is thin**, and MoL is acknowledged to work poorly for abstract material that resists visual-spatial encoding.

Most of what these exams test — derive a bound, prove a property, trace an algorithm, justify a design choice — is exactly that abstract material. The prompt even concedes the difficulty ("for genuinely abstract concepts, allow multi-locus encoding"), which is a workaround for a mismatch rather than a fix.

This is also the **single largest recoverable block of session time**, which makes it a direct cost to the "just sit down and study" goal.

### W6 — Confidence is collected and then never used

The prompt says to "optionally ask for a one-word confidence and store it," and there it ends. That is a wasted signal, because:

- The **hypercorrection effect** (Butterfield & Metcalfe): errors made with *high* confidence are corrected **better** than low-confidence errors given clear feedback, the advantage **persists at a week**, and high-confidence errors **do not return** if a test follows the corrective feedback. A confidently-wrong answer is the highest-yield teaching moment available, and the prompt currently treats it identically to a shrug.
- Learners' judgments track **current processing fluency**, not future retrievability — which is why material feels solid right after study and evaporates later. Calibration feedback measurably reduces overconfidence.

### W7 — The zero-decision experience is a stated goal but not an implemented contract

Session start currently runs: resolve Course/Exam → read ledger + notes → print banner → report missing files and fallbacks → possibly ask for `exam_date` → run 1–2 review items → pick a topic → pick an adapter → write a problematic → hook → rung 1. That is a lot of visible machinery, and **the tutor re-derives the whole plan from scratch every session** while the user watches.

There is also **no defined lesson boundary and no defined session end** — sessions terminate whenever the user quits. An unbounded task is measurably harder to start than a bounded one, so this works directly against the return-rate goal.

### W8 — Nothing supports *restarting* tomorrow (and the obvious fix is the wrong one)

The prompt optimises the *inside* of a session and ignores the transition between them. The tempting fix — streaks, points, badges — is contraindicated: Deci, Koestner & Ryan's meta-analysis (128 studies) found tangible rewards undermine free-choice intrinsic motivation, with **engagement-contingent d = −0.40, completion-contingent d = −0.36, performance-contingent d = −0.28**. A study streak is completion-contingent by construction. It would likely raise short-run compliance and damage the durable motivation this user actually needs over a multi-month exam horizon.

The evidence-backed alternative is unglamorous and nearly free: **implementation intentions** (Gollwitzer & Sheeran, 2006; 94 tests, 8,000+ participants, **d = 0.65** overall and **d = 0.61** specifically for *failures to get started*).

---

## Plan

Ordered by expected value. Each item states the counter-argument, because several of these are genuine trade-offs rather than clear wins.

### P0-1 — Split "first contact" from "the ramp" *(fixes W1)*

Add a **rung 0 probe** before rung 1 on any new topic: one short question, **explicitly labelled as a probe that is not graded and not gated**, answered cold. Then, regardless of outcome, deliver a **faded worked example** of a canonical instance. Then start rung 1 for real.

- **Why:** captures the pretesting benefit (which survives failure — that is the whole point of Richland et al.) while honouring the worked-example effect at the moment of lowest prior knowledge. Feedback follows immediately, as the pretesting-with-feedback literature requires.
- **Why it also serves the UX goal:** the current design's most likely bad session is *fail rung 1 twice on a new topic in the first ten minutes*. That is the session the user does not come back from.
- **Counter-argument:** this weakens the retrieval-first purity that makes the tutor rigorous, and a worked example at first contact could induce the illusion of fluency. **Mitigated by:** the probe is unavoidable and comes first, the worked example is *faded* (one step blanked, not a full solution), and rung 1 still gates.
- **Cost:** one new label, ~15 lines.

### P0-2 — Recalibrate the thresholds and demote the controller to something authorable *(fixes W2)*

- Rung 1 and middle rungs: PASS at **≈85%** *and* **no fatal conceptual error** (the second clause is what actually protects rigour — a fluent answer with a broken invariant fails at any percentage).
- Final rung: hold **≈90%**, since it stands in for the real exam.
- Replace the probabilistic 85% target with a **three-state observable rule**: two consecutive first-try clean passes → harden; two fails in a topic → bridge question; otherwise hold.
- Keep the existing self-check ("if success sits near 100%, that is your calibration failure, not my genius") — it is the honest core of the controller and survives the simplification.

**Why:** the current formulation is unimplementable as written, so it is already being approximated — this makes the approximation explicit and auditable. **Counter-argument:** lowering to 85% risks marking as "mastered" work that is not exam-ready. **Mitigated by:** the no-fatal-error clause, the unchanged 90% final rung, and the unchanged cold boss-check.

### P0-3 — The Session Plan contract: one command, three lines, then teach *(fixes W7 — the user's headline requirement)*

Two coupled changes:

**(a) End every session by writing a `next_session` block into the ledger** — next topic, why it was chosen, which review items are due, the adapter, and the opening move. Planning happens at the *end* of the previous session, when the tutor already holds all the context.

**(b) Start every session by executing that block, not by re-deriving it.** The entire visible opening becomes:

```
📊 {Course} · {Exam} — 47/120 marks secured (39%) · 18 days to exam
Today: finish Feature Detection (rung 3 of 4), then 2 review items. ~30 min.
[Rung 3] …
```

Everything else — path resolution, ledger reads, missing-file fallbacks, adapter selection, ROI ranking — happens **silently**. The tutor announces a decision, it does not stage a deliberation. The **only** questions ever allowed before teaching starts are the two that are genuinely unanswerable: multi-Exam disambiguation, and a missing `exam_date`.

**Why:** this is precisely the user's stated goal, and it is where the current prompt is weakest — not because the sequencing logic is wrong, but because it is *performed in front of the user*. **Counter-argument:** a stale plan could be wrong if the user wants something else today. **Mitigated by:** one standing escape hatch (`"something else"` → re-plan silently), which preserves the SDT autonomy need without imposing a decision.

### P0-4 — Define the lesson as a bounded unit *(fixes W7, serves W8)*

A **Lesson** = one topic advance (1–3 rungs) + due review items + a mastery event if reached, with a stated up-front estimate and an explicit **"that's the lesson"** ending that names what comes next.

**Why:** bounded tasks are easier to start than unbounded ones, and a named endpoint converts "study computer vision" (aversive, undefined) into "finish rung 3, ~30 minutes" (startable). This is the same mechanism as P0-3 and they should ship together. **Counter-argument:** capping a session could interrupt genuine flow. **Mitigated by:** the boundary is an *offer*, not a cutoff — "that's the lesson; want the next one?"

### P1-5 — Make confidence mandatory and actually use it *(fixes W6)*

One word (`low`/`ok`/`high`) **before** each verdict is revealed. Then:

- **high + wrong** → the highest-value moment in the system. Mark it, correct it immediately and explicitly, and **guarantee a re-test of that exact point later in the same session** (hypercorrection persists at a week, and high-confidence errors do not return when a test follows the feedback).
- **low + right** → do not celebrate; it is a fluency accident. Schedule it sooner.
- Report a periodic **calibration line** ("you said `high` on 6, got 3 right — your confidence is running ahead of your accuracy").

**Why:** near-zero cost, uses a signal already being collected, and the calibration line is *honest feedback about the user's self-assessment* — exactly the non-sugarcoated register wanted, aimed at the task rather than the person. **Counter-argument:** forced confidence ratings add a micro-friction to every answer. **Accepted:** one word is cheap, and it is also the input that makes the difficulty controller trustworthy.

### P1-6 — Rewrite the tone rules as task-directed-only *(fixes W3)*

Keep: dry wit, sharp verdicts, roasting **the error**, specific earned praise, literal PASS/FAIL. Cut: "needle me when I stall," "relentless," and anything attributing a trait to the person. Add one line making the distinction explicit — *the joke targets the mistake, never the person making it* — because that is the boundary the meta-analysis actually draws.

**Why:** preserves everything the user asked for (accurate, unsoftened, funny) and removes the one documented mechanism by which feedback backfires. **Counter-argument:** the user explicitly likes the sharp persona and may read this as sanitising it. **Response:** it is not softer — "that answer skipped normalisation entirely and it cost you 3 marks" is harsher than a jab, because it is specific and true.

### P1-7 — Add a discrimination set at topic close *(fixes W4)*

After a topic is mastered, if it shares a `connections` edge with an already-mastered topic, run **2–3 mixed items where the first task is deciding which method applies and justifying why not the neighbour**. Once ≥3 topics are mastered, make one review item per session a mixed set rather than a single-topic recall.

**Why:** targets the actual exam failure mode (method selection under uncertainty), and the taxonomy already encodes which topics are confusable. **Counter-argument — and it is a real one:** interleaving's meta-analytic effect is small and heterogeneous, and a full-year RCT found non-significant gains. **Which is why this is P1, is scoped to confusable pairs only (the condition under which the effect is most reliable), and is capped at 2–3 items.** Do not interleave the ramp itself — that would fight cognitive load theory during acquisition, when blocking is correct.

### P2-8 — Demote loci from mandatory to targeted *(fixes W5)*

Change the trigger from "every topic at rung 1 and at mastery" to: **list-like, arbitrary, or order-dependent content** (criteria lists, taxonomies, parameter names, algorithm step-orders, "the four conditions for X") — plus anything the user has now failed twice on pure recall. For derivations, proofs, and reasoning chains, **skip it and say why**.

**Why:** the meta-analytic evidence is low-to-very-low quality and concentrated on recall of listable material; time spent encoding a proof as a bizarre kitchen scene is time not spent proving things. Recovers the largest block of session time in the system. **Counter-argument:** this is the user's own retention system, it is already built, has 27 stations mapped, and the user may value it beyond its measured effect. **Which is exactly why this is P2 and framed as *targeting*, not deletion** — the layer stays, it just stops firing on material it was never good at. Worth deciding deliberately rather than by default.

### P2-9 — Close each session with an implementation intention *(fixes W8)*

One line at session end: **"When and where is the next one?"** — record the answer in `session_log` and open the next session by referencing it.

**Why:** d = 0.65 overall and **d = 0.61 for getting-started failures specifically** — the single best-evidenced, lowest-cost intervention available for the stated goal of coming back. **Explicitly do NOT add** streaks, points, badges, or XP: tangible and completion-contingent rewards undermine intrinsic motivation (d = −0.36 to −0.40), and over a months-long exam horizon that trade is bad. The motivational engine stays **competence made visible** — the coverage banner, mastery events, and marks secured — which is what the SDT evidence points to anyway.

---

## Summary table

| # | Weakness | Fix | Priority | Evidence strength | Shipped in v9 |
|---|---|---|---|---|---|
| W1 | Retrieval gate at first contact | Probe + faded worked example | **P0** | Strong (worked example, expertise reversal, pretesting) | ✅ *First contact* section; `[Probe]`, `[Worked example]` |
| W2 | 95% bar; unauthorable controller | 85%/90% + no-fatal-error; 3-state rule | **P0** | Moderate–strong | ✅ *Grading thresholds*; *Difficulty controller* |
| W7 | Zero-decision UX not implemented | `next_session` block + 3-line opening | **P0** | Design (serves the stated goal) | ✅ `next_session` schema; *Session protocol → Opening* |
| W7b | No lesson boundary | Bounded Lesson unit with an offer to continue | **P0** | Design + behavioural | ✅ *The Lesson* |
| W6 | Confidence unused | Mandatory pre-verdict + hypercorrection routing | P1 | Strong | ✅ *Confidence and the hypercorrection loop* |
| W3 | Person-directed needling | Task-directed-only tone | P1 | Strong (FIT meta-analysis) | ✅ *Tone* — "wit targets the work, never the worker" |
| W4 | No discrimination practice | Confusable-pair mixed sets | P1 | Mixed — scoped deliberately | ✅ *Discrimination sets*; `[Discrimination]` |
| W5 | Loci over-applied | Target list-like content only | P2 | Weak evidence *for* loci ⇒ demote | ✅ **Exceeded** — fully decoupled optional add-on, off by default, never gates mastery |
| W8 | No return mechanism | Implementation intention; **no streaks** | P2 | Strong both directions | ✅ *Motivation*; session close step 18 |

Net effect on the prompt: **shorter, not longer.** P0-3, P0-4 and P2-8 remove more than P0-1 and P1-5 add — which is the right direction given VanLehn's interaction plateau.

---

## Sources

- VanLehn (2011), *The Relative Effectiveness of Human Tutoring, Intelligent Tutoring Systems, and Other Tutoring Systems*, Educational Psychologist 46(4) — https://www.tandfonline.com/doi/abs/10.1080/00461520.2011.611369
- Kluger & DeNisi (1996), *The Effects of Feedback Interventions on Performance*, Psychological Bulletin 119(2), 254–284 — https://cris.huji.ac.il/en/publications/the-effects-of-feedback-interventions-on-performance-a-historical/ · https://www.researchgate.net/publication/232458848_The_Effects_of_Feedback_Interventions_on_Performance_A_Historical_Review_a_Meta-Analysis_and_a_Preliminary_Feedback_Intervention_Theory
- Richland, Kornell & Kao (2009), *The pretesting effect*, JEP:Applied — https://learninglab.uchicago.edu/Pre-Testing_files/RichlandKornellKao.pdf
- *The Pretesting Effect: Exploring the Impact of Feedback and Final Test Timing* (2025), Journal of Cognition — https://pmc.ncbi.nlm.nih.gov/articles/PMC12292081/
- Wilson et al. (2019), *The Eighty Five Percent Rule for optimal learning*, Nature Communications 10:4646 — https://www.nature.com/articles/s41467-019-12552-4 · preprint: https://www.biorxiv.org/content/10.1101/255182v1.full
- Sweller/Kalyuga on worked examples and expertise reversal — https://www.cambridge.org/core/books/cambridge-handbook-of-expertise-and-expert-performance/cognitive-load-and-expertise-reversal/03F656FD334F23214426ACB4118FEBF9 · https://education.nsw.gov.au/content/dam/main-education/about-us/educational-data/cese/2017-cognitive-load-theory.pdf
- Kulik, Kulik & Bangert-Drowns (1990), *Effectiveness of Mastery Learning Programs: A Meta-Analysis*, RER 60(2) — https://journals.sagepub.com/doi/10.3102/00346543060002265
- Rohrer et al., interleaved mathematics practice RCT — https://gwern.net/doc/psychology/spaced-repetition/2019-rohrer.pdf · Brunmair & Richter meta-analysis context: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2019.00086/full
- Ondřej et al. (2025), *The method of loci: a systematic review and meta-analysis*, British Journal of Psychology — https://bpspsychub.onlinelibrary.wiley.com/doi/full/10.1111/bjop.12799
- Butterfield & Metcalfe, hypercorrection effect — https://link.springer.com/article/10.3758/s13423-011-0173-y · https://www.sciencedirect.com/science/article/abs/pii/S2211368114000242
- Gollwitzer & Sheeran (2006), *Implementation intentions and goal achievement: A meta-analysis* — https://cancercontrol.cancer.gov/sites/default/files/2020-06/goal_intent_attain.pdf
- Deci, Koestner & Ryan (1999), *A meta-analytic review of experiments examining the effects of extrinsic rewards on intrinsic motivation*, Psychological Bulletin 125 — https://home.ubalt.edu/tmitch/642/articles%20syllabus/Deci%20Koestner%20Ryan%20meta%20IM%20psy%20bull%2099.pdf
- SDT need-support meta-analyses — https://selfdeterminationtheory.org/wp-content/uploads/2024/02/2024_HowardSlempWang_Meta.pdf · https://pmc.ncbi.nlm.nih.gov/articles/PMC12276404/
