# Setting Up a New Course

How to add a new Course/Exam to this repo and get it studyable — for a new user with Claude Cowork, or for adding a second course to an existing install.

See `CONTEXT.md` for the Course/Exam/Topic vocabulary this doc assumes, and `docs/adr/0001-course-exam-hierarchy.md` / `docs/adr/0003-active-exam-resolution.md` for why the structure and disambiguation rules below exist.

---

## One-time setup (per machine, not per course)

1. **Python deps:**
   ```bash
   pip install -r requirements.txt
   ```
   Installs `openpyxl` and `pypdf` (core) plus the SDK for whichever `LLM_PROVIDER` you use.

2. **API key** — set the env var matching your provider (default `anthropic`):
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...      # LLM_PROVIDER=anthropic (default)
   # export DEEPSEEK_API_KEY=sk-...         # LLM_PROVIDER=deepseek
   # export OPENAI_API_KEY=sk-...           # LLM_PROVIDER=openai
   ```

3. **Install the tutor skill in Cowork** — upload `tutor/continue-study-session-v2.skill` as a Cowork skill so `/continue-study-session` is available. This is a separate step from the pipeline; the pipeline is a plain CLI script, the tutor only runs inside Cowork.

None of this is repeated per course — it's done once.

---

## Per-course workflow

### 1. Create the Exam folder

Nothing auto-creates this — `pipeline.py` exits with an error if the folder doesn't exist yet. Make it yourself:

```
Courses/<Course Name>/<type>_<date>/exams/
```

e.g. `Courses/Operating Systems/final_15_02_2027/exams/`.

- `<Course Name>` — the subject, e.g. "Operating Systems".
- `<type>_<date>` — the Exam folder name, e.g. `final_15_02_2027`, `theory_20_08_2026`. This is the atomic state boundary: everything under it (taxonomy, past papers, ROI sheet, mastery ledger) belongs to this Exam alone, even if another Exam exists under the same Course.

Drop the past-exam PDFs (or `.txt` files) into that `exams/` subfolder.

### 2. Run the pipeline

From `pipeline/`:

```bash
cd pipeline
python pipeline.py add-folder --total-marks <N> --course "Operating Systems" --exam final_15_02_2027
python pipeline.py rebuild --course "Operating Systems" --exam final_15_02_2027
```

- Use `add-folder` to process every file in `exams/` at once (same total marks applied to each), or `add <file.pdf> --total-marks <N>` one file at a time if totals differ per exam.
- `--course`/`--exam` are only *required* once a second Exam folder exists anywhere under `Courses/` — with a single Exam in the whole repo, plain `add-folder` / `rebuild` / `status` auto-detect it. The moment a second one exists, every command needs them (never silently guessed — see ADR 0003).
- This produces/updates `taxonomy.json`, `parsed/*.json`, and `Exam_ROI_Pipeline.xlsx` inside the Exam folder.

### 3. Sanity-check the taxonomy

The pipeline auto-tags topics with an LLM and prints a reminder afterward: **check `taxonomy.json` for near-duplicate topics and merge them by hand.** Also use:

```bash
python pipeline.py edit-topic --course "Operating Systems" --exam final_15_02_2027
```

to override any AI-assigned difficulty (D) or connection (C) score you disagree with, then it rebuilds the sheet automatically.

### 4. Start studying

In Cowork, run `/continue-study-session`. On the *first* run for a new Exam:

- The skill locates the live `TUTOR_SYSTEM_PROMPT_v*.md` (highest version, ignoring `_archive/`).
- It reads that Exam's `taxonomy.json`, `Exam_ROI_Pipeline.xlsx`, and `parsed/*.json`.
- It **creates `progress.json` itself**, bootstrapped from the taxonomy — you never hand-author the mastery ledger.
- `PROJECT_NOTES.md` (Exam-specific quirks) and `sessions.json` (throughput calibration) are likewise created/owned by the tutor as sessions happen.

From here, just keep invoking `/continue-study-session` each time you study; it resumes exactly where it left off.

### 5. Assets (as needed)

Any diagrams/explainers Claude produces for the course go in `Courses/<Course>/assets/` (create it on first use). Never at repo root, never shared across courses — each course gets its own.

### 6. Loci (shared, usually nothing to do)

`loci/` is shared global infrastructure across every course — do not create a per-course copy. New concepts just get encoded into an existing station and tagged with the new Course/Exam in `loci_encodings.md`. A new palace file is only needed once the current palace's stations (27, in the Living Room) are full.

---

## Checklist

- [ ] `pip install -r requirements.txt`, API key set
- [ ] Tutor skill installed in Cowork
- [ ] `Courses/<Course>/<type>_<date>/exams/` created, past papers dropped in
- [ ] `pipeline.py add-folder` (or `add`) run
- [ ] `pipeline.py rebuild` run → `Exam_ROI_Pipeline.xlsx` exists
- [ ] `taxonomy.json` reviewed for duplicate topics
- [ ] `/continue-study-session` run once to confirm `progress.json` is created

---

## Known gaps

- `PROJECT_BRIEF.md` currently states generalization "not yet done" — that line is stale; `TUTOR_SYSTEM_PROMPT_v9.md` and the `Courses/<Course>/<Exam>/` hierarchy already make the tutor course-agnostic. Worth fixing in the brief.
- The loci encoding rubric and multi-palace scaling are still open design problems (`docs/open/loci-*.md`) — a new course gets full ROI/mastery-gating support immediately, but loci support is thinner until those are resolved.
- File resolution is by filename search, not fixed paths, so folders can be renamed freely — but the expected filenames (`taxonomy.json`, `progress.json`, `TUTOR_SYSTEM_PROMPT_v*.md`, etc.) must stay exact.
