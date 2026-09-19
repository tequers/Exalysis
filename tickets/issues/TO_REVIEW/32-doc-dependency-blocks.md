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
    "commit": "53277bcd1bb859ffd1b2934d45adfb6750e0eef7",
    "checked_at": "2026-09-19T12:41:22+00:00",
    "criteria_digest": "a21c58e5ba14656a62dc71331067727d1cef5df2988da500b173c9d435feba75",
    "checker": "Codex declaration rollout audit",
    "result": "still_valid",
    "evidence": [
      "Owner approved the initial blocks. The clean checkout contains the implemented tool and no real declaration blocks; 25 owners require initial authoring."
    ],
    "provisional": false
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

## Relationship changes and discovery review

This first rollout adds 162 unique relationships across 25 covered documents.
No previous declarations existed, so none were removed. Every added pair's reason
and review trigger live in its owning document; those blocks are the authority.
The generated map is an ignored local view, not a second maintained relationship list.

- Architecture and ADR 0008 link to their stated module boundaries so a code query finds both accounts.
- ADR 0007 links to year selection, ID validation, and identity tests. README links to that ADR because the current behavior differs from the accepted decision.
- Runtime guides link to the modules and contracts behind their commands, guarantees, or formulas. Scoring now distinguishes candidates, accepted evidence, and the inactive connection-refresh helper.
- Development guides link to the ticket tools, CI configuration, scoped skills, and repository policy they describe. Excluded files are targets only; they receive no blocks.
- The two specification documents share one pair, owned by the technical reference under Unicode ordering for mutual reliance.
- The dated branch-consolidation record has an explicit empty block. Its statements are historical evidence, not promises about current runtime behavior.

Discovery and independent review added 22 pairs after the initial authoring pass. The remaining 47 discovery
candidates are intentionally not all declarations:

| Suggestions | Review decision |
|---|---|
| Task-index links and further-reading links | Keep navigation without duplicating every link as a review relationship. Status-bearing index claims have declarations. |
| Historical plan, branch-audit paths, and the README's suppressed portfolio decision | Preserve dated evidence. Current code changes must not rewrite historical claims. |
| Repository root-file inventory and glossary pointers | These identify locations or entry points; this rollout does not make each filename a separate semantic contract. Existing policy and workflow relationships cover the maintained placement rules. |
| AGENTS, CONTEXT, and README mentioned in the dependency coverage table | These are scope examples, not assertions about their contents. They do not need a pair merely because the spec names them. |

Discovery also reports 220 unresolved literal references. These include command
strings, branch names, extensions, field names, generated course filenames, local
skill paths, historical paths, and shortened names such as pipeline.py. They are
visible review warnings, not 220 missing tracked files or declarations. The author
inspected the distinct warning texts; a separate link-and-anchor audit checked the
actual Markdown links. No private files were added to silence discovery.

## Known drift and human decisions

- ADR 0007 remains accepted but unimplemented. Its dated note and the README expose the mismatch. The existing ticket 13 now records that its proposed year policy must be reconciled with ADR 0007 before approval. No filename behavior or decision was changed.
- The scoring guide had stale claims about direct accepted writes, automatic earlier-paper refresh, and pending storage recovery. These now describe the current implementation; the formula and evaluation contract are unchanged.
- Current structural coverage cannot reconstruct older declarations. The first comparison must report all 25 older owners as unknown and remain incomplete even after human acknowledgment.
- CI hooks, automatic completion gates, and changes to agent instructions remain outside this rollout.

## Verification

- `python scripts/doc_dependencies.py check`: exit 0, 25 of 25 owners covered, 64 nodes, 162 relationships.
- `python scripts/doc_dependencies.py build` and `python scripts/doc_dependencies.py check --against-artifacts .scratch/doc-dependencies`: local map generation and freshness checks pass. Maps remain ignored.
- `python scripts/doc_dependencies.py impact --file pipeline/exam_roi/identity.py --format json`: finds README, ADR 0007, ADR 0008, architecture, and the recovery guide through reverse lookup.
- `python -m unittest discover -s pipeline/tests -p 'test_*.py'`: 231 tests passed; no live calls.
- `python scripts/check_tickets.py`: 76 tooling tests passed, 0 ticket errors, six existing historical-closure warnings for 01, 02, 05, 07, 10, and 18.
- Local Markdown audit: 156 links and their Markdown anchors passed across the 25 covered documents.
- `git diff --check`: passed.

## Human review before closure

1. Read the Dependencies blocks in README, architecture, ADR 0007, and the scoring guide. Confirm that each reason and trigger describes a useful review obligation, and inspect other changed blocks in the PR.
2. Run `python scripts/doc_dependencies.py build`, then `python scripts/doc_dependencies.py check --against-artifacts .scratch/doc-dependencies`. Expect exit 0 and open the local graph.md to inspect the map and relationship table.
3. Run `python scripts/doc_dependencies.py impact --base 66f18d445cbb48bcf0c1d54b04726701e56c968b --head HEAD --format json`. Expect exit 3 with valid true, complete false, and 25 older owners missing declarations. Review the changed documents manually and acknowledge that historical relationships cannot be recovered from this map.
4. Acknowledge the ADR 0007 mismatch and its follow-up in ticket 13. The rollout does not resolve that product decision. Confirm the navigation and historical exclusions above before closure.

## Independent review

GPT-5.6 Sol reviewed the declarations, ownership, reasons, triggers, discovery
omissions, status corrections, and follow-up record. Final review passed with no
semantic blocker. The review added the missing ADR 0008 runtime-contract pair and
clarified two placement-policy reasons. The implementer also corrected mutual
specification ownership and narrowed dependency-installation triggers.

`impact --staged --format json` returned exit 3, valid true, complete false, and
all 25 historical owners without blocks. It reported exactly 162 added pairs and
no removed relationships. That is the expected first-rollout result, not a passing
historical coverage check. Human acknowledgment remains pending.
