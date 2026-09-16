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
    "pipeline/tests/test_input_selection.py"
  ],
  "verification": null,
  "closure": null
}
```

**What to build:** Convert filesystem arguments to `pathlib.Path` objects at the CLI parser boundary, so command handlers receive paths instead of raw strings.

- [ ] Parse `COURSE_FOLDER` as a `Path`.
- [ ] Parse every explicit `add-exam` input as a `Path`.
- [ ] Pass the parsed course path directly to course setup without converting it again.
- [ ] Preserve relative-path resolution, CLI text syntax, and string paths in JSON output.
- [ ] Add an offline CLI test that proves course and input arguments reach downstream code as `Path` objects.

**Architecture:** Keep path conversion at the outer CLI boundary. Domain and storage code continue to accept `Path` values, while serialization converts paths to strings where JSON requires it. This ticket does not change input discovery or persisted record formats.

## Evidence and history

Created for the MVP command path after a real-use test showed that users provide filesystem routes while `argparse` retains them as strings until deeper in the command flow.
