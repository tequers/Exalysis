# Project Notes — Computer Vision, final_26_08_2026

Per-Exam quirks and overrides for the tutor prompt (`tutor/TUTOR_SYSTEM_PROMPT_v9.md`, shared across every Course/Exam — highest version wins).
Exam-specific facts live **here**, not in the prompt. Append as new quirks are discovered.

This folder is one Exam under `Courses/Computer Vision/`, following the `Courses/<Course>/<Exam>/` layout and `<type>_<date>` naming convention — see root `CONTEXT.md` and `docs/adr/0001-course-exam-hierarchy.md` for why.

## Course / Exam

- **Course:** Computer Vision (RWTH Aachen)
- **Exam:** `final_26_08_2026`
- **Exam date:** 2026-08-26 (also set in `progress.json`)
- **Total marks:** 175 = combined `2023_Exam` + `Old_Exam_Tasks`. `mockup_exam_2023` is practice material and is **not** in the 175 total, though its questions are valid exemplars.

## Path deviations from the standard layout

- All pipeline outputs (`taxonomy.json`, `parsed/`, `Exam_ROI_Pipeline.xlsx`) and tutor state (`progress.json`, `sessions.json`) live in **this folder**, not under `pipeline/` or `tutor/` — this Exam is a fully self-contained unit (ADR 0001). `pipeline.py` and the tutor prompt itself stay shared at `pipeline/` and `tutor/`.
- ROI sheet: `Exam_ROI_Pipeline.xlsx` (this folder), sheet **`ROI Scores`**.
- There is no `.study-run.json` discovery cache anymore — it went stale (pinned a superseded prompt version) and was deleted after this migration. `/study-run` re-discovers paths by search every time now.
- No `tutor/glossaries/` directory yet — only `tutor/course_glossary_prompt.md` (the generator prompt, not a glossary). Treat the glossary as absent until one is built.

## Dead paths — never read

- `docs/archive/version_outputs/` — contains stale copies of `taxonomy.json` and `Exam_ROI_Pipeline.xlsx`. Filename matches here are traps.
- `tutor/_archive/` — superseded prompt versions (v1–v4).

## Skill sources — kept in `tutor/`, not here

Source-of-truth copies of the project's custom skills live in `tutor/` (shared across every Course/Exam, alongside the tutor prompt); the installed skill is saved to the account separately, so **edit both when changing one**.

- `tutor/PROBLEMATIC_SKILL_v1.md` → installed as `/problematic`
- `tutor/STUDY_RUN_SKILL_v2.md` → installed as `/study-run`

`/problematic` and the tutor prompt's `[Problematic]` beat share one rule: **requirement, never mechanism.** The tutor runs it automatically at every new topic; the slash command is for on-demand framing of a sub-step mid-ramp.

## Data quirks

- `taxonomy.json` holds **16 topics**; `progress.json` lists only started ones (10 as of 2026-08-01). **Pick the next topic from the ROI sheet or taxonomy, never from the ledger.**
- **13 of 105** parsed questions carry more than one topic → the coverage de-duplication rule is load-bearing here, not theoretical.
- Loci section headings are informal and don't match topic names exactly (e.g. "Canny Edge Detection" ↔ topic "Edge Detection"). Match on significant words.
- Semantic Segmentation marks (8) are **estimated** from parsed question totals, not read off an official mark scheme.

## Status snapshot (2026-08-01)

- Mastered: Image Filtering and Convolution, Feature Detection and Description, Clustering and Mixture Models, CNNs, Edge Detection, NN Training and Loss Functions, Boosting and Ensemble Classifiers, Semantic Segmentation.
- Locked: Sliding-Window Object Detection (rank 4), Stereo Vision and Epipolar Geometry (rank 6).
- No study session has run since 2026-06-29 — mastery has been flat at 78.9% (8/16 topics) for 5+ weeks as of this migration (2026-08-08). 18 days remain to the exam.

## Exam-prep (fast) mode — added 2026-08-21

The fast mode from the quantum-computing exam is now wired up here. It runs **alongside** the
deep tutor and shares no state with it: `/start-session`, `/session-end`, `/mock-exam`,
`/cheat-sheet`, governed by `tutor/EXAM_PREP_PROMPT_v1.md`. Deep mode (`/study-run` +
`/continue-study-session`) is untouched.

