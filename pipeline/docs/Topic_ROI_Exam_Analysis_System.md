# Topic ROI & Exam Analysis System

*A systematic method for extracting the highest-ROI study topics from past computer science exams.*

---

## 0. The core idea in one line

Treat every exam topic like a feature on a product roadmap: rank it by **value delivered per unit of effort**, where "value" is the exam points it directly earns *plus* the points it unlocks elsewhere, and "effort" is the learning time scaled by how deeply the format forces you to know it.

$$\text{Study Priority Score} = \frac{\text{Expected exam value (direct + unlocked)}}{\text{Learning effort} \times \text{Format depth}}$$

Everything below is the engineering of that ratio.

---

## 1. The ROI Formula

### 1.1 The four inputs, normalized

| Symbol | Metric | Definition | Scale |
|---|---|---|---|
| $\text{Freq}$ | **Frequency** | **Recency-weighted** fraction of analyzed exams in which the topic appeared (Section 1.5). A probability proxy for "will it appear next time," with newer exams counting more. | 0–1 |
| $\text{G\_Marks}$ | **Grade Points** | **Recency-weighted** average marks the topic is worth *when it appears*, divided by total marks on the exam. Expresses weight as a fraction of one exam. | 0–1 |
| $\text{Diff}$ | **Difficulty / Learning Time** | Estimated hours to reach mastery, *including prerequisite knowledge*. Use hours directly so the final score reads as "exam value per hour." | hours (>0) |
| $N$ | **Interconnectedness (Node Value)** | How much *other* exam value this concept unlocks as a prerequisite. Computed from the prerequisite graph (Section 1.3), not guessed. | derived |

Normalizing $\text{Freq}$ and $\text{G\_Marks}$ to $[0,1]$ keeps the numerator interpretable as "fraction of an exam's marks" and prevents any single raw scale from dominating. Both are time-weighted so that a syllabus drifting over the years is tracked rather than averaged away (Section 1.5).

### 1.2 The formula

**Own value** (the points the topic earns directly) is the expected-value product of probability × payoff:

$$OV_i = \text{Freq}_i \times \text{G\_Marks}_i$$

**Unlock value** (the node-value insight) is the exam value of every topic this concept is a prerequisite for, discounted by a decay factor $d$:

$$U_i = d \sum_{j \in \text{unlocked}(i)} OV_j \qquad (d \approx 0.5)$$

**Total value** and the final **Study Priority Score (SPS)**:

$$V_i = OV_i + U_i \qquad\qquad \boxed{\;SPS_i = \dfrac{V_i}{\text{Diff}_i \times M_{\text{format},i}}\;}$$

where $M_{\text{format}}$ is the format-depth multiplier from Section 3. Multiply the result by 100 for readable numbers. Higher score → study earlier.

**Why this shape.** It is a value/effort ratio (the same skeleton as the RICE model, Section 2), so a topic earns priority either by being worth a lot or by being cheap to learn. Crucially, **interconnectedness lives in the numerator**, which lets a genuinely foundational concept overcome a punishing difficulty in the denominator — exactly the behavior you asked for ("a high-difficulty concept that unlocks 4 questions has high ROI; an isolated medium concept has lower ROI").

### 1.3 Two ways to compute Node Value $N$

- **Practical (one-step propagation):** $U_i = d\sum OV_j$ over direct dependents, as above. Needs only a list of "Topic A is required by Topics X, Y, Z." Fast, transparent, good enough for a single course.
- **Rigorous (PageRank on the prerequisite graph):** build the directed prerequisite graph and run weighted PageRank, seeding each node with its $OV$. This propagates value through *multi-hop* chains (a concept that unlocks a concept that unlocks an exam question), which is the literal academic method for ranking concept importance (Section 2). Use this if your syllabus has deep dependency chains.

Both feed the same $SPS$ formula; start with the practical version and upgrade only if rankings feel insensitive to foundational topics.

### 1.4 Worked example (verified)

Five past exams, 100 marks each, decay $d=0.5$. "Downstream OV" is the summed own-value of topics each concept unlocks.

