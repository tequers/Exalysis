# 22: Parse CLI file arguments as paths

```json
{
  "schema_version": 1,
  "id": "22",
  "priority": "P2",
  "queue_order": 22,
  "areas": [
    "configuration",
    "extraction"
  ],
  "depends_on": [
    "20"
  ],
  "related_to": [
    "12"
  ],
  "references": [
    "pipeline/pipeline.py",
    "pipeline/exam_roi/inputs.py",
    "pipeline/tests/test_input_selection.py",
    "scripts/migrate_tickets.py",
    "scripts/tests/test_tickets.py"
  ],
  "verification": {
    "commit": "feaadb6d42a74d71cfb09f69256c8099a9270f80",
    "checked_at": "2026-09-16T16:42:59+00:00",
    "criteria_digest": "d5431f8fdd4dc7e306113a7c6e2cc7955c7dbe95f5f4f93db56a939f5038c019",
    "checker": "Codex",
    "result": "still_valid",
    "evidence": [
      "An offline patched CLI run at commit 6c99977 passed COURSE_FOLDER to setup as Path only after an explicit conversion in main, while args.paths reached cmd_add_exam as raw str values; the command printed COURSE_TYPE=WindowsPath and INPUT_TYPE=str."
    ],
    "provisional": false
  },
  "closure": null
}
```

**What to build:** Convert filesystem arguments to `pathlib.Path` objects at the CLI parser boundary, so command handlers receive paths instead of raw strings.

- [x] Parse `COURSE_FOLDER` as a `Path`.
- [x] Parse every explicit `add-exam` input as a `Path`.
- [x] Pass the parsed course path directly to course setup without converting it again.
- [x] Preserve relative-path resolution, CLI text syntax, and string paths in JSON output.
- [x] Add an offline CLI test that proves course and input arguments reach downstream code as `Path` objects.
- [x] Keep the historical 21-ticket migration test valid when newer structured tickets exist.

**Architecture:** Keep path conversion at the outer CLI boundary. Domain and storage code continue to accept `Path` values, while serialization converts paths to strings where JSON requires it. This ticket does not change input discovery or persisted record formats.

## Evidence and history

Created for the MVP command path after a real-use test showed that users provide filesystem routes while `argparse` retains them as strings until deeper in the command flow.

Implementation parses CLI filesystem arguments with `type=Path`, removes the redundant course-folder conversion in `main()`, and covers both argument types with an offline command-level test. The historical migrator now leaves later structured tickets unchanged while continuing to migrate its original 21-ticket inventory.

Verification completed on 2026-09-16: all 16 input-selection tests, all 220 pipeline tests, all 21 ticket-tool tests, and the 35-test ticket check suite passed offline. `git diff --check` reported no whitespace errors.