**`exam_ready` and `mastered` are different things and are never added together.**
`mastered` = unaided ≥90% on an exam-format question (deep mode, 138/175 marks).
`exam_ready` = 2 consecutive clean drills inside the time budget (fast mode, starts at 0).

### Files

- `archetypes_map.py` — **judgement only.** q_id → archetype, plus the playbooks. No arithmetic.
- `archetypes_postprocess.py` — **arithmetic only.** Computes every number and writes
  `archetypes.json`. Re-run it after editing the map; never hand-edit `archetypes.json`.
- `archetypes.json` — 33 archetypes, 105/105 questions, 220/220 marks mapped.
- `../.study-run.json` — **exam-prep cache only.** Carries no `paths`/`method` block for deep
  mode, so it cannot go stale the way the previous full cache did (see "Path deviations").

### Why the playbook shape differs from the quantum course

**This is a verbal exam.** 128 of 220 marks (58%) are `explain_derive`; the real 2023 paper
averages **2.0 marks per question**. The marks count *distinct scorable statements*, not steps
of a calculation. So the mode-level rule here is:

> **marks = number of things you must write.** 2 marks = 2 statements.

Playbooks therefore carry two fields the quantum ones didn't: `answer_shape` (the shape of a
full-mark answer, e.g. "2 methods × (1 adv + 1 disadv)") and `why` (**one sentence** of causal
intuition — on an explain-heavy paper the question literally asks "why", so a recipe alone
underperforms). `why` is capped at one sentence on purpose; it is not a derivation.

Recall archetypes (`algorithm-steps-recall`, `concept-brief-explain`) put the answer *shape* in
the playbook and cycle content through instances — no single step list covers Canny and k-Means.
Derivation archetypes (`derive-epipolar-constraint`) put the actual derivation in the playbook.

### Budget basis — do not re-derive from anything else

**`2023_Exam` alone: 94 marks / 47 questions / 90 minutes → 57.4 s per mark.**
Not the 220-mark sum of all three papers; not `Old_Exam_Tasks` (a compilation of tasks, not one
sitting); not `mockup_exam_2023` (practice). Those two supply archetypes and exemplars but never
timing. `archetypes_postprocess.py` asserts the summed budgets land within 10% of the exam
length — currently **−1.1%**. On the quantum port a wrong denominator made every budget 2.4×
too fast, which is why this check exists.

### The `must_cover` tier

Pure marks-per-minute ROI buries the big derivations, because they cost the most minutes per
mark. `derive-homography-A` (7 real marks) and `derive-epipolar-constraint` (6) ranked 28th and
30th of 33 — together **13 of the real paper's 94 marks**. Any archetype carrying ≥5 marks in the
genuine sitting is now flagged `must_cover` and floated to the front tier; ROI still orders
within tiers. Five archetypes qualify, covering **41 of 94 real-paper marks (44%) in ~46 min**.

### Open question — exam conditions NOT confirmed

- **Aids: assumed none, UNCONFIRMED.** No statement from course staff is on file. Recorded as
  such in `archetypes.json → exam_format`. `/cheat-sheet` will ask before producing anything
  rather than guess. **Worth asking staff** — on the quantum exam this turned out to permit a
  handwritten A4 sheet, which changed what was worth drilling.
- **Duration 90 min is the user's statement, not an official source.** It drives every budget.
  If it changes, edit `EXAM_MINUTES` in `archetypes_postprocess.py` and re-run — budgets rescale
  automatically, no re-mining needed.

### Known gaps

- **8 questions (21 marks, ~10%) depend on figures the parsed JSON does not contain** — e.g.
  *"What is the output of correlating the image below?"*. Their archetypes carry
  `figure_dependent: true` (`apply-on-given-grid`, `sketch-or-draw`, `read-figure-identify`).
  Drills must regenerate a textual matrix rather than reuse the original figure, so those
  variants won't look identical to the paper.
- **~72 of 220 marks sit in six topics deep mode never opened** (Stereo Vision 27 — the 3rd
  largest — plus Image Segmentation MRF, Homography, RANSAC, SVM, Camera Models, SfM). Exam mode
  ignores prerequisite locks, so these are reachable immediately and rank high.
