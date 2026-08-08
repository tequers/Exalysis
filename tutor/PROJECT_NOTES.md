# Project Notes — Computer Science Exams Pipeline

Per-project quirks and overrides for the tutor prompt (`TUTOR_SYSTEM_PROMPT_v7.md`).
Course-specific facts live **here**, not in the prompt. Append as new quirks are discovered.

## Course

- **Exam:** Computer Vision (RWTH Aachen)
- **Exam date:** `FILL_IN` in `tutor/progress.json` — ask and write it.
- **Total marks:** 175 = combined `2023_Exam` + `Old_Exam_Tasks`. `mockup_exam_2023` is practice material and is **not** in the 175 total, though its questions are valid exemplars.

## Path deviations from the standard layout

- Path resolver `.study-run.json` **exists** at the project root and is canonical.
- ROI sheet: `pipeline/Exam_ROI_Pipeline.xlsx`, sheet **`ROI Scores`**.
- No `tutor/glossaries/` directory yet — only `tutor/course_glossary_prompt.md` (the generator prompt, not a glossary). Treat the glossary as absent until one is built.

## Dead paths — never read

- `docs/archive/version_outputs/` — contains stale copies of `taxonomy.json` and `Exam_ROI_Pipeline.xlsx`. Filename matches here are traps.
- `tutor/_archive/` — superseded prompt versions (v1–v4).

## Skill sources kept in this folder

Source-of-truth copies of the project's custom skills live here alongside the tutor prompt; the installed skill is saved to the account separately, so **edit both when changing one**.

- `PROBLEMATIC_SKILL_v1.md` → installed as `/problematic`
- `STUDY_RUN_SKILL_v2.md` → installed as `/study-run`

`/problematic` and the tutor prompt's `[Problematic]` beat share one rule: **requirement, never mechanism.** The tutor runs it automatically at every new topic; the slash command is for on-demand framing of a sub-step mid-ramp.

## Data quirks

- `pipeline/taxonomy.json` holds **16 topics**; `tutor/progress.json` lists only started ones (10 as of 2026-08-01). **Pick the next topic from the ROI sheet or taxonomy, never from the ledger.**
- **13 of 105** parsed questions carry more than one topic → the coverage de-duplication rule is load-bearing here, not theoretical.
- Loci section headings are informal and don't match topic names exactly (e.g. "Canny Edge Detection" ↔ topic "Edge Detection"). Match on significant words.
- Semantic Segmentation marks (8) are **estimated** from parsed question totals, not read off an official mark scheme.

## Status snapshot (2026-08-01)

- Mastered: Image Filtering and Convolution, Feature Detection and Description, Clustering and Mixture Models, CNNs, Edge Detection, NN Training and Loss Functions, Boosting and Ensemble Classifiers, Semantic Segmentation.
- Locked: Sliding-Window Object Detection (rank 4), Stereo Vision and Epipolar Geometry (rank 6).
