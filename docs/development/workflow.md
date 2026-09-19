# Development workflow

This guide records how the developer maintains this portfolio MVP, with or without
AI assistance. It also gives future developers the context to continue the work.
Keep changes focused on a useful, working product that can be demonstrated.

Start with the [glossary](../glossary.md) and [current architecture](../architecture.md),
then use this guide to set up a checkout and complete one ticket. The
[documentation index](../README.md) groups the other guides by task. This route
needs neither an AI agent nor provider credentials.

## Set up offline development

The pipeline supports Python 3.10 or newer. Use Python 3.14 for the locally
verified development baseline. The ticket tool alone supports Python 3.9 or
newer; its CI matrix checks 3.9 and 3.14 on Windows and Linux. That matrix does
not test the full pipeline across every Python version.

From the repository root, create a virtual environment and install dependencies:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r pipeline/requirements.txt
```

On Windows, activate it with `.\.venv\Scripts\Activate.ps1` if your shell permits
scripts. Otherwise use `.\.venv\Scripts\python.exe` in place of `python` in every
command below. On macOS or Linux, activate with `source .venv/bin/activate`, then
run `python -m pip install -r pipeline/requirements.txt`.

Dependency installation needs package access, but subsequent offline checks need
no network or credentials. Do not create `.env` for offline development. The
requirements include the PDF readers, workbook writer, and provider SDKs; an
installed SDK does not require a configured provider.

Run the full local checks from the repository root:

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m unittest discover -s pipeline/tests -p 'test_*.py'
python scripts/check_tickets.py
git diff --check
```

On macOS or Linux, set `export PYTHONIOENCODING=utf-8` instead. Check each command's
exit status separately. The pipeline tests use synthetic files, fake clients, and
saved responses. The ticket check runs its own tests and validates the backlog.
Report warnings as review items even if a command exits successfully. Existing
ticket CI does not replace the full local pipeline run.

Inspect the CLI without a provider:

```text
python pipeline/pipeline.py --help
python pipeline/pipeline.py "path/to/your/course" add-exam --help
```

Use [new course setup](../guides/new-course-setup.md) to prepare your own course
folder and run `add-exam --dry-run`. The dry run lists selected paths and performs
no analysis. That guide also explains input selection and the limits of the
current candidate-only workflow.

## Choose and verify one ticket

```text
git status --short --branch
python scripts/tickets.py next
python scripts/tickets.py show ID
python scripts/tickets.py preflight ID
```

Replace `ID` with the selected ticket's ID. Read its whole record and references.
The permanent backlog is in `tickets/issues/`; the
[status table](../../tickets/TICKET_STATUS.md) is generated from
those records. Do not edit the table or remove dependencies to start blocked work.

Establish the current behavior, intended outcome, likely files, acceptance checks,
and non-goals with the developer. Reproduce the problem or inspect relevant code
and tests, then record actual evidence when preflight requests verification:

```text
python scripts/tickets.py verify ID --result still_valid --checker "Your name" --evidence "The check performed and the remaining problem"
python scripts/tickets.py preflight ID
```

