# Critique: Tutor Feedback Memory Files

Files reviewed: `feedback_final_rung_parsed_questions.md`, `feedback_label_exam_vs_warmup.md`, `feedback_visual_artifacts.md`

---

## Strong Points

**`feedback_label_exam_vs_warmup`** is the most actionable of the three. It names a specific failure mode ("user thought a warm-up was an exam question"), gives a concrete fix (bracketed labels), lists every label variant, and includes a forward-looking instruction ("Fix for future tutor prompt versions: Add an explicit labeling rule…"). That closing line is particularly strong — it doesn't just patch behavior, it points at the system artifact that needs updating.

**`feedback_final_rung_parsed_questions`** draws a clean, testable line: mastery = correct answer on a real parsed question. The "Why" is sound (constructed questions may not match exam depth). The fallback instruction ("If no parsed question exists, flag it explicitly") prevents silent failure.

---

## Weak Points

**`feedback_final_rung_parsed_questions`** asserts "mastery = ability to answer the real exam questions" as user-stated fact, but doesn't define what "correctly answers" means in ambiguous cases. Does partial credit count? Must the user answer unprompted, or is it acceptable after hints? A single wrong answer after ten right ones — does that reset mastery? The rule sounds crisp but will break on edge cases.

**`feedback_visual_artifacts`** is the weakest entry. The trigger — "inherently visual or spatial/algorithmic CV concepts" — is too vague to apply consistently. The example list (clustering, convolution, feature detection, etc.) helps, but the underlying test is the problem: *who decides* a topic is "visual enough" to warrant an artifact? A tutor might reasonably disagree on borderline topics (e.g., SVMs, PCA). Without a decision criterion, this feedback will be applied inconsistently.

Additionally, "build the artifact first, then run the ramp alongside it" assumes the artifact is always worth building before knowing whether the user will struggle with the concept. This is a cost assumption that's never examined.

---

## Potential Pitfalls

**The `parsed/*.json` dependency is a single point of failure.** If the parsed question pool is small, thin, or unrepresentative for a topic, the tutor is forced to either flag the gap (which stalls the session) or break the rule (which undermines the mastery definition). The feedback gives no guidance on what to do when the pool is genuinely inadequate — just "flag it explicitly," which is not a resolution.

**Labeling fixes presentation but not calibration.** Adding `[Exam question]` before a question signals the type — but if the question itself is too easy, too hard, or poorly formatted relative to actual exams, the label is false confidence. The feedback assumes the classification problem is the only problem.

**Proactive artifacts may backfire at Rung 1.** `feedback_visual_artifacts` says to build the artifact "before or alongside rung 1." At Rung 1, the user has zero context for the topic. Presenting an interactive k-means visualizer before any conceptual grounding assumes the user can meaningfully interact with it — this may hold for visual learners but could distract or overwhelm on unfamiliar topics.

---

## Problem Framing Check

All three feedback items are **reactive patches** — each one documents a specific past failure and adds a rule to prevent recurrence. That's the right instinct for a memory system, but it creates a fragile tutor: one that accumulates special-case rules rather than updating its underlying model of how the session should work.

The deeper problem none of these address: **there is no session protocol document being maintained.** `feedback_label_exam_vs_warmup` even says "Fix for future tutor prompt versions: Add an explicit labeling rule" — which implies the tutor prompt is the real source of truth, but that document isn't the target of any of these feedbacks. The memories are patching behavior that should be fixed upstream in the system prompt. If the tutor prompt ever gets rewritten from scratch, all three of these fixes disappear.

The root question is: **are these memories being read reliably at session start, and are they actually changing the tutor's behavior?** If the answer is "sometimes," the feedback system is producing a false sense of improvement.

---

## Verdict

The three feedback files are well-intentioned and individually reasonable, but they form a patchwork rather than a system. `feedback_label_exam_vs_warmup` is genuinely strong and actionable. `feedback_final_rung_parsed_questions` is sound but underspecified at the edges. `feedback_visual_artifacts` is the weakest — its trigger condition is too vague to apply reliably. The biggest structural problem is that these memories are functioning as a substitute for fixing the tutor system prompt, which is the actual failure point. Before adding more feedback entries, the priority should be propagating these rules into the TUTOR_SYSTEM_PROMPT so they're durable rather than session-dependent.
