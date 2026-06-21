# Topic ROI — MVP v1.0 (manual pilot)

*A stripped-down version of the full system, designed to be done by hand with a notebook (or one spreadsheet) and ~5 past exams. Goal: find out whether the ROI idea actually surfaces the right topics before investing in the full pipeline. The complete model lives in `Topic_ROI_Exam_Analysis_System.md` — graduate to it only if this pilot feels useful.*

---

## What's cut for v1.0

To keep it doable manually, this version drops the three heaviest pieces:

- **No prerequisite graph / PageRank.** "Node value" becomes a single 1–3 gut-check score.
- **No recency weighting / decay math.** Just look at your last ~5 exams and assume the format is roughly stable.
- **No normalized probabilities or hours.** Every input is a simple 1–5 integer you can eyeball.

You lose precision; you keep the core idea — **value over effort**.

---

## The v1.0 formula

$$\text{Priority} = \frac{F \times G \times C}{D \times \text{Fmt}}$$

Higher score = study earlier. All five inputs are small integers you assign per topic.

| Symbol | Question to ask | Scale |
|---|---|---|
| **F** — Frequency | In how many of your last ~5 exams did it appear? | 1–5 (just the count) |
| **G** — Grade weight | How many marks is it typically worth? | 1 = few marks · 3 = moderate · 5 = a whole big question |
| **C** — Connection | Does learning it help you answer *other* topics? | 1 = isolated · 2 = helps a couple · 3 = foundational, unlocks many |
| **D** — Difficulty | Hours to go from zero → exam-ready (see scale below) | 1–6 (use the hour-interval table; see "Scoring D" section) |
| **Fmt** — Format depth | How is it tested? | 1 = multiple choice / recognise · 2 = short answer / explain · 3 = write code / proof from scratch |

$F$, $G$, $C$ push the score **up** (value); $D$ and $\text{Fmt}$ push it **down** (cost). $C$ in the numerator is what lets a hard-but-foundational topic still rank high.

### Scoring D — hour-interval scale

"Exam-ready" = able to correctly answer the exam's format for this topic (MCQ, short answer, or write code/proof). Not production mastery.

| D | Study hours (focused, distraction-free) | Feel |
|---|---|---|
| 1 | < 30 min | A single definition or formula you just look up and remember |
| 2 | 30 min – 1 h | One short reading + a few practice problems |
| 3 | 1 – 3 h | Half a study session; concept + a worked example or two |
| 4 | 3 – 6 h | A full study session; multiple sub-skills to combine |
| 5 | 6 – 15 h | Two or three sessions; real practice needed to internalise |
| 6 | > 15 h | Multi-day; complex enough to require spaced repetition |

Use **Phase 1 / Phase 2 Claude prompts** below to estimate D instead of guessing — the baseline is always "absolute beginner (no prior CS knowledge)" so scores stay comparable across topics and students.

---

## Worked example (verified)

Scoring five topics from a hypothetical CS course:

| Topic | F | G | C | D | D (hours) | Fmt | **Priority** |
|---|---|---|---|---|---|---|---|
| Big-O notation | 5 | 2 | 3 | 3 | 1–3 h | 1 | **10.0** |
| Pointers / memory | 5 | 4 | 3 | 5 | 6–15 h | 3 | **4.0** |
| Sorting algorithms | 4 | 3 | 2 | 4 | 3–6 h | 2 | **3.0** |
| Recursion | 4 | 3 | 2 | 5 | 6–15 h | 3 | **1.6** |
| Regular expressions | 2 | 2 | 1 | 4 | 3–6 h | 2 | **0.5** |

*(D values re-scored on the new 1–6 hour scale assuming an absolute-beginner baseline.)*

The ranking tells a believable story: **Big-O** wins — frequent, foundational, and cheap because it's only ever tested lightly (MCQ/recognise). **Pointers** is worth the most raw marks but its high difficulty and code format pull it to 2nd. **Regex** is rare and isolated — study it last or skip it. That ordering matching your intuition is exactly the signal you're testing for.

---

## How to run the pilot (about one afternoon)

1. **Gather** your last ~5 past exams (PDF or text).
2. **Extract topics** — paste each exam into Claude Sonnet with the prompt below to get a topic-per-question list.
3. **Build the table** — list every distinct topic in one column (merge duplicates like "pointers" and "pointer arithmetic" into one row).
4. **Score** each topic 1–5 on F, G, C, D, Fmt. Trust your gut; don't agonise.
5. **Compute** Priority = (F×G×C) / (D×Fmt) for each row and sort descending.
6. **Sanity check** — does the top look right? If the topics *you* know matter are near the top, the method works. If something obviously important sits at the bottom, see "Reading the results."

