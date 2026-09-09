# Two-Exam Run-In — Quantum (Thu 20 Aug) → Computer Vision (Wed 26 Aug)

**Built:** Mon 17 Aug 2026 · **Starts:** Tue 18 Aug, morning · **Budget:** 5h/day max
**Total:** ~10h Quantum (2 days) + ~28h Computer Vision (6 days)

This plan is a target, not a record. Nothing here is written to either `progress.json` —
only `/study-run close` writes what actually happened.

---

## Where you actually stand

| | **Quantum** — final 20 Aug | **Computer Vision** — final 26 Aug |
|---|---|---|
| Coverage | **228 / 492 marks (46.3%)** | **138 / 175 marks (78.9%)** — see caveat |
| Last session | 16 Aug (yesterday) | **29 June — 7 weeks ago** |
| Mastered | 7 topics | 8 topics, all decayed |
| Mid-ramp | Hamiltonian Dynamics, rung 5 / 6 | — |
| Never opened | 6 topics (~130 marks reachable) | **8 topics**, incl. 2 of the 4 F=1.0 topics |

**The asymmetry that shapes everything:** Quantum is *behind but warm* — you were in it
yesterday, and one topic is a single clean rung from +58.5 marks. CV is *ahead but cold* —
78.9% secured on paper, but not retrieved once in seven weeks, and its whole geometry
branch was never opened.

> ⚠️ **Treat CV's 78.9% as optimistic.** That figure is from 29 June, and its marks
> attribution doesn't reconcile with the ROI sheet: mastered topics sum to G ≈ 0.81 while
> unmastered sum to G ≈ 0.62 — they overlap, so the "175 combined marks" denominator
> double-counts. The cold diagnostic on Thu 20 Aug is what turns that number back into a
> fact. Plan around the diagnostic, not around 78.9%.

---

# PART 1 — QUANTUM · Tue 18 – Thu 20 Aug

## The arithmetic

| Topic | Marks | State | In plan? |
|---|---|---|---|
| Hamiltonian Dynamics | 58.5 | rung 5/6 — one clean cold attempt away | **Day 1, first block** |
| Quantum Fourier Transform | 44.5 | untouched, D4, all prereqs mastered | **Day 1–2** |
| Partial Measurement | 29.0 | untouched, D4, prereqs freshly re-mastered | **Day 2** |
| Bernstein-Vazirani | 17.5 | untouched, D3 | Day 2 overflow |
| Physical Qubit Implementation | 12.0 | untouched, D3, descriptive | **Day 1, evening** |
| Bomb Tester | 6.0 | untouched, D3 | **Day 1, evening** |
| Grover's / Shor's / Stabilizer / QEC | 96.5 | D4–D5 behind unsecured prereqs | **cut** |

**Projected if this lands:** 378 / 492 ≈ **77%**, up from 46.3%.

**Cut deliberately (~96 marks).** Shor's, Stabilizer and QEC are D5 and each sits behind
two or three prerequisites that are themselves unsecured — in 10 hours they return partial
rungs on three topics instead of full mastery on three cheaper ones. Grover's is D4 with
four prerequisites. Not worth the hours you have.

---

## Day 1 — Tue 18 Aug · 5h · close the ramp, then open the big block

### Block 1 — 90m · **do this first, while fresh** · `/study-run 90m`

The 16 Aug log is explicit: HD's final rung "needs a clean day, not a tired one." This is
that day, and this is the clean hour. Do not open it after four hours of other work.

1. **Eigenbasis-normalization micro-drill (15m).** This is the *live* gap — it fired twice
   in one rung on 16 Aug (expanding a state in an eigenbasis with coefficients 1,1 instead
   of 1/√2,1/√2). The H−λI sign bug is already resolved; don't re-drill that. Drill only:
   given eigenvectors and a state, expand it *and normalize* — c₊² + c₋² = 1.
2. **Hamiltonian Dynamics rung 6, cold and unaided.** Fresh exemplar. Then boss-check.

**+58.5 marks → 286.5 (58.2%).** This is the single highest-value block of the two days.

### Block 2 — 75m · review sweep, protect the 228

All seven mastered topics. Five are overdue since 15 Aug (Probabilistic Matrices,
Probability Distribution Vectors, Quantum State Validity, Unitary Matrices, Quantum
Amplitudes); Tensor Products and Quantum Measurement come due **today** at a short
interval — that short interval is exactly the point of having re-secured them on 16 Aug.

> On 14 Aug, skipped/failed reviews dropped coverage from 46.3% to 25.0% **in one sitting**.
> Losing a mastered topic costs strictly more than gaining a new rung. This block is not
> optional and it does not get shortened when Block 1 runs over.

### Block 3 — 90m · **Quantum Fourier Transform**, first contact + rungs 1–3

44.5 marks, the largest untouched block, and it sits directly on Unitary Matrices +
Tensor Products + Amplitudes — all secured, two of them re-secured 48h ago. Don't chase
full mastery today; rungs 1–3 on 44.5 marks beats rung 6 on 12.

