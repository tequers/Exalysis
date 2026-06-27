# Solution Research: Connections Module + Active Recall Notes

*Researched against the open problems raised in `critique-mindmap-graph-connections.md`, in the context of `TUTOR_SYSTEM_PROMPT_v2.md`.*

## Problem statement

The critique left two modules with unresolved design questions. **Module A (Connections)** needs (1) a definition of what makes a student-articulated connection "valid" enough to persist, (2) a stated relationship between a `connections.json` file and the existing `taxonomy.json` prerequisite/connection data, and (3) a retrieval mechanic so the file is a learning tool, not a write-only archive. **Module B (Active Recall Notes)** needs a prior answer before implementation: is a full end-of-session brain dump the right format given that it is highest-value but also highest-friction at the moment of peak fatigue — or is there a lighter event that captures most of the retention benefit at a fraction of the cost — and should its output be a persistent note at all, or feed directly into the spaced-review queue? A secondary problem cuts across both: AI-checking free recall or connections for accuracy needs a ground-truth anchor that isn't the model's own training data. This research surveys what already exists for each.

## Top existing solutions

### 1. Novak & Gowin concept-map scoring (validity threshold for connections)

**What it is:** The canonical rubric for scoring concept maps, from the people who invented them. It scores four structural elements — propositions, hierarchy levels, cross-links, and examples — and critically, it grades *cross-links* (connections between separate branches of the hierarchy) on a two-tier scale.

**How it addresses the problem:** This is a near-exact match for "what makes a connection valid." The rubric distinguishes a connection that is merely *valid* (true but shallow) from one that is valid *and significant* — i.e., illustrates a genuine synthesis between two sets of concepts. In their scoring this is the difference between 2 points and 10 points. Mapped onto Module A, this gives you a ready-made specificity threshold: only write connections to `connections.json` that meet the "valid + significant synthesis" bar, and you can even store the tier so shallow and deep connections are distinguishable later. This directly answers the critique's "they both use matrices" (shallow, 2-point) vs. "eigendecomposition in PCA is structurally the spectral decomposition in kernel methods" (synthesis, 10-point) example.

**Evidence of effectiveness:** Decades of use in education research; the basis of essentially every subsequent concept-map assessment instrument. A 2024 *Journal of Engineering Education* systematic review confirms concept-map assessment (and rubrics derived from Novak) as an established, validated tool in technical/CS-adjacent education.

**Tradeoffs / limitations:** Designed for whole-map scoring by a human grader, not single-connection real-time judgment by an LLM. You'd adopt the *criteria* (validity + significance/synthesis), not the point-counting machinery. Inter-rater reliability of these rubrics is decent but not perfect, which foreshadows the consistency risk the critique already flagged for Claude's judgments.