- Semantic Segmentation's 8 marks remain estimated, as noted above.

### 2026-08-21 — Exam conditions CONFIRMED from the 2023 paper (OCR)

A clean OCR of `2023_Exam.pdf` was added at `exams/exams_txt/`. Its cover sheet settles both
questions that were previously recorded as assumptions:

- **"Duration of the exam: 90 minutes."** The 90-minute figure driving every budget is correct.
- **"No additional aids (notes, calculator, etc.) are allowed."** Closed book, **no cheat sheet**.
  `/cheat-sheet` does not apply to this exam and will refuse; use its revision-list fallback.
- **Handwritten on paper**, blue or black ink — pencil and red/green pens are *not graded*. 20 pages.
  This is **not** an electronic exam (contrast the quantum course's Dynexite sitting).
- Per-question marks: **Q1–Q4 = 15, Q5 = 19, Q6 = 15, total 94** — matches the parsed total exactly.

*Caveat:* these are the **2023** sitting's conditions. Strong evidence for 2026, not proof.

**Consequence for drilling:** no calculator means arithmetic in `cnn-parameter-count`,
`feature-vector-size-count` and `separable-filters` must stay hand-doable — which it already is.
No aid sheet raises the value of the trap list as a *memorised* final-review checklist.

### 2026-08-21 — Staff: lecture content has changed. Old exams are a FORMAT example only.

Verbatim from the campus message:

> "Please note that the content of the lecture has changed since three years ago. So use this
> old exam as an example, not as the basis for studying. The slides and exercises are the main
> content to be used for studying."

**This invalidates half the archetype model and explicitly endorses the other half.** The split
is now first-class in the data (`syllabus.json`, and `syllabus_status` on every archetype):

| | Anchored on | Confidence | Covers |
|---|---|---|---|
| **Form layer** | the 2022/2023 papers | **HIGH** — staff said to use the old exam *as an example*, which is exactly this | duration, mark total, `answer_shape`, "marks = distinct scorable statements", `trigger`, `budget_s`, format mix, the generic traps |
| **Content layer** | the 2022/2023 papers | **LOW** — pre-change | which topics appear, `marks_at_stake`, `roi`, `queue_rank`, `must_cover`, the topic-specific bodies of `playbook.steps` |

**Nothing was down-weighted on speculation.** All 16 topics are `unverified`, carried at full
weight, and flagged. Assuming a topic is gone is as unfounded as assuming it stays; the slides
settle it. `archetypes_postprocess.py` now emits a standing WARNING while `syllabus.json` is a
stub, so the provisional status cannot be forgotten.

**The likely real danger is a blind spot, not a bad weight.** Curricula of this kind usually
drift by *adding* material. If that holds here, the costly failure is a current syllabus topic
with **no archetype at all** — marks nothing in the queue drills. The postprocess computes
`blind_spots` as soon as the syllabus is filled in; while it is a stub it reports
"not checked", never "none".

**What is needed:** the current slide deck and exercise sheets, dropped into this folder
(`lectures/`, `exercises/`). The lecture titles / table of contents alone are enough to set each
topic's status; that is a five-minute job and it converts the whole content layer from
provisional to verified.

### 2026-08-21 — Corpus corrections

- **`Old Exam Tasks.pdf` = `cv_ss_2022.pdf`, byte-identical (261,431 bytes).** It was always the
  **SS 2022 exam paper**, not a compilation of tasks. Its 0.85 weight stands, but for a new
  reason: it is a real sitting, just the oldest and so the most exposed to the content change.
  `parsed/Old_Exam_Tasks.json` also carries `year: 2026`, which is wrong — it is 2022. Both are
  cosmetic until the next re-parse, which will fix them.
- **`exams/exams_txt/cv_2022.txt` is 0 bytes** — the 2022 OCR has not landed yet.
- `cv_2023.txt` and `mockup_2023.txt` are good. Both cover sheets independently confirm
  **90 minutes** and **no aids**.

### 2026-08-21 — Exam format confirmed from the CURRENT official slides

> "• Exam format
>  ➢ Written exam, duration 90min, closed book
>  ➢ Exam registration via RWTH Online"

This supersedes the 2023 cover sheet as the authoritative source: it is the **current** course
speaking, not a three-year-old sitting. **90 minutes and closed book are settled.**

**The finding that matters beyond the facts:** the current slides state the *same* duration and
the *same* closed-book rule as the 2023 paper. So while staff say the **content** changed, the
**form demonstrably did not.** The form/content split this mode is built on is now supported by
evidence rather than assumed — old papers remain a valid source for how questions are asked and
marked, and an invalid one for what they are about.

Detail nuance: "closed book" (current slides) does not itemise aids; "no additional aids (notes,
**calculator**, etc.)" comes from the 2023 paper only. Treated as no calculator — drills keep
arithmetic hand-doable, which they already do. Recorded separately in `exam_format.calculator`
so the weaker-sourced detail is not mistaken for the stronger one.

