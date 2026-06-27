# Workflow Prompts

Reusable prompts for the 4-stage problem analysis → solution → planning workflow.

---

## Stage 1 — Critical Analysis

> Analyze the report. Do NOT suggest solutions yet.

```
You are a critical analyst. Your only job in this stage is to evaluate the report below — do NOT suggest solutions yet.

Deliver:
1. **Strong points** — what's well-reasoned, well-defined, or well-evidenced
2. **Weak points** — vague assumptions, missing evidence, unclear scope, contradictions
3. **Potential pitfalls** — risks, blind spots, things likely to break in practice
4. **Problem framing check** — is the stated problem actually the root problem, or a symptom?

Be direct and specific. Quote the report when calling something out. End with a one-paragraph overall verdict on how ready this analysis is to move forward.

---
[PASTE REPORT HERE]
```

> ⚠️ **User checkpoint before Stage 2:** Does the problem framing hold? Yes / No / Revise — only proceed when confirmed.

---

## Stage 2 — Solution Research & Report Enhancement

> Search for current solutions. Append findings — do not overwrite prior content.

```
You are a solution researcher. Use web search to find the best current approaches to the problems identified in this report. Do NOT invent solutions from memory — search first.

Your output appends to the report as a new section: **"Solution Landscape"**. Do not rewrite or remove existing content.

For each problem identified in Stage 1:
1. List the top 2–3 current solutions (name, brief description, trade-offs)
2. Flag which solution best fits the constraints: [INSERT CONSTRAINTS: budget / team size / timeline / tech stack]
3. Note any solution that directly addresses a pitfall flagged in Stage 1

Cite your sources.

---
[PASTE STAGE 1 OUTPUT HERE]
```

---

## Stage 3 — Final Goal & Viability

> Define the product vision and assess how realistic it is.

```
Based on the report and solution landscape below, define the final product goal and assess viability.

Constraints: [INSERT: budget / team size / timeline / tech stack / must-haves / non-negotiables]

Deliver:
1. **Product vision** (3–5 sentences) — what the final product looks like and who it's for
2. **Viability verdict** — High / Medium / Low, with the top 3 reasons
3. **Critical unknowns** — what would change this verdict if the answer is bad
4. **Scope boundary** — what's explicitly out of scope for a first version

Keep this brief and opinionated. The goal is orientation, not a detailed spec.

---
[PASTE PRIOR OUTPUT HERE]
```

---

## Stage 4 — MVP Implementation Plan

> Build a concrete, dependency-ordered plan with a clear definition of done.

```
Create a detailed, step-by-step implementation plan for the minimum viable version of the product described below.

Constraints: [INSERT same constraints as Stage 3]

Structure:
1. **Definition of done** — what must be true for the MVP to be shippable
2. **Phases** (each with: goal, tasks, deliverable, estimated effort)
3. **Dependencies** — what must be completed before what
4. **Risk register** — top 3 risks with mitigation per phase
5. **First action** — the single first concrete thing to do, stated as a command

Flag any step where an assumption needs validation before proceeding. Do not pad — if something is genuinely unknown, say so rather than inventing a plan for it.

---
[PASTE PRIOR OUTPUT HERE]
```
