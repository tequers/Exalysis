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
    "docs/README.md",
    "docs/specs/doc-dependencies.md"
  ],
  "verification": {
    "commit": "a7b83a56109329513687635ffb04cbc503381e47",
    "checked_at": "2026-09-19T11:21:30+00:00",
    "criteria_digest": "eca7e3d83a6e0f0179df319b934c405cf6e174241c625bab8fb289ef4134b99a",
    "checker": "Codex specification audit",
    "result": "still_valid",
    "evidence": [
      "No documentation dependency specification or checker exists at the approved MVP base. Owner authorized specification-only work and independent review; implementation and rollout remain excluded."
    ],
    "provisional": false
  },
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

## Specification and independent review

The draft is `docs/specs/doc-dependencies.md`. The documentation index adds one
link labeled draft, not approved or implemented. Tool-specific vocabulary stays
in the specification and shared workflow terms link to the existing glossary.
No application code, Python tool, dependency blocks, generated maps, AGENTS,
skills, or enforcement changes are included.

GPT-6 Astra at high effort drafted the specification. GPT-5.6 Sol at high effort
reviewed it independently against the approved scope and existing workflow.
The parent also reviewed the full document. Review corrected seven contract
ambiguities: missing direct-query paths, JSON shapes and provenance, canonical
digests, interrupted artifact writes, bootstrap review, unresolved discovery
references, and coverage of committed plus pending changes. Final review also
clarified discovery evidence ownership and which files become graph nodes.
The reviewer reports no remaining substantive defect or scope expansion.

Relationships introduced by this documentation change:

- The documentation index links to the draft so humans can find and review it.
- The specification relies on the workflow, its glossary, and the folder policy
  for approval, shared terms, and artifact placement. These are ordinary links;
  this ticket does not roll out authoritative dependency declarations.
- Ticket 29 references the specification as its deliverable. Tickets 25 and 27
  are prerequisites because they establish the workflow and layout; ticket 28
  is related because future agent integration must remain project-local.
- No existing document relationship was removed.

Verification on this branch:

- `$env:PYTHONIOENCODING='utf-8'`; `python -m unittest discover -s pipeline/tests -p 'test_*.py'`: 231 passed.
- `python scripts/check_tickets.py`: 39 passed; 29 ticket records, zero errors, six existing unreviewed-closure warnings for tickets 01, 02, 05, 07, 10, and 18.
- A temporary local Markdown path and anchor audit checked 216 links with zero errors. Fenced illustrative examples were excluded from link validation.
- The specification's JSON example parses successfully. Proposed commands are specifications, not executable commands in this checkout; their behavior has not been tested or implemented.
- `git diff --check`: passed, with Git's existing Windows LF-to-CRLF notices.
- `git diff --name-only dd2b502 -- pipeline scripts .agents`: empty; runtime and tool code and local skills are unchanged.

## Required human review

1. Read the scope and declaration sections in `docs/specs/doc-dependencies.md`.
   Confirm coverage includes the root README and maintained docs, with the stated
   exclusions, and that one owner per pair with explicit reasons fits your work.
2. Read commands, Git comparisons, focused outputs, and the review sequence.
   Confirm the proposed inputs/outputs, historical-gap handling, local generated
   maps, and relationship-change reporting are the workflow you want.
3. Confirm the acceptance criteria and implementation boundary. Approval here
   accepts the design; the Python implementation and declaration rollout require
   their own approved work. This ticket remains TO_REVIEW pending your judgment.
