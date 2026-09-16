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

### 1. Create the Exam folder

Nothing auto-creates this — `pipeline.py` exits with an error if the folder doesn't exist yet.
Make it yourself:

```
Courses/<Course Name>/<type>_<date>/exams/
```

e.g. `Courses/Operating Systems/final_15_02_2027/exams/`.

- `<Course Name>` — the subject, e.g. "Operating Systems".
- `<type>_<date>` — the Exam folder name, e.g. `final_15_02_2027`, `theory_20_08_2026`. This is
  the atomic state boundary: everything under it (taxonomy, past papers, ROI sheet) belongs to
  this Exam alone, even if another Exam exists under the same Course.

Drop the past-exam PDFs (or `.txt` files) into that `exams/` subfolder.

### 2. Run the pipeline

From `pipeline/`:

```bash
cd pipeline
python pipeline.py add-folder --total-marks <N> --course "Operating Systems" --exam final_15_02_2027
python pipeline.py rebuild --course "Operating Systems" --exam final_15_02_2027
```

- Use `add-folder` to process every file in `exams/` at once (same total marks applied to each),
  or `add <file.pdf> --total-marks <N>` one file at a time if totals differ per exam.
- `--course`/`--exam` are only *required* once a second Exam folder exists anywhere under
  `Courses/` — with a single Exam in the whole repo, plain `add-folder` / `rebuild` / `status`
  auto-detect it. The moment a second one exists, every command needs them (never silently
  guessed — see ADR 0003).
- This produces/updates `taxonomy.json`, `parsed/*.json`, and the ranked output
  (`Exam_ROI_Pipeline.xlsx` and `.json`) inside the Exam folder. That's the pipeline's whole job
  — everything below this point is optional.

### 3. Sanity-check the taxonomy

The pipeline auto-tags topics with an LLM and prints a reminder afterward: **check
`taxonomy.json` for near-duplicate topics and merge them by hand.** Also use:

```bash
python pipeline.py edit-topic --course "Operating Systems" --exam final_15_02_2027
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
- [ ] `Courses/<Course>/<type>_<date>/exams/` created, past papers dropped in
- [ ] `pipeline.py add-folder` (or `add`) run
- [ ] `pipeline.py rebuild` run → `Exam_ROI_Pipeline.xlsx` and `.json` exist
- [ ] `taxonomy.json` reviewed for duplicate topics
- [ ] *(optional)* `exam-prep-prompt`'s system prompt pasted into an LLM tool, pointed at the
      Exam folder, run once to confirm `study_state.json` gets created

---

## Known gaps

- File resolution in `exam-prep-prompt` is by content, not fixed paths — but the expected
  filenames (`taxonomy.json`, `parsed/*.json`, `study_state.json`) should stay exact, since
  nothing guesses them from scratch.
- The repo ships one example `Course/Exam` (synthetic, currently an empty scaffold — see
  `Courses/Example_Course/`) rather than a real course, per
  `docs/adr/0005-portfolio-cleanup-and-repo-split.md`.
