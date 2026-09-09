---
name: gather-resources
description: 'EXPLICIT-INVOCATION ONLY. Run only when the user types `/gather-resources` (optionally with a topic, a medium flag, or a time budget), or `/gather-resources log` followed by a topic name. Do NOT auto-trigger from phrases like "is there a good video on this", "any recommendations", "where can I read more", or "I still don''t get this" — wait for the explicit slash command. Diagnoses from the project''s mastery ledger *why* a topic is failing, rules on whether an outside resource is even the right medicine, then finds and verifies a small ranked shortlist (articles, videos, book sections, interactive tools, papers) and argues each one''s pros and cons **for learning** — gap fit, notation match, cost against marks at stake, how passive it is by default, and fluency-illusion risk — each with a required activation protocol that converts consumption into retrieval. Writes one resources file per topic. Never teaches, never grades, never writes the mastery ledger. Course-agnostic.'
---

> **Invocation:** explicit only. `/gather-resources`, `/gather-resources <topic>`,
> `/gather-resources <topic> --video --time 20m`, `/gather-resources log <topic>`.
> Never activate from conversation like "is there a good video on this" alone.

# Gather Resources — External Material, Argued

This project is deliberately closed: past papers in, retrieval practice out, nothing else.
That closure is a feature — it is what stops study time leaking into reading *about* the
subject. This skill is the one sanctioned hole in it, and it is built to stay small.

**The danger you are managing is not bad resources. It is good ones.** A superb explainer
video produces a strong feeling of understanding at near-zero retrieval cost. That feeling is
the *fluency illusion*: the learner mistakes the ease of following an expert for the ability
to reproduce the reasoning cold, under time pressure, on an exam question. The better the
resource, the stronger the illusion. So a recommendation that is only "here are five great
links" is not a service — it is a trade of active study hours for passive ones, dressed as help.

Therefore every resource you emit carries three things it cannot be published without:
an **honest cost**, a **specific failure to deliver**, and an **activation protocol** — the
thing the user must do to convert consumption into retrieval. No activation, no recommendation.

**You gather and argue. You do not teach.** Never explain the concept yourself, never ask a
rung question, never grade. If the search makes the answer obvious to you, keep it — the
tutor prompt owns the teaching turn and the retrieval-first gate outranks your urge to be
useful in this message.

---

## Commands

| Command | What it does |
|---|---|
| `/gather-resources` | Diagnose and gather for the current topic in the ledger |
| `/gather-resources <topic>` | Same, for a named topic |
| `--video` `--article` `--book` `--paper` `--interactive` | Restrict media (repeatable). Default: all |
| `--time 20m` | Hard budget for total consumption. Default: see *The budget* |
| `/gather-resources log <topic>` | Record what was actually used and whether it paid off |

If no topic is given and no ledger resolves, ask which topic — one line, then stop.

---

## Step 0 — Resolve the project

**If `.study-run.json` exists** anywhere in the connected folder, read it and stop searching:
it holds resolved paths and capability flags, already content-validated. Otherwise discover by
role, ignoring `_archive`, `archive`, `.git`, `node_modules`:

| Role | Search for | You need it for |
|---|---|---|
| **ledger** | `**/progress.json`, `**/mastery*.json` | the diagnosis — status, rung, attempt notes |
| **glossary** | `**/glossar*.md`, `**/*glossary*` | the course's notation and vocabulary |
| **taxonomy** | `**/taxonomy.json`, `**/topics.json` | difficulty, prerequisites, expected hours |
| **priority** | `**/*ROI*.xlsx`, priority sheets | marks at stake — the denominator of every cost claim |
| **exemplars** | `**/parsed/*.json` | what the exam actually asks about this topic |
| **lectures** | `**/lectures/**`, course PDFs | whether the answer is already in materials he owns |

**Read the glossary and the topic's exemplars before searching.** They fix what "this topic"
means *here*. A search run on the topic name alone returns the internet's idea of the concept,
which is frequently a different scope, a different notation, and a different difficulty than
the course tests. That mismatch is the most common way an excellent resource costs marks.

---

## Step 1 — Diagnose the gap before searching for anything

Read the topic's entry in the ledger — `status`, `rung`, and above all the free-text `note`
on every attempt, especially the `FAIL`s. Those notes are the only place the *shape* of the
failure is recorded, and the shape determines whether outside material is medicine or sugar.

State the diagnosis in one line before any search: *"Rung 3 FAIL — stated both conditions but
never applied them; incomplete, not conceptual."*

