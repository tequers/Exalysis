---
name: feedback-visual-artifacts
description: Visual artifacts are a consolidation tool — offered after rung 1/2 or on confusion, never before the user tries first
metadata:
  node_type: memory
  type: feedback
---

Do NOT proactively build visual artifacts before the user attempts a topic. The user should try to visualize and understand first. Artifacts are a consolidation or rescue tool, not an intro tool.

**Why:** The user wants to engage with the concept first — attempting to build their own mental model is part of the learning. An artifact shown too early removes that effort. Text-only teaching of highly visual concepts is still inefficient, but the timing matters: it should come after an attempt, not before.

**How to apply:**

**When to offer an artifact:**
1. After rung 1 or rung 2 — as a consolidation aid once the user has engaged with the concept.
2. If the user signals genuine confusion or inability to visualize (e.g., "I can't picture this", repeated wrong answers on spatial/structural questions).
3. If the user explicitly asks for one.

**When NOT to build an artifact:**
- Before the user has attempted the topic at all.
- Proactively at the start of a session just because the topic sounds visual.

**Deciding whether a topic warrants an artifact:**
Use a "visual grade" heuristic:
- **High visual grade** (artifact clearly worth it): clustering, convolution, stereo vision, neural net architecture, feature maps, image pyramids, graph algorithms, spatial transforms.
- **Medium visual grade** (offer after confusion signals): PCA, SVMs, attention mechanisms, backpropagation flow.
- **Low visual grade** (probably not needed): pure math derivations, terminology, classification rules.

For high-grade topics, proactively *offer* an artifact after rung 1/2 ("Want me to build an interactive visualizer to consolidate this?") — but let the user accept. For medium/low, wait for confusion signals or a user request.

**Why:** The user found interactive artifacts useful for consolidation (k-means example) but wants to attempt the concept first. The artifact should feel like a reward/aid after engagement, not a shortcut around it.
