# 25: Publish an accurate developer onboarding and project guide

```json
{
  "schema_version": 1,
  "id": "25",
  "priority": "P1",
  "queue_order": 26,
  "areas": [
    "documentation"
  ],
  "depends_on": [
    "26"
  ],
  "related_to": [
    "08",
    "18",
    "19",
    "20",
    "27",
    "28"
  ],
  "references": [
    "README.md",
    "docs/glossary.md",
    "AGENTS.md",
    "docs/adr/0008-modular-pipeline-architecture.md",
    "docs/research/git-and-pull-requests-for-ai-development.md",
    "docs/guides/new-course-setup.md",
    "docs/development/ticket-workflow.md",
    "pipeline/pipeline.py",
    "docs/development/workflow.md",
    "docs/development/glossary.md",
    "docs/README.md",
    ".agents/skills/exam-next-ticket/SKILL.md"
  ],
  "verification": {
    "commit": "a4d3c464e8dbcb03dfa72c7796096cbaeff6a113",
    "checked_at": "2026-09-19T10:36:44+00:00",
    "criteria_digest": "bdd74c1ff7c55e32d662447d8532c8376ecbb194cf03d2799b88e0abeaf4da59",
    "checker": "Codex shared-workflow audit",
    "result": "still_valid",
    "evidence": [
      "Current guide covers setup, ticket commands, branches and review but lacks a complete approved-agreement-first route, workflow glossary, skills map and explicit enforcement boundaries. AGENTS.md permits features after sharing ground truth while also requiring ticket confirmation. Owner approved the specific documentation plan, narrow AGENTS alignment and subagent implementation. Existing product documentation remains in scope for preservation; no application changes are needed."
    ],
    "provisional": false
  },
  "closure": null
}
```

**What to build:** Give a new developer one documented route from the repository landing page to understanding the current two-stage MVP, its CLI lifecycle and architecture, running the offline checks, selecting a ticket, and following the branch and review workflow. Base every current-behavior claim on the checked-out `mvp-two-stage` implementation and CLI help. The route must not require agent-only instructions or a paid model call.

- [ ] The repository landing page links directly to an internal development guide and a task-based documentation index.
- [ ] The internal development guide covers supported Python versions, environment setup, the full offline checks, ticket selection and preflight, branch creation, focused verification, impact review, and the transition to human review or completion.
- [ ] Offline development setup is complete without provider credentials. Optional live-provider setup is separate and states the approval, cost, privacy, and secret-handling requirements.
- [ ] A current architecture overview explains the production modules, their responsibilities, and the path from exam input to candidate storage and accepted-record reporting.
- [ ] The overview describes the current two-stage MVP as implemented. It labels backlog work, proposed acceptance behavior, and later architecture as pending rather than mixing them into the current flow.
- [ ] The architecture decision for modularization records what has been implemented and what remains pending without rewriting its original decision history.
- [ ] The user and setup guides agree that `add-exam` writes a candidate, does not promote it, and does not create a new ranking from that candidate. Guidance about taxonomy checks and generated reports matches the current accepted-record workflow.
- [ ] The documentation index points readers to the glossary, current architecture, decision records, evaluation contract, ticket workflow, model limits, independent review, staged evaluation, and state recovery guidance.
- [ ] New and substantially revised entry documents use sentence-case headings and plain, direct language. They contain no em dashes or stock AI wording covered by the project's `unslop` guidance.
- [ ] Every local Markdown link resolves, the documented commands match their command-line help, and the full offline project checks pass.

**Architecture:** Treat the checked-out `mvp-two-stage` CLI, its command help, tests, and package modules as the source for current behavior. Keep approved decisions as history, and link to the versioned evaluation contract instead of restating its rules. Describe ticket 08 as pending work rather than documenting candidate promotion as available.

## Scope boundaries

- Do not change pipeline behavior, ticket semantics, scoring, acceptance policy, or provider configuration.
- Do not run a live model or OCR service.
- Keep the permanent backlog in `tickets/`, as established by ticket 27.

## Evidence and history

The documentation audit on 2026-09-17 found that all 96 checked local Markdown links resolve. The content is detailed, but the human development workflow has no direct documentation link, and the repository has no contributor guide or task-based documentation index.

The audit also found two correctness problems. The course setup guide says that `add-exam` leaves accepted state and reports unchanged, then its checklist says the same command creates the spreadsheet and JSON report. The modular architecture decision still describes module extraction as proposed, while the production CLI already delegates to the extracted package modules.

This ticket is ready without ticket 08. It must document the present candidate-only behavior accurately and can be updated again when promotion becomes available.

Ticket 26 must consolidate the project branches before this documentation work starts. This guide should describe the branch model that remains after that reviewed cleanup.

2026-09-19: The owner clarified that this portfolio MVP needs an internal development workflow, not a public contribution guide. Ticket 27 moves that guide to `docs/development/workflow.md` and the permanent backlog to `tickets/`. The earlier evidence above records the terminology and paths at the time of inspection. Ticket 25 remains in `TO_REVIEW` for human content review.

## Approved remaining scope, 2026-09-19

The owner approved extending this ticket into one clear internal workflow for a
portfolio MVP. Existing onboarding and architecture documentation remain useful.
The remaining problem is agreement before implementation: the agent previously
built unnecessary features when the product vision, scope, and expected result
were unclear. The owner explicitly approved the plan and requested implementation
with appropriate subagents. That approval includes the narrow AGENTS.md alignment
listed below. There is no public contributing section.

