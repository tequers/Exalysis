# CV Final — Study Plan v2 (10 h, 2 days)
Rebuilt 2026-08-24 from `archetypes.json` (42 archetypes, queue_rank order), `progress.json`
(3 interrupted sessions on 23 Aug), `syllabus.json` and `PROJECT_NOTES.md`. Supersedes v1,
which was written blind to this folder and pointed at blocks that are not the real queue.

**Exam Wed 26 Aug · 90 min · 94 marks · 6 questions (Q1–Q4 = 15, Q5 = 19, Q6 = 15) · handwritten,
blue/black ink · closed book, no notes, no calculator · 57.4 s per mark.**
`CV_RWTH_Exam_Cheat_Sheet.pdf` is revision material only — **it cannot go into the room.** The trap
list has to be memorised instead.

**Answer shape (the rule that decides the grade):** marks = number of distinct scorable statements.
2023 paper averages 2.0 marks/question, 58 % explain-derive. Count marks before writing.

## Where you actually stand
- **1 of 42 archetypes exam-ready** (`algorithm-steps-recall`, 22.35 marks) — and its RANSAC,
  Mean-Shift and Hough sub-drills are *still* uncorrected misses. The streak was archetype-level.
- 41 cold. Total first-pass drill estimate **270 min**; at your observed session pace (~1.6×)
  that is ~430 min of real drilling. Usable budget over 2 days ≈ **500 min**. It fits — with
  nothing to spare, which is why the drop list at the bottom is not optional.
- **pace_ratio has never been measured** (all three sessions interrupted). That is the single
  biggest unknown going in, and it is what the Day-2 half-mock is for.
- Course centre of gravity has moved to transformers: ranks 5–9 are new syllabus-derived
  archetypes with **no past-paper exemplar**. Old papers are a format example, not a content guide.

Budget rule: 300 min/day → 300 × 0.92 − 25 = **251 usable min/day**.

---

## Day 1 (today) — 251 min · repair the ready one, then the must_cover core + transformers

| Time | Sprint | Archetypes (queue_rank) | What specifically |
|---|---|---|---|
| 0:00–0:25 | **Repair, not review** | 1 `algorithm-steps-recall` | Per-sub-algorithm, not archetype-level: **RANSAC** (multiple-samples loop + re-fit on all inliers — dropped 5×), **Mean-Shift** (merge windows converging to the same mode — dropped), **Hough** (accumulator *cells* in parameter space, and it is not HOG — blanked 3×), **sliding window** (independent per-window classify + multi-scale pyramid + NMS, not a sequential pass) |
| 0:25–1:00 | **Formula + gloss** | 2 `def-formula-gloss` (13.7 stake, 9 real marks) | Indexed cross-correlation vs convolution, MRF energy `E(x,y)=Σφ+Σψ`, cross-entropy, camera intrinsics `K`, Gaussian kernel, hinge/L2. **Every formula gets a one-line gloss** — the gloss is the named trap and you hit it twice |
| 1:00–1:10 | break | | |
| 1:10–1:35 | **Figures** | 3 `read-figure-identify` (9 real marks) | Conv-type taxonomy standard/strided/transposed (output-vs-input size is the tell), same-padding case, and epipolar vocabulary: epipole vs epipolar line vs epipolar plane vs projected point (tangled 3×). Drill off the actual figures in `exams/exams_pdfs/2023_Exam.pdf` |
| 1:35–2:20 | **Transformers I** | 5 `attention-mechanics`, 6 `vit-architecture-and-tradeoffs` | `E=QKᵀ` → scale `/√D_k` → softmax over keys → `AV`; masked + multi-head; self vs cross; **why an MLP is required between attention layers**. ViT: patchify → CLS → pos-emb → encoder → MLP head; the three CNN inductive biases it gives up |
| 2:20–2:30 | break | | |
| 2:30–3:05 | **Transformers II** | 8 `triplet-loss-and-metric-learning`, 9 `transformers-for-dense-tasks`, 7 `self-supervised-and-multimodal` | Triplet + margin, batch-hard mining; DETR set prediction removing NMS, Mask2Former, EoMT; pretext tasks, contrastive, CLIP zero-shot |
| 3:05–3:30 | **EM** | 4 `em-for-mixture-models` | E-step responsibilities, M-step re-estimation, why it beats hard assignment. Must_cover, no exemplar — build the answer from the slides |
| 3:30–4:11 | **Cheap-ROI mixed sprint** | 14 `invariance-properties-check`, 15 `boosting-mechanics`, 16 `enumerate-and-describe`, 17 `viola-jones-mechanics`, 18 `harris-hessian-mechanics` | ~28 marks at stake for ~22 min of estimate — the best marks-per-minute on the board. Run mixed, one clock |