| Topic | $\text{Freq}$ | $\text{G\_Marks}$ | $OV$ | $U$ | $V$ | Effort $\text{Diff}{\times}M$ | **SPS** | SPS *without* N |
|---|---|---|---|---|---|---|---|---|
| Big-O Notation (MCQ/short answer) | 1.0 | 0.08 | 0.080 | 0.100 | 0.180 | 4×1.2 = 4.8 | **3.75** | 1.67 |
| Pointers / Memory (write C code) | 1.0 | 0.18 | 0.180 | 0.150 | 0.330 | 10×2.2 = 22.0 | **1.50** | 0.82 |
| Recursion (write code) | 0.8 | 0.12 | 0.096 | 0.090 | 0.186 | 8×2.2 = 17.6 | **1.06** | 0.55 |
| Regular Expressions (short answer) | 0.4 | 0.06 | 0.024 | 0.000 | 0.024 | 5×1.3 = 6.5 | **0.37** | 0.37 |

Read the story the formula tells:

- **Big-O wins** — frequent, cheap to learn, lightly tested by format, and it unlocks analysis questions. The classic "cheap high-yield" topic the Pareto principle says to grab first.
- **Pointers is foundational but expensive.** Its node value nearly doubles its score (0.82 → 1.50), pulling a hard, code-tested topic up the ranking instead of letting raw difficulty bury it — the node-value mechanic doing its job.
- **Regex ranks last:** rare, isolated, unlocks nothing. The first thing to cut if time runs short.

### 1.5 Recency weighting (exam date)

A 2019 exam and a 2025 exam should not count equally if the syllabus is drifting. Each exam gets an exponential **recency weight** based on its age, and the metrics above become *weighted* averages.

**Per-exam weight.** For an exam $t$ years old (newest = 0):

$$w_t = \lambda^{\,t}, \qquad \lambda \in (0,1]$$

**Weighted metrics** (weights appear in both numerator and denominator, so $\text{Freq}$ stays in $[0,1]$):

$$\text{Freq}_i = \frac{\sum_{t\,\in\,\text{present}(i)} w_t}{\sum_{t\,\in\,\text{all exams}} w_t} \qquad\qquad \text{G\_Marks}_i = \frac{\sum_{t\,\in\,\text{present}(i)} w_t \, g_{i,t}}{\sum_{t\,\in\,\text{present}(i)} w_t}$$

where $g_{i,t}$ is topic $i$'s mark-fraction on exam $t$. Setting $\lambda = 1$ recovers the original flat averages.

**Format consistency sets the decay rate.** The only reason to discount an old exam is that it might test differently, so format-stability $S \in [0,1]$ (how similar past exams are in question count, type, and topic coverage) drives $\lambda$ directly:

$$\lambda = 1 - k\,(1 - S), \qquad k \approx 0.5$$

| Format consistency $S$ | $\lambda$ (per-year) | Half-life | Behavior |
|---|---|---|---|
| 1.0 (identical every year) | 1.00 | ∞ | No penalty — old exams count fully |
| **0.8 (assumed here)** | **0.90** | **≈ 6.6 yrs** | Gentle 10%/yr discount; old exams still matter |
| 0.5 | 0.75 | ≈ 2.4 yrs | Old exams fade quickly |
| 0.2 | 0.60 | ≈ 1.4 yrs | Effectively only the last few exams count |

**What it buys you.** Two topics each appearing in 3 of 5 exams (2021–2025, $\lambda = 0.9$) get *identical* flat frequency (0.60) but separate once weighted: a **rising** topic in the three newest exams scores $\text{Freq} = 0.66$, while a **fading** topic in the three oldest scores $\text{Freq} = 0.54$. The weighting distinguishes a concept trending *into* the syllabus from one trending *out* — invisible to a flat count, and the core reason to track exam dates at all.

**Apply the same weights to the format multiplier.** Compute $M_{\text{format}}$ (Section 3) from a *recency-weighted* format distribution, so the current testing style dominates. If questions have shifted from short-answer toward writing raw code, your effort estimate tracks where the exam is heading. Low $S$ thus matters twice: it steepens the decay *and* signals the format mix itself is moving.

### 1.6 Tuning knobs

The defaults are deliberately conservative; expose these and calibrate against one held-out exam (Section 4):

