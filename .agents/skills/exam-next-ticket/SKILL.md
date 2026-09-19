---
name: exam-next-ticket
description: Select and carry out the next unblocked ticket in the exam-roi-pipeline repository using its ticket CLI, with model selection and an isolated agent handoff. Use for this project's next-ticket requests; excludes other repositories and personal skill maintenance.
---

# Exam pipeline next ticket

This is the repository-local next-ticket workflow. Personal `next-ticket` skills
keep their own behavior. Use this skill's exact name to select this copy.

## Confirm the project before acting

Resolve the active Git root with `git rev-parse --show-toplevel`. Confirm that:

- This loaded file is that root's `.agents/skills/exam-next-ticket/SKILL.md`,
  resolved to the same file, rather than a copy loaded from another checkout.
- `git remote get-url origin` identifies `tequers/exam-roi-pipeline` on GitHub.
  HTTPS and SSH forms, with or without `.git`, refer to the same repository.
- `scripts/tickets.py`, `tickets/areas.json`, and `tickets/issues/` exist there.

If any check fails, explain the mismatch and stop before running ticket commands
or changing files. Do not search sibling projects or fall back to personal skills.
These are agent instructions, not a filesystem sandbox. Keep this skill inside
the repository; do not install it in a user-wide skills directory.

Read the root [AGENTS.md](../../../AGENTS.md). Run commands from the verified
root. The [ticket workflow](../../../docs/development/ticket-workflow.md) defines
verification and closure semantics; use it when those steps need explanation.

## Select and assess one ticket

1. Run `git status --short --branch`, `python scripts/tickets.py check`, and
   `python scripts/tickets.py next`. Resolve structural errors before selection;
   report warnings as review items. Select the first candidate in the CLI's
   queue order, including candidates that need verification. If there is none,
   run `python scripts/tickets.py audit`, report the remaining blockers or
   reviews, and stop. A selection-only request ends before any mutation.
2. Run `python scripts/tickets.py show ID` and `preflight ID`. Read the complete
   record and inspect the relevant implementation and checks. Share the current
   behavior, remaining acceptance criteria, likely files, checks, and non-goals.
   Apply AGENTS.md's ground-truth confirmation rule before starting or assigning
   work. A stale verification is a request to inspect, not permission to bypass
   preflight or remove a dependency.
3. Choose a model and supported effort from the capabilities actually available
   for this task. Use the least costly choice expected to meet the criteria
   without weaker verification or likely rework; explain the choice briefly.
   When choosing `gpt-6-astra` at `xhigh`, `max`, or `ultra`, obtain explicit
   approval for that configuration before status changes or delegation. An
   existing instruction for that exact configuration counts as approval.

## Implement through the ticket tool

Follow the repository's branch and worktree rules using a freshly fetched base.
Preserve unrelated changes. If dirty files prevent valid preflight evidence,
use a clean worktree instead of clearing those files or forcing a transition.
In the implementation checkout, inspect and record actual evidence with
`python scripts/tickets.py verify ID --help` as the option reference. Re-run
`preflight ID`; start only when it reports ready. If the work is already resolved
or only partly remains, use the ticket workflow to record that result rather
than implementing the original scope blindly.

Use `python scripts/tickets.py move ID IN_PROGRESS` to start. The ticket CLI owns
state transitions, generated status rows, and blockers. Do not edit those views
by hand. The Markdown ticket remains the place for scope and actual evidence.

When delegation is available, give one implementation agent its own branch and
worktree, the absolute ticket path, the accepted scope, relevant checks, and the
chosen available model and effort. Keep the parent read-only in that checkout
while the agent writes. Wait for its result. If delegation is unavailable,
report that limitation and implement locally within the same authorized scope.

For failed or interrupted work, preserve the changes and record what remains.
Use the ticket tool for a state that matches reality; do not erase evidence or
reset a ticket to OPEN automatically. Defer user-aborted work as instructed.

## Verify and hand off

Run the checks required by AGENTS.md and review ticket impact against the actual
PR base. Report changed files, evidence, failures, and unresolved judgments.
Follow the repository's commit and PR workflow. Use `move ID TO_REVIEW` when
human judgment or environment checks remain. Use DONE only with the required
closure reason and genuine review evidence. Let the CLI update dependent tickets.
