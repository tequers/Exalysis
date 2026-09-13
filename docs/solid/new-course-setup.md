# Setting Up a New Course

How to add a new Course/Exam to this repo and get it studyable — for a first-time setup or for
adding a second course to an existing install.

See `CONTEXT.md` for the Course/Exam/Topic vocabulary this doc assumes, and
`docs/adr/0001-course-exam-hierarchy.md` / `docs/adr/0003-active-exam-resolution.md` for why the
structure and disambiguation rules below exist.

---

## One-time setup (per machine, not per course)

1. **Python deps:**
   ```bash
   cd pipeline
   pip install -r requirements.txt
   ```
   Installs `openpyxl` and `pypdf` (core) plus the SDK for whichever `LLM_PROVIDER` you use.

2. **API key** — set the env var matching your provider (default `anthropic`):
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...      # LLM_PROVIDER=anthropic (default)
   # export DEEPSEEK_API_KEY=sk-...         # LLM_PROVIDER=deepseek
   # export OPENAI_API_KEY=sk-...           # LLM_PROVIDER=openai
   ```

None of this is repeated per course — it's done once. This pipeline is the whole scope of this
repo; if you also want to study with the output (step 4 below), that's a separate, optional
project — [`exam-prep-prompt`](https://github.com/tequers/exam-prep-prompt).

---

## Per-course workflow

### 1. Pick the course folder

The folder you name on the command line *is* the Exam: everything in it (past papers, taxonomy,
ROI sheet) belongs to that Exam alone, even if the same subject has another exam elsewhere. It
can be any path on disk, and `pipeline.py` creates it if it isn't there yet.

This repo keeps its own under `Courses/<Course Name>/<type>_<date>/`, e.g.
`Courses/Operating Systems/final_15_02_2027/` — a convention that keeps several courses tidy in
one place, nothing the CLI requires.

Drop the past-exam PDFs (or `.txt` files) straight into that folder, or into an `exams/`
subfolder — `add-exam` looks in both. Keep every paper of a year, not one per year: models,
sittings and resits each count as a separate sample of what the examiner asks. Per-year
subfolders are fine too, even when the filenames inside them repeat.

### 2. Run the pipeline

From `pipeline/`:

Every command reads `python pipeline.py COURSE_FOLDER COMMAND [data]`:

```bash
cd pipeline
python pipeline.py "../Courses/Operating Systems/final_15_02_2027" add-exam --total-marks <N>
python pipeline.py "../Courses/Operating Systems/final_15_02_2027" status
```

- `add-exam` with no filename processes every paper in the folder (the same `--total-marks`
  applied to each); name a file — `add-exam final_2024.pdf --total-marks <N>` — when the totals
  differ per exam. Papers already processed are skipped unless you pass `--force`.
- This writes validated analyses and proposed taxonomy changes to `candidates/*.json`.
  Accepted `taxonomy.json`, `parsed/*.json`, and ranked outputs stay unchanged until a
  candidate is accepted through the separate acceptance workflow.

### 3. Sanity-check the taxonomy

The pipeline auto-tags topics with an LLM and prints a reminder afterward: **check
`taxonomy.json` for near-duplicate topics and merge them by hand.** Also use:

```bash
python pipeline.py "../Courses/Operating Systems/final_15_02_2027" edit-topic "Page Replacement" --diff 4 --conn 3
```

to override any AI-assigned difficulty (D) or connection (C) score you disagree with, then it
rebuilds the sheet automatically.

### 4. Start studying (optional, separate project)

The pipeline only decides *what* to study — it doesn't help you study it. For that, see
[`exam-prep-prompt`](https://github.com/tequers/exam-prep-prompt): paste its system prompt into
whatever LLM tool you're using and point it at (or paste in) the Exam folder from steps 1–3, then
just talk to it: "start a session, I have 90 minutes." It bootstraps its own state file
(`study_state.json`, next to the pipeline's output) on first run — you never hand-author it.

### 5. Assets (as needed)

Any diagrams/explainers made for the course go in `Courses/<Course>/assets/` (create it on first
use). Never at repo root, never shared across courses — each course gets its own.

---

## Checklist

- [ ] `pip install -r pipeline/requirements.txt`, API key set
- [ ] course folder chosen, past papers dropped in
- [ ] `pipeline.py <COURSE_FOLDER> add-exam` run → `Exam_ROI_Pipeline.xlsx` and `.json` exist
- [ ] `taxonomy.json` reviewed for duplicate topics
- [ ] *(optional)* `exam-prep-prompt`'s system prompt pasted into an LLM tool, pointed at the
      Exam folder, run once to confirm `study_state.json` gets created

---

## Known gaps

- File resolution in `exam-prep-prompt` is by content, not fixed paths — but the expected
  filenames (`taxonomy.json`, `candidates/*.json`, `parsed/*.json`, `study_state.json`) should
  stay exact, since
  nothing guesses them from scratch.
- The repo ships one example `Course/Exam` (synthetic, currently an empty scaffold — see
  `Courses/Example_Course/`) rather than a real course, per
  `docs/adr/0005-portfolio-cleanup-and-repo-split.md`.