- **Format consistency $S$** (sets $\lambda$): your single most important temporal lever. Estimate it by comparing the oldest and newest exams' structure; $S = 0.8$ is a sensible default for a stable course.
- **Decay $d$** (0.3–0.7): higher rewards foundational topics more aggressively.
- **Frequency vs. grade emphasis:** if you prefer a tunable weighted sum over the strict expected-value product, use $OV_i = \text{Freq}_i^{\,a}\,\text{G\_Marks}_i^{\,b}$ and adjust exponents $a,b$.
- **Difficulty units:** hours give an interpretable score; a 1–10 subjective scale works too but loses the "per hour" meaning.

---

## 2. Existing frameworks that validate this approach

This system is not invented from scratch — it recombines four established, real-world methods, one per metric.

**Value-over-effort scoring — RICE / Weighted Scoring (product management).** The RICE model ranks roadmap items by $(\text{Reach}\times\text{Impact}\times\text{Confidence})/\text{Effort}$ — value in the numerator, effort in the denominator. Our mapping is almost one-to-one: Frequency ≈ Reach, Grade Points ≈ Impact, Node Value ≈ a confidence/leverage multiplier, Difficulty×Format ≈ Effort. This validates the *ratio structure* and the practice of normalizing heterogeneous criteria before combining them ([RICE framework](https://www.tempo.io/guides/rice-score-prioritization-framework-product-management), [weighted scoring model](https://www.tempo.io/blog/weighted-scoring-model)).

**Difficulty as a measurable parameter — Item Response Theory (IRT) / Rasch.** Psychometrics, used to calibrate the SAT and GRE, models each item with separate **difficulty** and **discrimination** parameters rather than treating all questions equally. This is the precedent for keeping $\text{Diff}$ (difficulty) distinct from $\text{G\_Marks}$ (grade weight): a question can carry many marks yet be easy, or few marks yet hard. The 2-parameter logistic (2PL) model in particular justifies weighting items by more than their point value ([IRT / item analysis](https://www.speedexam.net/blog/item-analysis-improve-exam-question-quality/), [Rasch item weighting](https://www.teachingenglish.org.uk/sites/teacheng/files/a_study_on_teachers_item_weighting_and_the_rasch_model_v2_0.pdf)).

**Interconnectedness — PageRank on Educational Knowledge Graphs.** This is the strongest validation of the node-value idea. Researchers build directed concept graphs with **prerequisite relations** and run **PageRank to rank which concepts are core** to a body of material — the exact operation in Section 1.3's rigorous variant. Prerequisite-aware graphs are an established tool for curriculum planning and learning-path design ([core-concept identification via knowledge graphs + PageRank](https://link.springer.com/article/10.1007/s42979-024-03341-y), [concept graph learning](https://www.cs.cmu.edu/~hanxiaol/publications/yang-wsdm15.pdf), [AI-assisted prerequisite knowledge graphs](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)).

**The strategic goal — Pareto (80/20) + Spaced Repetition.** The premise that ~20% of concepts drive ~80% of exam marks is the documented "high-yield" study strategy behind board-exam prep (NCLEX, USMLE). The ROI ranking *is* the mechanism for finding that 20%; spaced repetition is then the documented way to lock it in once identified, with expanding-interval schedules (e.g., 2–7–17–40 days) outperforming cramming ([Pareto for students](https://subjectguides.york.ac.uk/study-revision/pareto-principle), [spaced repetition for board exams](https://www.iatrox.com/blog/spaced-repetition-board-exams-science-behind-iatrox-adaptive-learning)).

In short: the **ratio** comes from RICE, the **difficulty parameter** from IRT, the **node value** from knowledge-graph PageRank, and the **why** from Pareto. Each is a battle-tested analog, which is good evidence the combined heuristic is sound.

---

## 3. The Format Variable

**The problem.** *How* a concept is tested changes the depth of mastery required, and therefore the true cost. Recognizing the correct definition of a linked list in a multiple-choice question is a fraction of the work of writing, compiling, and debugging linked-list code under time pressure. Two questions on the same topic worth the same marks are not the same investment.

**The model.** Format is a **multiplier on effort**, $M_{\text{format}} \ge 1$, anchored to Bloom's taxonomy (recognition → recall → application → synthesis). It scales the difficulty $\text{Diff}$ in the denominator because the format dictates the *mastery threshold* — the minimum competence you must reach before the topic pays out.

| Format (how it's tested) | Bloom level | Cognitive demand | $M_{\text{format}}$ |
|---|---|---|---|
| Multiple choice, true/false, matching | Recognition | Recognize the right answer among options | **1.0** |
| Define, fill-in-the-blank, short answer | Cued recall | Produce a fact from memory with a prompt | **1.3** |
| Explain, derive, trace code execution by hand | Comprehension / application | Reconstruct a process and reason about it | **1.6** |
| Write / debug raw code, proofs, system design | Synthesis / production | Generate a correct artifact from a blank page | **2.2** |

**How to apply it per topic.** A topic rarely has one format. For each topic, take the **format distribution** across past exams weighted by marks, and use the mark-weighted average multiplier. If Pointers is tested as 70% code-writing (2.2) and 30% short-answer (1.3), then $M = 0.7(2.2)+0.3(1.3) = 1.93$. This rewards topics that, despite appearing often, are only ever tested shallowly — they're cheap to "exam-proof" even if deep mastery would take longer.

**Two refinements worth noting.** (1) Format can also raise $\text{G\_Marks}$, since code/design questions are often worth more marks — let that flow through naturally from the data rather than double-counting it in $M$. (2) The same multiplier doubles as a **study-mode prescription**: a topic dominated by $M=2.2$ tells you to practice by *writing code*, not re-reading notes — the ranking and the method-of-study fall out of the same number.

---

## 4. The Execution Pipeline

A reliable extraction pipeline obeys three rules: **one job per prompt** (decomposition beats one mega-prompt), **structured JSON in and out** (so stages compose and results merge), and a **controlled vocabulary** (so "pointers," "pointer arithmetic," and "memory management" don't fragment into three weak topics). Below is a copy-pasteable chain. Run Stages 1–3 once per exam, then 4–6 across the merged corpus.

### Stage 0 — Corpus prep (you, once)

Collect every past exam as text. Convert PDFs/scans to clean text (OCR if needed). For each exam record `exam_id`, `year`, and `total_marks`. Put one exam per file.

### Stage 1 — Atomic question extraction

> **Prompt:** You are an exam-parsing engine. From the exam text below, extract every distinct question and sub-question as a JSON array. For each item output: `{ "q_id", "verbatim_text", "marks", "format" }`. `format` must be one of: `mcq`, `short_answer`, `explain_derive`, `produce_code_proof_design`. Do not infer topics yet. Do not summarize — preserve enough text to identify the concept. If marks are not stated, set `"marks": null`.
> **Exam text:** `<<paste one exam>>`

### Stage 2 — Topic tagging against a controlled taxonomy

Maintain a growing `taxonomy.json` (canonical topic list). For the first exam, let the model propose it; for every later exam, **pass the existing taxonomy in** so it reuses labels instead of inventing synonyms.

> **Prompt:** Here is the canonical topic taxonomy: `<<taxonomy.json>>`. For each question object below, assign one or more `topic` labels **from the taxonomy**. If — and only if — a genuinely new concept appears, propose a new canonical label and add it under `new_topics`. Output each question augmented with a `"topics": [...]` field. Prefer existing labels; merge near-duplicates.
> **Questions:** `<<Stage 1 output>>`

After each exam, append `new_topics` to `taxonomy.json` (a quick human glance here prevents topic drift).

### Stage 3 — Per-topic metric aggregation

> **Prompt:** Across all tagged questions provided (all exams), aggregate by topic. Each exam carries an `exam_year`. For each topic output: `{ "topic", "exam_years_present": [...], "marks_per_exam": {year: mark_fraction}, "format_distribution": {format: mark_fraction}, "Diff_hours": <estimate>, "difficulty_rationale": "<1 sentence>", "prerequisites": [topics this depends on] }`. Keep results indexed by year so recency weights can be applied in Stage 5 — do **not** collapse to flat averages here. Estimate `Diff_hours` as time for a typical student to reach exam-ready mastery **including listed prerequisites**, using this rubric: trivial/recall 1–2h; standard procedure 3–6h; multi-step or abstract 7–12h; deep/compositional 13h+.
> **Tagged questions (all exams):** `<<concatenated Stage 2 outputs>>` · **Exam years + total marks per exam:** `<<from Stage 0>>`

### Stage 4 — Prerequisite graph + Node Value

> **Prompt:** Using the `prerequisites` fields, build the directed prerequisite graph (edge A→B means A is required for B). For each topic compute `unlocked_topics` (everything depending on it, directly) and report the graph as an adjacency list. Flag any cycles for me to resolve.

This produces the `unlocked(i)` sets for the formula. (For the rigorous variant, hand the adjacency list to a 5-line PageRank script rather than the LLM.)

### Stage 5 — Scoring & ranking

> **Prompt:** Compute the Study Priority Score for each topic. First set the recency parameters: format consistency `S` (default 0.8), per-year decay $\lambda = 1 - 0.5(1-S)$, and for each exam year an age (newest = 0) and weight $w_t = \lambda^{\text{age}}$. Steps: (1) $\text{Freq} = \big(\sum_{\text{years present}} w_t\big) / \big(\sum_{\text{all years}} w_t\big)$; (2) $\text{G\_Marks} = \big(\sum_{\text{present}} w_t\,g_t\big)/\big(\sum_{\text{present}} w_t\big)$ where $g_t$ is the year's mark-fraction; (3) $OV=\text{Freq}\,\text{G\_Marks}$; (4) $U = 0.5\times\sum OV$ over `unlocked_topics`; (5) $V=OV+U$; (6) $M$ = **recency-weighted** mark-weighted format multiplier using `{mcq:1.0, short_answer:1.3, explain_derive:1.6, produce_code_proof_design:2.2}` (weight each year's format mix by $w_t$); (7) $SPS = 100\times V/(\text{Diff\_hours}\times M)$. Output a table sorted by $SPS$ descending with all intermediate columns shown (include $\text{Freq}$ and its flat counterpart so recency effects are visible), then mark the cumulative top 20% of topics by $V$ as **Tier 1 (high-yield core)**.
> **Data:** `<<Stage 3 + Stage 4 outputs>>` · **Format consistency $S$:** `<<your estimate, default 0.8>>`

### Stage 6 — Validation (do not skip)

1. **Held-out check:** exclude your most recent exam from Stages 1–5, then verify that its actual questions concentrate in your Tier-1 topics. If they don't, your weights are off.
2. **Sensitivity sweep:** re-run Stage 5 with $d \in \{0.3, 0.5, 0.7\}$ and $S \in \{0.6, 0.8, 1.0\}$. Topics that swing with $d$ are graph-sensitive (check their prerequisite edges); topics that swing with $S$ are recency-sensitive — confirm whether they're genuinely rising/fading or just sparse.
3. **Face-validity pass:** eyeball the bottom of the ranking. Anything obviously important sitting near the bottom usually means a missing prerequisite edge (under-counted node value) or a difficulty over-estimate.
4. **Output:** a ranked study plan — attack Tier 1 first, schedule it on a spaced-repetition interval (2–7–17–40 days), and let the format multiplier dictate *how* you practice each one.

---

### Pipeline at a glance

| Stage | Input | Output | Run frequency |
|---|---|---|---|
| 0 Prep | Raw exams | Clean text + metadata | Once |
| 1 Extract | One exam | Questions w/ marks & format | Per exam |
| 2 Tag | Questions + taxonomy | Topic-labeled questions | Per exam |
| 3 Aggregate | All tagged questions | Per-topic metrics | Once (corpus) |
| 4 Graph | Prerequisites | Adjacency + unlocked sets | Once (corpus) |
| 5 Score | Metrics + graph | Ranked SPS table, Tier 1 | Once (corpus) |
| 6 Validate | Ranking + held-out exam | Confidence + study plan | Once |

---

*Start with the practical node-value variant and the default weights, run one held-out validation, then tune. The formula is intentionally simple enough to audit by hand and rich enough to make the non-obvious call — promoting the expensive foundational topic over the cheap isolated one.*
