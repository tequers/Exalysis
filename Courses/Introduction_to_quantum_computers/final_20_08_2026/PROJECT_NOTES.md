# Project Notes — Introduction to Quantum Computing (final_20_08_2026)

Per-exam quirks, overrides, and dead paths. Read at session start; overrides defaults.

## Overrides

- **2026-08-11 — No end-of-Lesson continue/stop check.** User wants teaching to run
  straight through Lessons without pausing to ask "continue or stop?" — only stop when
  they explicitly say so. Keep grading and advancing topics; don't offer the boundary.

- **2026-08-11 — Confidence ratings disabled.** User asked to stop being prompted for
  low/ok/high confidence after each graded answer. Explained the tradeoff once (it feeds
  the hypercorrection loop); user confirmed. Do not ask for confidence going forward.
  Attempt records write `"confidence": "not_collected"` instead. The calibration line
  and high-confidence-error routing are effectively off for this exam.

- **2026-08-12 — Unitary Matrices conjugation gap: resolved, worth reusing the drill.**
  The recurring bug (dropping the complex conjugate specifically on entries that have a
  nonzero real part, e.g. treating 1+i as unchanged while correctly flipping a pure
  imaginary entry like 2i → -2i) responded well to two small bridge questions on invented
  2×2 diagonal complex matrices *before* the real graded attempt, run under the
  difficulty controller's "two FAILs → bridge question" rule. First graded attempt after
  the bridge applied the fix correctly but was left incomplete (computed T† only, never
  checked T†T=I) — worth remembering that fixing the recall bug doesn't guarantee a
  complete answer; watch for the demonstration being cut short right after a fix lands.
  Boss-check on a harder, non-diagonal exemplar passed clean. If a similar sign/step-drop
  bug shows up on a future topic, this bridge-then-boss-check pattern is a good template.

- **2026-08-12 — Sessions routinely run past the `/study-run` board once "keep going"
  kicks in.** With the no-continue/stop-check override active, a Lesson that finishes the
  planned board tends to keep pulling in due reviews and open the next topic in the same
  sitting (mirrors 2026-08-11's log). `/study-run close` already treats this as normal —
  no action needed, just don't be surprised when actual session scope exceeds the planned
  board by a wide margin.

- **2026-08-14 — Matrix notation, then LaTeX, for all math.** User first asked for matrices
  written in matrix layout (not inline tuples), then a few turns later asked for LaTeX
  specifically ("that's so annoying to read" re: ASCII/unicode math). Use LaTeX for all math
  going forward, including matrices (`\begin{pmatrix}...\end{pmatrix}` or similar) — this
  supersedes the plain-ASCII matrix format used earlier the same session.

- **2026-08-14 — Both due reviews failed the same way: right numbers, one component missing
  or misordered.** Tensor Products (tensor-product order reversed on a 3-factor product) and
  Quantum Measurement (post-measurement state omitted entirely) both lost mastery on review
  the same session. Neither was a fatal conceptual error in the sense of a wrong belief —
  both got the substantive math right and then didn't finish the answer as asked. Worth
  watching for on future reviews of any topic: check the WHOLE question got answered, not
  just the numeric core.

- **2026-08-14 — Hamiltonian Dynamics rung 3 exposed shaky eigen-decomposition mechanics.**
  Needed heavy scaffolding to: get the sign right in H−λI for a negative eigenvalue, recall
  that a 2×2 matrix has two eigenvalues (not one), distinguish the trivial null-space
  solution from the real eigenvector, and re-derive |0⟩ in the |+⟩,|−⟩ basis (prerequisite
  content from Unitary Matrices, which is marked mastered but wasn't independently re-tested
  today). Rungs 4–6 need this machinery numerically — a short consolidation drill before
  continuing the ramp is recommended (see `progress.json` → `next_session`).

- **2026-08-17 — Exam conditions confirmed by course staff (email).** Verbatim facts:
  - **Electronic exam via Dynexite, in person**, on the exam room's computers. The practice
    e-tests are *Moodle*; the exam is *Dynexite*. Different system.
  - **Closed book.** Permitted: paper and pens, plus **one A4 page of handwritten notes,
    single sided, handwritten not printed**. Forbidden: calculators, phones, any other
    electronic device, any printout.
  - **Questions similar to the e-tests, except avoiding heavy calculations and Python.**
    No programming required.
  - Staff provided an **example exam from an earlier year**:
    `https://rwth-aachen.sciebo.de/s/bEPbnRDHwL3bYlh` — **downloaded and parsed 2026-08-18**
    as `exams/Summer Semester 2024.txt`. See the 2026-08-18 entry below; it changed the time
    budgets and added five archetypes.
  - Old e-tests re-opened in Moodle under "exam preparation". **Warning from staff:** solving
    them may change the homework point total Moodle displays; they don't count for bonus
    points. Check the total before using them.

  *Consequences already applied to the exam-prep mode:* `archetypes.json` gained an
  `exam_format` block; heavy-calculation archetypes are down-weighted via `exam_likelihood`
  (`shor-order-finding` 18→7.2, `qec-threshold` 10→5.0) rather than cut, since the topics can
  still appear in lighter form; drill variants must keep numbers doable without a calculator;
  and `/cheat-sheet` was added to build the permitted A4 sheet from the playbooks and the
  accumulated traps.

  *Note for deep mode:* none of this changes the ramp or mastery rules. It changes what a
  final-rung question should look like — no heavy arithmetic — and it means notation on the
  A4 sheet should match the glossary exactly.

- **2026-08-18 — The 2024 real paper is parsed, and it does NOT look like the practice e-tests.**
  `exams/Summer Semester 2024.txt` (the paper the staff linked) ran through the pipeline:
  19 questions, **100 marks exactly**, matching its stated maximum. Compare the practice
  e-tests: 129 and 113 questions at 182 and 310 marks.

  **The real exam is ~19 substantial multi-part questions at ~5.3 marks each — not a
  rapid-fire e-test.** At 90 minutes that is ~4.7 min per question and 54 s per mark, against
  the e-tests' ~45 s per question. Every time budget in `archetypes.json` was re-derived on
  that basis; the earlier derivation (22 s/mark from an assumed 246-mark paper) was 2.4x too
  fast and is recorded as superseded in `budget_basis`.

  **Five archetypes exist only in the real paper**, never in the e-tests — evidence that the
  e-tests under-cover the exam: `bv-circuit-modification` (does this change still compute the
  same s?), `oracle-circuit-to-function` (read a CNOT/Toffoli circuit, name f),
  `uniform-superposition-check`, `compute-norm`, `dft-period`.

  **Four topics are absent from the real paper entirely** — Probabilistic Matrices,
  Probability Distribution Vectors, Physical Qubit Implementation, Bomb Tester — despite
  ranking high off the e-tests. Archetypes absent from 2024 are down-weighted to 0.6.

  *Caveat:* one paper is one sample. Absence from 2024 is weak evidence of absence in 2026,
  which is why these are down-weighted rather than cut.

## Schema notes

- `progress.json` uses a pre-hierarchy schema (no `course`/`exam` top-level fields,
  no `rank`/`D`/`rungs`/`current_rung`/`rung_status` — uses `target`, `coverage`,
  and flatter per-topic fields: `difficulty_d`, `rung`, `marks`, `marks_secured`).
  Treating `target.name` as Course, folder name `final_20_08_2026` as Exam.
  `exam_date` added at top level 2026-08-11 (2026-08-20).
