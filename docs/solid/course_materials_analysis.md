# Critical Analysis: Course Materials as Pipeline Input

## Strong Points

- The observation that vocabulary alignment matters for exam grading is accurate and often overlooked. "A part of an exam grade is also to use the specific vocabulary that has been used in the course" is a concrete, testable claim with real consequences for generated solutions.
- Correctly identifies that course materials become *more* valuable when official solutions are absent — the reasoning is sound.
- The cost/noise problem is real and well-stated: slides and PDFs contain high redundancy, and feeding them raw to an LLM is expensive and degrades signal quality.
- "Compacting the information" as a desirable property is a legitimate design goal, not hand-waving.

## Weak Points

- "Slides and pdfs are hard and expensive to process" is asserted without specificity. Hard *how*? Expensive *relative to what threshold*? The pipeline already uses Claude for two stages — is one more call actually prohibitive, or is this a cost intuition that needs benchmarking?
- "A lot of unnecessary information" is vague. What counts as unnecessary? Navigation text, decorative headers, examples, footnotes? Without a definition, no compaction strategy can be evaluated.
- The report conflates two distinct problems: (a) vocabulary/terminology alignment and (b) solution format alignment. These likely require different treatments and shouldn't be bundled as one "course materials" problem.
- No mention of *which* course materials are typically available. Slides vs. textbook chapters vs. handwritten notes have wildly different structure, density, and processability. The proposal floats without grounding in the actual inputs.
- "Finding a way to compact the information" is stated as desirable but left entirely open. This is a placeholder, not a finding.

## Potential Pitfalls

- Course materials can be inconsistent with exam questions — professors sometimes test beyond the slides. Treating slides as the authoritative "playground" could *constrain* generated solutions incorrectly.
- Compaction is lossy. If the compaction step is itself AI-driven, you've added a failure mode: the compactor may discard the exact terminology that mattered. Who validates what was kept vs. dropped?
- Vocabulary from slides may be course-specific but *wrong* relative to the field. A pipeline that enforces course vocabulary could produce solutions that are locally correct but educationally misleading — fine for exam performance, but worth flagging as a design choice.
- PDF/slide processing is already a solved-enough problem (pypdf is in your requirements.txt). Framing it as a hard blocker may cause over-engineering of a preprocessing step that a simple chunked extraction would handle adequately.

## Problem Framing Check

The stated problem is "course materials are hard to process." The actual root problem being circled is: *how does the pipeline know what a correct answer looks like for this specific course?* Course materials are one answer to that, but official solutions, past marked scripts, or even a short manual "style guide" prompt could serve the same purpose more cheaply. The report identifies a real gap but frames it as an ingestion/compression engineering problem when it's fundamentally a *ground-truth calibration* problem. The hardest part isn't parsing the PDF — it's deciding what signal from it actually matters for answer quality.

## Overall Verdict

This is a well-motivated observation that correctly identifies a real gap in the pipeline, but it stops at the level of intuition rather than analysis. The core insight — that course-specific vocabulary and format conventions affect grading — is solid and should be carried forward. However, the report doesn't distinguish between the sub-problems it bundles together, doesn't quantify the cost concern it raises, and proposes "compaction" without enough definition to evaluate any approach. It's a good prompt for further analysis, not a finding ready to drive design decisions.

---

## Solution Landscape

**Constraints:** Solo developer · Claude API as primary tool · No additional infrastructure budget · Must integrate with existing Python pipeline.

The Stage 1 analysis identified four actionable problem clusters. Solutions are addressed in order of implementation priority for the given constraints.

---

### Problem 1: PDF and Slide Ingestion ("hard and expensive to process")

The Stage 1 critique correctly noted this claim lacked specificity. Research grounds it: Claude's PDF API consumes roughly 1,500–3,000 tokens per page (standard docs ~2,800 tokens/page), billed at normal API rates with no surcharge. A 100-page slide deck costs approximately the same as a long Stage 2 prompt — significant but not prohibitive for a one-time preprocessing step.

**Option A — Claude's native PDF API (via `base64` document blocks)**
Send the PDF directly to Claude as a document block. Claude's engine recognises headings, paragraphs, tables, and figures natively, and can return structured JSON. No extra libraries needed.
*Trade-offs:* Costs scale linearly with page count; no control over what gets extracted; can't diff between runs.
*Pitfall addressed:* Avoids the over-engineering risk flagged in Stage 1 — this is a three-line code change on top of the existing pipeline.

