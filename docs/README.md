# Documentation by task

Use the [development workflow](development/workflow.md) for a complete route through offline
setup, agreement and approval, ticket selection, implementation, checks, review, and merge.

| I want to... | Read |
|---|---|
| Decide where a file belongs | [Repository structure](repository-structure.md) |
| Understand the application vocabulary | [Application glossary](glossary.md) |
| Understand workflow terms such as spec, ADR, and verified | [Development workflow glossary](development/glossary.md) |
| Agree on a change before implementation | [Shared agreement and approval](development/workflow.md#agree-before-building) |
| View file and documentation relationships | [Published dependency map](development/dependency-map.md), with its source commit and refresh instructions |
| Inspect the documentation dependency checker | [Specification and usage](specs/doc-dependencies.md), initial declarations authored; semantic review remains required |
| Choose an agent skill or check what tools enforce | [Skills](development/workflow.md#use-skills-for-the-task) and [enforcement limits](development/workflow.md#know-what-enforces-the-workflow) |
| Trace the current two-stage pipeline and find its modules | [Current architecture](architecture.md) |
| Set up a course and inspect a candidate | [New course setup](guides/new-course-setup.md) |
| Understand the ranking's purpose and limits | [Scoring methodology](guides/scoring-methodology.md) |
| Check the authoritative evidence and evaluation rules | [Evaluation contract 1.2.0](../pipeline/exam_roi/contracts/evaluation-v1.2.0.md) |
| Understand a design decision | [Architecture decision index](adr/README.md), including [modularization and its current status](adr/0008-modular-pipeline-architecture.md) |
| Select, verify, or move a ticket | [Ticket workflow](development/ticket-workflow.md) and [current backlog](../tickets/TICKET_STATUS.md) |
| Choose a branch and prepare a review | [Development workflow](development/workflow.md#choose-the-branch-base) and [branch consolidation record](research/branch-consolidation-2026-09-17.md) |
| Split a large change or plan recovery | [Git and pull request research](research/git-and-pull-requests-for-ai-development.md), with its historical examples labeled |
| Run an approved provider-specific smoke test | [GLM testing](guides/glm-testing.md) |
| Configure model request budgets | [Model request limits](guides/model-request-limits.md) |
| Understand the retained reviewer implementation | [Independent review](guides/independent-review.md), unavailable in the MVP CLI |
| Capture, audit, or replay evaluation evidence | [Staged evaluation](guides/staged-evaluation.md), separate from normal processing |
| Recover after an interrupted write or diagnose course state | [Course state recovery](guides/course-state-recovery.md) |

The [architecture overview](architecture.md#pending-work) separates available
behavior from pending acceptance and calibration work. The
[architecture decision index](adr/README.md) separates current decisions from
suppressed history.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `docs/architecture.md` | Describes the boundary between available and pending features. | Architecture status or pending capability descriptions change. |
| `docs/specs/doc-dependencies.md` | Advertises dependency checking and its rollout status. | Tool availability, declaration coverage, or usage entry points change. |
| `docs/guides/independent-review.md` | Labels the retained reviewer as unavailable in the MVP CLI. | Production review availability changes. |
| `docs/development/workflow.md` | Names the development route, required skills, and enforcement limits. | Workflow stages, skill requirements, or enforcement claims change. |
| `docs/adr/README.md` | Directs readers to the current-versus-suppressed decision index. | Decision index location or status classification changes. |
<!-- doc-dependencies:end -->
