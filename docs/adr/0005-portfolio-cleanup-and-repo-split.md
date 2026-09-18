# Split `prompts/` into its own repo, drop personal content, generalize beyond CS

**Status:** accepted

[ADR 0004](./SUPPRESSED/0004-split-pipeline-from-portable-exam-prep-prompt.md) split this repo into `pipeline/` (the deliverable) and `prompts/` (a portable bridge)
as two folders in one repo. That was enough to decouple the code, but not enough to make the
repo readable as a single-purpose portfolio piece: it still carried real personal course data
(taxonomies, cheat sheets, study plans, progress logs — two actual RWTH courses), a superseded
tutor system, exploratory design docs for a feature that was never built, and a personal
git-commit helper unrelated to what the pipeline does. `taxonomy.json`'s topic-tagging prompt was
also hardcoded to "computer science curriculum analyst," even though nothing else in the pipeline
assumes CS — it works on any text-based exam.

We decided to go further: **`prompts/` becomes its own repo**
([`exam-prep-prompt`](https://github.com/tequers/exam-prep-prompt)), since it shares no code with
the pipeline — it only ever reads files the pipeline produces — so a physical split costs
nothing. This repo now ships exactly one example `Course/Exam` (synthetic, empty scaffold for
now) instead of the two real ones, which move to local-only, gitignored storage. The superseded
tutor (`_archive/`), the unbuilt-feature design docs, and `scripts/aicommit.sh` are dropped from
tracking the same way. The old copyrighted exam PDFs that had been committed before the original
`.gitignore` rules existed are purged from git history entirely (`git filter-repo`), not just
untracked going forward — a `git log --all` should never have been able to surface them. The
topic-tagging prompt's system message was generalized to "academic curriculum analyst." Finally,
`rebuild` now always writes `Exam_ROI_Pipeline.json` — the same ranked rows as the `.xlsx`, as a
flat JSON array — so the pipeline's actual output (not just the static taxonomy) is directly
readable by a script or an LLM, not only by opening a spreadsheet.

## Considered options

- **Keep `prompts/` as a folder in this repo, just de-emphasized in the README** — rejected. It
  still reads as "one repo, two things to explain" the moment someone opens the file tree, which
  is the exact problem being solved.
- **Keep the two real courses as tracked "real-world examples"** — rejected. Real course data is
  personal and, for the underlying source PDFs, copyrighted; a single synthetic example serves
  the same "see it work" purpose without either issue.
- **Leave the exam-PDF history alone** since the files aren't in the current tree — rejected.
  "Not currently tracked" is not the same as "not retrievable"; a public portfolio repo shouldn't
  have copyrighted material sitting in old commits regardless of whether HEAD still references it.
- **Add a `--format` flag for xlsx vs. JSON output** instead of always writing both — rejected.
  Writing the JSON is nearly free once the ranked `rows` list already exists in memory; a flag
  would be one more decision for no real cost saved.
