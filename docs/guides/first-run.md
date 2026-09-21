# Rank three LAW exams yourself

By the end of this guide you have two files on your machine: an Excel workbook and
a JSON file that rank the topics from three real A-level Law papers by study
priority. You do not need to know Python. You do need a paid API key, because one
step sends the exam text to an AI provider.

The whole run takes about 20 minutes. Most of that is installing Python and
downloading the three papers.

This guide reproduces the example shown in the [project README](../../README.md).
To analyze your own papers instead, follow [new course setup](new-course-setup.md)
after you finish here.

## Before you start

You need three things:

- A computer running Windows, macOS, or Linux.
- An API key from Anthropic, DeepSeek, OpenAI, OpenRouter, or UnoRouter.
- Credit on that key. The cost depends on the provider and the models you pick.

The commands below use Windows PowerShell. Where macOS and Linux differ, the
guide gives the other command directly under it.

## Step 1: Install Python

Download Python 3.10 or newer from [python.org](https://www.python.org/downloads/).
On Windows, select **Add python.exe to PATH** in the installer.

Open a new terminal and check the version:

```powershell
python --version
```

You see `Python 3.10.0` or a higher number. If the terminal does not find the
command, close the terminal, open a new one, and try again.

## Step 2: Download the code

Run these four commands from the folder where you keep projects:

```powershell
git clone https://github.com/tequers/exam-roi-pipeline.git
cd exam-roi-pipeline
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS or Linux, replace the last command with
`.venv/bin/python -m pip install -r requirements.txt`.

The install prints the packages it installed and ends with `Successfully
installed`. Every later command runs from this `exam-roi-pipeline` folder.

Check that the pipeline starts:

```powershell
.\.venv\Scripts\python.exe pipeline/pipeline.py --help
```

You see the help screen with the `add-exam`, `status`, `rebuild`, and
`edit-topic` commands. This step makes no API calls and costs nothing.

## Step 3: Download the three exam papers

The papers are not in the repository, because they are copyrighted. Create the
folder that holds them:

```powershell
New-Item -ItemType Directory -Force -Path "Courses/LAW_1/exams"
```

On macOS or Linux, run `mkdir -p Courses/LAW_1/exams` instead.

Download each paper and save it under the exact filename in the last column. The
pipeline reads the year from the filename.

| Year | Paper | Download | Save as |
| ---: | ----- | -------- | ------- |
| 2023 | AQA A-level Law Paper 2, 7162/2 | [PDF](https://filestore.aqa.org.uk/sample-papers-and-mark-schemes/2023/june/AQA-71622-QP-JUN23.PDF) | `2023_june.pdf` |
| 2024 | AQA A-level Law Paper 1, 7162/1 | [PDF](https://cdn.sanity.io/files/p28bar15/green/4cff369e127824d15c8bc708e9492a4e2e16a60d.pdf) | `2024_may.pdf` |
| 2025 | AQA A-level Law Paper 1, 7162/1 | [PDF](https://revisionworld.com/sites/default/files/revisionworld/documents/AALA251.PDF) | `2025_june.pdf` |

Confirm that the pipeline finds all three:

```powershell
.\.venv\Scripts\python.exe -X utf8 pipeline/pipeline.py "Courses/LAW_1" add-exam exams/ --prototype --dry-run
```

The command lists `2023_june.pdf`, `2024_may.pdf`, and `2025_june.pdf`. It makes
no API calls. If a file is missing from the list, check its name and its folder.

## Step 4: Add your API key

The next step sends the extracted exam text to the provider you choose. Read that
provider's data handling terms before you continue.

Set the provider, your key, and the two model IDs in the terminal:

```powershell
$env:LLM_PROVIDER = "unorouter"
$env:UNOROUTER_API_KEY = "<your-api-key>"
$env:LLM_MODEL_STAGE1 = "deepseek-v4.1-flash"
$env:LLM_MODEL_STAGE2 = "deepseek-v4.1-flash"

$env:LLM_CONTEXT_TOKENS_STAGE1 = "1000000"
$env:LLM_CONTEXT_TOKENS_STAGE2 = "1000000"
$env:LLM_MAX_OUTPUT_TOKENS_STAGE1 = "655536"
$env:LLM_MAX_OUTPUT_TOKENS_STAGE2 = "655536"
```

These values disappear when you close the terminal. To keep them, copy
[.env.example](../../.env.example) to a file named `.env` in the
`exam-roi-pipeline` folder and edit it there. Git ignores `.env`.

To use a different provider, set its key variable in place of
`UNOROUTER_API_KEY` and pick model IDs that the provider offers. The token
numbers are request budgets, so set them to the real limits of your models. See
[model request limits](model-request-limits.md).

Never paste your key into a commit, an issue, or a chat message.

## Step 5: Run the analysis

```powershell
.\.venv\Scripts\python.exe -X utf8 pipeline/pipeline.py "Courses/LAW_1" add-exam exams/ --prototype --total-marks 100
```

This command charges your API key. It runs two model stages on each paper. Stage 1
extracts the questions and marks. Stage 2 tags the topics and scores them.

The run takes several minutes. It prints progress for each paper and ends with the
paths of the two report files. If one paper fails, the other papers keep their
saved results, and the command reports which file failed.

## Step 6: Open the results

Both files are in `Courses/LAW_1/prototype/`:

- Open `Exam_ROI_Pipeline.xlsx` in Excel. The **ROI Scores** sheet ranks the topics.
  The **Taxonomy** and **Exam Log** sheets show the topics found and the papers read.
- Open `Exam_ROI_Pipeline.json` in a text editor. It holds the same ranking as a
  flat array, so you can paste it into a chat with an AI assistant.

The top rows look like this:

| Rank | Topic                                 | Exams | Priority |
| ---: | ------------------------------------- | ----: | -------: |
|    1 | Lay Magistrates                       |   2/3 |   3.3333 |
|    2 | Criminal Courts and Trial Procedure   |   2/3 |   3.2945 |
|    3 | Non-Fatal Offences Against the Person |   2/3 |   2.7083 |

Your rows can differ. A language model produces the topics and the judgments, so
two runs of the same papers do not always agree. Every sheet carries a banner that
marks the result as unreviewed. The [ranking methodology](scoring-methodology.md)
explains what the Priority number means and what it does not.

## If something goes wrong

| What you see | What to do |
| ------------ | ---------- |
| The terminal does not find `python` | Close the terminal, open a new one, and repeat Step 1. |
| The dry run lists no files | Check that the PDFs are in `Courses/LAW_1/exams/` under the exact filenames. |
| A page has no text layer | The paper is a scan. This pipeline does not read scans. Use a different copy. |
| The run stops with an authentication error | Repeat Step 4 in the terminal you run the analysis from. |
| The command cannot write the Excel file | Close the workbook. Run the Step 5 command again with `rebuild --prototype` in place of `add-exam exams/ --prototype --total-marks 100`. This makes no API calls. |

## What to do next

- Analyze your own past papers with [new course setup](new-course-setup.md).
- Read what each workbook and JSON field means in the
  [prototype output format](prototype-output-format.md).
- Turn the ranking into a study session with
  [exam-prep-prompt](https://github.com/tequers/exam-prep-prompt), a separate project.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `pipeline/pipeline.py` | Supplies the commands, flags, and printed output that this guide tells a first-time user to expect. | CLI arguments, command names, or console output change. |
| `requirements.txt` | Gives the install command used in Step 2. | The public install command or dependency-file location changes. |
| `.env.example` | Names the provider and budget variables set in Step 4. | Variable names, supported providers, or default models change. |
| `docs/guides/prototype-output-format.md` | Describes the workbook sheets and JSON fields that this guide tells the user to open. | Workbook structure, sheet names, or JSON fields change. |
| `docs/guides/new-course-setup.md` | Continues the route for a user who wants to analyze their own papers. | Course folder creation or the per-course workflow changes. |
| `docs/guides/scoring-methodology.md` | Explains the Priority number shown in the result table. | Formula, score interpretation, or stated limits change. |
| `docs/guides/model-request-limits.md` | Explains the token budget variables set in Step 4. | Budget variable names or their meaning change. |
<!-- doc-dependencies:end -->
