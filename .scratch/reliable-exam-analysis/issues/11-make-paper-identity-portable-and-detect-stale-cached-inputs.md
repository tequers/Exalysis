# 11: Make paper identity portable and detect stale cached inputs

**What to build:** Keep accepted papers identifiable after relocation and make source/configuration changes visible.

**Blocked by:** 08: Gate promotion into accepted course state; 10: Constrain exam IDs to the intended state directory.

**Status:** ready-for-agent

**Priority:** P2

- [ ] Preserve paper identity when a course folder or source location moves; do not rely on absolute source paths alone.
- [ ] Detect source-content and processing-configuration changes and offer explicit reprocessing instead of silently skipping stale analysis.
- [ ] Record content identity, provider/model, contract, and processing-version provenance.
- [ ] Define duplicate-content handling without silently merging genuinely distinct sittings; explain ambiguous duplicate decisions.
- [ ] Provide explicit cached-paper withdrawal/removal behavior and explain that deleting a source does not automatically remove its accepted contribution.
- [ ] Migrate existing identities without duplicating accepted papers and retain prior accepted revisions until replacements pass acceptance.
- [ ] Test relocation, edited content, changed settings, duplicate copies, distinct sittings, and legacy records.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Own persisted paper identity and provenance in storage/domain records; keep source location distinct from stable record identity.
