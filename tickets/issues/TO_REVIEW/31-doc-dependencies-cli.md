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
    "scripts/doc_dependency_graph.py",
    "scripts/doc_dependencies.py",
    "scripts/tests/test_doc_dependencies.py"
  ],
  "verification": {
    "commit": "141686e771e2a045676e07830897ffe34c59fb6b",
    "checked_at": "2026-09-19T12:25:26+00:00",
    "criteria_digest": "91f2512a1426b86883ffa734bd749e22badd7af977566ecfab019e922ed2df65",
    "checker": "Codex CLI implementation audit",
    "result": "still_valid",
    "evidence": [
      "Approved pure graph prerequisite30 is implemented and independently reviewed. The committed branch has no doc_dependencies.py or CLI integration tests. Owner authorized completing the approved tool; declaration rollout stays excluded."
    ],
    "provisional": false
  },
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

## Implementation and verification

- `scripts/doc_dependencies.py` supplies the four commands, Git snapshots, safe artifact writes, and text or JSON results.
- `scripts/tests/test_doc_dependencies.py` exercises the CLI with temporary Git repositories. The pure graph tests remain in ticket 30.
- `python scripts/check_tickets.py` passed all 76 tooling tests. Ticket validation reported 0 errors and six existing historical-closure warnings for tickets 01, 02, 05, 07, 10, and 18.
- `python -m unittest discover -s pipeline/tests -p 'test_*.py'` passed all 231 application tests. No live or paid model calls were made.
- Local Markdown link verification passed for 232 links. `git diff --check` passed.
- `python scripts/doc_dependencies.py check --format json` reported 25 required documents and 25 missing declaration blocks, with exit code 1. That failure is expected until declaration rollout.

GPT-5.6 Sol independently reviewed the completed core and CLI and found no remaining blockers.
The review caught error-precedence and Markdown rendering defects. The implementation now
rejects unsafe destinations and unrelated map files before loading declarations, and renders
prose literally. Regression tests cover those fixes. The reviewer inspected the final changes
but did not independently rerun the parent's test suite.

## Related documentation review

The documentation index, workflow guide, specification, and technical reference now state
that the tool exists and declaration rollout remains pending. The workflow links to the
specification because developers need its command and review contract. No dependency
blocks were added or removed. No implementation or enforcement claim was added to an ADR.

## Human review before closure

1. Run `python scripts/doc_dependencies.py --help`. Confirm that `check`, `build`, `impact`, and `discover` are listed.
2. Run `python scripts/doc_dependencies.py check --format json`. Confirm that missing declarations produce `valid: false`, `complete: false`, and exit code 1. The current expected count is 25.
3. Read the command table and workflow in `docs/specs/doc-dependencies.md`. Confirm that the output and review responsibilities match the approved workflow. Declaration rollout and semantic review are still required.

The independent technical review passed. Human output review remains pending, so this ticket
must stay in `TO_REVIEW` until the owner passes that review.
