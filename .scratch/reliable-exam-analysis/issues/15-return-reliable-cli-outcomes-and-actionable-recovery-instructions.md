# 15: Return reliable CLI outcomes and actionable recovery instructions

**What to build:** Let people and automation distinguish successful processing, partial failure, and export failure.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

**Priority:** P2

- [ ] Return a nonzero exit status when any requested paper fails; retain successful work and list failed inputs.
- [ ] Differentiate skipped cached papers, pending review, rejected candidates, accepted papers, and export failures when those states are available.
- [ ] Report whether recovery needs input correction, review, reprocessing, or only a rebuild.
- [ ] Do not describe an all-failed batch as nothing new to add or imply its requested work succeeded.
- [ ] Test all-success, all-failure, mixed batches, setup errors, and export failure through command-level exit assertions.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Keep outcome rendering and exit status in the CLI. Reusable modules return outcomes or raise defined failures.
