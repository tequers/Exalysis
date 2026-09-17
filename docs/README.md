# Documentation by task

Use the [contributor guide](../CONTRIBUTING.md) for a complete route through offline
setup, ticket selection, implementation, checks, and review.

| I want to... | Read |
|---|---|
| Understand the project vocabulary | [Glossary](../CONTEXT.md) |
| Trace the current two-stage pipeline and find its modules | [Current architecture](architecture.md) |
| Set up a course and inspect a candidate | [New course setup](solid/new-course-setup.md) |
| Understand the ranking's purpose and limits | [Scoring methodology](../pipeline/docs/Topic_ROI_Exam_Analysis_System.md) |
| Check the authoritative evidence and evaluation rules | [Evaluation contract 1.2.0](../pipeline/exam_roi/contracts/evaluation-v1.2.0.md) |
| Understand a design decision | [Decision records](adr/), including [modularization and its current status](adr/0008-modular-pipeline-architecture.md) |
| Select, verify, or move a ticket | [Ticket workflow](ticket-workflow.md) and [current backlog](../.scratch/reliable-exam-analysis/TICKET_STATUS.md) |
| Choose a branch and prepare a review | [Contributor workflow](../CONTRIBUTING.md#choose-the-branch-base) and [branch consolidation record](research/branch-consolidation-2026-09-17.md) |
| Split a large change or plan recovery | [Git and pull request research](research/git-and-pull-requests-for-ai-development.md), with its historical examples labeled |
| Configure model request budgets | [Model request limits](../pipeline/docs/model-request-limits.md) |
| Understand the retained reviewer implementation | [Independent review](../pipeline/docs/independent-review.md), unavailable in the MVP CLI |
| Capture, audit, or replay evaluation evidence | [Staged evaluation](staged-evaluation.md), separate from normal processing |
| Recover after an interrupted write or diagnose course state | [Course state recovery](course-state-recovery.md) |

The [architecture overview](architecture.md#pending-work) separates available
behavior from pending acceptance and calibration work. Approved decision records
preserve their original reasoning; their dates and implementation updates matter.
