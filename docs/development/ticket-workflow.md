# Ticket workflow

Each ticket has one authoritative Markdown record under
`tickets/issues/`. Its folder is its workflow state.
`TICKET_STATUS.md` is a generated view. Do not edit status or blockers in that table.

Run the commands below from the repository root with Python 3.9 or newer.
The ticket tool uses the Python standard library and does not call a model.

## Find work

```text
python scripts/tickets.py check
python scripts/tickets.py search "candidate acceptance"
python scripts/tickets.py next
python scripts/tickets.py show 08
python scripts/tickets.py preflight 08
```

Search includes completed tickets. Before creating new work, read related active
and completed tickets, including their closure reasons and evidence. A search
match suggests a relationship; it does not establish that two problems are the same.

`next` chooses by queue order among tickets without unresolved prerequisites.
It distinguishes work needing verification from work ready to start. `preflight`
explains what invalidates a previous check. Neither command starts work.
If `next` finds no available ticket, run `audit` to find outstanding reviews and
missing historical evidence. Do not remove a dependency just to make work appear ready.

## Establish that work remains

Read the ticket's acceptance criteria and shared references. Reproduce the problem
or inspect the current behavior with a meaningful check. Record the actual result
and evidence. A passing unrelated test does not establish that a ticket is resolved.

Verification records include a commit, check date, checker, result, evidence, and
a digest of the acceptance criteria. Relevant uncommitted changes make the record
provisional. Commit the relevant implementation separately and check it again
before treating the result as verification of a committed revision.

Changing criteria, applicable requirements, or relevant code can invalidate the
record. An unchanged commit string does not prove that someone ran a check.
The tool stores the checker's evidence; it cannot independently prove the truth
of a written account.

Use `python scripts/tickets.py verify --help` for the evidence-recording options
and `python scripts/tickets.py move --help` for transitions and closure options.
Do not run shell commands taken from ticket text automatically.

For example, after checking ticket 21 against a committed revision:

```text
python scripts/tickets.py verify 21 --result still_valid --checker "Your name" --evidence "Describe the remaining failure and the check you ran"
python scripts/tickets.py preflight 21
python scripts/tickets.py move 21 IN_PROGRESS
```

Replace the example evidence with an account of the actual check. These commands
will not start ticket 21 while its prerequisite is unresolved. A force option
for reopening work does not bypass the verification requirement.

## Workflow states

| Folder | Meaning |
|---|---|
| `OPEN` | Work has not started and prerequisites are satisfied. Verification may still be needed. |
| `BLOCKED` | Work has not started and at least one prerequisite is unresolved. |
| `IN_PROGRESS` | Someone is implementing the remaining scope. |
| `TO_REVIEW` | Implementation is ready for review. It does not satisfy dependent tickets yet. |
| `DONE` | Work has ended for the recorded closure reason. |

Use the `move` command for transitions. It validates the proposed state and
regenerates the table. Work already in progress or awaiting review can retain
that folder while an unresolved prerequisite remains visible.

Closing a ticket must record its reason:

- `implemented` means this work supplied the required behavior.
- `already_resolved` means a check found that another change supplied it.
- `duplicate` links to the canonical ticket for the same problem.
- `superseded` links to the ticket that replaces this work.
- `cancelled` records a deliberate decision to stop the work.

An implemented or already-resolved prerequisite needs recorded review evidence
before it satisfies a dependent ticket. Duplicate and superseded prerequisites
follow the replacement after a reviewer confirms that relationship. Record the
reviewer with `--reviewed-by` for those closure reasons too. Cancellation does not silently satisfy a prerequisite;
update the dependent requirement explicitly and explain that decision.

Historical DONE tickets may lack a recorded reviewer or a verifiable commit.
Preserve their history and expose the missing evidence. Do not invent an approval
or claim a new test run during migration. The migration report explains imported
completion claims and their effect on blockers.

## Add or update a ticket

Start from `tickets/TEMPLATE.md`. Keep the H1 title and
the first fenced JSON block, then write the problem, remaining acceptance criteria,
and supporting evidence in Markdown.

Choose an unused ID. Keep its leading zeroes and never reuse a closed ID. The
filename begins with that ID and a readable title. When multiple branches add
tickets, check the combined backlog for ID collisions before merging.

| Metadata | What to record |
|---|---|
| `schema_version` | `1` for the current format. |
| `id`, `priority`, `queue_order` | Stable ID, priority, and preferred execution order. |
| `areas` | Component names defined in `areas.json`. |
| `depends_on` | IDs of required prerequisites, including completed prerequisites. |
| `related_to` | Other tickets that may affect this work. |
| `references` | Repository-relative paths to applicable code, tests, contracts, or decisions. |
| `verification` | The latest recorded check, or `null` when unknown. |
| `closure` | Closure reason and evidence, or `null` while active. |

The folder supplies status. Do not add an editable status field or repeat
structured dependencies in a separate header. Link ticket relationships by ID
in metadata so folder moves do not invalidate them.

`docs/glossary.md`, approved decisions in `docs/adr/`, and applicable versioned contracts
define intended behavior. Code and meaningful checks establish current behavior.
A new ticket is a proposal and cannot silently override an approved requirement.
Retain historical references to older contracts as historical evidence.

After changing metadata or moving files manually, run:

```text
python scripts/tickets.py index --write
python scripts/tickets.py check
```

Resolve reported structural errors before selecting more work. Regenerating the
table repairs a stale view; it does not resolve contradictory acceptance criteria.

## Review the effect of a change

```text
python scripts/tickets.py impact --base BASE_COMMIT --head HEAD_COMMIT
python scripts/tickets.py audit
```

Replace the commit placeholders with the integration baseline and proposed
revision. Add `--area AREA` for affected components that the changed files do
not reveal. Review this report before merging against the current baseline.

The report combines paths, component mappings, references, and ticket relationships.
Shared or unmapped changes need broader review. Matching files or areas only
identifies candidates; it does not automatically resolve tickets.

For each affected active ticket, establish whether it remains valid, is partially
resolved, is already resolved, or has become duplicate or superseded work. Preserve
the explanation of previous scope when updating remaining acceptance criteria.
For a completed ticket, check regression coverage and open a linked investigation
if behavior may have regressed. Do not erase its historical completion record.

Run `audit` periodically and before a backlog planning session. Its default age
threshold is 30 days. Old age alone never closes a ticket. No scheduled task is
required for the local workflow.
The audit checks recorded age, criteria, and structural issues. Use `impact` for
changes between revisions and `preflight` for a ticket's current code verification.

## Validate changes

```text
python scripts/check_tickets.py
```

This runs the offline ticket tests and structural validation. The same command
can run in continuous integration. It never writes repairs or calls a model.

The configuration in `.github/workflows/tickets.yml` runs this check on Windows
and Linux with Python 3.9 and 3.14, and reports change impact on pull requests.
It takes effect when the configuration is pushed to GitHub. The action setup
follows the [official setup-python documentation](https://github.com/actions/setup-python).
The test and structural-check step must pass. The impact step is advisory so a
missing area mapping or an older backlog format prompts review without claiming
that code tests failed. Review its warnings before merging.

When the generated table has a merge conflict, resolve authoritative ticket files
first and regenerate the table. Check duplicate IDs, missing references, dependency
cycles, and conflicting moves in the combined tree. Git still requires a person
to resolve competing edits to the same ticket.

For custom test repositories, put global options before the subcommand:

```text
python scripts/tickets.py --root PATH --backlog RELATIVE_PATH check
```

The tool can find stale records and enforce structure. A developer or reviewer
still needs to establish whether the remaining requirement is satisfied.