**Source:** [Rubric for Assessing Concept Maps — University of Waterloo CTE](https://uwaterloo.ca/centre-for-teaching-excellence/catalogs/tip-sheets/rubric-assessing-concept-maps) · [Application of concept maps as an assessment tool in engineering education (systematic review, 2024)](https://onlinelibrary.wiley.com/doi/full/10.1002/jee.20548)

### 2. Educational Knowledge Graphs with prerequisite relations (connections.json ↔ taxonomy.json)

**What it is:** A research area on representing course material as a graph where nodes are concepts and edges are typed relations — prerequisites, similarity, and learner-articulated links — often built or enriched semi-automatically (e.g., the ACE and KnowEdu systems).

**How it addresses the problem:** It resolves the "shadow graph" worry directly. The literature treats *directly-extracted prerequisite edges as the base layer* and other discovered relations as **supplements that augment connectivity** on top of that base — exactly the "augment, not parallel" framing the critique asked for. Practically: `taxonomy.json` (D, C, prerequisites) is the authored base layer; `connections.json` should be a thin overlay of *typed, student-authored edges* keyed by the same topic IDs, not a second graph. One striking finding: relying on prerequisite edges alone produces a "blocked phenomenon" where learners can't discriminate between *similar* concepts — which is a research-backed argument *for* having a connections layer at all, since cross-topic links are precisely what build discrimination.

**Evidence of effectiveness:** Multiple peer-reviewed systems (ACE in the *Journal of Educational Data Mining*; KnowEdu; the Springer *Smart Learning Environments* prerequisite work). Knowledge graphs are widely deployed in adaptive-learning products.

**Tradeoffs / limitations:** Most of this work is about *automatic* graph construction at scale — heavier than a single learner needs. The transferable insight is the layering principle (base prerequisite graph + augmenting edges keyed to the same nodes), not the ML pipeline. Full graph tooling would reintroduce exactly the Obsidian-style complexity the critique praised the proposal for dropping.

**Source:** [ACE: AI-Assisted Construction of Educational Knowledge Graphs with Prerequisite Relations (JEDM)](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737) · [Exploring knowledge graphs for the identification of concept prerequisites (Smart Learning Environments)](https://slejournal.springeropen.com/articles/10.1186/s40561-019-0104-3)

### 3. Elaborative interrogation + self-explanation (the retrieval loop for connections)

**What it is:** Two closely-related, well-validated strategies: elaborative interrogation prompts "why is this true?" / "how does this relate?"; self-explanation prompts the learner to explain their reasoning aloud. Both work by forcing integration of new material with prior knowledge.

**How it addresses the problem:** This is the missing review mechanic for `connections.json`. A stored connection becomes a learning tool when the tutor later pulls it and asks the learner to *regenerate it from memory* ("You previously linked PCA to kernel methods via eigendecomposition — explain that link from memory"). Crucially, the research notes elaborative interrogation **pairs naturally with spaced practice**: on a later encounter the learner attempts the elaboration without scaffolding, testing both retrieval of the fact and retention of the constructed explanation. That means connections can ride the *existing* SM-2 review queue rather than needing a separate review system — connections become a question *type* in the spaced queue, not a new subsystem.

**Evidence of effectiveness:** Both strategies are catalogued in Dunlosky et al. (2013), the major review of effective learning techniques; rated as having real (if moderate) utility, and stronger when combined with retrieval and spacing.

**Tradeoffs / limitations:** Dunlosky rates elaborative interrogation/self-explanation as *moderate* utility on their own — well below retrieval practice and spacing. They earn their keep only when fused with the spaced retrieval the pipeline already runs, which is good news for integration but means a standalone "connections quiz" would underperform.

**Source:** [Improving Students' Learning With Effective Learning Techniques — Dunlosky et al. 2013](https://journals.sagepub.com/doi/abs/10.1177/1529100612453266) · [Elaborative Interrogation — The Learning Scientists](https://www.learningscientists.org/blog/2016/7/7-1)

### 4. Free recall ("brain dump") as a graded technique — and its cognitive-load ceiling (Module B core question)

**What it is:** Free recall / brain dump is the strategy the proposal named: dump everything you can recall, unaided, after learning. The Retrieval Practice Collaborative and Dunlosky's lineage both endorse it.

**How it addresses the problem:** It both validates and *re-frames* Module B. Free recall is genuinely high-effect — but the direct, decisive finding for the critique's tension is this: **free recall is significantly impaired by high cognitive load, whereas cued recall is not.** A controlled study found increasing cognitive load reduced both immediate and delayed recall; a separate study found cued recall is preserved even in an acutely mentally-fatigued state. This is the empirical answer to "is a full brain dump the right format at the end of a fatiguing session?" — **no.** At the exact moment Module B fires (peak fatigue), the unaided free-recall format is the one most degraded by fatigue, while a *cued* prompt ("walk to station X — what was the key step?", or "name the one thing that surprised you") retains its benefit. This points squarely at the critique's own suggestion: a lighter, *cued* session-end event (one hardest-question self-test, a "what surprised me" prompt, a per-concept one-liner) is not just less tiring — it's the format the fatigue research says actually survives the fatigue.

**Evidence of effectiveness:** Free recall's base effectiveness is decades-deep. The load/fatigue dissociation comes from peer-reviewed cognition studies (Psychonomic Bulletin & Review; a randomised crossover on cued recall under mental fatigue).

**Tradeoffs / limitations:** Cued recall is "easier," and easier retrieval can mean a smaller desirable-difficulty benefit when the learner is *fresh*. The implication is conditional, not absolute: free/full brain dump when fresh or mid-session; cued, minimal recall at the fatigued session end. This matches the pipeline's existing 85%-controller instinct of matching difficulty to current capacity.

**Source:** [Brain Dump: free recall — Retrieval Practice Collaborative](https://www.retrievalpractice.org/strategies/2017/free-recall) · [The impact of cognitive load on delayed recall (Psychonomic Bulletin & Review)](https://link.springer.com/article/10.3758/s13423-014-0772-5) · [Preservation of Cued Recall in the Acute Mentally Fatigued State (randomised crossover)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4695502/)

### 5. Cornell cue-column method (turning a session note into retrieval prompts)

**What it is:** A note format with three zones: a notes column, a narrow *cue column* of questions/keywords written after the fact, and a summary line. The cue column converts inert notes into a self-test.

**How it addresses the problem:** It answers the critique's "why won't Module B's note file fill up and rot like the Notion page did?" The answer in the Cornell tradition is that the persistent artifact is **not the prose dump — it's the cue questions.** A brain dump reviewed by Claude can be transformed into 5–8 cue questions, and *only those questions* persist (ideally straight into the SM-2 queue). This makes the output grow at the rate of *retrievable items*, not at the rate of *words written*, and it directly enables the critique's strongest reframing: that Module B's output should be "a structured prompt that feeds the next session's spaced-review queue," not a note. Cornell is essentially the manual, paper version of exactly that pipeline.

**Evidence of effectiveness:** Long-established, widely taught study system; the cover-and-recall cue review is itself an application of retrieval practice, which carries the underlying evidence base.

**Tradeoffs / limitations:** Cornell is a manual discipline; its weak point historically is that learners write notes but skip the cue review. In an LLM tutor that weakness flips into a strength — Claude can *generate* the cue questions from the dump automatically and enqueue them, removing the step humans skip.

**Source:** [Cornell method — University of York Subject Guides](https://subjectguides.york.ac.uk/note-taking/cornell) · [The Cornell Note-Taking System — MindTools](https://www.mindtools.com/axbdk4f/the-cornell-note-taking-system/)

### 6. RAG-based short-answer grading (ground-truth anchor for AI checking)

**What it is:** Retrieval-augmented generation applied to automated grading: before the LLM grades a free-text answer, it retrieves the relevant reference answer and rubric criteria from a curated repository and grades *against those*, not against its own priors.

**How it addresses the problem:** This is the established fix for the critique's recurring "ground-truth anchor" problem — both for brain-dump accuracy checking and connection validity. Off-the-shelf LLMs "rely on generalized internal knowledge" and hallucinate plausible-but-wrong justifications; injecting the exact rubric/reference at grading time measurably reduces this and improves agreement with human graders. The pipeline already has the repository: `parsed/*.json` exemplars and the source/lecture material are exactly the "reference answers and scoring criteria" a RAG grader needs. So when Claude checks a brain dump or a connection, the rule should be: retrieve and cite the relevant `parsed/*.json` exemplar or taxonomy entry, grade against *that*, and flag where the dump diverges — never grade against training-data recall of the concept. This also keeps notation and emphasis aligned to the actual course, the specific failure the critique named.

**Evidence of effectiveness:** Peer-reviewed (EDM 2025). RAG-augmented GPT-4 reached ~85% agreement vs. ~81% for standard GPT-4 on short-answer grading; GraphRAG variants push structural alignment further.

**Tradeoffs / limitations:** The gain is real but incremental (~4 points in that study), and it's only as good as the reference repository. For Module B this means the brain-dump checker is trustworthy only on topics with good `parsed/*.json` coverage; on thinly-covered topics Claude should say so rather than grade confidently from priors.

**Source:** [Enhancing LLM-Based Short Answer Grading with Retrieval-Augmented Generation (EDM 2025)](https://educationaldatamining.org/EDM2025/proceedings/2025.EDM.short-papers.81/index.html) · [From Flat to Structural: GraphRAG for Automated Short Answer Grading](https://arxiv.org/html/2603.19276)

## Sufficiency verdict

**Partially sufficient — and the gaps are now well-specified rather than open.** Existing, evidence-backed solutions answer all of the critique's open questions; none requires inventing a new mechanism, which fits the pipeline's stated minimalism. Concretely:

- **Module A is now implementable.** "Valid connection" gets a real threshold from the Novak cross-link rubric (valid vs. valid-and-significant-synthesis — store the tier). The `connections.json` ↔ `taxonomy.json` relationship is settled by the knowledge-graph layering principle: prerequisite graph is the base, connections are a thin overlay of typed edges keyed to the same topic IDs (augment, never parallel). The missing review loop is solved by routing stored connections back through the *existing* SM-2 queue as elaborative-interrogation prompts — no new subsystem.

- **Module B's prior question is answered by the evidence, and it confirms the critique's instinct.** A full free-recall brain dump is the *wrong* format at peak session-end fatigue, because free recall is precisely the retrieval mode most degraded by cognitive load while cued recall is preserved. The session-end event should be a light, *cued* recall (one hardest-question self-test, a "what surprised me," or a per-concept one-liner), reserving full free recall for fresh/mid-session moments. And its output should not be a growing note file: the Cornell cue-column model plus the pipeline's own queue mean the durable artifact is a handful of *cue questions enqueued into spaced review*, which grows at the rate of retrievable items, not words.

- **The cross-cutting AI-grading anchor is a known, validated pattern** (RAG against `parsed/*.json` + rubric), with the honest caveat that it only helps where the reference material is well-covered, and that the lift is incremental.

**What is genuinely not settled by existing work** is the *interaction cost* the critique raised — three generative recall events (connection at mastery, mid-ramp retrieval, session-end recall) in one session. No off-the-shelf solution governs the per-session total cognitive budget; this remains a design decision (e.g., a session-level cap, or making Module A's connection event *replace* rather than *add to* the session-end event). That, plus tuning the validity threshold to your own consistency tolerance, is where `/solution-create` would add value. Everything else can be assembled from the solutions above.