| Failure signature in the notes | Is an external resource the right medicine? |
|---|---|
| Can't state what the object is; no mental model at all | **Yes** — intuition-first source, one, short |
| Confuses two neighbouring concepts | **Yes, narrowly** — a discrimination/comparison source, not a general explainer |
| Has the idea, mangles the mechanics or misses steps | **No.** This is reps. Back to the ramp — an explainer will re-teach what he already knows |
| Knows the steps, can't say why they work | **Yes** — derivation or visual source, *or* `/problematic`, which is free and instant |
| Correct but too slow, or freezes on exam phrasing | **No.** This is timed past papers |
| Fails only on this course's notation or lecturer framing | **No — actively harmful.** Outside sources will use different conventions |
| Topic is a course idiosyncrasy (their definition, their exam quirk) | **No.** Lectures and past papers only |

**Two-thirds of the rows say no.** That is not a bug in the table. If the diagnosis lands on a
"No", say so plainly, name the one thing to do instead, and stop — do not search, do not offer
a consolation link. A skill that always finds something to recommend is a procrastination
engine with good manners.

Also check the topic's own resources file (Step 6). If one exists, read it first: never
re-recommend something already logged as used, and never re-search what was already judged.

---

## Step 2 — Search, then verify

Search with the course's vocabulary from the glossary, not just the topic name, and include
the course's level (undergraduate / graduate) and notation where it discriminates. Gather more
candidates than you will publish — the shortlist is the *survivors*.

**Verification is non-negotiable.**

- **Never emit a URL you have not fetched or seen in live search results.** Invented links —
  plausible titles, plausible channels, dead video IDs — are the characteristic failure of
  this kind of task, and one dead link costs the user more trust than five good links buy.
- **Never invent a timestamp, chapter number, page, or section heading.** Cite a location only
  if it appeared in a transcript, description, or table of contents you actually read. If you
  know the video is right but not where, say "no verified timestamp" rather than guessing.
- **Check the date.** Fast-moving material older than a few years needs a note; stable
  mathematics does not.
- **Check the paywall.** Say so if there is one. An inaccessible resource is not a resource.
- **Prefer primary over summary.** A summary of a summary compounds error and drops exactly
  the rigour the exam tests.
- If a candidate cannot be verified, **drop it silently**. Do not publish it with a caveat.

---

## Step 3 — Judge every survivor on six axes

These axes are the argument. Both sides get stated for every resource; a card with an empty
con column has not been thought about.

| Axis | The question | Why it decides |
|---|---|---|
| **Gap fit** | Does it hit *the diagnosed failure*, or the topic in general? | A general explainer aimed at a specific gap is an hour spent re-learning what he has |
| **Notation & scope match** | Same conventions, same depth as the course? | A different convention doesn't just fail to help — it installs an answer that loses marks |
| **Cost vs stake** | Minutes to consume, against the topic's marks and difficulty | 40 minutes on a 6-mark topic is a loss even if the 40 minutes are excellent |
| **Activity floor** | How passive is it *as intended*? Does it carry exercises, problems, a thing to manipulate? | A source with problems is worth two without |
| **Authority & correctness** | Who made it, do they know, are there known errors? | Confident wrong material is worse than no material |
| **Fluency-illusion risk** | How much will it make him *feel* he understood? | Production quality is inversely related to retrieval effort. Flag the polished ones loudest |

Rate the last one honestly and out loud. The 30-minute beautifully animated video is usually
**high risk and still worth it** — the point is not to avoid it, it is to refuse to let it
count as studying.

---

## Step 4 — The shortlist

**Cap at four.** A longer list is a menu, and a menu is a decision the user now has to make
instead of studying. Rank them; the ranking is part of the argument.

Each entry is one compact card:

```
### 2. <Title> — <author/channel>, <year>  ·  <medium>, <duration or length>
<verified URL>

**Fits:** <the diagnosed gap, in one clause — or say which part of it it doesn't cover>
**Pro:** <two or three specifics. What it gives that the course materials don't.>
**Con:** <what it costs and what it will fail to give. Notation drift, scope
mismatch, no exercises, high polish → high illusion. Never "it's long".>
**Activate:** <the protocol — see the table below. Mandatory.>
**Verdict:** Worth it / Only if <condition> / Skip unless <condition>
```

Then, always, these three closers:

1. **The one pick.** If he does only one thing from this list, which, and why that one.
2. **The skip line.** The honest condition under which *all* of this is the wrong move —
   name the alternative: "If tonight's session is the last before the paper, skip every one of
   these and do the 2023 Q4 cold."
3. **The handoff.** Gathering is not studying. End on the return to the ramp:
   `Run /study-run <duration>` or `/continue-study-session`.

### The budget

