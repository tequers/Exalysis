# 18: Extract report rendering behind a stable package interface

**What to build:** Create the first internal package seam while preserving the existing CLI and semantic exports.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

**Priority:** P2

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md); preserve behavior while establishing the interface described here.

- [ ] Establish characterization checks for intended CLI and report behavior using synthetic course data and isolated temporary output.
- [ ] Keep the current script invocation working from both the repository root and the pipeline working directory.
- [ ] Move XLSX and ranked JSON rendering into one reports module with explicit destinations and a supplied snapshot; retain orchestration outside rendering.
- [ ] Keep current score values, order, worksheet content, and public output shape unchanged; document known defects rather than making them new permanent requirements.
- [ ] Rendering must not read course globals, decide acceptance, call a model, or mutate taxonomy.
- [ ] Verify semantic workbook cells and JSON data rather than binary workbook identity; separate relocation from functional fixes.
- [ ] Record the initial package interface and verify imports without adding a framework or speculative module hierarchy.
