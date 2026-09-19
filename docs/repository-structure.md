# Repository structure

This policy defines where maintained files belong in this portfolio MVP. Choose a
location by the file's purpose. Keep a single authoritative copy and link to it.
The [documentation index](README.md) is the entry point for human readers.

## Location policy

| Location | Purpose and contents | Exclusions and tracking | Maintenance |
|---|---|---|---|
| Repository root | Project entry points and configuration required by tools. See the exceptions below. | Track the approved entry files and shared configuration. Keep credentials and generated output local. | Keep the README map concise and link to this policy. |
| `docs/` | Human documentation, including the index, `architecture.md`, `glossary.md`, and this policy. The glossary defines the application's domain language. | Track maintained prose. Keep runtime resources, ticket records, and private material in their own locations. | Update current behavior with the code change that affects it. Link to decisions and contracts instead of duplicating them. |
| `docs/guides/` | Course setup, CLI usage, providers, scoring methodology, request limits, evaluation, and recovery guidance. | Track reproducible instructions and explanations. Keep provider keys, real papers, and generated captures out. | Check commands and relative links when behavior or locations change. |
| `docs/development/` | The owner's internal development workflow, ticket workflow, and its design plan. Workflow terms belong here; application domain terms belong in `docs/glossary.md`. | Track development instructions and their rationale. This is a portfolio maintenance guide, not a public contribution program. | Keep instructions consistent with the ticket commands, checks, and `AGENTS.md`. Label future proposals as proposals. |
| `docs/adr/` | Architecture decision records and their index. `SUPPRESSED/` preserves superseded decision history. | Track decisions, their status, and links to newer decisions. Do not turn old decisions into current usage guides. | Preserve the original reasoning; add dated status context when implementation changes. |
| `docs/research/` | Maintained investigations and evidence that explain technical choices. | Track reusable findings and cited sources. Keep raw private material and temporary research notes local. | Date findings and identify historical commands or examples. Update navigable links without rewriting evidence. |
| `pipeline/` | Application entry points, dependencies, package modules, runtime resources, and application tests. | Track code, dependency declarations, and synthetic fixtures. Human guides live in `docs/guides/`. | Preserve package boundaries and update focused tests with behavior changes. |
| `pipeline/exam_roi/contracts/` | Versioned evaluation contracts loaded by the application. | Track these Markdown resources with the runtime even though people can read them. They are not ordinary guides. | Preserve version meaning. Link guides to the applicable contract. |
| `pipeline/tests/` | Offline application regression tests and synthetic fixtures. | Track test code and approved synthetic or replay fixtures. Keep real course inputs and private captures out. | Keep application checks runnable without credentials or live model calls. |
| `scripts/` | Repository development tools, including ticket validation, migration, and historical impact. `scripts/tests/` contains their tests. | Track development utilities. Do not move application entry points here. | Test command behavior and keep defaults aligned with `tickets/`. |
| `tickets/` | Permanent backlog records, template, area map, generated status table, and retained ticket migration or implementation reports. State folders under `issues/` are authoritative. | Track ticket history and support files. `TICKET_STATUS.md` is generated but committed; `.gitkeep` preserves empty workflow folders. | Use `scripts/tickets.py` for transitions and index generation. Keep IDs stable and retain actual evidence. |
| `Courses/` | Optional local home for course folders. Create it when needed; no course folder is included in a fresh clone. | Keep real papers, extracted text, accepted records, candidates, and generated reports out of Git. Never assume a new course name is ignored. | Inspect `git status` before staging. Apply the existing private-data policy to each new local course folder. |
| `.scratch/` | Temporary local experiments, logs, and smoke-test files. | Ignore the whole folder. It no longer contains the tracked backlog. | Keep only disposable local material here. Do not move permanent decisions or tickets back into scratch. |
| `.agents/`, `.claude/`, `.codex/`, `.github/` | Tool-defined agent instructions, shared settings and hooks, and CI workflows. | Keep shared configuration at the location its tool expects. Ignore local overrides and secrets. | Document human workflow in `docs/development/`; change shared tool behavior deliberately. |
| `graft/` | Regenerable local code graph. | Ignore the graph cache. `.ignore` allows searches of its cards. | Regenerate using the graft tool when needed; do not commit generated cards. |