**Option B — PyMuPDF (`fitz`) pre-extraction → Claude for structure**
Use PyMuPDF (free, local) to extract raw text and table data from PDFs, then pass the cleaned text to Claude. PyMuPDF can export to JSON, CSV, or plain text, stripping navigation chrome and image-only decorations before any API call is made.
*Trade-offs:* Adds one dependency; requires handling scanned/image-only PDFs separately (Nougat OCR or Claude vision fallback). Reduces token cost by 40–60% vs. sending raw pages.
*Pitfall addressed:* Directly reduces the cost concern; also creates a local intermediate representation that can be inspected and version-controlled.

**Option C — Anthropic Batch API (50% token discount)**
For one-time or infrequent preprocessing of large slide sets, submit PDF extraction as a batch job. Halves the per-token cost with no code change beyond the API call mode.
*Trade-offs:* Asynchronous — results arrive minutes to hours later, not suitable for interactive use. Fine for a pipeline that runs offline.

**Best fit for constraints:** Option B (PyMuPDF pre-extraction) combined with Option C (batch mode) for large inputs. PyMuPDF is already adjacent to the stack (`pypdf` is in `requirements.txt`; PyMuPDF is a drop-in with more capability). This keeps costs low and produces auditable intermediate files consistent with the pipeline's existing `parsed/` pattern.

---

### Problem 2: Document Compaction ("a lot of unnecessary information")

Stage 1 flagged that "unnecessary" was undefined and that lossy AI-driven compaction adds a failure mode. Research confirms both concerns and points to a spectrum of approaches.

**Option A — Extractive compression via targeted Claude prompt**
Instead of summarising the whole document, prompt Claude to extract only: (1) definitions, (2) named algorithms or data structures, (3) worked examples, (4) explicit warnings or "common mistakes." This is extraction, not summarisation — verbatim sentences are lifted, not paraphrased, reducing the risk of terminology drift flagged in Stage 1.
*Trade-offs:* Prompt must be tuned per course type; misses implicit vocabulary embedded in prose.
*Pitfall addressed:* Directly addresses the "compactor discards terminology that mattered" risk — verbatim extraction preserves wording.

**Option B — Hierarchical chunked summarisation (map-reduce)**
Split the document into chunks, summarise each with a cheap model (Claude Haiku), then summarise the summaries. Research shows 5–20× compression with 70–94% cost savings at scale.
*Trade-offs:* Two-stage abstraction increases hallucination surface; the final summary is paraphrased, which is the exact failure mode Stage 1 warned about for vocabulary alignment. Requires validation.
*Pitfall addressed:* Partially addresses cost, but introduces the compaction-lossiness pitfall.

**Option C — Manual "course glossary" prompt (zero-cost, zero-infrastructure)**
The Problem Framing section identified that a short manual style guide could substitute for full document ingestion. Concretely: the user writes a 200–500 word prompt section listing key terms, notation conventions, and answer format expectations for the course. This costs nothing, adds no pipeline complexity, and is immune to compaction errors.
*Trade-offs:* Requires human effort upfront; must be maintained if course changes.
*Pitfall addressed:* Sidesteps the entire compaction problem; also addresses the "slides may not cover everything" pitfall by letting the user explicitly set scope.

**Best fit for constraints:** Option C first (manual glossary prompt as a Stage 2 system prompt addition), then Option A if the glossary proves insufficient for a specific course. Option B is the weakest fit given the vocabulary-preservation constraint.

---

### Problem 3: Vocabulary and Terminology Alignment (the root problem)

Stage 1 correctly reframed the root problem as *ground-truth calibration* — the pipeline needs to know what a correct answer looks like for *this course*, not just for the topic in general.

**Option A — System prompt domain grounding**
Inject course-specific vocabulary and notation directly into the Stage 2 system prompt. Research confirms this is the lowest-overhead approach for solo developers: "prompt engineering obviates the need for extensive training and reduces resource expenditure." Effective prompts can specify output vocabulary, notation style, and answer format explicitly.
*Trade-offs:* Token cost per call increases modestly; requires the user to curate vocabulary once. Does not scale automatically to new courses without re-curating.
*Pitfall addressed:* Directly prevents the "locally correct but educationally misleading" risk by binding the model to course-specific rather than field-standard terminology.

**Option B — RAG over extracted course materials**
Embed chunks of course slides/notes into a vector store; retrieve the top-k relevant chunks at query time and inject into the prompt. Grounds vocabulary in actual course content dynamically.
*Trade-offs:* Requires a vector database (e.g., ChromaDB or FAISS), an embedding pipeline, and retrieval tuning — significant infrastructure for a solo developer with no budget for additional services. Quality degrades with poor chunking. IBM and Sprinklenet both recommend exhausting prompt engineering before reaching for RAG.
*Pitfall addressed:* Addresses the "professor tests beyond slides" risk if retrieval is comprehensive — but can also amplify it if retrieval is incomplete.

