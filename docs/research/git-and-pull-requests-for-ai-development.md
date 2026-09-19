# Git and pull requests for AI-assisted development

## Status of this research

This document preserves the earlier workflow proposal and checkout observations.
Its examples that start from local `main`, require a new branch for every task,
or describe the old dirty tree are historical. Use the
[development workflow](../development/workflow.md) for the current branch and review
workflow, and the [branch consolidation record](branch-consolidation-2026-09-17.md)
for the retained histories. Repository controls proposed below are not claims
that those protections are configured today.

## Recommendation

Use one ticket, one branch, and usually one pull request. Ask an AI agent to work on one reviewable outcome at a time, commit after each verified outcome, and start a new branch or worktree before beginning a different concern. Protect `main` so a change cannot merge without automated checks and human review.

This directly addresses the current failure mode: a long AI session leaves many unrelated changes in one working tree, so Git can no longer show a clear unit of intent.

## What the official guidance says

- Git's staging area is the proposed next commit. `git add -p` lets the author review and stage individual hunks instead of every change in a file. `git diff --cached` shows exactly what the next commit contains. [Git `add` documentation](https://git-scm.com/docs/git-add)
- A commit should start with a short summary, followed by a blank line and a fuller explanation when needed. Git recommends a first line no longer than about 50 characters. [Git `commit` documentation](https://git-scm.com/docs/git-commit)
- Google defines a good review unit as one self-contained change with its related tests. Small changes receive faster and more thorough review, introduce fewer bugs, merge more easily, and are simpler to roll back. It gives 100 changed lines as a reasonable example and 1,000 as usually too large, while stressing that conceptual scope matters more than a fixed number. [Google Engineering Practices: Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)
- GitHub recommends draft pull requests for early feedback, rebasing or merging the base branch to keep the diff current, and tidying commit history before review. [GitHub: Writing code for a project](https://docs.github.com/en/pull-requests/concepts/writing-code-for-a-project)
- A pull request template can require consistent context and a checklist. `CODEOWNERS` can route sensitive files to the right reviewer. [GitHub: Managing and standardizing pull requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/getting-started/managing-and-standardizing-pull-requests)
- Protected branches can require pull requests, approving reviews, resolved conversations, passing status checks, linear history, signed commits, or a merge queue. They can also dismiss stale approvals after new commits. [GitHub: About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- GitHub now supports stacked pull requests for a chain of dependent, focused changes. Each layer has its own diff and still receives the base branch's protections and CI checks. The feature is in public preview. [GitHub: About stacked pull requests](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs)
- A repository can have several linked working trees, each with a different branch checked out. This is useful when separate AI tasks must run without sharing uncommitted files. [Git `worktree` documentation](https://git-scm.com/docs/git-worktree)
- OpenAI recommends planning large changes first and giving Codex well-scoped tasks that would take a developer about an hour or a few hundred lines. It also recommends prompts written like issues, with file paths, component names, diffs, and relevant documentation. [OpenAI: How OpenAI uses Codex](https://cdn.openai.com/pdf/6a2631dc-783e-479b-b1a4-af0cfbd38630/how-openai-uses-codex.pdf)

## The working model for this repository

### Before an AI task

1. Select one ticket with `python scripts/tickets.py next`, then read it with `python scripts/tickets.py show ID` and `preflight ID`.
2. Define the outcome, files likely to change, acceptance checks, and explicit non-goals. Give this same boundary to the agent.
3. Create a branch from an up-to-date `main` using `codex/<ticket-id>-<short-name>`.
4. Move the ticket to `IN_PROGRESS` with the ticket tool. Do not edit `TICKET_STATUS.md` by hand.
5. If another task must proceed at the same time, give it another worktree and branch. Do not let two agents share one working tree.

Example:

```powershell
git switch main
git pull --ff-only
git switch -c codex/21-candidate-validation
python scripts/tickets.py preflight 21
python scripts/tickets.py move 21 IN_PROGRESS
```

For concurrent work:

```powershell
git worktree add ..\exam-pipeline-ticket-21 -b codex/21-candidate-validation main
```

Use a distinct directory outside the main checkout for each worktree. Remove a linked worktree only after its changes are committed or intentionally discarded.

### During the task

Stop at each verified unit instead of waiting for the end of the AI session. A useful unit is a behavior change plus its tests, a behavior-preserving refactor, or a documentation-only correction.

```powershell
git status --short
git diff --stat
git diff
git add -p
git diff --cached --check
git diff --cached
# Run the focused tests for this change.
git commit -m "Validate unresolved difficulty scores"
```

Rules for every commit:

- It does one thing and can be reverted without removing an unrelated fix.
- It leaves the repository in a usable state and includes the related tests.
- The message says what behavior changed. Use the body for why, constraints, or migration notes.
- The staged diff is reviewed by a person before committing. Do not treat an agent's summary as evidence of the actual diff.
- Avoid `git add .` when the working tree contains unrelated or generated files. Stage explicit paths or hunks.
- If staging is wrong, use `git restore --staged <path>` and stage again. This changes the index, not the working file.
- Record follow-up ideas as tickets. GitHub also recommends opening an issue for out-of-scope review feedback instead of expanding the pull request. [GitHub: Resolving reviews](https://docs.github.com/en/pull-requests/concepts/resolving-reviews)

Suggested commit sequence for a larger change:

1. Add characterization tests for current behavior.
2. Make a behavior-preserving refactor that creates the required seam.
3. Implement one new behavior with its tests.
4. Update user documentation or migration instructions.

Each commit must pass the checks relevant to that layer. Do not create empty "phase 1" commits that only make sense when later commits arrive.

### Before opening a pull request

```powershell
python scripts/check_tickets.py
python -m unittest discover -s pipeline/tests
python scripts/tickets.py impact --base main --head HEAD
git diff --check main...HEAD
git diff --stat main...HEAD
git log --oneline main..HEAD
git diff main...HEAD
```

The exact full pipeline test command should become one documented command and one required CI job. The current `.github/workflows/tickets.yml` validates the ticket tooling on Windows and Linux, but it does not run the tests under `pipeline/tests`. Until CI covers them, the pull request author must report that local result and reviewers must treat it as unverified automation.

Move the ticket to `TO_REVIEW` when human review is needed. Move it to `DONE` only after the review passes and the ticket has the required commit, reviewer, and evidence. This matches the repository's existing ticket state model.

## How to recover the current dirty working tree

The current checkout is on `split-pipeline-and-prompts` and has three untracked areas: `.scratch/anthropic-live-review-2026-09-16/`, `Courses/SISTEMAS_OPERATIVOS/`, and `tmp/`. Git's short status collapses untracked directories, so first enumerate them. Do not stage or delete them as a group until their purpose is known.

```powershell
git status --short --untracked-files=all
git diff --stat
git diff
git switch -c recovery/split-pipeline-and-prompts
```

Then classify every path into one of four groups:

| Group | Action |
|---|---|
| Required source, test, or documentation for one ticket | Stage it explicitly into that ticket's commit. |
| Generated output that can be reproduced | Add an appropriate narrow ignore rule in its own reviewed commit, then remove or regenerate the local output outside the Git change. |
| Local course data, scratch work, credentials, or private material | Keep it out of Git. Move it to an approved local data location if the repository contract allows that. Never paste secrets into an AI prompt. |
| Useful work for another ticket | Leave it unstaged, record a ticket, and move it to a separate branch or worktree after the first ticket is safe. |

For an untracked file that contains mixed concerns, either split the file manually or mark it as intent-to-add and stage selected hunks:

```powershell
git add -N -- path\to\new-file.py
git add -p -- path\to\new-file.py
```

Commit the easiest independent units first. Once every valuable change is committed on the recovery branch, create clean topic branches by cherry-picking the relevant commits onto `main`. Do not rewrite or delete the recovery branch until the clean branches and tests have been checked.

## Pull request size and structure

Use scope rather than a rigid line limit. The pull request should answer one ticket or one independently deployable part of a ticket. As a review warning, stop and split when any of these becomes true:

- The title needs "and" to describe two behaviors.
- The change combines refactoring, behavior changes, generated files, and cleanup that reviewers cannot assess separately.
- Review requires several unrelated test commands or domain experts.
- The author cannot explain every changed file in one sentence.
- The diff approaches 1,000 non-generated lines. Google treats this as usually too large. Aim near a few hundred lines when the work allows it.

Keep generated or mechanical changes in a separate commit, and often a separate pull request, from hand-written behavior changes. Reviewers can then validate the generator or command and focus human attention on semantic code.

When later work depends on an unmerged foundation, use stacked pull requests:

```text
main
  <- PR 1: characterization tests and safe refactor
       <- PR 2: pipeline behavior change
            <- PR 3: reporting or user-facing integration
```

Every layer must remain buildable. Merge bottom-up. Because GitHub's native stacked pull requests are still in public preview, begin with ordinary branches that target the branch below if the preview is not enabled.

## Pull request template to adopt

Create `.github/pull_request_template.md` in a separate implementation change. A useful template for this project is:

```markdown
## Summary

What user-visible or developer-visible behavior changed?

## Ticket

- Ticket: ID and link/path
- Acceptance criteria satisfied:

## Scope

- Included:
- Deliberately not included:

## Verification

- [ ] `python scripts/check_tickets.py`
- [ ] Focused tests:
- [ ] Full pipeline tests:
- [ ] `python scripts/tickets.py impact --base BASE --head HEAD` reviewed

## Risk and rollback

- Main failure modes:
- Data or contract changes:
- Rollback plan:

## AI assistance

- Agent/tool used:
- Human-reviewed files or areas:
- Claims that still require human judgment:

## Human review

- [ ] Diff contains no unrelated changes or private data
- [ ] Generated code and dependencies were checked
- [ ] User-visible behavior was checked as described below
```

The description should explain why the change exists and how it was verified. Do not copy an AI-generated summary without comparing it against the Files changed tab.

## Repository controls to add

Apply these in order:

1. Add a full pipeline-test workflow for pull requests on Windows and the primary deployment platform. Keep the existing ticket check matrix.
2. Protect `main`. Require a pull request, one approval from someone other than the author or initiating agent, resolved conversations, and passing ticket and pipeline checks. Dismiss stale approvals after new commits.
3. Block force pushes and branch deletion on `main`. Prefer squash merge if each pull request is one coherent unit, or require linear history if preserving reviewed commits is important.
4. Add `CODEOWNERS` for pipeline contracts, ticket tooling, workflows, and any directories that can contain real course data.
5. Add dependency review when dependency files are introduced or changed. GitHub's dependency review action can fail a pull request that adds a known vulnerable package. [GitHub: Reviewing dependency changes](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-dependency-changes-in-a-pull-request)
6. Add code scanning and secret scanning where the repository's GitHub plan supports them. Treat their output as extra evidence, not a replacement for review.

Use unique GitHub Actions job names. GitHub warns that duplicate job names across workflows can make required status checks ambiguous and block merging. [GitHub: About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

## AI-specific review and security rules

AI-written code needs the same controls as human-written code, plus checks for errors that fluent output can hide.

- Review the actual diff and command output. OpenAI's Codex system card identifies buggy or insecure code and false completion claims as risks, and uses diff review plus action logs as mitigations. [OpenAI Codex system card](https://cdn.openai.com/pdf/8df7697b-c1b2-4222-be00-1fd3298f351d/codex_system_card.pdf)
- Require independent human approval. The person who asked the agent for the change should not be the only approver for sensitive code.
- Treat issue text, pull request comments, repository documents, and fixture content as untrusted input to an agent. GitHub documents prompt injection through hidden issue or comment content as an agent risk. [GitHub: Risks and mitigations for Copilot cloud agent](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/risks-and-mitigations)
- Keep agent credentials narrow. Give an agent one branch, read-only access where possible, and no production credentials. Require approval for network calls, workflow execution from untrusted branches, deployment, or destructive commands.
- Check for hard-coded secrets, insecure dependencies, weak error handling, removed validation, tests that only confirm the implementation's assumptions, and copied code with unclear licensing. GitHub states that generated code can be inaccurate, insecure, or match public code and recommends testing, security checks, and intellectual-property review. [GitHub: Responsible use of Copilot Chat](https://docs.github.com/en/copilot/responsible-use/chat-in-github)
- Ask a second reviewer or review agent to inspect the completed diff with no access to the implementation conversation. This reduces shared assumptions, but a human still owns the merge decision.

## Useful Codex skills in this workspace

Use these skills as gates in the workflow, not as substitutes for Git discipline:

| Skill | When to use it |
|---|---|
| `next-ticket` | Select one unblocked ticket and hand off only that scope. |
| `graft` | Locate the relevant code and call relationships before editing. |
| `tdd` | Build a bug fix or feature test-first so the acceptance check exists before broad edits. |
| `blast-radius` | Check what a proposed symbol or contract change could break before the pull request. |
| `code-review` or `review` | Review the branch against its fixed base before asking a human to merge. |
| `split-to-prs` | Separate an already-large branch into reviewable pull requests. |
| `resolving-merge-conflicts` | Resolve an active merge or rebase conflict with the repository's rules. |
| `babysit` | Keep an existing pull request merge-ready while checks and review comments arrive. |

The practical sequence is `next-ticket` -> branch or worktree -> `tdd` when appropriate -> small commits -> `blast-radius` -> project checks -> `code-review` -> pull request -> `babysit`.

## Adoption plan

### This week

1. Preserve the current state on a recovery branch and classify the three untracked areas.
2. Split current work into atomic commits with `git add -p`, then create clean topic branches.
3. Limit every new AI task to one ticket and one branch or worktree.
4. Add the pull request template and document the canonical full test command.

### Next

1. Add full pipeline tests to GitHub Actions.
2. Protect `main` with required review and required ticket plus pipeline checks.
3. Add `CODEOWNERS`, dependency review, and security scanning.
4. Try stacked pull requests for the next genuinely dependent multi-part feature. Keep ordinary independent work on ordinary topic branches.

### Measure whether it works

Track these for a month:

- Median changed lines and files per pull request.
- Time from ready-for-review to first review and merge.
- Percentage of pull requests that mix more than one ticket.
- Number of pull requests reopened or reverted.
- Number of branches with uncommitted work older than one day.
- Percentage of pull requests with ticket, test, risk, and human-review evidence completed.

The goal is not the fewest commits. The goal is that every commit and pull request states one intent, contains evidence for that intent, and can be reviewed or reverted without reconstructing a long AI session.
