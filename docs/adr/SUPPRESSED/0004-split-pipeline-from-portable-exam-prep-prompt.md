# Split the repo into `pipeline/` (the deliverable) and `prompts/` (a portable exam-prep bridge)

**Status:** suppressed. [ADR 0005](../0005-portfolio-cleanup-and-repo-split.md) moved `prompts/` to its own repository and removed the archived tutor systems from this repository.

Before this decision the repo was one tangled system: a provider-agnostic CLI pipeline sitting
alongside a tutoring layer built as Claude-Code Skill bundles (YAML frontmatter, slash-command
invocation) plus a separate Claude-Cowork-specific prompt per course, covering two study modes
(a deep understanding tutor and an exam-prep drill mode) that deliberately shared no state. That
shape was reasonable for personal daily use but unreadable as a portfolio/thesis project, and
"prompts you can use with every LLM" is not true of a system built entirely on one vendor's
Skill/Cowork packaging.

We decided to split the repo into two independent parts. **`pipeline/`** is the actual
deliverable — the CLI that turns past exam papers into a ranked study priority (it was already
provider-agnostic; this pass only consolidated it into one location and fixed a path bug that
followed from a stale duplicate copy). **`prompts/`** is a single portable system prompt covering
exam-prep mode only, rewritten to name no product or slash-command system, that reads the
pipeline's own output (`taxonomy.json`, `parsed/*.json`, the ROI ranking) directly — it derives
its archetype/playbook map live rather than depending on a separate hand-authored per-course
mapping script. The deep-understanding tutor, the `loci` memory-palace add-on, and the old
Claude-Skill/Cowork-specific exam-prep implementation are preserved under `_archive/`, not
deleted — real design thinking went into them and a thesis narrative benefits from showing work
that was deliberately set aside, not erased.

## Considered options

- **Generalize both study modes** — rejected. The project's stated goal is the pipeline; carrying
  two modes with a "share no state" rule into the portable version would import that complexity
  for no reader benefit.
- **Keep the archetype-mapping script layer** (`archetypes_map.py` / `archetypes_postprocess.py`)
  as a required step before the portable prompt runs — rejected. It's hand-authored judgment per
  course, already diverged into two independently-forked, non-shared scripts across the two
  example courses. Making the prompt derive archetypes live from parsed questions removes the
  least-generalizable, least-shared part of the old system from the boundary entirely.
- **Delete the superseded systems outright** instead of archiving — rejected for the deep tutor
  (real, still-referenced design work); considered more seriously for the old exam-prep
  implementation since it's directly superseded rather than set aside, but archived anyway for
  consistent treatment.
