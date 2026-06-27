# Solution Landscape

*Companion to `learning_system_report.md` (Stage 1 — Problem Analysis). Standalone file; the Stage 1 report is unchanged.*

**Researched:** June 2026 · web-search-based, current approaches only.
**Constraints applied throughout** — flagged as **[BEST FIT]** for the project's actual setup:

> **Solo developer. Claude Pro subscription + Claude Code. No external budget. All state lives in local files (markdown / JSON / xlsx). No team, no server, no multi-user.**

This means the bar for "best fit" is: works inside a single Claude prompt/session, stores state in plain files, needs no paid SaaS, no vector DB, no training pipeline, and no second engineer to maintain. Heavier research-grade options are listed so you know what exists and what you're trading away — but the **[BEST FIT]** flag always points at the prompt-and-file-native option.

A note on what this section is *not*: most of the published "solutions" below are research systems (MWPTutor, DDKT, SocraticAI). You can't install them. What you *can* do is lift their **design pattern** into the tutor system prompt. So each problem gives you the named systems for credibility and the extractable pattern for implementation.

---

## Problematic 1 — Traditional Studying Is Ineffective and Demotivating

### 1.1 — Passive Learning: No Active Thinking Before Answers [CRITICAL]

**Top current solutions**

1. **Finite-state / functional-slot tutoring (MWPTutor, "AutoTutor meets LLMs").** Instead of letting the LLM free-generate each turn, the conversation is driven by a fixed state machine — pump for the student's attempt → Socratic hint → increasingly directive prompt → only-then reveal. The LLM fills *slots* inside that machine rather than choosing what kind of turn to make. The paper makes "don't reveal the answer" a *personality trait* and "reach the correct answer" the *goal*, which is a concrete prompt technique you can copy verbatim. *Trade-off:* full FSM is engineering you don't need; the slot ordering and the goal/personality split are the parts worth stealing.
2. **Khanmigo's Socratic gate.** Deliberately refuses to give the solution; opens with "What have you tried? Where are you stuck? What's the first step?" and only ever questions, never reveals. A 2025 Harvard RCT on active-learning-designed AI tutoring reported students learning roughly twice as much in less time. *Trade-off:* it's a closed product — you get the design principle, not the code, and Khanmigo itself uses a moderation layer to stop answer-extraction that you'd have to approximate in-prompt.
3. **Structured-input gating (SocraticAI).** Requires the student to submit their current understanding / attempted solution / relevant work *before* any feedback is generated. *Trade-off:* adds friction; for a solo motivated user that friction is the point, not a cost.

**[BEST FIT]** Your tutor prompt already does this ("Always make me retrieve first. Never explain a concept before asking me to attempt it"). Harden it with the two transferable patterns: **(a)** the MWPTutor goal/personality framing ("revealing the answer is against your nature; your job is to get *me* to the answer"), and **(b)** a SocraticAI-style hard precondition — Claude must not emit any rubric, hint past level 1, or explanation until the student has submitted *something*. Both are pure prompt edits, zero infrastructure. This is the highest-leverage change in the whole report and it costs nothing.

**Pitfall coverage (Stage 1 flagged: cognitive overload from questioning misaligned with readiness).** The research literature explicitly warns that Socratic questioning "misaligned with a learner's cognitive readiness can lead to cognitive overload." Your existing ramp (D+1 rungs, gated) is exactly the mechanism that prevents this — the Socratic gate should fire *within* the current rung's difficulty, not above it. Keep the gate and the ramp coupled.

