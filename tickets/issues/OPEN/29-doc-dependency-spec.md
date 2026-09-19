# 29: Specify documentation dependency checking

```json
{
  "schema_version": 1,
  "id": "29",
  "priority": "P2",
  "queue_order": 29,
  "areas": [
    "documentation"
  ],
  "depends_on": [
    "25",
    "27"
  ],
  "related_to": [
    "28"
  ],
  "references": [
    "docs/development/workflow.md",
    "docs/development/glossary.md",
    "docs/repository-structure.md",
    "docs/README.md"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** A reviewable specification for the proposed offline `scripts/doc_dependencies.py` tool. The owner approved step 1 and requested appropriate drafting and independent-review agents. No tool implementation is authorized by this ticket.

- [ ] Publish `docs/specs/doc-dependencies.md` as draft, not implemented, and link it from the documentation index.
- [ ] Define the shared vocabulary, concise File / Reason / Review when declarations, coverage and exclusions, relationship ownership, and reverse lookup without mirrored declarations.
- [ ] Specify exact inputs, commands, outputs, versioned JSON and Mermaid examples, Git comparison behavior, validation and exit codes, including removed and renamed files and relationships.
- [ ] Separate mechanical discovery candidates and structural checks from semantic judgment; require explicit reasons for added or removed relationships and independent review with unresolved issues escalated to the human.
- [ ] Explain before-edit and before-review use, generated-map maintenance, focused output and token costs, functional organization, acceptance tests, and implementation non-goals.
- [ ] Review the specification independently, run the repository checks, and leave substantive design approval in TO_REVIEW.

**Architecture:** Follow the existing internal workflow and repository structure. Existing ticket metadata remains authoritative for ticket relationships. Keep tool-specific vocabulary in the specification and link the shared workflow glossary.

## Approved scope

Input: the owner's dependency-workflow discussion, current documentation, existing ticket tooling, and the approved internal workflow.
Output: one specification, a navigation link, and this ticket's review evidence.
Excluded: Python implementation, dependency-block rollout, generated maps, CI/hooks, AGENTS changes, skill changes, application behavior, and external issue publishing.

## Evidence and history

2026-09-19: The owner requested implementation of step 1 only and delegated drafting and review. Base is origin/codex/mvp-two-stage at dd2b502d4b2bc411e1e82553e6d7a6cf2e97805b. The repository currently has no documentation dependency specification or checker. This specification must be approved before implementing the later stages.
