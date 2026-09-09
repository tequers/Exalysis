# Computer Science Exams Pipeline

A solo, file-based study system for university CS exams: a CLI pipeline that ranks topics by exam ROI, feeding a Cowork tutor that teaches them via mastery-gated retrieval practice and spaced review. The method of loci is an optional add-on, not a dependency.

## Language

**Course**:
A university subject (e.g. "Computer Vision", "Operating Systems"). Purely an organizational grouping in `Courses/<Course>/` — it owns no taxonomy, priority, or progress state of its own.
_Avoid_: using "exam" to mean the course as a whole (older docs say "Exam: Computer Vision (RWTH Aachen)" — that's naming the Course, not an Exam).

**Exam**:
A specific examination within a Course, e.g. Computer Vision's one exam, or Operating Systems' Practical exam vs its Theory exam. The atomic, fully independent unit of study state: each Exam owns its own past-paper corpus, `taxonomy.json`, `parsed/` exemplars, ROI spreadsheet, and `progress.json` mastery ledger. Nothing is shared or merged across Exams, even within the same Course — a topic tested in two Exams gets scored independently in each.
_Avoid_: conflating with Course; avoid "subject" or "module" for this term.

**Topic**:
A single examinable concept within an Exam's taxonomy (e.g. "Edge Detection"), scored on difficulty (D), connection value (C), and tagged with prerequisites. Lives in that Exam's `taxonomy.json` — not shared across Exams.

**Palace**:
One memory-palace instance mapped to a real physical location the student owns (e.g. the living room), holding a fixed number of Stations. Palaces are **shared global infrastructure across every Course and Exam** — not duplicated per course — because the constraint is real locations owned, independent of what's being studied. When a Palace fills, a new physical location becomes a new Palace (its own file), never a bigger single file.
_Scope_: Palace, Station and Encoding belong to the **optional loci add-on**. No other part of the system depends on them — mastery, coverage, sequencing and review are complete without any `loci/` files, and from `TUTOR_SYSTEM_PROMPT_v9` the add-on fires only for list-like material and only on offer. Do not treat these terms as core study-state vocabulary.
_Avoid_: "memory palace" as a generic term once a specific instance is meant — name it (e.g. "the Living Room palace").

**Station**:
A single fixed point within a Palace where one concept's mnemonic Encoding lives. Finite per Palace (the Living Room has 27).

**Encoding**:
The concrete, vivid, bizarre image a student attaches to a Station for one concept. Tagged with the Course/Exam it currently belongs to, so a Station can be identified as eligible for repurposing once that Course/Exam is finished. Evaluated on two axes: **information accuracy** (does the image structurally reflect the concept's defining properties?) and **retrieval power** (is it anchored to the station object, physical, emotionally charged, vivid, specific?). Status tracked as ❌ empty / ⚠️ needs sharpening / ✅ solid.

**Rung**:
One step in a Topic's difficulty ramp (length = D + 1): recognition → guided application → partial exam → full exam question. Gated — a rung isn't shown until the previous one passes.
_Not rungs_: the `[Probe]` and `[Worked example]` of **first contact** run before rung 1 on a new topic and are ungraded and ungated — they precede the gate rather than forming part of the ramp.

**Lesson**:
One bounded unit of work in a session — due review, plus one Topic advanced by 1–3 rungs, plus any mastery event. It has a stated size up front and an explicit end. The next Lesson is chosen from how this one went, and recorded in the ledger's `next_session` block so the following session starts without re-planning.

**Priority Score (ROI)**:
`100 × (F × G × C) / (D × Fmt)` — the ranking that answers "which topic gives the most exam marks per hour of study," computed per Exam from that Exam's own `F`/`G`/`Fmt` (from its past papers) and `C`/`D` (from its own taxonomy).
