# 28: Add a project-local next-ticket skill

```json
{
  "schema_version": 1,
  "id": "28",
  "priority": "P2",
  "queue_order": 28,
  "areas": [
    "documentation"
  ],
  "depends_on": [
    "27"
  ],
  "related_to": [],
  "references": [
    "docs/repository-structure.md",
    "docs/development/ticket-workflow.md",
    "scripts/tickets.py",
    "docs/development/workflow.md",
    ".agents/skills/exam-next-ticket/SKILL.md"
  ],
  "verification": {
    "commit": "839f5507bf2f3fdd0ef4e1ee218dd3b7519f1815",
    "checked_at": "2026-09-19T10:16:20+00:00",
    "criteria_digest": "45fbf057114b1c7521a894d149c913a37edc56b047e38f9270a8e8874a8111e1",
    "checker": "Codex project-scope audit",
    "result": "still_valid",
    "evidence": [
      "Inspected both installed next-ticket skills: they discover .scratch boards and prescribe manual status updates. No exam-next-ticket skill exists in this repository. Owner requires a project-local skill and unchanged personal installations. Existing CLI next finds ticket 28 in tickets; preflight requests initial verification."
    ],
    "provisional": false
  },
  "closure": null
}
```

**What to build:** Add a repository-local `exam-next-ticket` skill that uses the permanent `tickets/` backlog through the ticket CLI. Leave both installed personal `next-ticket` skills unchanged so other projects retain their current behavior.

- [ ] Add `.agents/skills/exam-next-ticket/SKILL.md` with a distinct name, project-specific discovery, and a check that refuses operation outside this repository before ticket commands or mutations.
- [ ] Use `scripts/tickets.py` for queue discovery, preflight, evidence recording, and state transitions. Preserve ticket history and let the tool generate the status table and blockers.
- [ ] Retain model/effort selection and bounded implementation handoff using available capabilities, isolated worktrees for delegated writers, and the project's authorization and review rules.
- [ ] Link the local skill from the maintained workflow and location policy; explain how to invoke the correct copy without relying on precedence over the personal skills.
- [ ] Validate skill structure, local queue discovery, refusal outside this project, and review/failure behavior. Verify both personal skill files remain byte-for-byte unchanged.
- [ ] Report what checks prove and leave app discovery or unresolved human judgment for explicit review.

**Architecture:** Keep the tracked skill under `.agents/skills/` and use the existing ticket tool as the authority. This change adds no global configuration, shared skill edits, new backlog, or application behavior.

## Evidence and history

2026-09-19: The repository reorganization audit found the old `.scratch/*/TICKET_STATUS.md` discovery rule in both local installations:

- `C:/Users/alber/.codex/skills/next-ticket/SKILL.md`
- `C:/Users/alber/.agents/skills/synced/9d9aa035-8226-4ff8-9717-75dae02f00a6_7aa387e2-0a24-46ad-b3cf-dd32183f0617/next-ticket/SKILL.md`

Ticket 27 deliberately does not edit these personal files. Until this follow-up is complete, use `python scripts/tickets.py next`, `show`, and `preflight` directly. This ticket depends on the reviewed location policy in ticket 27.

2026-09-19 scope correction: The owner requested implementation only for this project, with no effect on other projects. This supersedes the earlier plan to edit personal installations. The inspected personal copies both search `.scratch/*/TICKET_STATUS.md` and prescribe manual status-table edits; the local skill will use the current ticket CLI instead.

## Implementation and verification, 2026-09-19

Implemented the project-only scope on `codex/28-project-next-ticket`, based on
`origin/codex/mvp-two-stage` at `aaa03cf40b8e2f4e86524e3edbaad1f030dffa5d`.
The new `.agents/skills/exam-next-ticket/SKILL.md` uses a distinct name and the
existing ticket CLI. Workflow and folder-policy links point to that copy.
The documentation area map includes the skill. No application code, AGENTS.md,
user-wide configuration, or installed personal skill was changed.

- `python C:/Users/alber/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/exam-next-ticket`: passed.
- `python -m unittest discover -s pipeline/tests -p 'test_*.py'` with `PYTHONIOENCODING=utf-8`: 231 tests passed.
- `python scripts/check_tickets.py`: 39 tests passed; 28 tickets, zero errors, seven existing warnings. Ticket 25 has changed criteria; tickets 01, 02, 05, 07, 10, and 18 lack historical review evidence.
- Local Markdown audit: 23 links and heading anchors passed across the skill and three changed guides.
- `git diff --check`: passed.
- SHA-256 comparison before and after implementation confirmed both installed personal skill files listed above are byte-for-byte unchanged.

An independent read-only agent followed the local skill's project checks and ran
`check`, `next`, and `audit`. With ticket 28 already IN_PROGRESS, it correctly
reported no unblocked OPEN ticket and made no mutations. Before starting this
work, the existing CLI had selected ticket 28 from `tickets/`.

The reviewer also evaluated hypothetical requests from an unrelated repository,
a stale preflight with unrelated dirty files, and a failed implementation with
useful partial code. It reported refusal before ticket commands outside this
project, preservation of dirty files and partial work, and no forced transitions.
Those scenarios are instruction review, not executed foreign-project writes or
an end-to-end implementation run. No actionable findings remained.

## Human review

1. In a new Codex task using this branch's checkout, invoke `$exam-next-ticket` with the request: "Show the next ticket only; do not start work."
2. Confirm the selected skill is `.agents/skills/exam-next-ticket/SKILL.md` in this project. Expect CLI queue output or an explanation that no eligible ticket exists, with no ticket state changes.
3. Review the skill's project checks and handoff instructions. Personal `$next-ticket` skills are deliberately unchanged. If the local skill is not listed, explicitly reference its file and report discovery as unresolved.

Ticket 28 remains TO_REVIEW until this app discovery and workflow review passes.
The skill's scope checks are instructions to the agent, not operating-system
access controls. No claim of live UI discovery is made by the static validator
or the read-only reviewer.
