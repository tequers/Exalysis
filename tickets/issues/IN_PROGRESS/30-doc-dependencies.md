# 30: Implement documentation dependency graph core

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
    "docs/development/workflow.md",
    "scripts/doc_dependency_graph.py",
    "scripts/tests/test_doc_dependency_graph.py"
  ],
  "verification": {
    "commit": "a75f7236c819fb7f90dbb9f631be550fcf6b6931",
    "checked_at": "2026-09-19T12:23:01+00:00",
    "criteria_digest": "c47a84ebdab9477f2fa7712bc58780eecbe3b4a76a2823d79634db0635191d24",
    "checker": "GPT-5.6 Sol independent core review",
    "result": "already_resolved",
    "evidence": [
      "Committed core implements the approved parsing, graph and discovery contract. Thirteen pure tests passed; independent review found no substantive core defect. CLI remains a separate ticket31 and is not part of this core completion."
    ],
    "provisional": true
  },
  "closure": null
}
```

**What to build:** The pure parsing, discovery, and graph layer of the approved documentation dependency specification. Ticket 31 completes the CLI, Git snapshots, and artifact I/O. This split keeps each pull request reviewable without reducing the owner's requested implementation.

- [ ] Parse the approved declaration grammar and report coverage, invalid targets, malformed blocks, and duplicate relationships with source locations.
- [ ] Build deterministic review graphs, reverse lookup, bounded impact, rename aliases, and before/after relationship changes.
- [ ] Discover undeclared reference candidates without modifying declarations or claiming semantic completeness.
- [ ] Verify the pure layer against synthetic fixtures and obtain independent review before the CLI layer depends on it.

**Architecture:** `scripts/doc_dependency_graph.py` contains deterministic logic with no Git, filesystem, or CLI dependency. The approved specification remains the contract; ticket 31 supplies I/O.

## Approved implementation and review split

The owner approved ticket 29 and requested full tool implementation on 2026-09-19.
The planned tool and tests exceed the preferred pull request size. Ticket 30 now
covers the independently testable core; ticket 31 covers the CLI and integration.
Both layers remain in the active implementation task. Declaration rollout, CI,
AGENTS, skills, paid calls, and pipeline behavior remain excluded.

Input: explicit snapshot inventories and owner bytes, selected paths, and rename mappings.
Output: validated declarations, coverage diagnostics, graphs, impact selections,
relationship changes, and discovery candidates. No command or file write is introduced by this layer.

## Verification and review

`python -m unittest discover -s scripts/tests -p test_doc_dependency_graph.py -v`
passes 13 pure tests, including raw-byte digests, Unicode, reverse traversal,
cycles, rename aliases, removed/changed relationships, malformed declarations,
unsafe paths, coverage gaps, and discovery provenance. GPT-5.6 Sol independently
reviewed the core against the specification and reported no substantive defect.
The later CLI layer has separate integration tests and review evidence.
