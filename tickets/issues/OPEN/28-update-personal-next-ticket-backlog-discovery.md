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
    "scripts/tickets.py"
  ],
  "verification": null,
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
