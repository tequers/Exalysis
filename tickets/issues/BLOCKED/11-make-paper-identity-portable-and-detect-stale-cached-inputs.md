# 11: Make paper identity portable and detect stale cached inputs

```json
{
  "schema_version": 1,
  "id": "11",
  "priority": "P2",
  "queue_order": 16,
  "areas": [
    "storage",
    "configuration"
  ],
  "depends_on": [
    "08",
    "10"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/identity.py",
    "pipeline/exam_roi/storage.py",
    "pipeline/tests/test_exam_identity.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Keep accepted papers identifiable after relocation and make source/configuration changes visible.

- [ ] Preserve paper identity when a course folder or source location moves; do not rely on absolute source paths alone.
- [ ] Detect source-content and processing-configuration changes and offer explicit reprocessing instead of silently skipping stale analysis.
- [ ] Record content identity, provider/model, contract, and processing-version provenance.
- [ ] Define duplicate-content handling without silently merging genuinely distinct sittings; explain ambiguous duplicate decisions.
- [ ] Provide explicit cached-paper withdrawal/removal behavior and explain that deleting a source does not automatically remove its accepted contribution.
- [ ] Migrate existing identities without duplicating accepted papers and retain prior accepted revisions until replacements pass acceptance.
- [ ] Test relocation, edited content, changed settings, duplicate copies, distinct sittings, and legacy records.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Own persisted paper identity and provenance in storage/domain records; keep source location distinct from stable record identity.