*Sources:* [AutoTutor meets LLMs (arXiv 2402.09216)](https://arxiv.org/pdf/2402.09216) · [LLM-Powered Tutoring Solutions (EmergentMind)](https://www.emergentmind.com/topics/llm-powered-tutoring-solutions) · [SocraticAI literature review](https://www.themoonlight.io/en/review/socraticai-transforming-llms-into-guided-cs-tutors-through-scaffolded-interaction) · [Socratic Students (arXiv 2512.13102)](https://arxiv.org/html/2512.13102v3) · [Khanmigo from 68k to 700k users](https://aiforcause.org/stories/khanmigo-ai-tutor)

---

### 1.2 — Lack of Motivational Context: "Why Does This Even Matter?" [CRITICAL]

**Top current solutions**

1. **Keller's ARCS model (Attention, Relevance, Confidence, Satisfaction).** The standard instructional-design framework for engineering motivation. 2025 work pairs it directly with AI chatbots (AIC-ARCS) and a systematic review confirms its effect on teaching effectiveness in higher ed. The **Relevance** component is your 1.2 fix made formal: open with why-this-matters before the abstract definition. *Trade-off:* ARCS is a checklist, not a tool — it tells you *what* to include, not *how* to phrase it. Pairs naturally with an LLM doing the phrasing.
2. **Exam-relevance framing from your own pipeline.** You already compute marks-per-topic in `Exam_ROI_Pipeline.xlsx`. Surfacing "this topic = X% of your exam score" *is* the ARCS Relevance hook, and you have the data nobody else does. *Trade-off:* none — it's data you already produce, currently underused at the motivation layer.
3. **Goal-framed openers ("to solve problems like this…").** Frame the concept from the student's goal before defining it abstractly — a relevance technique repeatedly recommended in the ARCS literature.

**[BEST FIT]** Add a one-line **ARCS-Relevance opener** to the tutor prompt's per-topic intro, fed by two sources you already have: the exam-coverage number from the ROI sheet ("secures ~X marks") and a one-sentence real-world use case. No new files, no tools — a prompt rule plus a column you already computed.

**Pitfall coverage.** The Stage 1 risk is disengagement "within minutes." ARCS treats Attention and Relevance as the *first* two letters deliberately — they're front-loaded for exactly this reason. Tying the hook to the real exam-mark number (not a generic "this is important") is what makes it land for a motivated exam-prep user.

*Sources:* [Keller's ARCS Model (Pressbooks)](https://isu.pressbooks.pub/thuff/chapter/kellers-arcs-model-of-motivational-design/) · [AI chatbot-based ARCS approach (Interactive Learning Environments 2025)](https://www.tandfonline.com/doi/abs/10.1080/10494820.2025.2454443) · [ARCS systematic review (Discover Education 2025)](https://link.springer.com/article/10.1007/s44217-025-00674-5)

---

### 1.3 — No Narrative / "Lore": Missing Emotional Connection [HIGH]

**Top current solutions**

1. **ARCS-Attention via narrative.** The ARCS literature explicitly recommends "language, analogies, or stories that learners can relate to" to win and hold attention. A 2–3 sentence origin story is a textbook Attention device. *Trade-off:* over-narration becomes the "history lesson" failure Stage 1 itself warns about — needs a hard length cap.
2. **LLM-generated origin stories on demand.** Claude can produce a calibrated 2–3 sentence "who discovered this and what problem it solved" for essentially any CS concept with no source files. *Trade-off:* factual drift on obscure attributions — keep lore to well-established history (e.g., Canny 1986, Harris-Stephens 1988) and let the student flag anything that smells wrong.
3. **Lore density as a user preference.** Stage 1 already proposes this; the ARCS framing supports it — Attention needs vary by learner.

**[BEST FIT]** A prompt rule: *optional 2–3 sentence origin story, capped, only when it makes the abstraction feel inevitable rather than arbitrary, with a `lore: on/off/brief` switch.* Pure prompt. The cap is the whole solution — the science says narrative helps, Stage 1 correctly says the risk is overrun, so the spec is "narrative with a hard ceiling."

**Pitfall coverage.** Directly addresses the Stage 1 calibration pitfall ("enough lore to inspire, not so much it becomes a history lesson") by making density a switch and capping length in the prompt rather than leaving it to Claude's discretion per session.

*Sources:* [Keller's ARCS Model (eLearning Industry)](https://elearningindustry.com/arcs-model-of-motivation) · [ARCS systematic review (Discover Education 2025)](https://link.springer.com/article/10.1007/s44217-025-00674-5)

---

### 1.4 — No Analogies or Concrete Anchors for Abstract Concepts [HIGH]

**Top current solutions**

1. **LLM-generated analogies, student-selected (CHI 2025, "Unlocking Scientific Concepts").** Controlled in-class study: LLM analogies improved understanding, but *required human guidance to prevent over-reliance and overconfidence*. Critically: when the *student* specifies the analogy target, analogies are more diverse, creative and relevant than model-only generation. *Trade-off:* unsupervised analogies can mislead — the fix is student involvement, which is exactly your method-of-loci pedagogy.
2. **Dual-coding theory (Paivio).** Concrete, imageable material is recalled roughly *twice as well* as matched abstract material because it's encoded in both verbal and visual systems. This is the scientific basis for pairing every abstract CS concept with a concrete image. *Trade-off:* none conceptually — it's the mechanism your loci layer already exploits.
3. **Student-generated analogies with LLM (CS1 study).** Having students craft analogies *with* the model beats model-only on creativity and relevance.

**[BEST FIT]** This problem and your loci layer are **the same problem**. The analogy-generation literature says the strongest results come when the *student* proposes and the model *refines* — which is the exact user-first encoding ownership you already resolved for loci. Reuse the loci evaluation rubric (information accuracy + retrieval power) as the analogy rubric. One mechanism covers 1.4 and the entire loci redesign. No new infrastructure.

**Pitfall coverage.** Stage 1's pitfall here (and the loci analysis's) is *anchoring the student to the model's imagery*. The CHI 2025 finding is the empirical backing for your user-first decision: model-only analogies cause over-reliance and overconfidence; student-proposed ones don't. The research validates the architectural choice you already made.

*Sources:* [Unlocking Scientific Concepts (arXiv 2502.16895)](https://arxiv.org/abs/2502.16895) · [CHI 2025 proceedings](https://dl.acm.org/doi/10.1145/3706598.3714313) · [Dual-Coding Theory (ScienceDirect)](https://www.sciencedirect.com/topics/neuroscience/dual-coding-theory) · [Student-generated analogies in CS1 (arXiv 2403.09409)](https://arxiv.org/html/2403.09409v1)

---

### 1.5 — Dry, Complex Academic Language [MEDIUM]

**Top current solutions**

1. **LLM register-shifting (plain-language rewrite).** The single thing LLMs do most reliably: rewrite dense passive-voice textbook prose into short, active, conversational sentences calibrated to a stated level. *Trade-off:* over-simplification can drop precision that matters for an exam — guard by keeping the formal term available after the plain explanation lands.
2. **Jargon-deferral.** Introduce the concept in plain words first, name the technical term *after* understanding — a standard cognitive-load reduction. *Trade-off:* none; cheap and effective.
3. **CEFR/level-tagged delivery.** Position-paper work on LLM tutors in education advocates explicitly tagging target level so the model holds register consistently. *Trade-off:* requires you to state the level once.

**[BEST FIT]** A prompt register rule: *plain conversational English, short sentences, active voice; introduce jargon only after the concept lands; keep the formal term for exam accuracy.* This is the lowest-risk item in the report — entirely mechanical, no files, no tools, and Claude's native strength.

**Pitfall coverage.** The implicit pitfall is stripping exam-necessary precision. The "keep the formal term after the plain explanation" clause prevents the simplification from costing marks — the student still meets the exact terminology the `parsed/*.json` exemplars demand.

*Sources:* [Position: LLMs Can be Good Tutors (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.885.pdf) · [Keller's ARCS Model (eLearning Industry)](https://elearningindustry.com/arcs-model-of-motivation)

---

## Problematic 2 — Lack of Progressive Difficulty (The Cognitive Load Problem)

### 2.1 — No Knowledge of the Exact Exam Format and Question Types [CRITICAL]

**Top current solutions**

1. **Question-type taxonomy + exemplar linking.** Classify each exam question by type (calculation / proof / conceptual / multi-step application) and link every prioritized topic to real exemplars. This is the prerequisite Stage 1 correctly identifies for everything else in Problematic 2. *Trade-off:* requires a one-time parse of past exams.
2. **Your existing pipeline (`parsed/*.json` + `taxonomy.json`).** You *already built this.* `parsed/*.json` holds real past-exam questions tagged by topic with marks and format; `taxonomy.json` holds per-topic difficulty. The tutor prompt already names them as "terminal targets … never invent exam style — derive it from these exemplars." *Trade-off:* the question-*type* classification (calc/proof/conceptual) may not yet be an explicit field — worth adding.
3. **LLM difficulty prediction from question text (DDKT, Sci. Reports 2025).** Fine-tuned LLMs estimate unseen-question difficulty from the text itself. *Trade-off:* fine-tuning is out of scope for you; the *idea* — let Claude read an exemplar and infer its type/depth — is in scope and free.

**[BEST FIT]** This problem is largely **already solved** by your CLI pipeline — that's the project's genuine edge. The only gap is making **question type** a first-class field. Add a `question_type` tag (calculation / proof / conceptual / multi-step) to each entry in `parsed/*.json` (or derive it on the fly by having Claude classify the exemplar). Pure local-file edit, no tools.

**Pitfall coverage.** Stage 1 calls this "a prerequisite for everything else." Because you already produce the exemplar files, you've de-risked the dependency that the rest of Problematic 2 hangs on. The remaining work is one tag, not a system.

*Sources:* [Difficulty-aware programming knowledge tracing via LLMs (Scientific Reports 2025)](https://www.nature.com/articles/s41598-025-96540-3) · [LLM Difficulty Prediction (EmergentMind)](https://www.emergentmind.com/topics/llm-based-difficulty-prediction)

---

### 2.2 — Jumping Straight to Exam-Level Exercises [CRITICAL]

**Top current solutions**

1. **Faded worked examples (Renkl & Atkinson).** The best-established cognitive-load technique for this exact problem: start from a full worked example, then *successively fade* steps — remove one solution step at a time so the student takes on increasing responsibility, ending at an unscaffolded problem. This *is* your ramp (rung 2 = worked skeleton with one step blanked → middle = skeleton removed → final = no scaffold), and it has decades of evidence behind it. *Trade-off:* none — it's the gold standard and you've already adopted its shape.
2. **Parsons problems as an intermediate scaffold (CS-specific, 2024).** For *code-writing* topics specifically, Parsons problems (reorder given code blocks) are a validated middle rung between recognition and free coding, with faded and pseudocode variants. Especially relevant for your CV exam's coding questions. *Trade-off:* only applies to code-output topics, not proofs/derivations.
3. **Mastery-gated progression (Bloom).** Gate each level behind success on the prior one — the formal mastery-learning structure your prompt already enforces.

**[BEST FIT]** Your D+1 ramp already *is* faded worked examples + mastery gating — keep it, and now you can cite the science (Renkl's fading procedure) rather than treating it as a homegrown heuristic. The one *addition* worth making: for code-writing topics, insert a **Parsons-problem rung** (reorder shuffled code blocks) between guided application and partial exam. Claude can generate these in-prompt from any code exemplar — no tool, just an instruction for code-typed topics.

**Pitfall coverage.** Stage 1's pitfall is the overload→frustration→dropout spiral from starting at exam level. Faded worked examples are *the* documented countermeasure (they reduce extraneous cognitive load during skill acquisition). The Parsons addition targets the specific CS failure mode where a student understands an algorithm but can't yet produce syntactically correct code from a blank page.

*Sources:* [Worked-example effect (Wikipedia, Renkl/Atkinson fading)](https://en.wikipedia.org/wiki/Worked-example_effect) · [How Fading Worked Solution Steps Works (Instructional Science)](https://link.springer.com/article/10.1023/B:TRUC.0000021815.74806.f6) · [Parsons problems as scaffolding (arXiv 2512.22407)](https://arxiv.org/pdf/2512.22407) · [Faded worked examples (ERIC EJ1086007)](https://files.eric.ed.gov/fulltext/EJ1086007.pdf)

---

### 2.3 — No System to Stay in the "Sweet Spot" of Difficulty [HIGH]

**Top current solutions**

1. **The 85% Rule (Wilson et al., Nature Communications 2019).** Puts the "sweet spot" on a mathematical footing: for gradient-descent-style learning, the optimal training accuracy is ~85% (error ~15.87%). This is the empirical target for your "~70–85% passable" calibration — and 85% is precisely the *upper* edge of your stated band. *Trade-off:* it's a target, not a controller — you still need a rule that adjusts when you're off it.
2. **Bayesian Knowledge Tracing (BKT).** The classic interpretable mastery estimator: per-skill parameters for prior knowledge, learning transition, slip, and guess. Simple, transparent, runs on a sequence of pass/fail. *Trade-off:* needs a history store and parameter fitting; weak on non-linear skill progression. Overkill for a solo file-based setup.
3. **LLM-driven knowledge tracing (DDKT, arXiv 2502.19915).** Combines LLM-assessed difficulty, statistical difficulty from historical correctness, and the student's *subjective perceived difficulty*; handles cold-start better than BKT. *Trade-off:* a full research model — not deployable in your stack, but its **three-signal** idea (objective + statistical + self-reported) is a directly usable heuristic.

**[BEST FIT]** A **lightweight 85%-rule controller in the prompt**, driven by the pass/fail history you *already* write to `progress.json`. Rule: if the running success rate on a rung is above ~85% → skip/advance faster; below ~70% → insert a bridge question or scaffold hint; in band → hold. Borrow DDKT's third signal cheaply by asking the student a one-word confidence after each answer and storing it. No BKT parameter fitting, no model — just a threshold rule over data you already log. This upgrades your *static* ramp into a *dynamic* one, which is exactly the 2.3 gap.

**Pitfall coverage.** Stage 1's pitfall is static ramps drifting out of the productive zone as the student's pace varies. The 85% controller closes the loop. The transparency point Stage 1 raises ("You're at level 3 of 5") is free here — `progress.json` already tracks `current_rung`, so surface it in the coverage banner.

*Sources:* [The Eighty Five Percent Rule (Nature Communications 2019)](https://www.nature.com/articles/s41467-019-12552-4) · [Learning optimized at 15% failure (ScienceDaily)](https://www.sciencedaily.com/releases/2019/11/191105113457.htm) · [Bayesian Knowledge Tracing (EmergentMind)](https://www.emergentmind.com/topics/bayesian-knowledge-tracing) · [DDKT dual-channel difficulty (arXiv 2502.19915)](https://arxiv.org/abs/2502.19915)

---

### 2.4 — No Mode for Going Beyond Exam-Level Difficulty [MEDIUM]

**Top current solutions**

1. **Unlockable "mastery mode" (edge-case + cross-topic generation).** Once a student consistently clears exam-level, generate harder items that explore edge cases or *combine* topics — and flag clearly as beyond-exam scope so it isn't confused with exam prep. Stage 1 already proposes this; the cross-topic combination is the high-value part. *Trade-off:* can distract from passing if unlocked too early — gate it strictly behind mastery.
2. **Cross-topic synthesis using `taxonomy.json` connections.** Your taxonomy already encodes connection value `C` and prerequisites. That graph is exactly what you'd traverse to generate *cross-topic* mastery questions (e.g., a question spanning Harris corners *and* SIFT scale-space). *Trade-off:* none — it reuses a structure you already have.
3. **Desirable-difficulty extension.** The Bjork framework supports deliberately harder-than-comfortable practice for transfer; mastery mode is its natural home. *Trade-off:* only appropriate *after* mastery, never before.

**[BEST FIT]** A prompt-gated mastery mode that fires *only* on topics already marked `mastered`, generating (a) edge-case variants of the final-rung exemplar and (b) cross-topic questions traversing `taxonomy.json`'s `C`/prerequisite links. Reuses two things you already have (the mastery flag and the connection graph). Strictly optional, strictly post-mastery — which respects Stage 1's "secondary to passing" ranking.

**Pitfall coverage.** Stage 1's pitfall is students confusing beyond-exam content with exam prep. The hard gate (`mastered` only) plus an explicit "BEYOND EXAM SCOPE" banner prevents the confusion and the premature-distraction failure mode.

*Sources:* [The Eighty Five Percent Rule (Nature Communications 2019)](https://www.nature.com/articles/s41467-019-12552-4) · [Desirable difficulties in adaptive tutoring (arXiv 2605.04816)](https://arxiv.org/html/2605.04816)

---

## Cross-Cutting Layer — Spaced Repetition & Method of Loci

These aren't separate Stage 1 sub-problems, but they underpin the spaced-review and loci mechanisms the tutor prompt already runs, and the research directly addresses pitfalls flagged in `loci-method-analysis.md`.

### Spaced repetition scheduling

**Top current solutions**

1. **FSRS (Free Spaced Repetition Scheduler).** Open-source, ML-based, now the default-available algorithm in Anki across all platforms; needs fewer reviews than SM-2 for the same retention and handles delayed reviews far better. *Trade-off:* designed for flashcard apps — adopting Anki itself means a second tool outside your file-based loop.
2. **SM-2 (SuperMemo 2).** The classic, simple, fully specified interval algorithm. Easy to reimplement in a few lines over `review_queue`. *Trade-off:* less efficient than FSRS, but trivially portable into your JSON.
3. **Your current `review_queue` (oldest-first).** Simplest possible scheduler; already implemented. *Trade-off:* ignores per-item difficulty and forgetting curves.

**[BEST FIT]** Keep state in `progress.json`; upgrade `review_queue` from oldest-first to a **minimal SM-2 interval** per topic (store `last_seen`, `interval`, `ease`; on PASS lengthen, on FAIL reset). This stays 100% inside your file-based loop with no external app, while capturing most of the spacing benefit. FSRS is the better algorithm if you ever decide to mirror cards into Anki — noted as the upgrade path, not the [BEST FIT] given your no-external-tool constraint.

**Why it matters (evidence).** Combining spaced practice with retrieval practice is synergistic: meta-analysis puts retrieval practice at g ≈ 0.50 over rereading, and the two largest "what works" reviews rank distributed practice + practice testing as the two most effective techniques across 169k+ participants. Your tutor already does retrieval; proper spacing is the multiplier.

*Sources:* [FSRS4Anki (GitHub)](https://github.com/open-spaced-repetition/fsrs4anki) · [What algorithm does Anki use (Anki FAQ)](https://faqs.ankiweb.net/what-spaced-repetition-algorithm) · [Spaced + retrieval synergy (Evidence Based Education)](https://evidencebased.education/resource/retrieval-and-spaced-practice-study-strategies-that-must-be-combined/) · [Spaced retrieval meta-analysis (IJ STEM Education 2024)](https://link.springer.com/article/10.1186/s40594-024-00468-5)

### Method of loci — the one pitfall to respect

The 2025 *British Journal of Psychology* systematic review and meta-analysis confirms the method of loci improves recall (a VR study showed +22.2% on second use; medical students use it for board exams) **but explicitly flags that it is less effective for abstract concepts** — which is most of a CV/CS syllabus.

**This is the load-bearing pitfall for your loci redesign.** The fix the research points to is **dual coding via concrete imagery**: abstract concepts must be *converted* into concrete, imageable, emotionally charged scenes before they'll stick (concrete material is recalled ~2× as well). That is precisely what your existing encodings already do well — e.g., the Harris structure-tensor "two detectives + pink swan" scene turns pure linear algebra into a concrete narrative. So:

- The **retrieval-power axis** of your loci rubric is doing the real work — it's the operationalization of dual coding. Score it on: concrete physical object anchored to the station, physical action, emotional charge (bizarre/violent/funny), and *structural* fidelity to the concept's defining properties.
- The **user-first ownership** decision is empirically backed (1.4 above): model-supplied imagery causes over-reliance; student-generated encodings don't. Keep Claude as evaluator, not author.
- For genuinely abstract concepts that resist a single image, the meta-analysis's limitation is the signal to allow **multi-locus encoding** (the `loci-method-analysis.md` gap "no handling of multi-stage encoding") rather than forcing a 1:1 mapping.

*Sources:* [Method of loci meta-analysis (British Journal of Psychology 2025)](https://bpspsychub.onlinelibrary.wiley.com/doi/full/10.1111/bjop.12799) · [VR memory palace feasibility (PMC9540171)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9540171/) · [Dual-Coding Theory (ScienceDirect)](https://www.sciencedirect.com/topics/neuroscience/dual-coding-theory) · [Pharmacology retention via method of loci (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0022356524176197)

---

## Summary — Best-Fit Solution per Problem

| # | Problem | [BEST FIT] (solo / Claude Pro / local files) | New infra needed? |
|---|---|---|---|
| 1.1 | Passive learning | Harden Socratic gate: MWPTutor goal/personality framing + structured-input precondition | None (prompt) |
| 1.2 | Missing motivation | ARCS-Relevance opener fed by ROI exam-mark % | None (prompt + existing data) |
| 1.3 | No lore | Capped 2–3 sentence origin story with `lore` switch | None (prompt) |
| 1.4 | No analogies | Reuse loci user-first rubric (accuracy + retrieval power) for analogies | None (shared with loci) |
| 1.5 | Dry language | Plain-register rule; defer jargon; keep formal term for exam accuracy | None (prompt) |
| 2.1 | Exam format unmapped | Already built (`parsed/*.json`); add `question_type` tag | One local-file field |
| 2.2 | Jump to exam level | Faded worked examples (already your ramp) + Parsons rung for code topics | None (prompt) |
| 2.3 | No sweet-spot control | 85%-rule controller over `progress.json` pass/fail + 1-word confidence | None (logic over existing data) |
| 2.4 | No beyond-exam mode | Mastery-gated mode; cross-topic via `taxonomy.json` connections | None (reuses mastery flag + graph) |
| ✚ | Spaced repetition | Minimal SM-2 intervals in `review_queue` (FSRS = future upgrade path) | None (JSON fields) |
| ✚ | Loci / abstract concepts | Dual-coding via concrete imagery; retrieval-power rubric; user-first; multi-locus for abstract | None (rubric + schema) |

**The through-line:** almost every best-fit solution is a *prompt rule or a small field added to a file you already produce*. The project's real asset is the CLI pipeline (`parsed/*.json`, `taxonomy.json`, ROI sheet) — it already solves the hardest prerequisite (2.1) and supplies the data that powers the motivation hook (1.2), the dynamic controller (2.3), and the beyond-exam mode (2.4). The research doesn't ask you to add infrastructure; it asks you to name what you've built (faded worked examples, the 85% rule, dual coding) and tighten the prompt around it.

---

*End of Solution Landscape. Stage 1 report (`learning_system_report.md`) left unchanged, as instructed.*