`docs/specs/` contains approved or draft behavior contracts, including the
[documentation dependency specification](specs/doc-dependencies.md). Add a
specification when a substantial change needs a shared contract. Generated
working dependency maps stay under ignored `.scratch/doc-dependencies/`. The owner
authorized [one published snapshot](development/dependency-map.md) under
`docs/development/` for GitHub readers. Keep its source commit and refresh instructions
visible; this exception does not permit tracking course data or other generated output.

## Root exceptions

- `README.md` is the repository landing page; `LICENSE` records its license.
- `AGENTS.md` stays at the root for repository-wide agent discovery.
- `CONTEXT.md` is a short discovery pointer for domain-modeling tools that expect
  that name at the root. Definitions live only in [the glossary](glossary.md).
- `.env.example` is the tracked environment template. `.env` and private variants
  remain ignored.
- `.gitignore`, `.gitattributes`, `.ignore`, and `.mcp.json` stay where their tools
  read them. Shared tool directories retain their required locations as listed
  above.

`CONTRIBUTING.md` moved to [the internal development workflow](development/workflow.md).
The provider-specific root guide moved to [GLM testing](guides/glm-testing.md).
There is no separate public contributor guide.

## Backlog relocation and history

The permanent backlog moved from `.scratch/reliable-exam-analysis/` to `tickets/`.
Only tracked files moved. Existing ignored material stays local, including old
private reports under `docs/solid/` and superseded files under `pipeline/docs/`.
Their ignore rules remain in place so a directory cleanup cannot expose them.

Ticket commands now default to `tickets/`. Historical impact and verification
reads recognize the two known locations at each commit. An existing but malformed
backlog produces its normal error; it never falls back to a different board.
Explicit custom `--backlog` paths keep their own history.

Historical evidence can still contain the former paths. Those strings describe
the files at the recorded commit. Current Markdown links point to the moved files.
Retained migration and implementation reports are evidence, not current setup
instructions.

Use the repository-local
[`exam-next-ticket` skill](../.agents/skills/exam-next-ticket/SKILL.md) for agent
selection and implementation of the next ticket. Its instructions verify this
project before running the ticket CLI. The distinct name avoids relying on
precedence over the personal `next-ticket` skills, which remain unchanged and
may still use `.scratch/` in other projects. The local skill is tracked only in
this repository. The [ticket workflow](development/ticket-workflow.md) also
provides the direct CLI commands. Skill instructions guide agent behavior;
they do not provide filesystem access controls.

## Maintain the layout

For a new file, choose the row that describes its purpose. Add a folder only when
it holds real maintained content. Add new human entry points to `docs/README.md`.

For a move, inspect tracked files before moving anything. Update relative Markdown
links, repository-relative references, tooling defaults, tests, and relevant
entries in `tickets/areas.json`. Preserve historical evidence and state explicitly
when a quoted path is historical. Do not move ignored private material alongside
tracked files.

Run the [offline development checks](development/workflow.md#set-up-offline-development),
check local Markdown links and anchors, and inspect ticket impact against the
actual review base. Review `git status --short` and the staged diff before
committing to catch private or generated files.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `.gitignore` | States which course data, scratch files, and generated artifacts stay local. | Ignore rules or tracking policy change. |
| `CONTEXT.md` | Assigns the root context file a glossary-discovery role. | The pointer location or authoritative vocabulary home changes. |
| `docs/development/workflow.md` | Assigns this file the maintained development-instructions role. | The workflow file location or assigned documentation role changes. |
| `docs/development/ticket-workflow.md` | Assigns this file the maintained ticket-procedure role. | The ticket guide location or assigned documentation role changes. |
| `.agents/skills/exam-next-ticket/SKILL.md` | Identifies the repository-scoped ticket skill and its discovery path. | Skill name, location, scope checks, or backlog discovery change. |
| `scripts/tickets.py` | Documents the permanent backlog default and supported operations. | Default backlog location or path-resolution behavior changes. |
| `scripts/ticket_history.py` | Describes recognition of current and historical backlog paths. | Historical location detection or fallback rules change. |
<!-- doc-dependencies:end -->
