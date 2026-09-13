# One record per paper, and the year a paper was sat

**Status:** accepted

A year rarely has one exam. Spanish EVAU sets a Lunes paper, a Martes paper and a *coincidencias*
paper in the same ordinary sitting; other courses have models A and B, a resit, a practical and a
theory paper. Until now the pipeline treated the year as if it identified an exam: it took the
first four-digit number in the filename, and labelled the spreadsheet's per-exam columns with it.
Three papers from 2022 therefore produced three groups of columns all headed `2022`, and papers
filed one folder per year (`2022/modelo_A.pdf`, `2023/modelo_A.pdf`) collided on the filename-derived
id, so the second was reported as "already parsed" and silently dropped.

**The paper, not the year, is the unit.** Each paper gets its own record in `parsed/`, its own
columns in the sheet, and its own entry in every topic's `per_exam`. Where two papers would claim
the same id, the id is qualified with the folder the paper came from, because the alternative —
one record overwriting or masking another — loses an exam without saying so.

**Papers that share a year are told apart by what their names do not share.** The tokens common to
every name in the group, front and back, are dropped and the remainder becomes the column label:
`2022 Lunes`, `2022 Martes`, `2022 coincidencias`. This beats numbering them (`2022 #1`, `2022 #2`,
which carry no meaning and change as papers are added) and beats using the full filename (which no
column is wide enough for). A year holding one paper keeps the bare year.

**An academic year resolves to its later half.** `2021-2022 Ordinaria ...` is a paper sat in 2022,
so ranges written `2021-2022`, `2021/22` or `2021_22` yield 2022; the string as written is kept
alongside as `year_label`, since that is how the person who filed it refers to it. Taking the first
number instead would date every EVAU paper a year early and order the sheet wrongly.

**The year is read, never guessed.** The filename is consulted first (it is what the person filing
the paper meant), then the first pages of the paper itself, then — only if both are silent — the
year Stage 1 reports from having read the whole paper. If nothing says, the paper is filed with no
year and the run says so, rather than defaulting to the current year as it previously did: a
fabricated year silently reorders the sheet and mislabels a column, and is worse than a visible gap
the user can fix with `--year`.

**`Freq` keeps counting papers, not years.** A topic in all three 2022 sittings but in neither 2023
paper scores 3/5, not 1/2. Each paper is an independent draw from what the examiner asks, and a
topic that appears on every model of a sitting is genuinely more likely to appear on the next one
than a topic that appeared on only one of them — that difference is signal, and averaging it away
per year would discard it.