A spreadsheet makes step 5 trivial: put the formula `=(F*G*C)/(D*Fmt)` in a column and sort.

---

## Extraction prompt for Claude Sonnet

Run this once per exam. It does the tedious parsing so you only have to do the scoring.

> You are helping me analyse a past exam. From the exam text below, list every distinct question. For each one give me a single row: **topic** (a short canonical name — reuse the same name for the same concept), **marks** (or "?" if not stated), and **format** (one of: `mcq`, `short_answer`, `write_code_or_proof`). If a question spans two topics, output two rows. Keep topic names consistent so I can group them. Output as a simple table.
>
> Exam text:
> `<<paste one exam>>`

After doing all exams, optionally paste the combined tables back and ask: *"Group these into a deduplicated topic list, and for each topic tell me how many of the exams it appeared in and its typical marks."* That hands you the F and G columns; you fill in C, D, Fmt by judgement.

---

## Using Claude to score D (two-phase approach)

Guessing D by gut is error-prone. Two short prompts give you a calibrated, repeatable score.

**Why two phases?** Phase 1 uses an absolute-beginner baseline so scores are *objective and comparable across all topics*. Phase 2 personalises — it asks what you already know and shrinks the estimate by that delta. Running Phase 1 first also gives you a ceiling you can reason against.

---

### Phase 1 — Absolute-beginner estimate (run once per topic)

> You are estimating how long a complete beginner (zero prior CS knowledge) needs to reach exam-passing competency on a specific topic.
>
> **Topic:** `{topic name}`
> **Course:** `{course name and level, e.g. "Introduction to Computer Science, 1st year university"}`
> **Exam format for this topic:** `{mcq | short_answer | write_code_or_proof}`
> **Typical marks:** `{marks or "unknown"}`
>
> "Exam-ready" means the student can correctly answer the exam's format for this topic at a passing level. Not production mastery, not full understanding — just enough to score the marks.
>
> Respond with:
> 1. **Hour estimate** — a specific number or narrow range of focused study hours
> 2. **D bucket** — one of: `<30min (D=1)` · `30min–1h (D=2)` · `1–3h (D=3)` · `3–6h (D=4)` · `6–15h (D=5)` · `>15h (D=6)`
> 3. **Rationale** — 2 sentences: why this bucket, what drives the time
> 4. **Sub-skills needed** — bullet list of what the student must acquire to be exam-ready

---

### Phase 2 — Personalise based on what you already know (run after Phase 1)

Paste Phase 1's response, then add:

> The student reports their current knowledge of this topic: `{describe what you already know — concepts, tools, languages, prior courses}`
>
> Given this prior knowledge, adjust the D estimate for **{topic}**. Focus only on the remaining gap to exam-readiness — what still needs to be learned or practised.
>
> Respond with: updated hour estimate, updated D bucket, and a 1-sentence rationale for the adjustment.

---

### Tips for reliable scores

- **Run Phase 1 the same way for every topic** — same course context, same format framing. Consistency matters more than precision.
- **Phase 2 is optional** — skip it for topics you're confident you know nothing about (Phase 1 is already the right estimate). Use it when you have partial knowledge.
- **If Claude gives a surprisingly high D**, check the Fmt column — a topic tested as MCQ might genuinely be D=2 even if the full subject is hard. The exam format caps the required depth.
- **Batch it** — paste a list of 5–10 topics into one Phase 1 prompt and ask Claude to score them all in a table. This is much faster than one at a time and keeps estimates consistent relative to each other.

---

## Reading the results

- **Top of the list = study first.** These are your high-yield core.
- **A "wrong" ranking is useful data, not a failure.** If an important topic ranks low, check which input caused it — usually you under-rated **C** (it's more foundational than you scored) or over-rated **D**. Adjust and re-sort. The act of finding that mistake is the method working.
- **If the whole ranking feels random**, the approach may not fit your course — stop here, you've spent an afternoon, not a week.
- **If it feels right**, graduate to the full model (`Topic_ROI_Exam_Analysis_System.md`) for recency weighting, a real prerequisite graph, and the LLM scoring pipeline.

---

*v1.0 is intentionally crude. Its only job is to answer one question — "does ranking topics by value-over-effort point me at the right things?" — cheaply enough that finding out costs an afternoon.*