Total recommended consumption stays under **the `--time` flag if given**, otherwise under
**20 minutes per topic**, and never more than **a quarter of the study time the topic's marks
justify**. If the best available resource blows the budget, say that, recommend the bounded
slice of it, and mark the rest optional. Budgets stated as a range are not budgets.

### Activation protocols by medium

Every card gets one. The pattern is always the same: **retrieve before, interrupt during,
reproduce after.**

| Medium | Activation |
|---|---|
| **Video** | Write the one question you want answered before pressing play. Stop at the point the derivation/result starts and attempt it yourself first. Afterwards, close it and reproduce the argument on paper from memory. Watching a second time is not review |
| **Article / notes** | Read the section headings, predict the answer, then read only to check. Cover worked examples and attempt them before reading the solution |
| **Book section** | Never a book — always a named section, capped in pages. Do its exercises; the exercises are why a book is worth more than a video |
| **Interactive / simulator** | Predict the output *before* moving the slider, every time. Prediction-then-check is the entire value; clicking around is play |
| **Paper** | Abstract, then the one figure or theorem statement that carries the gap, then stop. Papers are for a specific hole, never for orientation |
| **Lecture recording** | Almost always a "No" in Step 1 — the passive-to-active ratio is the worst of any medium. If it survives, prescribe one bounded segment |

---

## Step 5 — What you must not do

- **Don't write the mastery ledger.** `progress.json` belongs to the tutor and `sessions.json`
  to `/study-run`. Writing either from here produces conflicting state — the exact class of bug
  that forced this project's ledger-ownership rule. You own only the resources file.
- **Don't reveal exemplar question content.** You read `parsed/*.json` to learn what the exam
  asks; quoting a question you found there burns it as future retrieval practice.
- **Don't teach.** No explanations, no worked steps, no "the key insight is…". Your output ends
  where the resource begins.
- **Don't recommend to fill the page.** Zero verified resources is a valid, publishable result:
  say what you searched, why nothing cleared the bar, and what to do instead.
- **Don't launder uncertainty.** "I believe this covers…" means you didn't verify it. Verify or drop.

---

## Step 6 — Write the file

Write to `<exam folder>/resources/<topic-slug>.md`, creating `resources/` if needed. Mirror
whatever heading structure an existing resources file uses. The file holds: the diagnosis line
and its date, the shortlist as rendered, the one pick, the skip line — and a stub table for
outcomes:

```
## Used

| Date | Resource | Time spent | Did it move the rung? | Keep / drop |
|---|---|---|---|---|
```

`/gather-resources log <topic>` fills one row: ask which resource, how long it took, and
whether the next attempt on that topic passed. Then write **one line of judgment** — was the
medium right for this kind of gap? That line is the only way this skill gets better at Step 1,
because it is the only place the prediction gets checked against what happened.

---

## Anti-patterns — reject these drafts

| Draft | Why it fails |
|---|---|
| Five links, each with a one-line summary | A menu, not an argument. No cost, no failure mode, no activation |
| "Con: it's quite long / it's a bit advanced" | Not a con. What will it *fail to give him*, and what does the length cost against the topic's marks? |
| Recommending a whole book, or a whole lecture series | Unactionable at exam distance. Name the section |
| A link that was not fetched | The single most damaging output this skill can produce |
| Searching before diagnosing | Produces topic-shaped resources for a mechanics-shaped failure |
| Recommending something when the diagnosis said "reps" | The polite version of wasting his week |
| Explaining the concept while introducing the resource | Breaks the retrieval gate the whole system runs on |
| Ignoring the course's notation | Installs an answer that loses marks. The worst outcome here, and it looks like help |

---

## Self-check before sending

- Is the diagnosis stated, in one line, from the ledger's own notes — before any search?
- Did the diagnosis permit an external resource at all, or did I search past a "No"?
- Is every URL one I actually fetched or saw in live results? Every timestamp real?
- Does every card have a con that names a *specific failure to deliver*, not a length complaint?
- Does every card have an activation protocol with a concrete stopping point?
- Four or fewer? Under the time budget? One pick named?
- Is the skip line there — the condition under which all of this is the wrong move?
- Did I avoid teaching, avoid quoting exam questions, and avoid touching the ledger?
- Does the message end by handing back to the ramp?

---

## What this skill is NOT

It is not a reading list, a curriculum, or a substitute for the ramp. It does not teach, grade,
plan sessions, or track mastery. It exists to let a small, argued amount of outside material
into a closed system — and to make sure that whatever comes in arrives with its cost printed
on the label and a protocol for turning it back into retrieval. **Its most valuable output is
often the sentence "nothing here beats one more past-paper question."**
