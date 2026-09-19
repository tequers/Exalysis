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
