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
    "20"
  ],
  "references": [
    "README.md",
    "docs/glossary.md",
    "AGENTS.md",
    "docs/adr/0008-modular-pipeline-architecture.md",
    "docs/research/git-and-pull-requests-for-ai-development.md",
    "docs/guides/new-course-setup.md",
    "docs/development/ticket-workflow.md",
    "pipeline/pipeline.py"
  ],
  "verification": {
    "commit": "7d57f897563e62b7c6a77ccee633a7925dd50054",
    "checked_at": "2026-09-17T18:14:31+00:00",
    "criteria_digest": "8eeb95d0c768e37cbe35260301d445f3f2b4970858f54bc93c78bf518b9e737d",
    "checker": "Codex next-ticket, 2026-09-17",
    "result": "still_valid",
    "evidence": [
      "pipeline.py help confirms the current two-stage add-exam command saves validated candidates and leaves independent review unavailable in the MVP.",
      "README.md and docs/solid/new-course-setup.md still need one contributor route, consistent candidate-only reporting guidance, and a task-based documentation index.",
      "docs/adr/0008-modular-pipeline-architecture.md requires a current implementation-status update while preserving the original decision history."
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
