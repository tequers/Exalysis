# Documentation dependency checking

**Approved by the owner on 2026-09-19.** Ticket 29 covers this specification only.
The Python tool is implemented in tickets 30 and 31. Offline tests verify the
covered tool behavior. Declaration rollout and automatic enforcement remain pending.

This page explains the proposed workflow. The linked
[technical reference](doc-dependencies-reference.md) defines the exact implementation contract.
Both documents form one specification.

- To review the proposal, read this page.
- To implement it, also read the technical reference.

## What problem does this solve?

When a document or code file changes, related documents can become incorrect.
The tool helps the developer find what needs review before that happens.

- Documents record their relationships in a short table.
- Python reads those tables and finds connections in both directions.
- Humans see a Mermaid map; agents receive focused JSON results.
- An agent or human decides whether each related file actually needs an edit.

**A passing check proves structure, not truth.** The tool cannot prove that prose
matches code, that every relationship was found, or that a human approved a change.

## The workflow at a glance

The commands below are available. Until declaration rollout, this repository
reports missing blocks rather than a complete dependency graph.

1. **Before editing:** query the files you intend to change with `impact --file`.
   Read the related declarations and claims. Use `discover` to find possible omissions.
2. **After editing:** update affected documents and relationship tables.
   Inspect `git status --short` and stage intended new files so the tool includes them.
3. **Before review:** run `check` and inspect impact against the actual review base
   and head. Check remaining staged and unstaged changes separately.
4. **Refresh saved maps:** when using maps, run `build`, then
   `check --against-artifacts .scratch/doc-dependencies`.
5. **Review independently:** another agent or person checks the content, relationship
   changes, and evidence. The human resolves outstanding judgments before closure.

For every added, removed, or changed relationship, report:

- Which two files are involved.
- What the relationship meant before and means now.
- Why it changed, including ownership moves and renames.

Also explain rejected discovery suggestions and why an affected document needs no
edit, when that is the conclusion. Keep the evidence in the ticket or review
description, without creating another dependency registry.

## What goes in each document?

A declaration is one row with three fields:

| Field | What it explains |
|---|---|
| File | The related file, using its path from the repository root. |
| Reason | Why the two files must stay consistent. |
| Review when | The concrete changes that require a consistency review. |

Example declaration block for the later rollout:

```markdown
<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `pipeline/pipeline.py` | Documents command invocation and outcomes. | CLI arguments, exit statuses, or recovery messages change. |
| `docs/architecture.md` | Uses the boundary between available and pending behavior. | A capability becomes available or its status changes. |
<!-- doc-dependencies:end -->
```

