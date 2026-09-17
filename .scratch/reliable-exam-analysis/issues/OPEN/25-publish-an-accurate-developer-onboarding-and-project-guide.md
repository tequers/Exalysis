# 25: Publish an accurate developer onboarding and project guide

```json
{
  "schema_version": 1,
  "id": "25",
  "priority": "P1",
  "queue_order": 26,
  "areas": [],
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
    "CONTEXT.md",
    "AGENTS.md",
    "docs/adr/0008-modular-pipeline-architecture.md",
    "docs/research/git-and-pull-requests-for-ai-development.md",
    "docs/solid/new-course-setup.md",
    "docs/ticket-workflow.md",
    "pipeline/pipeline.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Give a new developer one documented route from the repository landing page to understanding the current two-stage MVP, its CLI lifecycle and architecture, running the offline checks, selecting a ticket, and following the branch and review workflow. Base every current-behavior claim on the checked-out `mvp-two-stage` implementation and CLI help. The route must not require agent-only instructions or a paid model call.

- [ ] The repository landing page links directly to a contributor guide and a task-based documentation index.
- [ ] The contributor guide covers supported Python versions, environment setup, the full offline checks, ticket selection and preflight, branch creation, focused verification, impact review, and the transition to human review or completion.
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
- Do not move the existing backlog. A later ticket can change its location if the documented location remains confusing after this onboarding path exists.

## Evidence and history

The documentation audit on 2026-09-17 found that all 96 checked local Markdown links resolve. The content is detailed, but the human development workflow has no direct documentation link, and the repository has no contributor guide or task-based documentation index.

The audit also found two correctness problems. The course setup guide says that `add-exam` leaves accepted state and reports unchanged, then its checklist says the same command creates the spreadsheet and JSON report. The modular architecture decision still describes module extraction as proposed, while the production CLI already delegates to the extracted package modules.

This ticket is ready without ticket 08. It must document the present candidate-only behavior accurately and can be updated again when promotion becomes available.

Ticket 26 must consolidate the project branches before this documentation work starts. This guide should describe the branch model that remains after that reviewed cleanup.
