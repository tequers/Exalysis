# 13: Resolve ambiguous sitting years and support metadata correction

**What to build:** Avoid treating historical dates in questions as sitting years and correct cached metadata without paid extraction.

**Blocked by:** 08: Gate promotion into accepted course state; 11: Make paper identity portable and detect stale cached inputs.

**Status:** ready-for-agent

**Priority:** P2

- [ ] Use an explicit precedence policy for overrides, filename metadata, directory metadata, and paper evidence; do not accept arbitrary first-year mentions as authoritative.
- [ ] Leave unresolved or conflicting evidence undated and show the candidates and their sources.
- [ ] Document supported year bounds and academic-year conversion, including ambiguous ranges.
- [ ] Allow a sitting-year correction for an existing accepted paper without repeating extraction or changing its identity.
- [ ] Record metadata correction history and regenerate labels and reports consistently.
- [ ] Test history-question dates, conflicting filename/header years, academic-year ranges, undated papers, and cached corrections.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Keep evidence-based sitting resolution in inputs and commit corrections through the accepted-revision workflow.
