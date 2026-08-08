# Project Notes — Computer Vision, final_26_08_2026

Per-Exam quirks and overrides for the tutor prompt (`tutor/TUTOR_SYSTEM_PROMPT_v7.md`, shared across every Course/Exam — highest version wins).
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
