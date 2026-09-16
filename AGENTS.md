# Project instructions

## Communication and authorization

- Use plain language. Add complexity only when it improves accuracy or safety.
- Treat questions as read-only. You may inspect files, Git state, and test output, but do not modify files unless the user asks for a change.
- Modify this file only with the user's permission.
- Preserve unrelated user changes. If they overlap the requested work, stop and explain the conflict.

## Project constraints

- OCR is outside the MVP. Do not add, enable, or call an OCR service unless the user approves a separate change after seeing its expected cost.
- Do not run live or paid model calls until the user approves the provider, model, and expected cost.
- Keep course data, scratch files, credentials, generated outputs, and private material out of Git unless the user explicitly asks to track a specific file.

## Start one bounded task

1. Run `git status --short --branch` before editing.
2. Select one ticket when the task maps to the backlog. Use `python scripts/tickets.py next`, `python scripts/tickets.py show ID`, and `python scripts/tickets.py preflight ID`.
3. Define one outcome, its likely files, its acceptance checks, and its non-goals.
4. Run `git fetch origin --prune`, then verify the remote base. Do not assume that the local `main` is current or tracks `origin/main`.
5. Create a short-lived branch named `codex/<ticket-id>-<short-name>`. If no ticket applies, use `codex/<short-name>`. Do not implement changes directly on `main`.
6. Move the selected ticket to `IN_PROGRESS` with `python scripts/tickets.py move ID IN_PROGRESS`. Do not edit `TICKET_STATUS.md` by hand.

For dependent work, base the branch on the branch it needs. For independent work, base it on the current remote `main`. If several tasks run at once, give each task its own branch and worktree. Never let two agents edit the same working tree.

## Make reviewable commits

- Commit one verified behavior, refactor, test addition, or documentation change at a time.
- Keep each commit usable and reversible without removing unrelated work.
- Review `git status --short`, `git diff --stat`, and `git diff` before staging.
- Stage explicit paths or hunks with `git add -p`. Avoid `git add .` when the working tree contains unrelated or untracked files.
- Review `git diff --cached --check` and `git diff --cached` before committing.
- Write a commit subject that states the behavior changed. Add a body only for the reason, constraints, or migration details.
- Push completed commits to the topic branch. Do not force-push or rewrite reviewed history unless the user explicitly approves it.
- Record follow-up work in another ticket instead of expanding the current change.

## Test before review

Run focused tests while developing. Before requesting review, run the full local checks from the repository root:

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m unittest discover -s pipeline/tests -p 'test_*.py'
python scripts/check_tickets.py
git diff --check
```

For ticket impact, compare the actual pull request base with the branch head:

```powershell
python scripts/tickets.py impact --base BASE --head HEAD
```

Report the exact commands and results. Treat warnings as review items. Do not describe a check as passing when it did not run or when its output is incomplete.

## Create small pull requests

- Use one ticket and one reviewable outcome per pull request.
- Open a draft pull request early when feedback can change the design.
- Prefer a few hundred changed lines when practical. Split a pull request that approaches 1,000 non-generated lines or mixes unrelated behavior.
- Explain the change, ticket, included and excluded scope, verification, risks, rollback, AI assistance, and required human checks.
- Compare the pull request description with the actual diff before publishing it.
- Keep generated or mechanical changes separate from behavior changes when reviewers need different evidence.

For stacked pull requests:

- Make every layer buildable and testable.
- Set each pull request base to the branch directly below it.
- State the stack order in every pull request description.
- Merge from the bottom of the stack upward.
- Do not add unrelated work to an existing stack.

Use `docs/research/git-and-pull-requests-for-ai-development.md` when planning a split, recovering a large dirty tree, creating a pull request description, or choosing repository protections.

## Ticket status and human review

Store tickets in `OPEN`, `IN_PROGRESS`, `BLOCKED`, `TO_REVIEW`, or `DONE` according to their current state. Use the ticket tool to move them.

When implementation and checks finish, decide whether the user must review anything.

- If automated checks prove the result and no human judgment is needed, move the ticket to `DONE`.
- If a person must check behavior, output, content, or environment-specific results, move the ticket to `TO_REVIEW`.
- Do not move a ticket from `TO_REVIEW` to `DONE` until the review passes.
- State exactly what the user must check, how to check it, and the expected result.
- Use a short numbered checklist with concrete commands, paths, or screens. Make each step independently verifiable.

## Protect recovery paths

- Before a risky history operation, create a named backup branch or ref.
- Prefer recoverable operations. Do not delete untracked files, stashes, backup branches, or worktrees unless the user names the exact target.
- Never use `git reset --hard`, `git clean`, or a force push as a routine cleanup step.