Each covered document needs exactly one block outside fenced examples.
An empty table means "no known relationships." A missing block means incomplete coverage.
See the [parsing rules](doc-dependencies-reference.md#declaration-parsing) for exact syntax.

### Which file owns the row?

- **Document to code or another file:** the covered document owns it.
- **Document to document:** the document relying on the other owns it.
- **Mutual or unclear reliance:** the first repository path in Unicode sort order owns it.
- **Several reasons for the same pair:** keep one row and describe all obligations in its cells.

Do not mirror the row in both documents. Reverse lookup finds the relationship
from either end. Moving a row to the other owner is reported as an ownership change,
not as removing and adding the relationship.

Ownership needs judgment. Python can check that a pair appears only once, but it
cannot decide whether one document truly relies on another.

## Which files are covered?

| File category | Needs its own block? | Can be a target? |
|---|---|---|
| Root `README.md` and tracked Markdown under `docs/` | Yes, except the suppressed ADR subtree. | Yes. |
| `docs/adr/SUPPRESSED/`, including its index | No. Preserve historical decisions. | Yes. |
| Code, tests, configuration, `AGENTS.md`, `CONTEXT.md`, and skills | No. | Yes, if tracked regular files. |
| Runtime contracts under `pipeline/exam_roi/contracts/` | No. They are application resources. | Yes. |
| Anything under `tickets/` | No. Existing ticket metadata owns these relationships. | No. Ordinary navigation links remain allowed. |
| Untracked files, ignored material, generated output, course data, and scratch files | No. | Only tracked regular files can be targets; private and generated material stays untracked under repository policy. |

Additional rules:

- Coverage includes documentation indexes, current ADRs, guides, research, and specifications.
- Historical paragraphs do not exempt a maintained document. Research declares
  relationships of current conclusions or navigation, not every historical path quote.
- Targets cannot be directories, globs, URLs, symlinks, or Git submodules.
- New documents enter coverage after staging. Every worktree result states that
  untracked content was excluded.
- Coverage changes require a specification change. A later rollout must review
  these exclusions and author the real declarations.

## What commands are available?

| Command | Purpose | Result |
|---|---|---|
| `check` | Validate declarations and optionally saved maps. | Counts, coverage gaps, and errors. |
| `build` | Generate maps from valid, complete declarations. | Local `graph.md` with Mermaid and `graph.json`. |
| `impact` | Find related files before editing or after a Git change. | A focused list with reasons, review conditions, and source evidence. |
| `discover` | Look for undeclared relationships in links and path mentions. | Suggestions with evidence; no automatic edits. |

Example before editing:

```text
python scripts/doc_dependencies.py impact --file pipeline/pipeline.py --format json
```

The default impact query includes direct relationships, regardless of who owns
the row. Request `--depth 2` to go further. Requested limits must report omissions.
Agents read the focused JSON; they do not need to scan the whole Mermaid graph.

See the [command reference](doc-dependencies-reference.md#commands-and-exit-status)
for flags, defaults, and exit codes.

### What is the Git change list?

It is a temporary list computed for one chosen comparison, not a global file.

| Mode | What gets compared |
|---|---|
| `--file PATH` | No Git diff. Query the named current file before editing. |
| `--base B --head H` | The two committed endpoint trees. |
| Add `--merge-base` | The common ancestor of B and H against H. |
| `--staged` | HEAD against the staging area. |
| `--unstaged` | The staging area against files on disk. |

Use the actual review base. Committed comparisons exclude pending edits, so
review those separately. The tool never guesses the base branch.

## How are missing and removed connections handled?

- Impact combines declarations from **before and after** the change.
- Deleted files and removed relationships remain visible through the older graph.
- Renames retain old and new paths. Changed reasons and review conditions are reported.
- Discovery suggests connections from links and exact path mentions. It cannot
  find every semantic connection, and a navigation link may need no declaration.
- Agents must still inspect meaning, identify omissions, and explain accepted or
  rejected suggestions. The tool never writes declarations automatically.

During the first rollout, old commits will lack blocks. Impact must report that
gap and return an incomplete result. A human can accept documented manual review
of the historical gap; the tool still reports it. See
[historical safety](doc-dependencies-reference.md#snapshots-comparisons-and-historical-safety).

## How do maps stay current, and what do they cost?

- Declarations remain the source of truth. Saved maps are derived output.
- Maps live locally in ignored `.scratch/doc-dependencies/` and are not committed.
- Rebuild after changes to document content, tracked membership, or format versions.
- A freshness check compares source digests and expected map contents, not timestamps.
- Impact always reads fresh sources and does not require a saved map.
- Python scans all covered documents locally. That scan uses no LLM tokens.
- Only the output read by an agent consumes model context. Focused queries reduce
  that output; no specific token saving is guaranteed.

The graph includes covered documents and declared targets, plus query seeds.
It does not fill the map with unrelated code files.

## What must pass before completion?

- Structural checks pass, or historical gaps receive the documented manual bootstrap review.
- The implementer reports relationship additions, removals, changes, and relevant no-edit decisions.
- An independent reviewer checks the actual content and evidence against the approved scope.
- The reviewer reports omissions, stale claims, unjustified removals, deviations,
  and unnecessary additions.
- The human resolves substantive disagreements and outstanding content judgments.
- Decided, implemented, and verified remain separate claims.

The [acceptance checklist](doc-dependencies-reference.md#implementation-boundary-and-acceptance)
defines the later tool tests. Agent instructions and CI integration require later
approved work; this specification does not enforce them.

## Shared vocabulary

| Term | Meaning here |
|---|---|
| Declaration | One authoritative table row containing File, Reason, and Review when. |
| Reverse lookup | Finding owners from a target by traversing the same declarations in reverse. |
| Git change list | Temporary added, modified, deleted, or renamed paths from one selected comparison; never a global maintained file. |
| Owner | The maintained document containing the one authoritative declaration of a relationship. |
| Target | The repository file named by an owner's declaration. |
| Relationship | One file pair, with a reason and concrete conditions that call for review. |
| Graph | The files and declared relationships derived from a selected snapshot. |
| Snapshot | Worktree content, index content, or tracked content at one resolved commit. |
| Impact | Files reachable from selected changed or proposed paths through declared relationships. |
| Candidate | A mechanically observed reference that may justify a declaration after semantic review. |
| Coverage | Whether every required owner in a snapshot has an explicit declaration block. |

Use the [workflow glossary](../development/glossary.md) for decided, implemented,
verified, specification, ADR, and review. The [development workflow](../development/workflow.md#agree-before-building)
controls approval; the [repository structure](../repository-structure.md) controls placement.