**End of day:** `/session-end` — persist state before you stop, not tomorrow.

---

## Day 2 (exam eve) — 251 min · judgement + compute + stereo, then measure your pace

| Time | Sprint | Archetypes (queue_rank) | What specifically |
|---|---|---|---|
| 0:00–0:20 | **Decay check** | yesterday's 3 weakest | 2 drills each, cold. Anything that fails goes back to cold — that already happened once to `read-figure-identify` |
| 0:20–1:05 | **Judgement family** | 19 `feasibility-judgement`, 20 `why-design-choice`, 33 `failure-mode-and-fix`, 34 `why-method-unsuitable`, 29 `compare-two-methods` | ~24 marks. These are all "justify your answer" — the justification is a separate mark, a bare verdict scores zero. Name the artefact (aliasing, ringing, checkerboard, broken edges) |
| 1:05–1:15 | break | | |
| 1:15–1:55 | **Compute family** | 21 `code-vision-function`, 23 `cnn-parameter-count`, 27 `separable-filters`, 28 `feature-vector-size-count`, 36 `receptive-field`, 31 `apply-on-given-grid` | ~27 marks. Only place arithmetic speed matters; no calculator, so show the full multiplication. Watch HOG cell size × bin count (the correction logged in PROJECT_NOTES) |
| 1:55–2:25 | **Stereo / epipolar** | 25 `epipolar-glossary`, 37 `fundamental-matrix-rank`, 10 `derive-epipolar-constraint` (must_cover, 6 real marks) | The 3rd-biggest topic by marks and deep mode never opened it. Glossary first — the derivation is worthless if the vocabulary is still tangled |
| 2:25–2:35 | break | | |
| 2:35–3:20 | **Half mock, 45 min, exam conditions** | `/mock-exam 45m` | Handwritten, blue/black ink, no notes, no calculator, one clock. Purpose is the **pace_ratio you have never measured**, not the score |
| 3:20–3:40 | Grade + log traps | | Grade against the mark scheme in one pass; every miss goes in the trap list |
| 3:40–4:11 | **Leftovers by ROI** | 22 `concept-brief-explain`, 24 `mrf-graphcut-mechanics`, 26 `pyramid-mechanics`, 30 `segmentation-via-clustering`, 35 `conv-correlation-properties`, 32 `sketch-or-draw`, 11 `deformable-part-models`, 12 `resnet-and-training-practices` | Take in that order; stop when the clock stops, don't extend |

**Exam eve, 20 min, no new material:** recite the trap list and the step-lists (RANSAC, Mean-Shift,
Hough, sliding window, Canny, Harris, attention's 4 ops). Closed book means this list only exists
in your head.

---

## Deliberately dropped — say it out loud so it isn't an accident
`13 derive-homography-A` (at risk, syllabus weight 0.5 — timebox to 10 min if any slack appears,
do not chase exam-ready) · `38 derive-eight-point` · `39 derive-ransac-iterations` ·
`40 multiscale-dense-prediction` · `41 derive-triangulation` (15 min for 3.6 marks — worst ROI on
the board) · `42 derive-sfm-dof` (at risk, weight 0.5).
Combined ≈ 15 marks of stake, ~40 min saved, and every one of them is either not-in-the-real-paper
or not confirmed by the current slides.

## Enforce on every single answer
1. Count the marks first. Paragraph for 1 mark = stolen time; one sentence for 4 = three marks gone.
2. Two-part questions have two halves — you routinely answer only the first.
3. "Justify" = separate mark. Name the artefact; "worse results" scores nothing.
4. Formula questions want formula **+ gloss**.
5. Step-list questions want the *complete* list — your misses are always the last step (RANSAC re-fit, Mean-Shift merge).
