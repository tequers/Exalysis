# Development workflow glossary

These terms describe how work is agreed, implemented, and reviewed. The
[development workflow](workflow.md) gives the steps. The
[application glossary](../glossary.md) defines course, exam, topic, and other
product terms.

| Term | Meaning in this workflow |
|---|---|
| Ground truth | The current behavior and constraints established from the checkout, applicable contracts, and observed evidence. Assumptions and intended future behavior remain labeled separately. |
| Shared agreement | The human-approved description of the problem, intended behavior, inputs, outputs, examples, constraints, acceptance criteria, scope, exclusions, and resolved product questions. It bounds implementation. |
| Scope | The behavior and work included in the agreement. Exclusions state what the change will not add. A scope expansion needs approval before implementation. |
| Acceptance criteria | Observable conditions that establish whether the agreed result is complete. Each has a check or a named human judgment. |
| Ticket | A bounded unit of tracked work, with criteria, dependencies, state, and evidence. In this repository, its authoritative record lives under `tickets/issues/`. A ticket can contain a small change's agreement. |
| Specification, or spec | A concise description of a substantial feature's agreed behavior and boundaries. Draft specifications propose work. Approval permits implementation within that scope. Store these under `docs/specs/` when needed and link them from tickets. |
| Architecture decision record, or ADR | A record of a lasting design choice, its context, alternatives, reasoning, and consequences. An approved decision does not prove that its implementation is complete. This repository keeps ADRs in `docs/adr/`. |
| Architecture overview | A description of the implemented system's parts and how they interact. The [current architecture](../architecture.md) separates available behavior from pending work. |
| Decided | The human has approved a choice or agreement. The work may still be unimplemented. |
| Implemented | The code or documents for a change exist at a stated revision. The result may still need verification or review. |
| Verified | A stated check has produced evidence for a stated claim at a stated revision. Verification covers that claim, not every possible behavior or the human's approval. |
| Preflight | The ticket tool's readiness check for prerequisites and current verification. A ready result does not approve scope or start implementation. |
| Independent review | A person or agent other than the implementer compares the actual change and evidence with the agreement. This development review is separate from the pipeline's retained model-review capability. |
| Human review | The developer's assessment of product behavior, content, or environment-specific results that automated checks or an agent cannot decide on their behalf. |
| Done | A ticket state with a recorded closure reason and evidence. It does not by itself mean the change is merged, deployed, or approved for every use. |

Use decided, implemented, and verified as separate claims. For example, a decision
can be approved while its implementation is pending, and an implemented change
can pass offline tests while its content still awaits human review. Record the
revision, checks, and remaining judgments instead of calling all three complete.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `scripts/tickets.py` | Defines implemented ticket states, preflight, and closure evidence. | State transitions or meanings of verification and completion change. |
<!-- doc-dependencies:end -->
