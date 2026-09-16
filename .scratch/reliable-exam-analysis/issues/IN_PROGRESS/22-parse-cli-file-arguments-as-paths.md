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
    "commit": "f123e95764569b6e068aff16e06d85e4426ae8d2",
    "checked_at": "2026-09-16T16:51:53+00:00",
    "criteria_digest": "2428a3edd54f601cd73672f9149cc3cde847b43e840be6951ef4bcd7bacfd6ad",
    "checker": "Codex",
    "result": "already_resolved",
    "evidence": [
      "At commit f123e95, argparse converts COURSE_FOLDER and explicit add-exam PATH arguments to pathlib.Path before command dispatch. Focused 16-test input selection suite, full 220-test pipeline suite, 21 ticket-tool tests, and 35 ticket checks passed; git diff --check was clean."
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
