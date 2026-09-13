# 12: Discover intended papers consistently and expose input selection

**What to build:** Make default input discovery include both supported paper locations and show exactly what will be analyzed.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

**Priority:** P2

- [ ] Combine matching papers in the course root and its exams subfolder, deduplicating resolved inputs.
- [ ] Preserve explicit recursive-search behavior and exclude pipeline-managed candidate and accepted output directories.
- [ ] Document relative-input-path precedence and make the selected resolved files visible before processing.
- [ ] Explain that matching TXT/PDF files are treated as papers and provide a documented way to select or exclude unrelated material.
- [ ] Test mixed root/subfolder inputs, explicit files plus folders, duplicates, recursive discovery, and ambiguous relative filenames.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Keep file selection in inputs with explicit course context. This fix can land before extraction; coordinate later relocation.
