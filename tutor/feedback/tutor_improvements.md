# Tutor Improvements Log

Mistakes in session management / learning process. Each entry: what happened, rule to apply next time.

---

## 2026-06-26 — Rushed loci encoding before concept was solid

**What happened:** Kept prompting for a loci encoding after rung 1 PASS while the user was still asking clarifying questions and clearly didn't have the concept solid yet.

**Rule:** Don't trigger loci encoding until the user has demonstrated they understand the concept — either through a clean rung 1 answer with no follow-up confusion, or explicitly saying they're ready. If they're still asking "but what is X?" the concept isn't solid. Prioritize understanding over encoding cadence.

---

## 2026-06-26 — Exam review question on unmastered topic

**What happened:** After Neural Network Training exam review (Q5e), jumped straight into CNNs rung 1 framed as "new material" — but then also tried to run an exam review question on CNNs, which is not mastered.

**Rule:** Exam review questions (spaced retrieval) are ONLY for topics with status `mastered` in `progress.json`. Never ask an exam-format review question on a topic that is `unlocked` or `locked`, even if it's the current active topic.
