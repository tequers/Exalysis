# 06: Add an independent model review of candidate analyses

**What to build:** Offer a configurable evidence-based review stage that challenges candidate analyses before acceptance.

**Blocked by:** 02: Apply the evaluation contract and validate candidate analyses; 03: Validate question marks and supported exam scoring structures; 05: Preserve question context and respect model request limits.

**Status:** ready-for-agent

**Priority:** P1

- [ ] Provide the reviewer with source evidence, the evaluation contract, and the candidate analysis; allow a separately configured model or provider.
- [ ] Check extraction omissions, unsupported claims, mark allocation, topic consistency, and difficulty/connection rubric application.
- [ ] Return structured findings with source evidence, severity, and an explicit disposition; model agreement alone must not establish correctness.
- [ ] Do not silently rewrite candidates or let a reviewer approve its own corrections; review revised candidates through the configured workflow.
- [ ] Bound correction attempts and send unresolved disagreements to a visible needs-review state.
- [ ] Record reviewer model, contract version, findings, and whether review was enabled; reviewer failure cannot masquerade as a pass.
- [ ] Test correct candidates, seeded defects, disagreements, malformed reviews, unavailable reviewers, and retry exhaustion.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Consume candidate and contract representations through an evaluation interface. Keep reviewer results distinct from the acceptance decision and persistence commit.
