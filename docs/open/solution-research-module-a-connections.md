# Solution Research: Module A — Connections (with Upstream Dependency)

*Scope: Module A only. Module B (active-recall notes) is deliberately excluded — it is a separable, lower-priority problem to tackle after Module A. Researched against `critique-mindmap-graph-connections.md`, `TUTOR_SYSTEM_PROMPT_v2.md`, and `course-materials-context-report.md`.*

## Why Module A first

Module A (a lightweight, optional flow where the student articulates a connection between a newly-mastered topic and a previously-mastered one, which Claude evaluates and — if valid — persists) is the higher-priority module for three reasons. It is mechanically close to ready: the critique judged it "close to ready," needing only a validity definition and a stated relationship to `taxonomy.json`. Its building blocks already exist in the pipeline (generate → evaluate → persist is the same pattern as loci and the mastery gate). And it is decoupled from the fatigue/motivation tension that still blocks Module B. So Module A can ship once two questions are answered — and, as this report argues, once one upstream dependency is in place.

## Problem statement

Module A has three open design questions: (1) what makes a student-articulated connection **valid** enough to persist; (2) what the relationship is between a `connections.json` overlay and the existing `taxonomy.json` (augment vs. parallel vs. replace); and (3) what **retrieval loop** keeps the stored connections a learning tool rather than a write-only archive. Underlying all three is a ground-truth problem the original critique kept surfacing: to judge a connection's validity and significance *for this specific course*, Claude needs to grade against the course's real concepts, vocabulary, and emphasis — not its own training priors. That requirement is what ties Module A to the course-materials report.

---

## Upstream dependency: Module A needs the course-materials anchor first

**The dependency in one line:** Module A's "valid connection" judgment is only as trustworthy as the ground-truth it grades against, and `course-materials-context-report.md` describes the missing half of that ground-truth.

The pipeline today ingests only *past exams*. The course-materials report shows that this leaves two gaps that are directly load-bearing for Module A's validity judgment:

**1. Canonical vocabulary (report Problem 1a) gates connection identity.** A connection links two topics — but the same concept can carry different names ("hash map" / "dictionary" / "associative array"). If the student connects "dictionary" to "hash table," Claude must know these are the same concept *as this course teaches it* before it can judge the link. Without the course glossary the report proposes, Claude falls back on training-data priors and risks mis-grading a valid connection as invalid (or the reverse) purely on terminology. This is exactly the "notation/emphasis drift from training data" failure the critique flagged for AI-checking.

**2. Course emphasis (report Problem 2c) gates connection *significance*.** The validity threshold this report adopts (see Solution 1) separates a merely-valid connection from a valid-*and-significant* one. Significance is course-relative: a synthesis that is deep in general CS may be irrelevant to *this* exam, and vice versa. Without the course-materials signal that distinguishes "taught and testable" from background, Claude cannot reliably judge whether a connection *matters here* — only whether it is true in the abstract.

**Concrete artifact overlap.** My Module A finding is that `connections.json` should augment `taxonomy.json` with typed edges keyed to topic IDs. The course-materials report independently proposes enriching `taxonomy.json` with a `course_term` field per topic. These are complementary enrichments of the same file — and `course_term` is effectively a *precondition* for a clean connections graph, because you cannot reliably key student-authored edges to topics whose canonical labels are still drifting (Problem 1a).

**Sequencing implication.** Treat the course-materials glossary as **upstream of Module A**, not parallel to it:

