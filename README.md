# Computer Science Exams Pipeline

A systematic, science-based study system for university Computer Science exams. Two layers: a **CLI pipeline** that decides *what* to study (ROI ranking), and a **Cowork tutor** that teaches the prioritized topics using active recall, spaced repetition, and the method of loci.

> **Start here:** `PROJECT_BRIEF.md` is the ground-truth document — read it before designing any solution. `PROJECT_BRIEF.html` is the same content as a readable web page.

---

## Repository map

The repo is organized **by component** (what each thing *is*), except for per-course/per-exam study data, which is organized **by Course then Exam** (see `CONTEXT.md`). Within `docs/`, material is split **by lifecycle** (open problems vs. consolidated vs. archived).

```
.
├── README.md                  ← you are here (repo map)
├── CONTEXT.md                 ← glossary — Course, Exam, Topic, Palace, Station, Encoding, ...
├── PROJECT_BRIEF.md / .html   ← ground-truth project description (entry point)
├── requirements.txt           ← Python deps for the pipeline
│
├── Courses/                   ← per-course, per-exam study data. One self-contained unit per Exam.
│   └── Computer Vision/
│       ├── assets/                    ← diagrams, explainers, visual artifacts made FOR this course
│       │   ├── concept_map_clustering.drawio
│       │   ├── concept_map_clustering.mermaid
│       │   ├── convolution_explainer.html
│       │   ├── exam_roi_pipeline_plan.svg
│       │   ├── maxpool_visualizer.html
│       │   └── start-study-session-eval-review.html
│       └── final_26_08_2026/  ← name = <type>_<date>. Everything below is owned by this Exam alone.
│           ├── exams/                 ← source exam PDFs
│           │   ├── 2023_Exam.pdf
│           │   ├── Old Exam Tasks.pdf
│           │   └── mockup_exam_2023.pdf
│           ├── taxonomy.json          ← per-topic difficulty D, connection C, prerequisites
│           ├── Exam_ROI_Pipeline.xlsx ← ranked study agenda (regenerated on rebuild)
│           ├── parsed/                ← one JSON per past exam, questions tagged by topic
│           ├── progress.json          ← mastery ledger (single source of truth for this Exam's state)
│           ├── sessions.json          ← per-session calibration log
│           └── PROJECT_NOTES.md       ← Exam-specific quirks for the tutor
│
├── pipeline/                  ← LAYER 1 — the CLI itself. Shared across every Course/Exam.
│   ├── pipeline.py            ← the script; resolves the active Exam under Courses/ (see ADR 0003)
│   └── docs/                  ← pipeline design + spec docs
│       ├── pipeline_docs.md
│       ├── Topic_ROI_Exam_Analysis_System.md
│       └── Topic_ROI_MVP_v1.md
│
├── tutor/                     ← LAYER 2 — the study tutor. Shared prompt + shared skills.
│   ├── TUTOR_SYSTEM_PROMPT_v7.md       ← the LIVE prompt (highest version wins), course-agnostic
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
│       ├── TUTOR_SYSTEM_PROMPT_v3.md
│       ├── TUTOR_SYSTEM_PROMPT_v4.md
│       ├── TUTOR_SYSTEM_PROMPT_v5.md
│       └── TUTOR_SYSTEM_PROMPT_v6.md
│
├── loci/                      ← memory-palace subsystem — global, shared across every course/exam
│   ├── loci_living_room.md    ← the 27-station palace map
│   └── loci_encodings.md      ← concept→station encodings with status (❌/⚠️/✅), tagged by Course/Exam
│
├── docs/                      ← reports & analysis, split by lifecycle
│   ├── adr/                    ← architecture decisions (why, not what — see each file)
│   │   ├── 0001-course-exam-hierarchy.md
│   │   ├── 0002-loci-shared-global-scaled-per-palace-file.md
│   │   └── 0003-active-exam-resolution.md
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

`pipeline.py` resolves its active `Courses/<Course>/<Exam>/` folder before running: automatically when exactly one exists, or via `--course "Computer Vision" --exam final_26_08_2026` the moment a second one does. It reads that Exam's `taxonomy.json` / `parsed/` and writes its `Exam_ROI_Pipeline.xlsx` — see `docs/adr/0003-active-exam-resolution.md`.

**Run the tutor** (teaches the topics): invoke `/continue-study-session` in Cowork. The skill finds the highest-versioned `TUTOR_SYSTEM_PROMPT` (searching recursively, ignoring `_archive/`), reads the active Exam's `progress.json` and `PROJECT_NOTES.md` plus the shared `loci/` files by name, and continues the session one atomic step per turn.

---

## Conventions (so this stays scalable)

- **By component first**, except study data — a new *tool* concern (pipeline, tutor) gets its own top-level folder; a new *course or exam* goes under `Courses/<Course>/<Exam>/` instead, never at root.
- **`Courses/<Course>/<Exam>/` is the atomic state boundary.** Course is purely organizational; each Exam owns its own past-paper corpus, taxonomy, ROI sheet, and mastery ledger — nothing is shared across Exams, even within one Course. See `CONTEXT.md` and `docs/adr/0001-course-exam-hierarchy.md`.
- **Exam folder names are `<type>_<date>`**, e.g. `final_26_08_2026`, `theory_20_08_2026`.
- **Lifecycle lives in `docs/`.** `open/` = problems to solve next · `solid/` = settled · `archive/` = kept for reference, not active · `adr/` = decisions made and why.
- **Versioned files:** keep the live one in the component folder; move superseded versions to that component's `_archive/`. The newest `_vN` is always the live one. This applies to `tutor/TUTOR_SYSTEM_PROMPT_v*.md` too — when a new version is written, move the version(s) it replaces into `tutor/_archive/` in the same change, so exactly one `TUTOR_SYSTEM_PROMPT_v*.md` ever lives outside `_archive/`.
- **Assets are per-course, not global.** Diagrams/explainers/visualizations Claude produces for a course live in `Courses/<Course>/assets/` — never at repo root, and never shared across courses. If a new course is added, it gets its own `assets/` folder.
- **Adding a course:** create `Courses/<Course>/<type>_<date>/`, drop its exam PDFs in an `exams/` subfolder there, and run the pipeline against it. The `loci/` layer is shared across all courses — do not duplicate it per course; individual encodings are tagged by Course/Exam instead (`docs/adr/0002-loci-shared-global-scaled-per-palace-file.md`).
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

### Committing changes — `aicommit`

This repo uses a custom helper, **`aicommit`**, that drafts a Conventional Commit message from the staged diff using Claude, then opens it in your editor to confirm. Prefer it over a plain `git commit` so messages stay consistent.

```bash
git add <files>     # stage what you want to commit first
aicommit            # Claude drafts a <type>(<scope>): summary + why-bullets, opens it to edit/save
```

**Where it works / prerequisites:**

- Runs in **bash only** (Git Bash or WSL) — *not* PowerShell or cmd. From PowerShell, use a normal `git commit -m "..."`.
- Requires the `claude` CLI on PATH in that shell, and **staged** changes (it aborts if nothing is staged).
- Opens the drafted message in your editor (`git commit -e`) so you always review/edit before it's final.

**The maintained version lives in [`scripts/aicommit.sh`](scripts/aicommit.sh).** Install it by sourcing that file from your `~/.bashrc`:

```bash
# in ~/.bashrc
source "/c/Users/alber/Claude/Projects/Computer Science Exams Pipeline/scripts/aicommit.sh"
```

then `source ~/.bashrc`. (Or paste the function body directly into `~/.bashrc`.)

What the maintained version adds over a naive draft-and-commit:

- **Adaptive context.** Large diffs are sent to Claude as a compact `--stat` + name-status summary instead of the full patch, so big commits (like a 50-file reorg) don't overflow the model's context or run up cost. Full patches are used only under `AICOMMIT_DIFF_BUDGET` lines (default 600). Verified: a 51-file / 1810-line staged change auto-switches to the summary path.
- **No blank commits.** If Claude returns an empty/whitespace-only message, it aborts without committing. Verified.
- **Valid Conventional Commit type.** The prompt constrains `<type>` to the standard set (`feat`/`fix`/`docs`/`refactor`/`chore`/…), avoiding non-standard types like `repo:` that break changelog tooling.
- **Optional pinned model** via `AICOMMIT_MODEL` for reproducible message quality.
- **Safer temp handling** (`mktemp` + cleanup `trap`) instead of a reused `.git/AI_COMMIT_MSG`, and it strips stray ``` fences if the model adds them.
