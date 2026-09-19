# 31: Implement the documentation dependency CLI and Git integration

```json
{
  "schema_version": 1,
  "id": "31",
  "priority": "P2",
  "queue_order": 31,
  "areas": [
    "documentation"
  ],
  "depends_on": [
    "30"
  ],
  "related_to": [
    "29"
  ],
  "references": [
    "docs/specs/doc-dependencies.md",
    "docs/specs/doc-dependencies-reference.md",
    "scripts/doc_dependency_graph.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Complete the owner's approved documentation dependency tool using ticket 30's parsing and graph layer.

- [ ] Provide check/build/impact/discover commands with the exact approved flags, JSON contract, exit codes, and focused text output.
- [ ] Read current, index, and committed Git snapshots safely; retain removed/renamed relationships and distinguish staged, unstaged, endpoint, and merge-base comparisons.
- [ ] Generate deterministic local Mermaid/JSON maps and reject stale artifacts, unsafe paths, and misleading success after I/O failures.
- [ ] Verify CLI behavior with offline temporary Git repositories, update implementation-status docs, and obtain independent review and the required human output review.

**Architecture:** Keep Git/filesystem I/O in `scripts/doc_dependencies.py` and use the pure graph module from ticket 30.

## Scope agreement

The owner approved the specification and explicitly requested implementation.
This is the second implementation layer, split for pull request review size.
Input: tracked declarations and explicit file or Git comparison selections.
Output: the CLI, integration tests, and accurate implementation-status documentation.
Excluded: declaration rollout, CI/hooks, AGENTS or skill changes, automatic semantic approval, paid calls, and pipeline behavior.

The real repository must report missing declarations until the later rollout;
passing synthetic tests must never be described as complete repository coverage.
