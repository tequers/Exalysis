# Course/Exam hierarchy with per-Exam state independence

**Status:** accepted

Before this decision, the pipeline and tutor used flat, ungrouped paths (a single `taxonomy.json`, a single `progress.json`) implicitly scoped to one exam (Computer Vision) with no course dimension — adding a second course's exams would have silently merged its topics into CV's taxonomy and ROI sheet. Generalizing to other courses required deciding where the state boundary sits, especially once it became clear a single Course can have structurally different Exams (e.g. Operating Systems: a Practical exam and a Theory exam, with potentially different syllabi and formats).

We decided on `Courses/<Course>/<Exam>/` as the folder hierarchy, where **Course is purely organizational** (no data of its own) and **Exam is the atomic, fully independent state unit** — each Exam owns its own past-paper corpus, `taxonomy.json`, `parsed/`, ROI spreadsheet, and `progress.json`. Nothing is shared or merged across Exams, even within the same Course.

We rejected sharing a taxonomy at the Course level (for topics that overlap between a course's exams) because it would require reconciling potentially different D/C scores for the same topic across different exam contexts, with no clear rule for doing so. Full independence is simpler and matches how the system already treated "one exam" as the atomic unit — the Course layer just adds an organizing folder above it, without changing that unit.

Computer Vision must be migrated into this structure in place, preserving its live `progress.json` and loci state — it remains the actively-studied exam throughout the refactor, not a fixture rebuilt from scratch.
