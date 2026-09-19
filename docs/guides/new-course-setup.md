# Set up a new course

This guide creates candidates from past papers. The current two-stage MVP has no
CLI command to accept them, so a new course cannot yet produce a ranking from its
new candidates. Existing accepted records can still produce reports.

Read the [glossary](../glossary.md) for Course, Exam, and Topic. The
[course-folder decision](../adr/0006-course-folder-as-cli-argument.md) explains
the independent state boundary. For development without model calls, start with
the [development workflow](../development/workflow.md).

## Set up the environment

Follow [offline environment setup](../development/workflow.md#set-up-offline-development)
once per machine. Tests, help, input previews, status, and rebuilding accepted
records require no provider credentials.

To analyze papers, complete the separate
[live-provider setup](../development/workflow.md#optional-live-provider-setup). Approve
the provider, exact models, and expected cost before running live analysis. Check
that the paper may be sent to that provider. Keep `.env`, source papers, candidates,
and generated reports out of Git. No step below enables or calls OCR.

Run every command below from the repository root.

## Choose a course folder and preview inputs

One course folder holds one Exam's papers and state. Another Exam uses a separate
folder, even within the same Course. The CLI accepts any folder path and creates
it on first use. This repository uses `Courses/<Course>/<type>_<date>/` by convention.

Place UTF-8 `.txt` papers or PDFs with a text layer in that folder or its `exams/`
subfolder. Every PDF page must yield text. Scanned PDFs are unsupported, and even
a text-layer PDF needs inspection for damaged formulas or reading order.

```powershell
python pipeline/pipeline.py "Courses/Operating Systems/final_15_02_2027" add-exam --dry-run
```

The preview lists resolved paths and makes no model calls. Add `--recursive` for
deeper folders. Every matching TXT/PDF is treated as a paper, including notes or
slides. Name only intended files or folders to replace the default search.
Relative paths prefer an existing path in the shell's working directory, then a
path inside the course folder. An absolute path removes that ambiguity.

Keep distinct papers from the same year, including resits and alternate sittings.
Each paper has its own ID. See [paper identity and replacement](../../README.md#paper-ids-and-replacement)
before using `--exam-id` or `--force`.

## Analyze an approved input

After live-provider approval and configuration:

```powershell
python pipeline/pipeline.py "Courses/Operating Systems/final_15_02_2027" add-exam "final_2024.pdf" --total-marks 100
```

Replace the filename and total with the paper's actual values. Omit `--total-marks`
to use the command's inferred total. With multiple papers, one supplied total
applies to all of them; invoke the command separately when totals differ.

Stage 1 extracts questions and marks. Stage 2 tags topics and supplies qualitative
judgments. Python validates the responses and computes deterministic metrics.
Successful analysis saves `candidates/EXAM_ID.json`, including source provenance,
evidence, uncertainty, and `proposed_taxonomy_changes`. Existing candidates or
accepted records are skipped unless `--force` is supplied. Forced analysis replaces
only the candidate after success.

Inspect the candidate's questions and evidence against the paper. Check proposed
topic names for duplicates and read any `needs-review` findings. Independent model
review is disabled in this MVP; `--review` is unavailable.

Without `--prototype`, `add-exam` does not update `parsed/`, accepted `taxonomy.json`, or reports. Ticket
08's acceptance workflow is pending. Do not treat a candidate as accepted or copy
it into `parsed/` as an undocumented promotion step.

For a first demonstration using compulsory-question papers, use
`add-exam --prototype --total-marks N`. This writes separate unreviewed Excel and
JSON reports under `prototype/`. It does not accept candidates. See the
[LAW prototype run guide](run-law-prototype.md) for commands and checks.

## Inspect accepted state and rebuild reports

```powershell
python pipeline/pipeline.py "Courses/Operating Systems/final_15_02_2027" status
python pipeline/pipeline.py "Courses/Operating Systems/final_15_02_2027" rebuild
```

These commands make no model calls. `status` counts accepted papers and taxonomy
topics and reports whether output files exist. A saved candidate does not increase
the accepted-paper count. `rebuild` uses accepted records from `parsed/` and
recomputes their taxonomy summaries and ranking. With no accepted papers it creates
no new Excel or JSON report.

If accepted state already exists, inspect its taxonomy and reports independently
of the new candidate. To override difficulty or connection for an existing exact
topic name:

```powershell
python pipeline/pipeline.py "Courses/Operating Systems/final_15_02_2027" edit-topic "Page Replacement" --diff 4 --conn 3
```

This saves human overrides and rebuilds reports. It fails if that topic is absent
from the accepted taxonomy. It does not accept a proposed topic or merge duplicate
labels. Use the [recovery guide](course-state-recovery.md) for damaged records,
interrupted writes, or locked course state.

## Check the result

- [ ] Offline setup and checks run without credentials.
- [ ] The dry run lists only intended papers.
- [ ] Any live analysis has provider, model, cost, and data-sharing approval.
- [ ] Successful analysis saved a candidate whose evidence and proposals were inspected.
- [ ] Accepted state and report counts were not inferred from candidate creation.
- [ ] If accepted records existed, `rebuild` wrote `Exam_ROI_Pipeline.xlsx` and
      `Exam_ROI_Pipeline.json`, or reported a specific recovery action.

The repository does not include a sample course dataset. A separate optional project,
[exam-prep-prompt](https://github.com/tequers/exam-prep-prompt), can use generated
reports for study sessions. It shares no code or state-management implementation
with this pipeline. Keep course-specific diagrams under `Courses/<Course>/assets/`.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `README.md` | Relies on the detailed paper-ID and replacement rules. | Custom IDs, collisions, force behavior, or the linked section changes. |
| `docs/glossary.md` | Uses Course and Exam to define independent setup folders. | Course, exam, or state-boundary definitions change. |
| `docs/adr/0006-course-folder-as-cli-argument.md` | Applies the explicit course-folder command decision. | Course argument or destination policy changes. |
| `docs/development/workflow.md` | Requires offline setup and separate live-provider approval. | Setup, credentials, approval, or offline verification steps change. |
| `docs/architecture.md` | Describes candidate creation separately from pending acceptance. | Candidate acceptance or other available workflow steps change. |
| `docs/guides/course-state-recovery.md` | Directs failed setup and rebuilds to the recovery procedure. | Recovery actions or supported state repairs change. |
| `pipeline/pipeline.py` | Provides the exact setup, analysis, status, rebuild, and override commands. | Arguments, defaults, validation, outcomes, or availability gates change. |
| `docs/guides/run-law-prototype.md` | Supplies the optional first-demo path. | Prototype setup or outputs change. |
| `pipeline/exam_roi/inputs.py` | Defines the supported sources and dry-run selection rules. | Input formats, discovery, exclusions, or extraction validation change. |
| `pipeline/exam_roi/storage.py` | Defines the course artifacts and candidate-versus-accepted state. | Stored paths, write boundaries, or course initialization change. |
<!-- doc-dependencies:end -->
