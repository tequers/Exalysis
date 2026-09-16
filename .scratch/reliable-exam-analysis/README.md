# Reliable exam analysis tickets

Open [Ticket status](TICKET_STATUS.md) to see the queue, workflow states, and unresolved blockers. This table is generated from the ticket files; do not edit it directly.

Each Markdown file under `issues/` defines one ticket's scope, acceptance criteria, relationships, and evidence. Its folder is its authoritative state: `DONE`, `TO_REVIEW`, `OPEN`, `BLOCKED`, or `IN_PROGRESS`. The first fenced JSON block holds structured metadata. IDs remain stable when files move.

Follow the [ticket workflow](../../docs/ticket-workflow.md) to record verification, move tickets, and review changes affecting earlier work. Start new tickets from [the template](TEMPLATE.md). The architecture rationale and proposed module ownership live in [ADR 0008](../../docs/adr/0008-modular-pipeline-architecture.md).

Keep ticket IDs stable. Tickets 18 through 20 add preparatory refactoring; tickets 01 through 17 retain their original scope with architecture notes.

Run these commands from the repository root:

```text
python scripts/tickets.py check
python scripts/tickets.py next
python scripts/tickets.py preflight 08
python scripts/tickets.py search "acceptance"
python scripts/tickets.py impact --base BASE_COMMIT --head HEAD_COMMIT
python scripts/tickets.py audit
```

Replace the commit placeholders with the revisions being reviewed. Use `move --help`
and `verify --help` for update commands. After a manual metadata edit, regenerate
the table with `python scripts/tickets.py index --write`, then run `check`.

The [migration report](MIGRATION_REPORT.md) records how the original 21 tickets
were reconciled. Missing historical verification stays unknown. A DONE ticket
without recorded review evidence does not automatically satisfy a prerequisite.

Run `python scripts/check_tickets.py` for the full offline ticket check.