`/cheat-sheet` remains inapplicable to this exam.

**The user has the slides.** Filling in `syllabus.json` is now a reading task, not a blocked one
— the lecture list / table of contents is all that is needed.

### 2026-08-21 — `syllabus.json` BUILT from the official slide blocks. Blind spots found.

The user supplied the current slide deck's five block descriptions. `syllabus.json` is now built
from them and the content layer is verified rather than provisional.

**Result: 14 current · 2 at_risk · 6 new (blind spots) · 0 dropped.**

#### The finding that justified the whole exercise

**Six topics the current slides teach appear in NO past paper.** The blind-spot concern was not
hypothetical — the course drifted by *adding*, exactly as suspected:

| Blind spot | Block | Evidence |
|---|---|---|
| **Metric Learning and Triplet Embeddings** | 4 | Siamese networks, triplet loss, anchor/positive/negative, batch hard vs batch all |
| **Expectation-Maximization for Mixture Models** | 2 | MoG "optimized via the EM algorithm" — EM itself never examined in any past paper |
| **Deformable Part-based Models** | 3 | root filter + part filters + deformation cost |
| **Multi-scale Dense Prediction (FPN, ASPP)** | 4 | named for multi-scale dense prediction |
| Thin Lens Model | 1 | "pinhole and thin lens models" |
| Region Proposals | 3 | named alongside cascading classifiers |

**Four archetypes were built to close the significant ones** (`triplet-loss-and-metric-learning`,
`em-for-mixture-models`, `deformable-part-models`, `multiscale-dense-prediction`). They carry
`source: "syllabus"`, `marks_estimated: true`, empty `exemplars`, and an `exemplar_note`.

*Why this doesn't violate the no-guessing rule:* that rule forbids inventing archetypes where
real-paper evidence exists. Here it doesn't — the content is named by the course itself, and the
**form** is independently confirmed. Content from the slides, shape from the measured form;
neither half invented. Mark estimates come from the block's question total in 2023 (Q3/Q4 = 15,
Q5 = 19) spread across the sub-areas the slides name.

Thin Lens and Region Proposals are left open as accepted low-priority risk.

#### A factual error the slides caught

**HOG uses 9 orientation bins**, per the current slides. The `feature-vector-size-count` playbook
said 8, taken from the mockup paper's question. That was wrong for the current course and would
have cost marks. Corrected, with a trap added telling the user to read cell size and bin count
off the question rather than from memory.

#### Two archetypes demoted, not cut

`Homography and Image Alignment` and `Structure from Motion` are **named in no block**, while
their sibling topics in Block 5 are. Status `at_risk`, weight **0.5** — demoted, not dropped,
because the source is a block *summary*, and under-drilling a topic that turns out to be examined
costs far more than over-drilling one that isn't. `derive-homography-A` stays in the must-cover
tier (7 marks in 2023) at a lower rank.

**Worth 60 seconds:** search the slide TOC for *homography*, *image alignment*, *panorama*,
*warping*. That single check settles the most consequential uncertainty left in this exam.

#### Two ordering bugs fixed

1. **Multi-topic status propagation took the WORST status; it must take the BEST.** An archetype
   is a question *pattern* — if any one of its topics is still taught, the pattern can still be
   examined. Worst-wins had demoted `derive-triangulation` (Stereo = current, SfM = at_risk) even
   though Block 5 names triangulation verbatim, and `derive-ransac-iterations`, whose RANSAC half
   is "integrated throughout".
