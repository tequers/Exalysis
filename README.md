# Computer Science Exams Pipeline

A systematic, science-based study system for university Computer Science exams. Two layers: a **CLI pipeline** that decides *what* to study (ROI ranking), and a **Cowork tutor** that teaches the prioritized topics using active recall, spaced repetition, and the method of loci.

> **Start here:** `PROJECT_BRIEF.md` is the ground-truth document — read it before designing any solution. `PROJECT_BRIEF.html` is the same content as a readable web page.

---

## Repository map

The repo is organized **by component** (what each thing *is*), so both you and the AI can retrieve files by purpose. Within `docs/`, material is split **by lifecycle** (open problems vs. consolidated vs. archived).

```
.
├── README.md                  ← you are here (repo map)
├── PROJECT_BRIEF.md / .html   ← ground-truth project description (entry point)
├── requirements.txt           ← Python deps for the pipeline
│
├── pipeline/                  ← LAYER 1 — the CLI. Self-contained unit; files must stay together.
│   ├── pipeline.py            ← the script (reads its data via Path(__file__).parent)
│   ├── taxonomy.json          ← per-topic difficulty D, connection C, prerequisites
│   ├── Exam_ROI_Pipeline.xlsx ← ranked study agenda (regenerated on rebuild)
│   ├── parsed/                ← one JSON per past exam, questions tagged by topic
│   │   ├── 2023_Exam.json
│   │   ├── Old_Exam_Tasks.json
│   │   └── mockup_exam_2023.json
│   └── docs/                  ← pipeline design + spec docs
│       ├── pipeline_docs.md
│       ├── Topic_ROI_Exam_Analysis_System.md
│       └── Topic_ROI_MVP_v1.md
│
├── tutor/                     ← LAYER 2 — the study tutor. Live prompt + runtime state.
│   ├── TUTOR_SYSTEM_PROMPT_v4.md       ← the LIVE prompt (highest version wins)
│   ├── progress.json                  ← mastery ledger (single source of truth for state)
│   ├── continue-study-session-v2.skill← the /continue-study-session skill bundle
│   ├── feedback/                      ← working feedback + improvement logs
│   │   ├── tutor_feedback.md
│   │   ├── tutor_improvements.md
│   │   ├── feedback_final_rung_must_use_parsed_questions.md
│   │   ├── feedback_label_exam_vs_warmup.md
│   │   └── feedback_visual_artifacts.md
│   └── _archive/                      ← superseded prompt versions (do not load)
│       ├── TUTOR_SYSTEM_PROMPT.md
│       ├── TUTOR_SYSTEM_PROMPT_v2.md
│       └── TUTOR_SYSTEM_PROMPT_v3.md
│
├── loci/                      ← memory-palace subsystem (shared infra across courses)
│   ├── loci_living_room.md    ← the 27-station palace map
│   └── loci_encodings.md      ← concept→station encodings with status (❌/⚠️/✅)
│
├── exams/                     ← source exam PDFs
│   └── computer_vision/
│       ├── 2023_Exam.pdf
│       ├── Old Exam Tasks.pdf
│       └── mockup_exam_2023.pdf
│
├── docs/                      ← reports & analysis, split by lifecycle
│   ├── open/                  ← OPEN PROBLEMS — to tackle next
│   │   ├── Solution_Landscape.md
│   │   ├── loci-files-brief-for-opus.md
│   │   ├── loci-method-analysis.md
│   │   ├── solution-research-connections-active-recall.md
│   │   ├── solution-research-module-a-connections.md
│   │   ├── critique-mindmap-graph-connections.md
│   │   └── critique-tutor-feedback-memories.md
│   ├── solid/                 ← CONSOLIDATED — good enough, settled
│   │   ├── course-materials-context-report.md
│   │   ├── course_materials_analysis.md
│   │   └── workflow_prompts.md
│   └── archive/
│       └── version_outputs/   ← old pipeline run outputs (v1_full_sonnet, v1_haiku_sonnet)
│
├── assets/                    ← diagrams, explainers, visual artifacts
│   ├── concept_map_clustering.drawio
│   ├── concept_map_clustering.mermaid
│   ├── exam_roi_pipeline_plan.svg
│   ├── convolution_explainer.html
│   └── start-study-session-eval-review.html
│
└── _to_delete/                ← junk & exact duplicates, safe to remove (see below)
```

---

## How to use it

**Run the pipeline** (decides what to study):

```bash
cd pipeline
python pipeline.py add <exam_file.pdf> --total-marks <N>   # process a new exam
python pipeline.py rebuild                                  # rebuild the ROI sheet
python pipeline.py status                                   # show pipeline state
```

The pipeline reads `taxonomy.json` and `parsed/` and writes `Exam_ROI_Pipeline.xlsx`, all as siblings inside `pipeline/`. **Keep these together** — the script resolves them relative to its own location.

**Run the tutor** (teaches the topics): invoke `/continue-study-session` in Cowork. The skill finds the highest-versioned `TUTOR_SYSTEM_PROMPT` (searching recursively, ignoring `_archive/`), reads `progress.json` and the course/loci files by name, and continues the session one atomic step per turn.

---

## Conventions (so this stays scalable)

- **By component first.** A new concern gets its own top-level folder, not a dumping ground at root.
- **Lifecycle lives in `docs/`.** `open/` = problems to solve next · `solid/` = settled · `archive/` = kept for reference, not active.
- **Versioned files:** keep the live one in the component folder; move superseded versions to that component's `_archive/`. The newest `_vN` is always the live one.
- **Adding a course:** drop its exam PDFs in `exams/<course>/`, run the pipeline to produce its `taxonomy.json` / parsed / ROI sheet, and swap those course files for the tutor. The `loci/` layer is shared across all courses — do not duplicate it per course.
- **Files referenced by name, not path.** The tutor and skill locate files by filename via recursive search, so moving things between component folders won't break them — but keep filenames stable.

---

## `_to_delete/` — pending cleanup

These are exact duplicates and junk, quarantined here because file deletion wasn't permitted during the reorg. **Safe to delete this whole folder** whenever you like (drag to Recycle Bin, or `rmdir /s /q _to_delete` on Windows):

- `*- copia.*` — byte-identical duplicates of files kept elsewhere
- `ziCljPtl`, `ziU9P2qz` — stray OS temp artifacts (zip copies)
- `__pycache__/` — Python bytecode cache (already gitignored, regenerates)
- `continue-study-session_OLD.skill` — the pre-reorg skill bundle (replaced by `-v2`)
- `_skill_build/`, `_test_perms/`, `parsed_empty_dir/`, `exams_cv_empty_dir/` — empty leftover dirs from the move

## Note on git

The git index was corrupted during the reorg (an `index.lock` couldn't be cleared under the sandbox's permissions). Your commit history and objects are intact — only the index cache is affected. To repair, from the project root:

PowerShell (note the comma — PowerShell needs it to pass two paths):

```powershell
del .git\index, .git\index.lock    # if index.lock is already gone, that error is harmless
git reset                          # regenerates the index from HEAD
git add -A; git status             # then review the reorganization as changes
```

cmd.exe equivalent:

```bat
del .git\index .git\index.lock
git reset && git add -A && git status
```

macOS / Linux:

```bash
rm -f .git/index .git/index.lock && git reset && git add -A && git status
```
