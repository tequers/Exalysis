# Plan: keep tickets aligned with current project state

## Outcome

Keep one authoritative record per ticket. Generate the shared status table from those records, and check whether a ticket's problem still exists before implementation starts. After a change, identify the older tickets that need another check.

This historical plan records the inspection before the ticket tooling migration on
2026-09-15. The original observations and paths below describe that checkout.
The final section records the implementation result. Use the
[current ticket workflow](ticket-workflow.md) and
[repository structure policy](../repository-structure.md) for present-day locations.

## What exists today

The backlog lives in `.scratch/reliable-exam-analysis/`. It contains 21 ticket files under `issues/`, organized into `DONE`, `TO_REVIEW`, `OPEN`, `BLOCKED`, and `IN_PROGRESS`.

The current workflow repeats state in three places: folder placement, each ticket's `Status` line, and the manually edited `TICKET_STATUS.md` table. Active blockers are also maintained manually in the table.

There is already a mismatch. The table lists ticket 01 as `Review` and links to `issues/TO_REVIEW/01-...md`, while the actual file is in `DONE` and says `Done`. Tickets 09 and 17 still list 01 as an active blocker in that table. Migration must reconcile this using review evidence; folder placement alone does not prove completion.

Moving tickets into status folders changes their link depth. Migration must validate local links as well as statuses, and repair any links that still assume an earlier location.

The project already has shared definitions in `CONTEXT.md`, architecture decisions in `docs/adr/`, and versioned contracts in `pipeline/exam_roi/contracts/`. Its existing Python tests use `unittest`. No tracked GitHub Actions workflow was found in this inspection.

The working tree contains existing changes, including ticket moves. Implementation must preserve them and establish a reviewed baseline before claiming commit-based verification.

## Design decisions

### Keep the current backlog location and IDs

Retain `.scratch/reliable-exam-analysis/issues/` and IDs 01 through 21. Treat IDs as strings and preserve leading zeroes. Future IDs may have more digits. Never reuse an ID.

Keep the five existing folders. Their names are the authoritative workflow state. Remove the manually maintained status line from ticket bodies after migration. The generated table presents the folder state directly, including `BLOCKED`.

Preserve priority and explicit queue order as ticket metadata. Queue order expresses a preference; dependency and freshness checks determine whether work can start.

### Separate state, dependencies, and verification

- Folder state records where the work is in the workflow.
- Dependencies record prerequisites by stable ticket ID.
- Verification records what was checked, against which revision, and with what result.
- Closure records why work ended and links to evidence or a replacement ticket.

`TO_REVIEW` does not satisfy a dependency. A completed prerequisite satisfies it only when its closure represents an implemented and reviewed result. A duplicate or superseded prerequisite redirects to its canonical replacement. A cancelled prerequisite needs an explicit dependency decision; cancellation must not silently unblock dependents.

For work that has not started, unresolved prerequisites imply `BLOCKED`; otherwise use `OPEN`. Work already in `IN_PROGRESS` or `TO_REVIEW` keeps that state and displays unresolved blockers. This preserves the current situation where ticket 06 is awaiting review but still depends on ticket 03.

### Reference shared requirements

Tickets reference approved contracts and architecture decisions rather than copying their rules. Historical completion evidence retains the contract version used at that time. Current work points to the applicable approved version.

A new ticket can propose a requirement change, but cannot make that change authoritative by itself. An approved contract or architecture change triggers a review of tickets that reference it.

## Step 1: define the ticket format and workflow

Add `docs/ticket-workflow.md`, a ticket template, and `areas.json` under the backlog directory. Use one fenced JSON metadata block near the beginning of each Markdown ticket. Python's standard library can parse JSON without adding a YAML dependency.

The metadata contains:

| Field | Purpose |
|---|---|
| `schema_version` | Start at 1; reject unsupported formats. |
| `id`, `priority`, `queue_order` | Stable identity and ordering. |
| `areas` | Controlled component names, such as extraction, evaluation, storage, acceptance, scoring, reports, and configuration. |
| `depends_on`, `related_to` | Prerequisites and other relevant tickets, referenced by ID. |
| `references` | Repository-relative paths to applicable contracts, decisions, code, or tests. |
| `verification` | Null until checked; then revision, check date, criteria digest, checker, result, and evidence. |
| `closure` | Null while active; otherwise reason, fixing commit or replacement ID, and review evidence. |

Keep the title, problem, remaining acceptance criteria, and explanatory evidence readable in Markdown. Metadata holds relationships and structured facts; avoid repeating them in editable prose headers.

Define closure reasons as `implemented`, `already_resolved`, `duplicate`, `superseded`, and `cancelled`. All closed tickets live in `DONE`, with the reason visible in the generated table. Only the first two assert that the required behavior exists.

Define `areas.json` as a small mapping from repository-relative path patterns to component names. Include tests, contracts, and shared configuration. Shared infrastructure changes can conservatively affect every active ticket. Unknown paths that may affect behavior produce a warning rather than an empty impact report.

