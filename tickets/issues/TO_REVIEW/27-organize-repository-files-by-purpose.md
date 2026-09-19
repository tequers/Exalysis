# 27: Organize repository files by purpose

```json
{
  "schema_version": 1,
  "id": "27",
  "priority": "P2",
  "queue_order": 27,
  "areas": [
    "documentation"
  ],
  "depends_on": [],
  "related_to": [
    "25"
  ],
  "references": [
    "README.md",
    "docs/glossary.md",
    "docs/development/workflow.md",
    "docs/README.md",
    "scripts/tickets.py",
    "scripts/ticket_history.py"
  ],
  "verification": {
    "commit": "722b5ee94a721de04c22fea284b1a908a52f1c8f",
    "checked_at": "2026-09-19T09:35:20+00:00",
    "criteria_digest": "570d09ffe962ccade2a7099c8a4faa2168dc398fb9afaadb5b9d9564c4a238b1",
    "checker": "Codex repository structure audit",
    "result": "still_valid",
    "evidence": [
      "Inspected c893b92 and committed ticket scope: human docs are split across root, docs, and pipeline/docs; permanent tickets remain under .scratch; historical impact uses one backlog path for both commits."
    ],
    "provisional": false
  },
  "closure": null
}
```

**What to build:** Give this portfolio MVP an explicit location policy and move human documentation and the permanent backlog to their documented homes.

- [ ] Document each maintained folder's purpose, contents, exclusions, tracking rules, and maintenance in `docs/repository-structure.md`; link it from the README map and documentation index.
- [ ] Keep human documentation under `docs/`, with guides, development workflow, architecture, glossary, decisions, and research. Preserve runtime contracts, package code, tests, and tool-defined agent configuration locations.
- [ ] Reframe the development guide as the owner's internal workflow, preserving valid setup, Git, testing, and review instructions and anchors. Do not add public contributor framing or future review automation.
- [ ] Move only the tracked permanent backlog to `tickets/`, preserving ticket IDs, state, and historical evidence. Ignore temporary `.scratch/` material.
- [ ] Update current links, path references, ticket defaults, migration utilities, and configuration. Keep historical quotes intact and explain retained legacy paths.
- [ ] Prove historical impact across the old and new backlog locations, including removed relationships, malformed history, and custom backlog support with focused regression tests.
- [ ] Run full offline checks, local Markdown link and anchor validation, and committed ticket impact. Report existing warnings and personal skill limitations.
- [ ] Leave this ticket and ticket 25 in `TO_REVIEW` for the owner's judgment of the layout and workflow language.

**Architecture:** Follow the user-confirmed purpose-based layout. Runtime evaluation contracts remain in `pipeline/exam_roi/contracts/`. Reserve `docs/specs/` for future real specifications; do not create an empty folder.

## Scope boundaries

Do not change application behavior, expand workflow policy, implement a dependency checker, run OCR or live model calls, move private material, or edit installed personal skills. Ticket 25 is related documentation work, not a prerequisite for this independent maintenance change.

## Evidence and history

2026-09-19: The owner approved the location policy and implementation. At source commit `c893b92e9da67ba54982abe354386f211e513979`, human prose is split among the root, `docs/`, and `pipeline/docs/`; the tracked backlog is under `.scratch/reliable-exam-analysis/`. The ticket impact command passes the current backlog path to both commit snapshots, so relocation requires historical path support.

## Implementation and checks, 2026-09-19

The migration is committed in `abb40eb`; `9159b0d` aligns impact handling of valid
state-folder markers with the snapshot reader. The working branch is
`codex/27-repository-structure`, from `origin/codex/mvp-two-stage` at
`c893b92e9da67ba54982abe354386f211e513979`.

- `$env:PYTHONIOENCODING='utf-8'` then `python -m unittest discover -s pipeline/tests -p 'test_*.py'`: 231 tests passed. No application modules, runtime contracts, application tests, or requirements changed.
- `python scripts/check_tickets.py`: 39 tests passed; 28 ticket records, zero errors, seven warnings. Six historical closures lack review evidence, for tickets 01, 02, 05, 07, 10, and 18. Ticket 25's owner-approved wording change invalidates its earlier criteria digest. Its original verification evidence remains unchanged for human review.
- `python -m unittest discover -s scripts/tests -p 'test_backlog_relocation.py' -v`: four regression tests passed for old-base/new-head impact, removed historical relationships and tickets, malformed-current-data rejection, custom backlog isolation, and verification lookup across the move.
- `python -m unittest discover -s scripts/tests -p 'test_ticket_impact_history.py' -v`: five tests passed, including valid marker recognition and continued warnings for unknown files and states.
- Local Markdown path and heading-anchor audit: 193 links passed across 68 Markdown files. A pre-existing ticket 04 link to `README.md#what-it-can-read` now points to the current `#input-files` section.
- `python scripts/migrate_tickets.py`: read-only preview found all 28 tickets exactly once and proposed no metadata additions, moves, or link repairs.
- `git diff --check` and `git diff --cached --check`: passed.
- `python scripts/tickets.py impact --base c893b92 --head HEAD`, at `9159b0d`: completed with exit 1, 105 changed paths, all eight areas, and candidate tickets 01 through 28. Its three unmapped-path warnings are reviewed below. Exit 1 is retained honestly because those paths have no area mapping.

The `.gitignore` warning covers the deliberate whole-folder exclusion of temporary
`.scratch/` material. The retired `CONTRIBUTING.md` warning covers its move to the
internal workflow. The `Courses/Example_Course/final_01_01_2026/README.md` warning
covers one glossary link update in the synthetic scaffold. None changes pipeline
behavior; the actual diff was inspected rather than suppressing these warnings.

The remaining retired-path strings are historical evidence in the ticket tooling
plan, the branch-consolidation research, ticket 25's original verification, and the
ticket 07 implementation report; explicit compatibility paths and regression
fixtures; or ignore rules protecting local private and superseded files. The
repository policy explains the move and retained exceptions. Ticket 28 records
the separate installed personal-skill update, blocked by review of this ticket.

## Human review

1. Open `README.md`, follow the documentation index to `docs/repository-structure.md`, and confirm the layout and root exceptions fit the portfolio MVP.
2. Read `docs/development/workflow.md` and confirm its owner-focused language and preserved setup, branch, testing, and review instructions. Ticket 25 remains in `TO_REVIEW` for this content judgment.
3. Run `python scripts/tickets.py show 27` and `python scripts/tickets.py show 28`. Expect ticket 27 in `TO_REVIEW` and ticket 28 blocked by 27; installed personal skills remain unchanged.

No human review approval is recorded by this implementation handoff.
