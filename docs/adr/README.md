# Architecture decisions

These files record accepted architecture decisions. Acceptance does not prove
implementation. Read each decision's status and the [current architecture](../architecture.md)
when planning or reviewing MVP work.

| ADR | Decision |
|---|---|
| [0001](0001-course-exam-hierarchy.md) | One Course folder contains one exam type. |
| [0006](0006-course-folder-as-cli-argument.md) | Every command names its Course folder as the first argument. |
| [0007](0007-one-record-per-paper-and-the-sitting-year.md) | Require year-prefixed exam filenames; current CLI enforcement is pending. |
| [0008](0008-modular-pipeline-architecture.md) | Pipeline responsibilities move behind testable module interfaces. |

## Suppressed decisions

[Suppressed decisions](SUPPRESSED/README.md) record designs that current decisions replaced. They provide history but do not define the current MVP.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `docs/adr/0001-course-exam-hierarchy.md` | Summarizes the course state-boundary decision. | Decision title, status, path, or scope changes. |
| `docs/adr/0006-course-folder-as-cli-argument.md` | Summarizes the explicit course-folder command decision. | Decision title, status, path, or scope changes. |
| `docs/adr/0007-one-record-per-paper-and-the-sitting-year.md` | Indexes the filename decision and its implementation gap. | Naming decision or implementation status changes. |
| `docs/adr/0008-modular-pipeline-architecture.md` | Summarizes the module-boundary decision. | Decision title, status, path, or scope changes. |
| `docs/adr/SUPPRESSED/README.md` | Distinguishes current decisions from suppressed history. | A decision is suppressed, restored, or replaced. |
<!-- doc-dependencies:end -->