2. **Syllabus-derived archetypes sank to ranks 31–34** because ROI is computed from past-paper
   marks — the exact measure the staff warning undermined. They now enter the front tier by a
   second route: being the only coverage of confirmed-current material. Front tier is now 9
   archetypes, ~80 min.

Total drill estimate: **225 min** (was 191), of which 34 min is the new syllabus material.

### 2026-08-21 — Exercise notebooks mined. Vision Transformers found; nothing else covered them.

`exercises/*.ipynb` (Exercises 1–5, Jupyter) were added and mined.

**They are programming tasks, but that is not what makes them useful.** Their *markdown* cells
carry conceptual questions in exactly the exam's voice:

> "Which network has more parameters, this or the previous one?"
> "What is the size of the receptive field of the units in the layer directly before the global average pooling?"
> "Why do we use addition instead of concatenation?"
> "provide formulas to compute $T$ and $D$ given the other terms"

Those prompts — not the code — are the archetype source. Several even ship worked answers.

#### The find: Vision Transformers

**Exercise 4 covers ViT in depth, and it appears in NO past paper AND in none of the slide block
summaries.** It surfaced only from the exercises — which is exactly why staff named slides *and*
exercises as the study basis, and the single strongest vindication of mining both.

Covered there with formulas: patchify (`T = H_n×W_n`, `D = C×H_p×W_p`), positional encoding
(sin/cos, given explicitly), **why addition rather than concatenation**, self-attention
`softmax(QK^T/√d)V`, the transformer block `z' = MSA(LN(z)) + z`, class-token classification.
Plus ResNet residual blocks, global average pooling, LR decay, L2/weight decay, and a worked
receptive-field-with-stride answer (3 → 7 → 15, *not* 3 → 5 → 7).

Two archetypes added: **`vit-and-self-attention`** (5 marks est.) and
**`resnet-and-training-practices`** (3 marks est.).

#### The block summaries were incomplete — which changes how to read absence

The summaries omitted transformers, yet the exercises prove they are taught. So **absence from a
block summary is weaker evidence than it first appeared.** This is a reason *not* to demote
`Homography and Image Alignment` or `Structure from Motion` any further than `at_risk` 0.5, and it
is recorded against those entries.

#### Exercises are the practical subset — absence there means little

Absent from every exercise: triplet/Siamese, FPN/ASPP, EM/MoG/k-Means/Mean-Shift, DPM, homography,
SfM, Viola-Jones/boosting/cascades, U-Net/SegNet/FCN. Several of those *are* named in the slides,
so exercise-absence does **not** override slide-presence. The examinable set is the **union** of
slides and exercises, per staff — not the intersection.

Strong corroborations: Exercise 2b (graph cuts: colour histograms → unary → pairwise → iterative)
maps almost one-to-one onto 2023 Q3a/Q3b, and Exercise 5b names *Normalization* alongside
Fundamental-matrix estimation, confirming the normalized-8-point emphasis.

#### State

**39 archetypes** — 33 past-paper, 6 syllabus/exercise-derived carrying ~22 estimated marks.
Must-cover tier: **11 archetypes, ~99 min**. Total drill estimate **244 min** (from 191).
Remaining blind spots, accepted as low priority: Thin Lens Model, Region Proposals.

### 2026-08-21 — Lecture summaries mined. The course has moved to transformers.

`lectures/_summaries/*.txt` (8 files, 124 KB, slide-level) added and mined. This is the most
authoritative content source available and it substantially redrew the picture.

#### Handle these files with care — two defects

1. **`cnn_2.txt` is a BYTE-IDENTICAL duplicate of `5_transformers.txt`** (same md5). A genuine
   "CNN part 2" summary may therefore be missing.
2. **Filenames do not match contents.** `7_reconstruction.txt` is *transformers*;
   `6_local_features.txt` is *3D reconstruction / stereo / stitching / Harris / SIFT / SURF*;
   `5_transformers.txt` is *FCN pose estimation + Siamese/triplet/contrastive*. Trust contents.

**The summaries are demonstrably INCOMPLETE.** Epipolar geometry, Fundamental/Essential matrices,
the 8-point algorithm, RANSAC and the Hough transform appear in **no** summary — yet Block 5 names
the first four outright and Block 1 gives the Hough voting equation verbatim.

