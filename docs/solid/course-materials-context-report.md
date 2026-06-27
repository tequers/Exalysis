# Course Materials as Contextual Grounding for the Exam Pipeline

## 🎯 Executive Summary

The exam pipeline currently relies solely on past exam files to extract topics and score ROI — but course materials (slides, PDFs, lecture notes, textbooks) carry critical signal that exams alone cannot provide: canonical vocabulary, solution format conventions, and pedagogical framing. The core challenge is that these materials are verbose and expensive to feed directly to an LLM, so a compaction strategy is needed to extract their value without inflating cost or hallucination risk.

---

## ⚠️ The Problem Landscape

### Problem 1: Missing Canonical Vocabulary and Course-Specific Framing

- **Core Issue:** Exams without official solutions leave the pipeline blind to *how* answers should be expressed. A significant part of exam scoring is using the exact terminology, notation, and phrasing taught in the course. Without access to course materials, the pipeline may tag topics correctly but fail to capture the vocabulary lens through which they are taught.
- **Sub-problem 1a:** Different courses may use different names for the same concept (e.g., "hash map" vs. "dictionary" vs. "associative array"). Without a vocabulary anchor, topic labeling in `taxonomy.json` risks inconsistency or misalignment with what the instructor expects.
- **Sub-problem 1b:** Solution format conventions — such as whether proofs should be written formally or informally, whether pseudocode or a specific language is expected, or how diagrams should be structured — are typically embedded in slides and lecture notes, not in the exam questions themselves.

---

### Problem 2: High Cost and Noise of Processing Raw Course Materials

- **Core Issue:** Slides, PDFs, and textbooks are information-dense but low signal-to-noise for this pipeline's purpose. Feeding them wholesale to an LLM is expensive (token cost), slow, and risks diluting the prompt with irrelevant content — increasing hallucination risk rather than reducing it.
- **Sub-problem 2a:** Lecture slides often contain decorative content, repetitive bullet points, and incremental reveal structures that do not add informational value when linearized into text.
- **Sub-problem 2b:** PDFs with mixed content (equations, figures, tables) are hard to parse cleanly, and partial or malformed extraction can introduce noise that misleads the model.
- **Sub-problem 2c:** Textbooks and long notes may cover far more ground than what the course actually emphasizes, making it difficult to distinguish "taught and testable" content from background reading.

---

## 💡 Proposed Solutions & Strategies

### Solution for Problem 1: Vocabulary and Format Anchoring

- **Approach:** Extract a "course glossary" from materials — a compact mapping of canonical term → definition/usage as taught in this specific course. This glossary would be injected into Stage 2 prompts alongside `taxonomy.json`, giving the model a vocabulary anchor when tagging topics and describing expected solution formats. It could also enrich `taxonomy.json` with a `course_term` field per topic.
- **Expected Value/Impact:** Reduces topic label drift, aligns AI-generated study guidance with what the instructor actually rewards, and makes the pipeline output directly actionable for exam preparation in course-specific language.

### Solution for Problem 2: Compaction Before Ingestion

- **Approach:** Introduce a pre-processing step — a "materials summarizer" — that runs once per course material file and produces a compact structured summary: key topics covered, canonical definitions, solution format norms, and any explicit exam guidance (e.g., "always justify your answer", "use Big-O notation only"). This summary is stored (similar to `parsed/` for exams) and reused on subsequent runs without reprocessing the source file.
- **Expected Value/Impact:** Decouples the expensive processing of raw materials from the fast per-exam pipeline runs. Keeps prompt sizes manageable, reduces token cost to a one-time expense per material, and gives the model a clean, curated context window rather than raw noisy input.

---

## 🔍 Open Challenges (Pending Solutions)

- **What is the right granularity for the compacted summary?** Too coarse and it misses vocabulary nuance; too fine and it recreates the verbosity problem. How do we define the optimal compression target?
- **How should course materials be versioned or updated?** If slides are revised mid-course, how does the pipeline know to re-summarize and whether prior parsed exams need re-tagging?
- **How do we handle materials with no machine-readable text** (e.g., scanned handwritten notes, image-heavy slides)? OCR adds another processing layer and potential failure point.
- **How do we weight course materials vs. exam evidence** when there is a conflict — e.g., a topic appears heavily in slides but never in past exams? Should it appear in the ROI spreadsheet at all?
- **Who triggers the materials ingestion step?** Should it be a new CLI command (e.g., `python pipeline.py add-materials slides.pdf`), and how does it integrate with the existing `add` / `rebuild` workflow?
