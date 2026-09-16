# Course/exam-type hierarchy with per-exam-type state independence

**Status:** accepted. The state boundary stands. The folder layout below is now a convention only because [ADR 0006](./0006-course-folder-as-cli-argument.md) made the CLI take its working folder as an argument.

Before this decision, the pipeline and tutor used flat, ungrouped paths (a single `taxonomy.json`, a single `progress.json`) implicitly scoped to one exam type (Computer Vision) with no course dimension. Adding another course's exams would have silently merged its topics into CV's taxonomy and ROI sheet. Generalizing to other courses required deciding where the state boundary sits, especially once it became clear that a single Course can have structurally different exam types, such as Operating Systems practical exams and theory exams, with different syllabi and formats.

We decided on `Courses/<Course>/<EXAM_TYPE>/` as the folder hierarchy. **Course is purely organizational** and owns no data. **Exam Type is the atomic, fully independent state unit.** Each Exam Type owns one past-paper corpus, one `taxonomy.json`, `parsed/`, an ROI spreadsheet, and `progress.json`.

`EXAM_TYPE` and `EXAMS` are different levels. An `EXAM_TYPE` groups individual `EXAMS`, and every exam in that group must be of the same type. Each `EXAM_TYPE` has exactly one `taxonomy.json`. The pipeline builds and updates that taxonomy using all exams in the group. It must never share or merge the taxonomy across different exam types. For example, all theory exams contribute to one theory `taxonomy.json`, while all practical exams contribute to a separate practical `taxonomy.json`. An individual exam does not get its own taxonomy.

We rejected sharing a taxonomy at the Course level because different exam types may have different topics or assign different D/C scores to the same topic. The exam-type boundary avoids having to reconcile those differences. The Course layer only organizes exam-type folders.

Computer Vision must be migrated into this structure in place while preserving its live `progress.json` and loci state. Its exam type remains the active unit of study throughout the refactor, not a fixture rebuilt from scratch.
