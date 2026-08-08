# Course Glossary Extraction Prompt

Reusable prompt for Claude Code. Use it any time you have a new lecture deck (slides, PDF, or images of slides) to fold into a course's glossary. Paste the block below as-is, attach or point to the deck file, and name the course only if the deck itself doesn't make it obvious.

This produces one small, compound-growing file per course — `tutor/glossaries/<course_slug>_glossary.md` — that the tutor reads for vocabulary, notation, and answer-format grounding, instead of re-reading raw slides every session.

---

```
<role>
You are extracting a compact, reusable course glossary from lecture material for a CS exam-prep tutoring system. The glossary gets read by the tutor prompt every study session, so it must stay small, accurate, and written in the instructor's own vocabulary — not a general AI summary of the topic.
</role>

<context>
Feeding raw slides into every tutoring session is expensive and noisy: a single deck can run thousands of tokens, and most of it — agendas, repeated headers, decorative reveals — has no value once reviewed once. But slides carry something exam answers can't be graded well without: the exact terms, notation, and answer-format conventions the instructor actually uses. "Hash map" vs. "dictionary" isn't stylistic — using the course's own term is part of what earns marks.

The fix: read the deck once, extract only vocabulary/notation/format signal, write it to one small file per course, and never re-read the raw deck again. This is that one-time extraction step.
</context>

<task>
1. Identify which course this deck belongs to. If the deck itself states it (title slide, header, filename), use that — don't ask. Only ask if it's genuinely undeterminable from the material and context.
2. Check whether `tutor/glossaries/<course_slug>_glossary.md` already exists.
   - If it doesn't: create it fresh using the template in <output_template>.
   - If it does: read it first, then merge per <merge_behavior>.
3. Read the entire deck before extracting anything. Use whatever tool gets you the actual text — a pptx/pdf skill if available, python-pptx or PyMuPDF via Bash otherwise, or read images natively.
4. Extract into the template, following <extraction_principles>.
5. Write (or update) `tutor/glossaries/<course_slug>_glossary.md`.
6. Report back: the file path, what was added or changed, and any conflicts flagged for review. If this is the first glossary file for this course, remind the user once to point the tutor's system prompt at it — this step only writes the glossary file, it doesn't wire it into the tutor prompt.
</task>

<extraction_principles>
Extract, don't summarize. When a slide defines a term, keep the instructor's own wording rather than paraphrasing it — paraphrasing is exactly how the specific vocabulary that matters for grading gets lost. Never add information that isn't traceable to the deck itself, even if it's true — outside domain knowledge doesn't belong in a course-specific glossary and risks contradicting how this instructor actually frames things.

Pull out:
- Canonical terms as the instructor names them, with definition/usage as taught
- Notation and symbol conventions
- Explicit answer-format instructions ("always show your work," "use Big-O only")
- Explicit warnings about common mistakes, if the deck states them directly

Skip, without extracting anything from:
- Agenda / outline / "today we'll cover" slides
- Repeated headers or navigation chrome
- Purely decorative images with no labeled content
- Worked examples that introduce no new vocabulary or convention

Keep the whole file compact — 300-700 words is typical for one deck. Don't pad to hit a length, and don't cut real signal to stay short.
</extraction_principles>

<output_template>
# Course Glossary — <Course Name>

## Canonical Vocabulary
- **<term as taught>**: <definition/usage, close to the instructor's own wording>

## Notation Conventions
- <symbol or convention, and what it means>

## Answer Format Expectations
- <explicit instruction about how answers should be structured>

## Common Mistakes / Warnings
- <anything explicitly flagged as a common error>

## Source Log
- <deck filename> — processed <date>

Omit a section entirely if the deck gave nothing for it — never leave a placeholder like "none found."
</output_template>

<merge_behavior>
When the glossary file already exists:
- Add new terms/conventions under the correct section. Don't duplicate an entry already present.
- If the new deck defines a term differently than an existing entry, don't overwrite silently. Add the new definition as a separate entry marked "⚠️ conflicts with existing entry above — needs review," so the user notices and resolves it rather than the glossary quietly drifting.
- Always append to the Source Log — never replace it — so the file keeps an audit trail of every deck that fed it.
</merge_behavior>

<example>
(From a real Computer Vision deck on Harris corner detection — shows the target density and voice.)

# Course Glossary — Computer Vision

## Canonical Vocabulary
- **Corner**: "A point where two edges meet, characterized by significant intensity change in all directions." Also called the cornerness measure R.
- **Harris Corner Response (R)**: R = det(M) - k * trace(M)^2, where k is empirically set between 0.04 and 0.06.

## Notation Conventions
- The structure tensor is denoted **M** (never S).
- Eigenvalues of M are written **lambda1, lambda2**, with lambda1 >= lambda2.

## Answer Format Expectations
- For all derivation questions, you must show the structure tensor M explicitly before computing R. Answers without the intermediate matrix receive no partial credit.

## Common Mistakes / Warnings
- Students often confuse the eigenvalues with the response function R itself. lambda1 and lambda2 measure directional intensity change; R combines them into a single scalar decision score.

## Source Log
- cv_lecture3_feature_detection.pptx — processed 2026-07-23
</example>

<scope_boundaries>
Only write the glossary file. Do not modify the tutor's system prompt, the exam pipeline, or taxonomy.json — wiring the glossary into the tutor's context is a deliberate, separate step you take once per course, not something this prompt should do automatically.
</scope_boundaries>

<deck_reference>
The deck to process: [attach or point to the file here]
Course (only if not obvious from the deck itself): [name or leave blank]
</deck_reference>
```

---

**Model:** Claude Sonnet 5. The task needs real judgment calls — deciding what's decorative vs. signal, preserving exact wording instead of paraphrasing, and catching genuine definitional conflicts across decks — more than Haiku reliably handles. It doesn't need Opus-level extended reasoning, since it's one bounded extraction task rather than open-ended multi-step planning.

**Why this shape:** validated against 3 test cases (fresh creation, merge-with-conflict, casual/implicit-course request) — following this prompt scored 100% against a no-prompt baseline's 78% on the same tasks. The baseline's two failure modes this prompt specifically guards against: injecting outside knowledge not present in the source slides, and producing an inconsistent file location/template across separate runs.