Use `partially_resolved` when only part remains. Relevant uncommitted changes make
verification provisional; recheck the committed revision before treating it as
current evidence. The [ticket workflow](ticket-workflow.md) explains other
verification results and closure reasons. For agent work, confirm the ground truth
before assignment unless the invoked `next-ticket` workflow handles that step.
Installed personal skills may still search the former backlog path; see the
[relocation note](../repository-structure.md#backlog-relocation-and-history).

## Choose the branch base

```text
git fetch origin --prune
git branch -vv
git log -1 --oneline origin/main
git log -1 --oneline origin/codex/mvp-two-stage
```

The current two-stage implementation is on `codex/mvp-two-stage`. Use its fetched
origin branch for work that depends on that implementation. The
[branch consolidation record](../research/branch-consolidation-2026-09-17.md)
explains the retained branches. Local `main` was preserved with history unrelated
to `origin/main` and no upstream. Do not assume they match or use `git pull` on
local `main` as a setup step. Independent work starts from the verified remote
`main` when it does not need the MVP changes.

A separate branch helps when the ticket needs its own pull request, a different
base, or isolation from other work. Keep small related follow-ups on a suitable
existing non-`main` branch when another branch adds no value. Never implement on
`main`. Preserve unrelated changes and stop if they overlap the ticket.

Before creating a branch, report its source as
`codex/ID-short-name <- origin/codex/mvp-two-stage @ SOURCE_COMMIT`, replacing
`SOURCE_COMMIT` with the fetched commit. For a new MVP-dependent ticket:

```text
git rev-parse origin/codex/mvp-two-stage
git switch -c codex/ID-short-name origin/codex/mvp-two-stage
python scripts/tickets.py move ID IN_PROGRESS
```

The move updates the authoritative ticket and generated table together. If tasks
run concurrently, give each one a separate branch and worktree. Do not let two
agents edit the same working tree. Preserve recovery branches and worktrees.

## Implement and verify the change

Keep one reviewable outcome in scope. Use focused checks for its behavior while
developing, then run the full checks above. For example, CLI changes can use:

```text
python -m unittest discover -s pipeline/tests -p 'test_cli_outcomes.py' -v
```

For documentation, compare commands with `--help`, resolve local links relative
to each document, and check behavior claims against production code and tests.
Use synthetic data for new fixtures. Never commit real papers, extracted text,
credentials, local scratch evidence, or generated course reports.

Review before staging and commit one verified outcome:

```text
git status --short
git diff --stat
git diff
git add -p
git diff --cached --check
git diff --cached
git commit -m "Describe the verified change"
```

Stage new files by explicit path. Avoid `git add .` when unrelated files exist.
Before review, compare the actual pull request base and committed head:

```text
python scripts/tickets.py impact --base BASE_COMMIT --head HEAD_COMMIT
git diff --check BASE_COMMIT...HEAD_COMMIT
git diff --stat BASE_COMMIT...HEAD_COMMIT
git diff BASE_COMMIT...HEAD_COMMIT
```

Replace both placeholders with actual commits. For an MVP-dependent pull request,
the base is the current `codex/mvp-two-stage` revision, not an assumed `main`.
Review impact warnings and affected tickets; a path match does not prove a ticket
is resolved. Push completed commits with `git push -u origin YOUR_BRANCH`.

## Hand off for review or completion

Open one pull request for the ticket, with its actual source branch as the base.
Use a draft when early feedback can change the design. Explain the change,
included and excluded scope, exact checks and results, risks, rollback, AI
assistance, and the concrete human checks still required. Compare the description
with the diff before publishing it. The
[Git and pull request research](../research/git-and-pull-requests-for-ai-development.md)
provides background for splitting larger work and reviewing recovery options.

When a person must judge behavior, output, prose, or platform-specific results:

```text
python scripts/tickets.py move ID TO_REVIEW
```

Provide a short numbered checklist with commands or paths and expected results.
Do not claim that this transition satisfies dependent tickets. After review passes,
record the real reviewer and evidence using the closure options in
`python scripts/tickets.py move --help`. For example:

```text
python scripts/tickets.py move ID DONE --reason implemented --commit COMMIT --reviewed-by "Reviewer name" --evidence "The completed review and checks"
```

If automated checks fully prove the outcome and no human judgment is needed,
project policy allows completion with the required closure evidence. Do not invent
review approval. Implemented prerequisites need recorded review evidence before
they unblock dependents. The `next-ticket` workflow always hands implementation
off in `TO_REVIEW` and leaves completion to review.

## Optional live-provider setup

Live analysis is separate from onboarding and offline verification. Before a live
run, get approval for the provider, exact Stage 1 and Stage 2 model IDs, and
expected cost. Budget for batching and retries; two stages can make more than two
requests. A model ID containing `free` is not a cost guarantee.

Confirm that the paper may be sent to the chosen provider and check its data
handling terms. The request includes extracted question text, retained context,
and analytical prompts. Candidates can retain source text and private paths.
Keep course data and captures local; use synthetic examples in commits or issues.

Copy [.env.example](../../.env.example) to `.env` at the repository root, then edit it
locally. Set `LLM_PROVIDER`, `LLM_MODEL_STAGE1`, `LLM_MODEL_STAGE2`, and the matching
API key. Supported providers are Anthropic, DeepSeek, OpenAI, OpenRouter, and
UnoRouter. The CLI loads `.env` for live `add-exam`; existing environment values
take precedence. Never paste keys into commands, prompts, logs, or commits.

Set request budgets to the selected models' actual limits using the
[model request limits guide](../guides/model-request-limits.md). After approval,
follow [new course setup](../guides/new-course-setup.md) to save a candidate.
Independent review and candidate promotion remain unavailable in the MVP CLI.
OCR is outside the MVP and needs a separate approved change with an expected cost.