1. **Course-materials compaction** → produce the compact per-course glossary + format/emphasis summary (report's Solution 2).
2. **Canonical `course_term` in `taxonomy.json`** → stabilise topic labels so edges have stable anchors (report's Solution 1).
3. **Module A connection validity** → now graded against a real, course-specific anchor (RAG over `parsed/*.json` *plus* the new glossary/summary).

A minimal version of Module A could ship before step 1 by grading connections only against `parsed/*.json` exemplars, but its validity and especially its *significance* judgments would be weaker and more inconsistent across sessions until the course-materials anchor exists. The dependency is "strong for significance, softer for bare validity."

---

## Top existing solutions for Module A

### 1. Novak & Gowin concept-map scoring — the validity threshold

**What it is:** The canonical concept-map rubric. It grades *cross-links* (connections between separate branches of a knowledge hierarchy) on a two-tier scale: valid-but-shallow vs. valid-*and-significant* (a genuine synthesis between two sets of concepts) — in their scheme, 2 points vs. 10 points.

**How it addresses the problem:** A near-exact match for "what makes a connection valid." Adopt the *criteria*, not the point-counting: only persist connections that meet the "valid + significant synthesis" bar, and store the tier so shallow and deep connections stay distinguishable in `connections.json`. This directly resolves the critique's example — "they both use matrices" (shallow, 2-point) vs. "the eigendecomposition in PCA is structurally the spectral decomposition in kernel methods" (synthesis, 10-point). The significance half of this judgment is exactly what the upstream course-materials anchor makes reliable.

**Evidence of effectiveness:** Decades of use; the basis of essentially every later concept-map instrument. A 2024 *Journal of Engineering Education* systematic review confirms concept-map assessment as a validated tool in technical education.

**Tradeoffs / limitations:** Built for whole-map human scoring, not single-connection real-time LLM judgment — adopt the criteria only. Inter-rater reliability is decent but imperfect, foreshadowing the consistency risk the critique flagged; a stable course-specific anchor is the main mitigation.

**Source:** [Rubric for Assessing Concept Maps — University of Waterloo CTE](https://uwaterloo.ca/centre-for-teaching-excellence/catalogs/tip-sheets/rubric-assessing-concept-maps) · [Concept maps as an assessment tool in engineering education (systematic review, 2024)](https://onlinelibrary.wiley.com/doi/full/10.1002/jee.20548)

### 2. Educational Knowledge Graphs with prerequisite relations — connections.json ↔ taxonomy.json

**What it is:** Representing course material as a graph of concept nodes and *typed* edges (prerequisite, similarity, learner-articulated), built or enriched semi-automatically (e.g., the ACE and KnowEdu systems).

**How it addresses the problem:** Resolves the "shadow graph" worry. The literature treats directly-extracted prerequisite edges as the *base layer* and other relations as **supplements that augment connectivity** on top — exactly the "augment, not parallel" answer the critique asked for. So `taxonomy.json` (D, C, prerequisites) is the authored base; `connections.json` is a thin overlay of typed, student-authored edges keyed to the same topic IDs. A notable finding: relying on prerequisite edges alone produces a "blocked phenomenon" where learners can't discriminate between *similar* concepts — a research-backed argument *for* having a connections layer, since cross-topic links are what build discrimination.

**Evidence of effectiveness:** Multiple peer-reviewed systems (ACE in the *Journal of Educational Data Mining*; the Springer *Smart Learning Environments* prerequisite work); knowledge graphs are widely used in adaptive-learning products.

**Tradeoffs / limitations:** Most of this work targets *automatic, at-scale* construction — heavier than one learner needs. Transfer the layering principle, not the ML pipeline; full graph tooling would reintroduce the Obsidian-style complexity the critique praised the proposal for dropping.

**Source:** [ACE: AI-Assisted Construction of Educational Knowledge Graphs with Prerequisite Relations (JEDM)](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737) · [Exploring knowledge graphs for the identification of concept prerequisites (Smart Learning Environments)](https://slejournal.springeropen.com/articles/10.1186/s40561-019-0104-3)

### 3. Elaborative interrogation + self-explanation — the retrieval loop

**What it is:** Two validated strategies: elaborative interrogation prompts "why is this true? / how does this relate?"; self-explanation prompts the learner to explain their reasoning. Both force integration of new material with prior knowledge.

**How it addresses the problem:** The missing review mechanic for `connections.json`. A stored connection becomes a learning tool when the tutor later pulls it and asks the learner to *regenerate it from memory* ("You linked PCA to kernel methods via eigendecomposition — explain that from memory"). The research notes elaborative interrogation **pairs naturally with spaced practice**: on a later encounter the learner attempts the elaboration unscaffolded, testing both retrieval and retention of the explanation. So connections can ride the *existing* SM-2 review queue as a question *type* — no new subsystem, which keeps Module A minimal.

**Evidence of effectiveness:** Catalogued in Dunlosky et al. (2013), the major review of effective learning techniques; rated real (if moderate) utility, stronger when fused with retrieval and spacing.

**Tradeoffs / limitations:** On their own these strategies are only *moderate* utility — well below retrieval practice and spacing. They earn their keep only when fused with the spaced retrieval the pipeline already runs, so a standalone "connections quiz" would underperform; route it through the queue instead.

**Source:** [Improving Students' Learning With Effective Learning Techniques — Dunlosky et al. 2013](https://journals.sagepub.com/doi/abs/10.1177/1529100612453266) · [Elaborative Interrogation — The Learning Scientists](https://www.learningscientists.org/blog/2016/7/7-1)

### 4. RAG-based short-answer grading — the ground-truth anchor (shared with the upstream dependency)

**What it is:** Retrieval-augmented grading: before judging a free-text answer, the LLM retrieves the relevant reference and rubric from a curated repository and grades *against those*, not its own priors.

**How it addresses the problem:** The established fix for the critique's recurring anchor problem, and the mechanism that *consumes* the upstream course-materials glossary. When Claude evaluates a connection, the rule should be: retrieve and cite the relevant `parsed/*.json` exemplar, the `taxonomy.json` entry, *and the course glossary/emphasis summary*, then grade against those — never against training-data recall. Off-the-shelf LLMs "rely on generalized internal knowledge" and hallucinate plausible-but-wrong justifications; injecting the exact reference measurably reduces this and improves agreement with human graders. This is precisely why the course-materials anchor is upstream: it is the missing input to this step.

**Evidence of effectiveness:** Peer-reviewed (EDM 2025). RAG-augmented GPT-4 reached ~85% agreement vs. ~81% for standard GPT-4 on short-answer grading; GraphRAG variants push structural alignment further.

**Tradeoffs / limitations:** The gain is real but incremental (~4 points in that study) and only as good as the reference repository — which is the whole argument for building the course-materials anchor before leaning on this for *significance* judgments.

**Source:** [Enhancing LLM-Based Short Answer Grading with Retrieval-Augmented Generation (EDM 2025)](https://educationaldatamining.org/EDM2025/proceedings/2025.EDM.short-papers.81/index.html) · [From Flat to Structural: GraphRAG for Automated Short Answer Grading](https://arxiv.org/html/2603.19276)

---

## Sufficiency verdict

**Partially sufficient — Module A is implementable, but its quality is gated by an upstream dependency that should be built first.**

The three open Module A questions all have evidence-backed answers, none requiring a new mechanism (consistent with the pipeline's minimalism):

- **Validity threshold** → Novak's cross-link tiering: persist only valid-*and-significant* connections, store the tier.
- **connections.json ↔ taxonomy.json** → knowledge-graph layering: prerequisite graph is the base; connections are a thin overlay of typed edges keyed to the same topic IDs (augment, never parallel).
- **Review loop** → route stored connections through the *existing* SM-2 queue as elaborative-interrogation prompts.

**The decisive finding for prioritisation** is the upstream dependency. Module A's validity — and especially its *significance* — judgments are only as good as the course-specific ground truth Claude grades against, and `course-materials-context-report.md` describes the missing half of that ground truth (canonical vocabulary + course emphasis). Recommended sequence: **(1) course-materials compaction → (2) `course_term` enrichment of `taxonomy.json` → (3) Module A connection validity.** A minimal Module A can ship before step 1 by grading only against `parsed/*.json`, but it will be weaker and less consistent on significance until the anchor exists.

**What remains genuinely unsolved by existing work** (and where `/solution-create` would add value): the per-session cumulative cognitive cost if Module A's connection event stacks with mid-ramp retrieval (the critique's interaction concern — bounded here to Module A's own footprint, since Module B is out of scope), and tuning the significance threshold to your tolerance for cross-session consistency. Both are design decisions, not gaps in the literature.
