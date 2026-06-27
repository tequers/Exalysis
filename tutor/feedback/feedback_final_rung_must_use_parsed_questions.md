---
name: feedback_final_rung_must_use_parsed_questions
description: Mastery gate = real parsed question + boss-check (user answers alone, ~90% correct, no fatal conceptual errors)
metadata:
  type: feedback
---

The final rung of any topic must be a real question pulled from `parsed/*.json` — not a constructed question — AND the user must pass a boss-check to be marked mastered.

**Why:** A constructed question may not match actual exam format or depth. And answering correctly after hints or dialogue does not prove independent recall — which is what the exam requires.

**How to apply:**

**Step 1 — Use a real parsed question.**
Before writing the final rung question, grep `parsed/*.json` for questions tagged with the current topic. Use one verbatim (or lightly adapted if it references an unavailable figure). If no parsed question exists, flag it explicitly and use the closest approximation — but mark it as unverified.

**Step 2 — Boss-check (mandatory before marking mastered).**
Once the user has worked through the question — including any hints, discussion, or corrections — the tutor must re-ask the question cold and require the user to answer fully by themselves, without help.

Mastery thresholds:
- Rung questions during the ramp: ~95% correctness expected
- Final rung / boss-check: ~90% correctness — no fatal conceptual errors; minor details can be imperfect, but the core understanding must be solid and independently demonstrated

If the user cannot answer the boss-check question alone at ~90%, they have not mastered the topic. Do not mark mastered. Offer another ramp cycle or additional consolidation, then re-run the boss-check.

**Step 3 — Mark mastered only after boss-check passes.**
The definition of mastery: the user can correctly answer a real parsed exam question by themselves, alone, without prompting — demonstrating solid independent understanding.
