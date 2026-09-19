# 30: Implement the approved documentation dependency tool

```json
{
  "schema_version": 1,
  "id": "30",
  "priority": "P2",
  "queue_order": 30,
  "areas": [
    "documentation"
  ],
  "depends_on": [
    "29"
  ],
  "related_to": [
    "28"
  ],
  "references": [
    "docs/specs/doc-dependencies.md",
    "docs/specs/doc-dependencies-reference.md",
    "docs/development/workflow.md"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Implement the approved offline `scripts/doc_dependencies.py` specification. The owner passed ticket 29 and explicitly requested implementation on 2026-09-19.

- [ ] Implement declaration validation, reverse lookup, discovery, deterministic Mermaid and JSON generation, and check/build/impact/discover commands with the approved flags and exit codes.
- [ ] Preserve deleted and renamed relationships across explicit Git snapshots; report historical gaps, truncation, malformed input, and stale artifacts without false success.
- [ ] Verify the acceptance checklist with offline synthetic Git repositories, including unsafe paths, unmerged state, snapshot separation, and interrupted or stale maps.
- [ ] Update implementation-status documentation accurately and obtain independent review. Record exact check evidence and remaining rollout limitations.

**Architecture:** The two specification files are the approved contract. Use the Python standard library and separate testable parsing/graph behavior from Git and filesystem I/O.

## Scope agreement

Input: tracked Markdown declarations, explicit file selections or Git comparisons, and the approved specification.
Output: the CLI and focused tests, with accurate status documentation and review evidence.
Excluded: authoring dependency blocks across existing documentation, CI/hooks, AGENTS or skill changes, automatic semantic approval, code-import graphs, paid calls, and pipeline behavior.

The absence of declarations in the current repository must remain a visible coverage failure. Synthetic fixtures establish tool correctness without pretending the rollout is complete.
