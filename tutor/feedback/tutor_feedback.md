# Tutor Feedback Log

## 2026-06-28 — Boosting session

**Issue: Missing problem framing before rung 2**

When introducing rung 2 (AdaBoost formula), Claude jumped straight to the formula skeleton without first establishing:
- What the real-world problem is (face detection, object detection)
- Why weak classifiers are useful (fast, cheap, interpretable)
- What a "round" means concretely
- What the dataset looks like and how error is measured

User explicitly called this out: *"you first have to say the problematic. So I can understand why is this useful. And the context."*

**Fix:** For any new rung that introduces a formula or mechanism, first anchor it to the use case and the problem it solves before presenting the skeleton. The ARCS hook (relevance) belongs before the question, not after.

**Note:** This feedback is already in `loci_after_retrieval` memory — the pattern is: context/problem first, then formula. Never formula first.
