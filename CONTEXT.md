# Computer Science Exams Pipeline

A solo, file-based study system for university CS exams: a CLI pipeline that ranks topics by exam ROI, feeding a Cowork tutor that teaches them via mastery-gated retrieval practice and the method of loci.

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
_Avoid_: "memory palace" as a generic term once a specific instance is meant — name it (e.g. "the Living Room palace").

**Station**:
A single fixed point within a Palace where one concept's mnemonic Encoding lives. Finite per Palace (the Living Room has 27).

**Encoding**:
The concrete, vivid, bizarre image a student attaches to a Station for one concept. Tagged with the Course/Exam it currently belongs to, so a Station can be identified as eligible for repurposing once that Course/Exam is finished. Evaluated on two axes: **information accuracy** (does the image structurally reflect the concept's defining properties?) and **retrieval power** (is it anchored to the station object, physical, emotionally charged, vivid, specific?). Status tracked as ❌ empty / ⚠️ needs sharpening / ✅ solid.

**Rung**:
One step in a Topic's difficulty ramp (length = D + 1): recognition → guided application → partial exam → full exam question. Gated — a rung isn't shown until the previous one passes.

**Priority Score (ROI)**:
`100 × (F × G × C) / (D × Fmt)` — the ranking that answers "which topic gives the most exam marks per hour of study," computed per Exam from that Exam's own `F`/`G`/`Fmt` (from its past papers) and `C`/`D` (from its own taxonomy).
