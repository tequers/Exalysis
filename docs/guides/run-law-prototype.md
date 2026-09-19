# Run the LAW portfolio prototype

Use the checkout containing ticket 33. Run the commands from that repository root. The real LAW data can stay in another folder. Replace the example course path below with its actual absolute path.

## Prepare the run

1. Install the dependencies with `python -m pip install -r pipeline/requirements.txt`.
2. Configure the provider, API key, and exact Stage 1 and Stage 2 model IDs in this checkout's `.env`. See [provider setup](../development/workflow.md#optional-live-provider-setup). A `.env` in another checkout is not loaded automatically. Existing process environment values take precedence.
3. Set the course path in PowerShell:

```powershell
$lawCourse = 'C:\path\to\Courses\LAW_1'
```

4. Check the selected file without AI calls:

```powershell
python -X utf8 pipeline/pipeline.py "$lawCourse" add-exam exams/2025_june.pdf --prototype --dry-run
```

The dry run must list only `LAW_1\exams\2025_june.pdf`. It checks selection, not model connectivity or output quality. This paper contains 11 compulsory questions worth 100 marks. Its PDF text layer was inspected locally; no OCR is needed.

## Analyze the paper

This command sends extracted exam text to your configured provider and may incur charges. Run it yourself after choosing the models and budget:

```powershell
python -X utf8 pipeline/pipeline.py "$lawCourse" add-exam exams/2025_june.pdf --prototype --total-marks 100
```

Stage 1 extracts questions. The prototype checks their marks before Stage 2 tags and scores topics. A successful run saves a candidate and prints the two report paths under `LAW_1\prototype\`. The [format reference](prototype-output-format.md) describes the workbook and agent JSON.

The current two-stage workflow can make more than two requests because tagging, scoring, batching, and transport retries are separate operations. No independent model review runs.

To analyze additional comparable papers with the same total, use `add-exam exams/ --prototype --total-marks 100`. Existing records are skipped. Use separate commands if the totals differ. Prototype mode supports papers where all questions are compulsory.

## Check the result before publication

1. Open `LAW_1\candidates\2025_june.json`. Expect `Q1` through `Q11` once each, with marks `1, 1, 1, 1, 1, 5, 5, 10, 15, 30, 30`. Check the complete scenarios and answer choices against the PDF.
2. Open `LAW_1\prototype\Exam_ROI_Pipeline.xlsx`. Check that the ROI Scores, Taxonomy, and Exam Log sheets have an unreviewed banner, readable topic names, and a 100-mark paper in Exam Log. Pay particular attention to the two 30-mark scenarios.
3. Open `LAW_1\prototype\Exam_ROI_Pipeline.json`. Confirm that topic order and priorities match Excel and its `generation_id` matches the workbook banner. Give this JSON to the study agent. Full question text remains in the candidate file.
4. Select the results you want to publish and check their topic quality. Keep the original exam, candidates, and private source paths out of Git. A live run and your content review are still required; offline tests do not establish model accuracy.

## Recover without repeating analysis

Close Excel before rebuilding:

```powershell
python -X utf8 pipeline/pipeline.py "$lawCourse" rebuild --prototype
```

This command uses saved candidates and makes no AI calls. It also includes candidates saved by a prior run without `--prototype`, provided their contract and mark totals are compatible. It fails clearly if no candidates exist.

If one paper fails in a batch, successful candidates remain saved and the command returns a nonzero exit code. Automatic export does not refresh a partial batch. Fix and retry the failed input, or explicitly rebuild to export the saved subset.

If rendering or file replacement fails, the command reports an export failure. It attempts to restore any replaced report. A process interruption can still leave files from different generations. Rebuild both reports before using them again.

To replace a bad analysis, rerun the analysis command with `--force`. That makes new AI calls and replaces the candidate only after successful validation. Do not use `--force` merely to fix an export failure.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `pipeline/pipeline.py` | Supplies run flags, selection, configuration, and recovery commands. | CLI arguments or outcomes change. |
| `pipeline/exam_roi/prototype.py` | Supplies total validation and offline report recovery. | Supported paper structure or export behavior changes. |
| `docs/guides/prototype-output-format.md` | Defines the files and human checks used in this guide. | Workbook structure or JSON fields change. |
| `docs/development/workflow.md` | Supplies provider setup and private-data constraints. | Configuration or live-run authorization changes. |
<!-- doc-dependencies:end -->