### Block 4 — 45m · evening, low-math

- **Physical Qubit Implementation** rungs 1–3 (12 marks, D3, descriptive — no algebra load
  at the end of a long day).
- **Bomb Tester** rung 1 (6 marks) if energy allows.

*Day 1 target: HD mastered, 228 protected, QFT at rung 3, ~300/492.*

---

## Day 2 — Wed 19 Aug · 5h · new marks, then rehearse the format

### Block 1 — 90m · reviews, then **Partial Measurement** rungs 1–4

Due reviews first (HD enters the queue at interval 1; Tensor and QM cycle again). Then
Partial Measurement — 29 marks, D4, but its prerequisites (Tensor Products + Quantum
Measurement) were re-mastered 16 Aug and reviewed twice since. It shares machinery with
everything you've just done, which makes it the cheapest new topic on the board.

### Block 2 — 90m · **QFT** rungs 4–5 → mastery attempt

44.5 marks. If the mastery attempt fails on completeness rather than concept, re-attempt
once with the whole-question check — that's a cheaper fix than another rung.

### Block 3 — 75m · **timed mixed past paper**, exam conditions

Both practice E-tests from `final_20_08_2026/exams/`. Mixed, timed, no scaffolding, no
notes. **This block exists specifically because answer completeness is where your marks
leak, and completeness only fails under time pressure.** It cannot be cut.

### Block 4 — 45m · triage

Whatever the paper exposed, in mark order. If it came back clean: **Bernstein-Vazirani**
rungs 1–2 (17.5 marks, D3) purely so it isn't a blank page.

**Close with `/study-run close`** so the ledger is accurate going into the exam.

*Day 2 target: PM + QFT secured, one timed paper marked, ~378/492 ≈ 77%.*

---

## Day 3 — Thu 20 Aug · EXAM DAY

**Pre-exam, 45 minutes maximum. No new material. No hard problems.**

- Skim `QC_Exam_Cheatsheet.pdf` and `Cheatsheet_Eigenvectors_psi_t.pdf`.
- One tensor-order check on a 3-factor product (the 14 Aug bug).
- One post-measurement-state check (the other 14 Aug bug).
- Re-read the completeness rule below. That's it. Then stop.

**In the exam — the two rules that are worth more than any topic:**

1. **Re-read every question and count its parts before you move on.** Three of your last
   four losses were right math with a component missing — not wrong beliefs.
2. **Your two named leaks are tensor factor order and the post-measurement state.** When
   either appears, check it twice.

**After the exam:** ~3h of CV, but low-cognition only — see Part 2, Day 0.

---

# PART 2 — COMPUTER VISION · Thu 20 – Wed 26 Aug

## The situation

Eight topics mastered on 29 June and untouched since. Eight topics never opened. Of the
four topics that appear in **every** past paper (F = 1.0), two are unmastered:
**Sliding-Window Object Detection** (rank 4, D2 — cheap) and **Stereo Vision and Epipolar
Geometry** (rank 6, D4 — expensive, ~11% of marks).

| Unmastered topic | Rank | F | D | Prereq chain | Verdict |
|---|---|---|---|---|---|
| Sliding-Window Object Detection | 4 | **1.0** | 2 | SVM | **must** |
| Stereo Vision and Epipolar Geometry | 6 | **1.0** | 4 | Camera Models → Homography | **must** |
| Image Segmentation (MRF / Graph Cuts) | 10 | 0.67 | 3 | Clustering ✓ | yes |
| RANSAC and Robust Estimation | 11 | 0.33 | 3 | none | yes — pairs with Homography |
| Homography and Image Alignment | 12 | 0.33 | 3 | Feature Detection ✓ | yes — gates Stereo |
| Camera Models and Projection | 13 | 0.67 | 2 | none | yes — gates Stereo |
| Support Vector Machines | 14 | 0.67 | 3 | none | yes — gates Sliding-Window |
| Structure from Motion | 16 | 0.67 | 4 | three prereqs | **cut** (overflow only) |

**The strategy:** the 138 stale marks are decayed, not lost, and re-securing them is far
cheaper per mark than building new topics — so they get retrieved early and cycled daily.
But six of the eight new topics form two clean prerequisite chains that unlock the two
F=1.0 topics, and those chains are the whole reason CV can move from "78.9% on paper" to
"actually passable." Both chains get run.

- **Geometry chain:** Camera Models (D2) → Homography (D3) → Stereo Vision (D4), with
  RANSAC (D3) taught adjacent to Homography — RANSAC *fits* homographies, so teaching them
  back to back is materially cheaper than teaching them apart.
- **Classifier chain:** SVM (D3) → Sliding-Window (D2).

---

## Day 0 — Thu 20 Aug, post-exam · ~3h · diagnostic only

Your brain is spent. Do retrieval, not learning.

### Block 1 — ~100m · **cold diagnostic sweep**

One past-paper exam question per mastered topic, unaided, no notes: Image Filtering,
Feature Detection, Clustering, Edge Detection, NN Training, CNNs, Semantic Segmentation,
Boosting. ~12m each.