- [ ] Make `docs/development/workflow.md` the human-readable route from an idea through clarified requirements, approval, implementation, verification, independent review, applicable human review, and merge. Include a small Mermaid overview.
- [ ] Require a shared agreement before implementation: problem, intended behavior, inputs and outputs, examples or expected experience, constraints, acceptance criteria, exclusions, and unresolved questions. A short agreement in the ticket suffices for small changes; substantial features or behavior changes use a specification under `docs/specs/`.
- [ ] Make human approval of that agreement explicit. Resolve questions affecting behavior or scope before implementation. Allow routine implementation choices within scope, but require approval before expanding it. Compare final results with the agreement and report unnecessary additions, missing behavior, or deviations.
- [ ] Describe human, implementing-agent, and independent-reviewer responsibilities. State what tools enforce, what relies on agent instructions, what requires human judgment, and which proposed capabilities are not implemented.
- [ ] Add `docs/development/glossary.md` for shared workflow terms, including specification, ADR, architecture, acceptance criteria, ground truth, and the distinctions between decided, implemented, and verified. Link application language to its existing glossary.
- [ ] Add a concise skills table with triggers and instruction locations. Include the local `exam-next-ticket` and `graft` skills, and relevant optional installed skills such as `grill-with-docs` and `to-spec`. Adapt optional drafting guidance to this repository's concise local documents; do not publish external issues or introduce a global skill dependency.
- [ ] Align AGENTS.md with the approved ground-truth rule and local skill reference without duplicating the full guide. Update the documentation index and only related links necessary for consistency. Preserve accurate setup, CLI, branch, test, and review instructions.
- [ ] Distinguish reusable principles from repository-specific paths. Keep documentation proportionate; do not create an empty specs folder, a public contributor guide, an example feature, dependency tooling, or new application behavior.
- [ ] Verify local links, documented commands and policy consistency, run the required offline checks, obtain an independent review, and leave human content approval in TO_REVIEW.

Input: the owner's approved workflow plan, the current guide, AGENTS.md, the
ticket CLI, local skills, and the existing documentation structure. Output: one
updated workflow guide, one concise workflow glossary, aligned agent instructions
and navigation, plus verification and review evidence. The dependency-tool
specification remains a later task. Do not silently turn proposed automation
into a claim of current enforcement.

## Unified workflow implementation and review, 2026-09-19

Branch `codex/25-shared-workflow` starts at `origin/codex/mvp-two-stage`
commit `c6618ac554f49e49c32b0b25ba225dbcd7796903`. Scope approval is recorded
in `a4d3c46`. The human-readable workflow now starts with an approved agreement,
includes a Mermaid route and roles, and states which checks are enforced by tools.
The workflow glossary distinguishes agreed intent, current implementation, and
verified claims. AGENTS.md points to the same approval rule; the old permission
to implement features after merely sharing ground truth is removed. Existing
approval of a concrete scope counts, and routine implementation choices remain
with the implementer.

Document relationships added or clarified:

- AGENTS.md and the ticket workflow link to the shared-agreement section because ticket eligibility is not human approval of scope.
- The documentation index links to the workflow glossary, approval steps, skills, and enforcement limits so humans and agents can find the same definitions.
- The workflow links to its glossary and the local ticket skill. The skills table distinguishes repository-local instructions from optional personal installations.
- Ticket 25 now relates to 27 because it uses the approved folder layout, and to 28 because it aligns the project-local next-ticket workflow. These are related-work links, not new prerequisites.

The obsolete assertion that next-ticket always ends in TO_REVIEW was replaced
with the actual conditional closure policy. No pipeline code, ticket-tool code,
local or personal skill files, runtime contracts, dependency checker, public
contributor guide, or empty specs directory changed.

Verification:

- `$env:PYTHONIOENCODING='utf-8'`; `python -m unittest discover -s pipeline/tests -p 'test_*.py'`: 231 tests passed.
- `python scripts/check_tickets.py`: 39 tests passed; 28 records, zero errors, six existing missing-review warnings for tickets 01, 02, 05, 07, 10, and 18.
- Local Markdown path and heading audit: 210 links passed across tracked Markdown plus the new glossary, before this evidence section was added.
- `python scripts/tickets.py verify --help`, `move --help`, and `impact --help`, plus `python pipeline/pipeline.py --help` and `python pipeline/pipeline.py "path/to/your/course" add-exam --help`: documented forms checked successfully.
- `git diff --check`: passed. The generated index retains Git's Windows line-ending warning.
- Compared `pipeline/`, `scripts/`, and `.agents/skills/` with base `c6618ac`: unchanged.

GPT-6 Astra at high effort drafted the five documentation/instruction files.
GPT-5.6 Sol at high effort independently audited actual ticket-tool enforcement
and reviewed the draft. It found two wording issues: inaccurate example terms
in the application-glossary pointer, and ambiguous ordering of selection and
approval in the skills table. Both were corrected as recommended. The reviewer
found no agreement, scope-control, or enforcement defect. The parent also read
the full diff and independently checked all 210 local Markdown links.

## Human review of the unified workflow

1. Read `docs/development/workflow.md#agree-before-building`. Confirm the agreement includes what you need to recognize the intended result, and that approval precedes implementation without repeated approval for unchanged scope.
2. Read the roles, review steps, skills table, and enforcement limits. Confirm independent review and human judgment are distinct, and proposed automation is not presented as implemented.
3. Read `docs/development/glossary.md` and the AGENTS.md diff. Confirm the vocabulary and agent rules express the same workflow.

Ticket 25 remains TO_REVIEW until the owner approves this content. Technical
checks and an independent consistency review do not substitute for that judgment.
