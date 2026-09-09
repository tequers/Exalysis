# 3-Day Plan → Final, Thu 20 Aug 2026

**Built:** Sun 16 Aug 2026 · **Budget:** ~3h/day, Mon 17 – Wed 19 (9h total) · **Strategy:** depth on high-ROI

**Position now:** 123.0 / 492.0 marks secured (25.0%). Five topics mastered but **overdue for review since 15 Aug**. Two high-mark topics (Tensor Products, Quantum Measurement) **lost mastery on 14 Aug** — both from incomplete answers, not wrong concepts. Hamiltonian Dynamics is mid-ramp at rung 4/6.

This plan is a target, not a record. Nothing here is written to `progress.json` — only `/study-run close` writes what actually happened.

---

## The arithmetic that drives it

| Topic | ROI rank | Marks | State | In plan? |
|---|---|---|---|---|
| Tensor Products | 1 | 74.5 | lapsed, rung 4, overdue | **Day 1** |
| Hamiltonian Dynamics | 5 | 58.5 | in progress, rung 4/6 | **Day 1–2** |
| Quantum Fourier Transform | 6 | 44.5 | untouched (D4) | **Day 3** |
| Quantum Measurement | 4 | 30.5 | lapsed, rung 3, overdue | **Day 1** |
| Shor's Algorithm | 12 | 30.5 | locked (needs QFT) | cut |
| Partial Measurement | 8 | 29.0 | untouched (D4) | **Day 2** |
| Stabilizer Formalism | 11 | 26.0 | locked (D5) | cut |
| Grover's / QEC / BV / Physical / Bomb | 13–17 | 75.5 | untouched | cut (see below) |

**Cut deliberately.** Shor's, Stabilizer, and QEC are all D5 and each sits behind two or three prerequisites that are themselves unsecured — at 3h/day they would eat a full day and return partial rungs on three topics instead of full mastery on two. Grover's, BV, Bomb Tester and Physical Qubit are cheap but low-ROI; they are the Day-3 overflow if anything runs early.

**Projected coverage if the plan lands:** ~345 / 492 ≈ **70%**, up from 25%.

---

## Day 1 — Mon 17 Aug · re-secure what you already earned

The single highest-value hours of the three days: 105 marks are sitting one clean answer away each.

**Session A (~90m)** — `/study-run 90m`

- Review sweep, five overdue mastered topics (Probabilistic Matrices, Probability Distribution Vectors, Quantum State Validity, Unitary Matrices, Quantum Amplitudes). These protect the 123 you have. Fast — they're all rung 3–4 passes.
- **Tensor Products** → back to rung 4. Failure mode on 14 Aug was *tensor-order reversal on a 3-factor product*. Order discipline is the whole drill.
- **Quantum Measurement** → back to rung 3. Failure mode was *omitting the post-measurement state entirely*.

> Both lapses were the same bug: right math, unfinished answer. Before submitting anything, re-read the question and check every part got an answer.

**Session B (~90m)** — `/continue-study-session` (or a fresh `/study-run 90m`)

- Short eigen-decomposition consolidation drill — H−λI sign handling, two eigenvalues for a 2×2, distinguishing the trivial null-space solution, re-deriving |0⟩ in the |+⟩/|−⟩ basis. Rungs 4–6 need this machinery numerically and it needed heavy scaffolding on 14 Aug.
- **Hamiltonian Dynamics** rung 4, then rung 5 if the drill went clean.

*Day 1 target: 105 marks re-secured, HD at rung 5.*

---

## Day 2 — Tue 18 Aug · finish the ramp, open the dependent topic

**Session A (~90m)** — `/study-run 90m`

- Due reviews first (Tensor Products and Quantum Measurement come back due today at a short interval — that's the point of re-securing them yesterday).
- **Hamiltonian Dynamics** rungs 5–6 → mastery. 58.5 marks.

**Session B (~90m)** — `/continue-study-session`

- **Partial Measurement** rungs 1–3. It was locked behind Tensor Products + Quantum Measurement; yesterday unlocked it. 29 marks, D4, and it shares machinery with everything you just did — it is the cheapest new topic on the board right now.

*Day 2 target: HD mastered, PM at rung 3.*

---

## Day 3 — Wed 19 Aug · biggest untouched block, then consolidate

**Session A (~90m)** — `/study-run 90m`

- Due reviews (short).
- **Quantum Fourier Transform** rungs 1–3. 44.5 marks, the largest untouched block, and it sits directly on Unitary Matrices + Tensor Products + Amplitudes — all secured by now. Don't chase full mastery; rungs 1–3 on 44.5 marks beats rung 6 on 20.

**Session B (~90m)** — `/study-run 90m`, exam-format bias

- Full-length past-paper conditions from `final_20_08_2026/exams/` — mixed, timed, no scaffolding. This is the completeness rehearsal, which is exactly where marks have been leaking.
- If time remains: **Bomb Tester** (6 marks, D3) and **Bernstein-Vazirani** (17.5, D3) at rung 1–2 each, purely so they aren't blank pages.

**Close the last session with `/study-run close`** so the ledger is accurate going into the exam.

*Day 3 target: QFT at rung 3, one timed mixed paper, ~70% coverage.*

---

## Standing rules for all three days

- Every session opens with due reviews. Losing a mastered topic costs more than gaining a new rung — 14 Aug dropped coverage from 46% to 25% in one sitting.
- Cap of 3 graded questions per session still applies; the plan assumes reviews are quick and don't count against it.
- Answer completeness is the live failure mode, not conceptual error. Three of the last four losses were unfinished answers.
- If a session runs long and pulls in the next topic, let it — that's normal here and `close` reconciles it.