**This is the most important block in the CV half of the plan.** It converts "78.9% seven
weeks ago" into a real number, and it tells you which topics need repair before you spend
a single hour on new material. Record every result — this is what Day 1's first block acts on.

### Block 2 — 60m · **Camera Models and Projection**, first contact + rungs 1–3

D2, no prerequisites, and it's the gate on the entire geometry chain. Starting it tonight
means Homography can start tomorrow morning instead of tomorrow afternoon.

---

## Day 1 — Fri 21 Aug · 5h · repair, then open geometry

| | |
|---|---|
| 90m | **Repair** the 2–3 weakest topics from the diagnostic, in mark order. Re-master, don't re-teach. |
| 90m | **Camera Models** finish → mastered. Then **Homography** first contact + rungs 1–2. |
| 90m | **RANSAC** rungs 1–4 → mastered (D3, no prereqs). Taught right after Homography's setup on purpose. |
| 30m | Due reviews + close. |

---

## Day 2 — Sat 22 Aug · 5h · finish Homography, open Stereo

| | |
|---|---|
| 30m | Due reviews (the June-mastered set is now cycling at short intervals). |
| 120m | **Homography** rungs 3–4 → mastered. |
| 120m | **Stereo Vision and Epipolar Geometry** first contact + rungs 1–3. The big one: D4, 5 rungs, F=1.0. |
| 30m | Consolidation + close. |

---

## Day 3 — Sun 23 Aug · 5h · close Stereo, run the classifier chain

| | |
|---|---|
| 30m | Due reviews. |
| 90m | **Stereo Vision** rungs 4–5 → mastered. ~11% of the paper, appears in every past exam. |
| 90m | **Support Vector Machines** first contact + rungs 1–4 → mastered (D3). |
| 60m | **Sliding-Window Object Detection** rungs 1–3 → mastered (D2, now unlocked, F=1.0). |
| 30m | Reviews + close. |

---

## Day 4 — Mon 24 Aug · 5h · last new topic, first full rehearsal

| | |
|---|---|
| 30m | Due reviews. |
| 90m | **Image Segmentation with MRF and Graph Cuts** rungs 1–4 → mastered (D3; Clustering prereq already held). |
| 120m | **Full timed mock: `2023_Exam.pdf`.** Exam conditions. No notes, no scaffolding, clock running. |
| 60m | Mark it honestly. Write down every leak, with marks attached. |

**This is the last day any new topic opens.**

---

## Day 5 — Tue 25 Aug · 5h · repair and rehearse only

| | |
|---|---|
| 120m | Repair every leak from yesterday's mock, in mark order. |
| 90m | **Second timed paper:** `mockup_exam_2023.pdf` + `Old Exam Tasks.pdf`, mixed. |
| 60m | Mark it. Repair the top 3 leaks. |
| 30m | Fast recognition-level sweep across all mastered topics. |

**No new topics today, at all.** Structure from Motion is the only overflow candidate, and
only if everything above genuinely landed.

---

## Day 6 — Wed 26 Aug · EXAM DAY

45 minutes, cheatsheet-level skim, no new material, no hard problems. Then stop.

---

# Standing rules — both exams

1. **Every session opens with due reviews.** Non-negotiable. On 14 Aug, skipping this cost
   105 marks and dropped quantum coverage from 46.3% to 25.0% in a single sitting.
2. **Answer completeness is your documented #1 leak.** Three of the last four quantum
   losses were correct math with a component missing. Before submitting anything: re-read
   the question, count the parts, confirm each one got an answer.
3. **Cap of 3 graded questions per session.** Reviews don't count against it.
4. **Close every session with `/study-run close`,** so the ledger reflects reality rather
   than this plan.
5. **If a block runs long and pulls the next topic in, let it.** That's normal here and
   `close` reconciles it.
6. **Never cut a mock exam to buy time for a topic.** The mock is what tests the failure
   mode that's actually costing you marks.

---

# Risks, stated plainly

- **CV's 78.9% is unverified and seven weeks old.** The Thu 20 Aug diagnostic is the load-
  bearing block of the entire CV half. If it comes back much worse than 78.9%, shift Fri–Sat
  toward repair and cut MRF/Graph Cuts (Day 4) — cut new topics before you cut reviews or mocks.
- **Fri–Sun CV throughput is aggressive.** Three D3–D4 topics reaching mastery in three days
  assumes clean rungs. If Stereo Vision slips past Sun 23 Aug, drop MRF/Graph Cuts and let
  Stereo take Monday morning. Stereo is F=1.0 and MRF is not.
- **Quantum Day 1 Block 1 is load-bearing and time-of-day sensitive.** HD's final rung has
  already failed once from fatigue. If Tuesday morning gets disrupted, move it to Wednesday
  morning and push QFT rungs 4–5 to the evening — do not attempt it tired a second time.
- **~96 quantum marks are written off** (Shor's, Stabilizer, QEC, Grover's) and Structure
  from Motion is written off in CV. These are deliberate, not oversights. Revisit only if a
  day finishes early.
