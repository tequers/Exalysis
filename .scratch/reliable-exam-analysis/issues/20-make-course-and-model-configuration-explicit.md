# 20: Make course and model configuration explicit

**What to build:** Allow reusable pipeline operations and separately configured model clients without process-global course state or import side effects.

**Blocked by:** 18: Extract report rendering behind a stable package interface.

**Status:** ready-for-agent

**Priority:** P2

**Architecture:** Follow [ADR 0008](../../../docs/adr/0008-modular-pipeline-architecture.md); preserve behavior while establishing the interface described here.

- [ ] Pass course paths or a course storage/context instance explicitly instead of relying on mutable module-global destination paths.
- [ ] Create provider and model configuration at startup and pass clients to analysis functions; allow separately configured analyzer and reviewer clients without implementing review policy yet.
- [ ] Read environment defaults and configure console streams in CLI startup; importing reusable modules must not require credentials, exit, create files, or reconfigure streams.
- [ ] Preserve documented environment-variable defaults and CLI behavior, with missing credentials diagnosed only for operations requiring model calls.
- [ ] Expose defined failures from reusable code and map them to user messages at the CLI rather than calling process exit inside reusable modules.
- [ ] Verify two course contexts and two fake provider clients can be exercised in one process without leaking paths or client configuration.
- [ ] Verify rebuild and help remain usable without model credentials; avoid introducing a global configuration singleton under a new name.