**Option C — Fine-tuning**
Train a custom model on course-specific Q&A pairs to bake in vocabulary and format norms.
*Trade-offs:* Requires labelled data, compute budget, and model hosting — all outside the stated constraints. Sprinklenet explicitly advises reserving fine-tuning until prompt engineering and RAG have been found insufficient.
*Not recommended* for this context.

**Best fit for constraints:** Option A (system prompt grounding with a curated course glossary). This maps directly to the existing pipeline's Stage 2 prompt, requires no new infrastructure, and is the approach most consistent with the solo-developer, Claude-API-only constraint.

---

### Problem 4: Conflation of Vocabulary Alignment vs. Format Alignment

Stage 1 identified that the original report bundles two distinct problems. Research supports treating them separately:

- **Vocabulary alignment** → solved via system prompt injection (Problem 3, Option A above)
- **Format alignment** (what a correct *answer structure* looks like — e.g., proof style, pseudocode conventions, step-by-step derivations) → solved via few-shot examples in the Stage 2 prompt

Few-shot prompting with 2–3 worked examples in the target format is well-documented as effective for format conformity without additional infrastructure. The examples can be drawn from any available past solutions, or written manually from the user's own notes.

**Best fit for constraints:** Add a `format_examples` field to the Stage 2 prompt template, populated with 1–3 manually written or sourced examples per course. Low effort, high signal.

---

### Summary Table

| Problem | Recommended solution | Effort | Cost |
|---|---|---|---|
| PDF/slide ingestion | PyMuPDF pre-extraction + Claude batch API | Low | Low |
| Document compaction | Manual course glossary prompt (Option C) | Low | None |
| Vocabulary alignment | System prompt domain grounding (Option A) | Low | Minimal |
| Format alignment | Few-shot examples in Stage 2 prompt | Low | Minimal |

All four recommended solutions require no new infrastructure, no new services, and fit within a single Python file addition to the existing pipeline.

---

### Sources

- [LLMs for Structured Data Extraction from PDFs in 2026](https://unstract.com/blog/comparing-approaches-for-using-llms-for-structured-data-extraction-from-pdfs/)
- [Extracting PDF Data for LLM Processing: Techniques, Tools and Intelligent Routing](https://www.datavise.ai/blog/extracting-pdf-data-for-llm-processing-tools-techniques-and-intelligent-routing)
- [RAG/LLM and PDF: Enhanced Text Extraction — Artifex](https://artifex.com/blog/rag-llm-and-pdf-enhanced-text-extraction)
- [PDF support — Claude API Docs](https://docs.claude.com/en/docs/build-with-claude/pdf-support)
- [Claude PDF Processing API Guide 2026](https://claudereadiness.com/blog/claude-pdf-processing-api/)
- [5 Ways Context Compaction Cuts Enterprise LLM Costs](https://bbinsight.com/blog/5-ways-context-compaction-cuts-enterprise-llm-costs)
- [Prompt Compression Techniques: Reducing Context Window Costs](https://medium.com/@kuldeep.paul08/prompt-compression-techniques-reducing-context-window-costs-while-improving-llm-performance-afec1e8f1003)
- [Context Window Optimization Strategies — DataHub](https://datahub.com/blog/context-window-optimization/)
- [RAG vs Fine-tuning vs Prompt Engineering — IBM](https://www.ibm.com/think/topics/rag-vs-fine-tuning-vs-prompt-engineering)
- [RAG vs. Fine-Tuning vs. Prompting: How to Choose — Sprinklenet](https://sprinklenet.com/rag-vs-fine-tuning-vs-prompting-how-to-choose)
- [Ultimate Guide to Domain Vocabulary for LLM Fine-Tuning — Latitude](https://latitude.so/blog/ultimate-guide-to-domain-vocabulary-for-llm-fine-tuning)
- [Injecting Domain-Specific Knowledge into Large Language Models — arXiv](https://arxiv.org/html/2502.10708v1)
- [Document Summarization with LLMs in 2026 — FutureAGI](https://futureagi.com/blog/revolutionizing-document-management-llm-2025/)
- [How to Summarize Huge Documents with LLMs — DEV Community](https://dev.to/dmitrybaraishuk/how-to-summarize-huge-documents-with-llms-beyond-token-limits-and-basic-prompts-57ao)