**Acceptance:** the format represents all existing tickets, including historical dependencies, an unverified ticket, and a review-stage ticket with an outstanding blocker. Every fact has one editable home.

## Step 2: build the reader, validator, and generated index

Add a standalone Python entry point at `scripts/tickets.py`. Keep ticket management independent of the production exam pipeline and its model dependencies.

Implement these commands first:

```text
python scripts/tickets.py check
python scripts/tickets.py index --write
python scripts/tickets.py show 08
```

`check` is read-only. It validates metadata types, unique IDs, known folders and areas, filename/ID consistency, relationship targets, dependency and replacement cycles, required closure evidence, and local reference paths. It reports inconsistent OPEN/BLOCKED placement and a stale generated table.

`index --write` replaces `TICKET_STATUS.md` with a deterministic view containing queue, ID, title, priority, folder state, computed blockers, verification state, and closure reason. Add a generated-file notice. Resolve every ticket link through an in-memory ID-to-path map so folder moves do not break the table. Do not create a second editable registry.

`show` resolves an ID regardless of its folder and displays the ticket, its blockers, and its evidence.

Keep read-only commands free of automatic file moves. Structural errors return a nonzero exit code with the affected ID and a repair instruction. Review warnings remain distinguishable from malformed data.

**Acceptance:** changing a dependency's authoritative record changes the computed blockers and links without manually editing dependent tickets or the table.

## Step 3: migrate the existing 21 tickets

1. Produce a reconciliation report comparing folder, body status, table status, dependencies, and available completion evidence.
2. Resolve contradictory claims individually. Do not use modification times or automatically prefer the most optimistic status. Start with ticket 01 and its dependents.
3. Add structured metadata while preserving IDs, scope, queue order, history, and completion evidence. Record unavailable historical verification as unknown; do not invent commit IDs or approvals.
4. Remove mirrored status and dependency headers after their information has migrated. Repair broken local links. Preserve historical contract references with clear historical wording.
5. Generate the status table and check every ticket reference.
6. Update the backlog README to explain that tickets and folders are authoritative and the table is generated.

Run migration in preview mode first and make it safe to rerun without duplicating content or overwriting unrelated edits. Preserve the existing working-tree moves.

**Acceptance:** all 21 IDs survive exactly once, scope and history are preserved, every discrepancy has an explicit outcome, and a second migration run proposes no further changes.

## Step 4: add checks before work and after changes

Add these read-only commands:

```text
python scripts/tickets.py next
python scripts/tickets.py preflight 08
python scripts/tickets.py impact --base <commit> --head <commit>
python scripts/tickets.py audit
```

`next` excludes work with unresolved blockers. It clearly distinguishes a ticket needing verification from one ready for implementation. It never claims or starts work automatically.

`preflight` checks the selected ticket's criteria and verification record against the current checkout. It reports the checks needed to establish that the problem remains. An agent or developer must reproduce the problem or inspect the relevant behavior and record the outcome before starting implementation.

Record verification against a real commit and a digest of the acceptance criteria. Relevant uncommitted changes make verification provisional; do not attribute those checks solely to HEAD. A missing commit, changed criteria, changed applicable requirement, or relevant code change makes previous verification insufficient. A date or commit string by itself is not proof that a check ran.

`impact` combines changed paths, the area map, explicit relationships, and reverse dependencies. Include both old and new paths for renames and deletions. A ticket-only change must also inspect changed dependencies, references, areas, and replacement links. Expand affected components conservatively for shared behavior; provide an explicit way to name extra affected areas.

The output lists candidate tickets and the reason each needs review. It does not decide that a bug is fixed based on matching filenames or topics.

`audit` lists never-verified tickets, old verification records, unresolved structural warnings, and candidates for duplicate review. Use a documented default age threshold, such as 30 days, adjustable by argument. Age alone never closes a ticket. Search includes DONE tickets so old resolutions remain discoverable.

Review each flagged active ticket as still valid, partially resolved, already resolved, duplicate, or superseded. For partial resolution, update only the remaining scope and preserve the historical explanation. For completed tickets affected by new code, first examine regression coverage; a suspected regression creates a linked candidate for investigation rather than silently rewriting completion history.

**Acceptance:** a fixture where one change satisfies another ticket flags that ticket, while an unrelated change does not mark it resolved. An omitted relationship can still be caught at preflight.

## Step 5: support safe updates and enforce the workflow

Add an explicit `move` command for normal transitions and an explicit command to record verification evidence. Validate the proposed state before writing; reject destination collisions, invalid dependencies, and unsupported transitions. Move only paths resolved inside the backlog. Regenerate the table after successful updates. If interrupted, `check` must expose any inconsistency and `index --write` must repair the derived view without losing ticket content.

Use the workflow at these points:

