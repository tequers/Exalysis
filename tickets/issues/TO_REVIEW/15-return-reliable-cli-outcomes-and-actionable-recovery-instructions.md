# 15: Return reliable CLI outcomes and actionable recovery instructions

```json
{
  "schema_version": 1,
  "id": "15",
  "priority": "P2",
  "queue_order": 5,
  "areas": [
    "configuration",
    "reports"
  ],
  "depends_on": [],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/pipeline.py",
    "pipeline/tests/test_cli_outcomes.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Let people and automation distinguish successful processing, partial failure, and export failure.

- [x] Return a nonzero exit status when any requested paper fails; retain successful work and list failed inputs.
- [ ] Differentiate skipped cached papers, pending review, rejected candidates, accepted papers, and export failures when those states are available.
- [ ] Report whether recovery needs input correction, review, reprocessing, or only a rebuild.
- [x] Do not describe an all-failed batch as nothing new to add or imply its requested work succeeded.
- [ ] Test all-success, all-failure, mixed batches, setup errors, and export failure through command-level exit assertions.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Keep outcome rendering and exit status in the CLI. Reusable modules return outcomes or raise defined failures.

## Review findings

Automated review found four gaps. No human review is needed until they are fixed.

1. `pipeline/pipeline.py:1120` describes a batch with one skipped paper and one failure as "All 1 requested paper(s) failed." Include skipped inputs when classifying the final batch outcome and add a regression test.
2. `pipeline/pipeline.py:227` maps unrecognized paper failures to `--force`, even when the error requires a distinct `--exam-id` or different model request limits. Add recovery categories for these cases and test the final messages.
3. `pipeline/tests/test_cli_outcomes.py:202` calls setup code before UTF-8 console configuration. The documented Windows test command fails with `UnicodeEncodeError` on the default CP1252 stream. Make the tests independent of the host console encoding.
4. The exit-code table in `README.md:108` omits state failure code 5 even though the CLI returns it.

Review results: all 9 focused tests passed in UTF-8 mode. Four tests errored under the default Windows encoding. Targeted probes reproduced both contradictory CLI messages.
