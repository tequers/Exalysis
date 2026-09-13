# 10: Constrain exam IDs to the intended state directory

**What to build:** Keep custom exam identifiers from escaping the course's parsed-record boundary.

**Blocked by:** None (can start immediately).

**Status:** implemented and reviewed (2026-09-12)

**Priority:** P1

- [x] Reject absolute paths, traversal, path separators, platform-invalid filenames, and empty or reserved identifiers with actionable errors.
- [x] Verify the resolved destination remains within the intended state directory before any write, including force-reprocessing paths.
- [x] Preserve valid custom IDs and specify collision and replacement behavior.
- [x] Test traversal, absolute paths, reserved names, collisions, and force-enabled overwrite attempts using temporary directories.

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md). Keep identifier validation at the course persistence/input seam and test resolved containment. This fix can land before package extraction with relocation coordinated later.


## Implementation and verification

- `pipeline/exam_roi/identity.py` validates portable filename IDs and resolved record destinations without CLI or provider dependencies.
- Both `parsed/` and `candidates/` boundaries are checked before processing and after model work. The final save checks its destination again, including forced reprocessing. Redirected directories, symbolic links, and hard-linked records are rejected.
- Automatic collision resolution checks every generated ID and fails when all are occupied. Valid custom IDs retain their spelling. README and command help document custom IDs, automatic normalization, collisions, and replacement.
- Self-review fixed course-root redirection during analysis and preserved actionable validation messages in CLI argument errors. No remaining actionable findings in this change.
- All 103 offline tests pass, including 18 new identity/path tests with temporary directories and no live API calls. Tests cover traversal, absolute paths, invalid and reserved names, exhausted collisions, symlinks, hard links, changed destinations, and successful forced candidate replacement.
- Writer locking and transactional recovery remain ticket 07 work; these checks do not claim protection against concurrent filesystem changes between a check and an operation.