> **Consequence, recorded in `syllabus.json`: nothing is marked `dropped` anywhere.** With sources
> this incomplete, absence can never justify deleting an archetype — only the `at_risk` demotion,
> which keeps it in the queue at half weight.

#### The centre of gravity has moved

`7_reconstruction.txt` is the largest summary (24 KB) and runs
**attention → ViT → DETR / Mask2Former / EoMT → CLIP / self-supervised learning**. None of it is in
any past paper. Five archetypes now cover it, replacing the single earlier `vit-and-self-attention`
(one archetype could not hold it, and the slides examine mechanics and architecture-level
trade-offs as different question types):

- `attention-mechanics` — scaled dot-product, `E = QK^T`, masked, multi-head, self vs cross, and why an MLP is required between attention layers
- `vit-architecture-and-tradeoffs` — patchify, CLS token, ViT vs CNN, and the three CNN inductive biases (locality, equivariance, invariance)
- `transformers-for-dense-tasks` — DETR set prediction removing NMS, Mask2Former, EoMT
- `self-supervised-and-multimodal` — pretext tasks, contrastive, CLIP's shared embedding space, zero-shot
- (`triplet-loss-and-metric-learning` confirmed in depth by `5_transformers` slides 11–18)

#### Corrections the slides forced

- **ASPP / atrous convolution appear in no lecture summary while FPN does.** The block summary
  named both. `multiscale-dense-prediction` narrowed to FPN, cut 3 → 2 marks, with a trap saying
  not to spend time on ASPP without better evidence.
- **α-expansion** (non-binary graph cuts) and augmenting-path max-flow added to
  `mrf-graphcut-mechanics`.
- **Generalized Distance Transform** added to `deformable-part-models` — it is how the maximisation
  over part placements is made tractable, and the slides give it its own slide.
- **Image Stitching** (`6_local_features` slides 27–30) *is* homography estimation, so the
  capability is taught even though the word never appears. Another reason `derive-homography-A`
  stays in the must-cover tier.
- **Mean-Shift** appears only in the *detection* summaries, never in `image_segmentation`, where
  EM/MoG is the centrepiece. De-emphasised, not proven absent.

#### State

**42 archetypes** — 33 past-paper, 9 derived. Must-cover tier **13 archetypes, ~120 min**.
Remaining un-archetyped blind spots, accepted as low priority: Backpropagation and Optimisation,
Human Pose Estimation with FCNs, Region Proposals, Thin Lens Model.

### 2026-08-24 — Recovered figure for a `figure_dependent` exemplar (mockup_exam_2023 Q1a)

The user photographed the actual figure for `apply-on-given-grid`'s mockup exemplar (`Q1a`,
2 marks, Σ=7 for the whole Question 1). Parsed JSON had `marks: null` and no image data — this was
previously drilled as a generated 3×3/Sobel-X variant. The real figure is much smaller and
structurally different:

- **1D image** I = [1, 2, 3, 4] (not 2D).
- **2-element (even-length) filter** [-1, 1] — no natural center, unlike every other filter drilled
  so far (all odd-length, e.g. 1×3, 3×3). Alignment convention must be assumed/stated: first filter
  tap aligned with the current pixel, reaching one step forward → forward difference,
  G[i] = I[i+1] − I[i].
- Same-padding with zeros, output size 4.

**This is now a real, exact drill target** — not a variant — the moment this text exists as a
source. `archetypes_map.py` should absorb this figure text into the `Q1a` exemplar on the next
re-mapping pass so `apply-on-given-grid` gets a genuine exemplar instead of only the 2023 one.
**Do not hand-edit `archetypes.json`'s exemplar structure directly** — this note is the input for
the next `archetypes_postprocess.py` run, per the project's own write-ownership rule.

**Open question this raises:** even-length filters may appear elsewhere in the real exam figures
that are still missing image data (`read-figure-identify`, other `apply-on-given-grid` instances).
Worth flagging to the user that "no natural center" is now a confirmed real trap, not a
hypothetical one — the playbook trap list for `apply-on-given-grid` should get a line for it next
re-mapping pass.
