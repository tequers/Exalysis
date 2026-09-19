# 28: Update personal next-ticket backlog discovery

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

**What to build:** Update the owner's installed personal `next-ticket` skills to discover the permanent `tickets/` backlog after ticket 27 passes review. Keep the repository ticket CLI as the source for queue state.

- [ ] Inspect both installed skill copies and update their backlog discovery from `.scratch/*/TICKET_STATUS.md` to `tickets/TICKET_STATUS.md` or the repository ticket CLI.
- [ ] Preserve support for other repositories that use a different backlog location rather than imposing this repository's layout globally.
- [ ] Verify the updated skill finds this repository's queue without creating a second backlog or editing ticket evidence.
- [ ] Record which personal files changed and how the owner can confirm the correct skill copy is active.

**Architecture:** Follow [the repository location policy](../../../docs/repository-structure.md#backlog-relocation-and-history) and keep installed personal skills outside this repository's tracked files.

## Evidence and history

2026-09-19: The repository reorganization audit found the old `.scratch/*/TICKET_STATUS.md` discovery rule in both local installations:

- `C:/Users/alber/.codex/skills/next-ticket/SKILL.md`
- `C:/Users/alber/.agents/skills/synced/9d9aa035-8226-4ff8-9717-75dae02f00a6_7aa387e2-0a24-46ad-b3cf-dd32183f0617/next-ticket/SKILL.md`

Ticket 27 deliberately does not edit these personal files. Until this follow-up is complete, use `python scripts/tickets.py next`, `show`, and `preflight` directly. This ticket depends on the reviewed location policy in ticket 27.
