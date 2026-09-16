# 20: Make course and model configuration explicit

```json
{
  "schema_version": 1,
  "id": "20",
  "priority": "P2",
  "queue_order": 8,
  "areas": [
    "configuration",
    "storage",
    "evaluation"
  ],
  "depends_on": [
    "18"
  ],
  "related_to": [],
  "references": [
    "docs/adr/0008-modular-pipeline-architecture.md",
    "pipeline/exam_roi/llm.py",
    "pipeline/exam_roi/storage.py",
    "pipeline/pipeline.py",
    "pipeline/tests/test_explicit_configuration.py"
  ],
  "verification": null,
  "closure": {
    "reason": "implemented",
    "commit": null,
    "replacement": null,
    "reviewed_by": "Codex independent review /root/review_ticket_20",
    "evidence": [
      "Historical completion claim and scope are preserved in this ticket body.",
      "Independent specification review found no material or acceptance-blocking findings across all Ticket 20 criteria.",
      "Focused test_explicit_configuration suite passed 11 tests; full pipeline suite passed 191 tests using the dependency-complete Python runtime."
    ]
  }
}
```

**What to build:** Allow reusable pipeline operations and separately configured model clients without process-global course state or import side effects.

**Architecture:** Follow [ADR 0008](../../../../docs/adr/0008-modular-pipeline-architecture.md); preserve behavior while establishing the interface described here.

- [ ] Pass course paths or a course storage/context instance explicitly instead of relying on mutable module-global destination paths.
- [ ] Create provider and model configuration at startup and pass clients to analysis functions; allow separately configured analyzer and reviewer clients without implementing review policy yet.
- [ ] Read environment defaults and configure console streams in CLI startup; importing reusable modules must not require credentials, exit, create files, or reconfigure streams.
- [ ] Preserve documented environment-variable defaults and CLI behavior, with missing credentials diagnosed only for operations requiring model calls.
- [ ] Expose defined failures from reusable code and map them to user messages at the CLI rather than calling process exit inside reusable modules.
- [ ] Verify two course contexts and two fake provider clients can be exercised in one process without leaking paths or client configuration.
- [ ] Verify rebuild and help remain usable without model credentials; avoid introducing a global configuration singleton under a new name.