| Event | Required action |
|---|---|
| New ticket | Search active and closed tickets; add shared references and relationships. |
| Start implementation | Run preflight and record current evidence that work remains; then move to IN_PROGRESS. |
| Submit for review | Record implementation evidence and affected-ticket findings; move to TO_REVIEW. |
| Complete review | Record the reviewed closure, move to DONE, and reconcile affected dependents. |
| Before merging changes | Run structural checks and review the impact report against the current integration baseline. |

Document local commands in the backlog README. Add a small repository check script usable both locally and in continuous integration. Since no tracked CI configuration was found, introducing an automated workflow is a separate rollout step after the local checks pass. The automated check must fail on invalid records and stale generated output, never commit repairs itself.

Do not execute arbitrary shell commands copied out of ticket prose. Automated checks use an explicit supported test interface; other evidence comes from the developer or reviewer.

Document a manual periodic audit first. Scheduling an automation or editing installed personal skills is separate configuration work. The existing AGENTS.md requires permission before modification; this plan does not change it. The workflow can initially live in the backlog README and `docs/ticket-workflow.md`.

**Acceptance:** one normal completion updates the ticket, generated view, and affected blockers consistently. Outstanding review is still a blocker, and a duplicate closure redirects rather than falsely satisfying a prerequisite.

## Step 6: verify correctness and scale

Add offline `unittest` tests under `scripts/tests/`, using temporary ticket trees and temporary Git repositories. Run with `python -m unittest discover -s scripts/tests`.

Cover behaviors that can cause lost work or false readiness:

- Duplicate IDs, missing targets, dependency cycles, and replacement cycles fail with actionable messages.
- Moving a ticket keeps ID lookup and generated links valid.
- Completed dependencies clear blockers; review-stage and cancelled dependencies do not silently clear them.
- Changed criteria, dirty relevant files, missing history, and renamed/deleted paths invalidate inappropriate verification claims.
- A change that partly resolves a ticket preserves its remaining criteria.
- Generated output is stable across runs, migration is repeatable, and interrupted updates preserve the authoritative ticket content.
- Two branches introducing the same ID or incompatible ticket updates are detected when combined; generated-table conflicts are resolved by regeneration.
- A synthetic backlog of 1,000 tickets supports indexing, structural checks, and impact selection without network calls or model calls. Measure runtime on the project machine and target a few seconds for each normal command.

Parse each ticket once per command. Build ID, reverse-dependency, and area lookup maps in memory. A lightweight scan of hundreds of metadata blocks is acceptable; repeated full AI reviews of every ticket are unnecessary. Unmapped changes and periodic audits cover gaps in targeted selection.

Run the existing pipeline test suite if integration changes touch its code or test setup. Ticket-only tooling does not need live model evaluation.

## Delivery order and completion criteria

Deliver Steps 1-3 together as the first usable change: a reconciled backlog and generated status table. Deliver Step 4 next, then controlled transitions and enforcement. Add the relevant Step 6 tests with each implementation step.

The work is complete when:

1. The existing backlog has no contradictory editable status copies or broken ticket links.
2. Blockers and queue readiness derive from authoritative ticket records.
3. Every implementation starts with a current check of the remaining problem.
4. A change produces an explainable list of older tickets needing review.
5. Closing tickets records evidence or an explicit non-implementation reason.
6. The same commands work on the migrated backlog and the 1,000-ticket test fixture.

The tool can enforce structure and expose stale assumptions. Determining whether a requirement is satisfied still requires a meaningful check and review.

## Implementation result, 2026-09-15

Implemented locally. The [workflow guide](ticket-workflow.md) documents the commands,
and the [generated backlog](../../tickets/TICKET_STATUS.md)
shows the migrated records. The [migration report](../../tickets/MIGRATION_REPORT.md)
preserves the reconciliation decisions and historical unknowns.

- All 21 ticket IDs were preserved. Repeating migration proposes no changes.
- `python scripts/check_tickets.py` passed all 35 offline tests using the bundled
  Python 3.12.14 runtime. The real backlog has zero structural errors.
- Indexing, validation, and a real commit-range impact check for 1,000 tickets
  took 4.41 seconds combined in that run. This is a local measurement, not a
  timing guarantee for other machines.
- Seven historical completion records lack review evidence. They remain visible
  as warnings and do not automatically satisfy dependent tickets. Ticket 21 moved
  to BLOCKED because ticket 20 has no recorded review.
- GitHub Actions configuration is included for Windows and Linux on Python 3.9
  and 3.14. The remote workflow has not run; it takes effect after a push.
- `impact` needs an area configuration at both compared commits. A revision from
  before this migration requires a new committed baseline. `audit` covers recorded
  age and structural findings; `preflight` checks current checkout freshness.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `docs/development/ticket-workflow.md` | Directs readers of the historical plan to current ticket procedures. | Current workflow location or the historical-versus-current distinction changes. |
| `docs/repository-structure.md` | Directs readers of old backlog paths to the maintained location policy. | Backlog locations or historical-path guidance change. |
<!-- doc-dependencies:end -->
