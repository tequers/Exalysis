# 32: Declare documentation dependencies

```json
{
  "schema_version": 1,
  "id": "32",
  "priority": "P2",
  "queue_order": 32,
  "areas": [
    "documentation"
  ],
  "depends_on": [
    "31"
  ],
  "related_to": [
    "29",
    "30"
  ],
  "references": [
    "docs/specs/doc-dependencies.md",
    "docs/specs/doc-dependencies-reference.md",
    "scripts/doc_dependencies.py"
  ],
  "verification": {
    "commit": "66f18d445cbb48bcf0c1d54b04726701e56c968b",
    "checked_at": "2026-09-19T12:40:37+00:00",
    "criteria_digest": "a21c58e5ba14656a62dc71331067727d1cef5df2988da500b173c9d435feba75",
    "checker": "Codex declaration rollout audit",
    "result": "still_valid",
    "evidence": [
      "Owner approved initial declaration rollout. Current check reports 25 missing blocks. Ticket31 is reviewed and DONE. No application or enforcement changes are needed."
    ],
    "provisional": true
  },
  "closure": null
}
```

**What to build:** Add the initial documentation dependency declarations approved by the owner on 2026-09-19.

- [ ] Give every covered document one valid File, Reason, Review when block, with one owner per relationship and no unsupported targets.
- [ ] Review document-to-document and document-to-code relationships against current claims, and record discovery decisions without inventing semantic certainty.
- [ ] Pass current coverage and artifact freshness checks, demonstrate reverse lookup, and report the historical gap in the first comparison.
- [ ] Obtain independent review and human acknowledgment of the initial relationship choices and historical gap before closure.

## Approved scope

Input: the 25 covered documents, their referenced tracked contracts and code, and the approved dependency specification.
Output: concise declarations, accurate rollout status, ignored local Mermaid and JSON maps, and review evidence in this ticket.
The owner passed the tool implementation and explicitly requested these blocks. This is authorization for the agreed initial declaration rollout.

Excluded: runtime behavior, tool behavior, suppressed ADR edits, ticket dependency blocks, AGENTS or skill changes, CI/hooks, and automatic semantic approval.
The Python checker proves structural validity. The independent reviewer checks relationship choices and reasons. The owner resolves open judgments and acknowledges unknown historical edges.
