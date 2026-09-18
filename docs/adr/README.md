# Architecture decisions

The files in this directory define the current architecture. Read these decisions when planning or reviewing MVP work.

| ADR | Decision |
|---|---|
| [0001](0001-course-exam-hierarchy.md) | One Course folder contains one exam type. |
| [0005](0005-portfolio-cleanup-and-repo-split.md) | This repository contains only the exam analysis pipeline. |
| [0006](0006-course-folder-as-cli-argument.md) | Every command names its Course folder as the first argument. |
| [0007](0007-one-record-per-paper-and-the-sitting-year.md) | Each past paper has one record and an explicit sitting year. |
| [0008](0008-modular-pipeline-architecture.md) | Pipeline responsibilities move behind testable module interfaces. |

## Suppressed decisions

[Suppressed decisions](SUPPRESSED/README.md) record designs that current decisions replaced. They provide history but do not define the current MVP.
