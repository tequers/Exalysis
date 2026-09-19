# Exam topic relative priority

The pipeline works from exam papers alone. Its authoritative rules are the
[evaluation contract 1.2.0](../../pipeline/exam_roi/contracts/evaluation-v1.2.0.md).

## Each paper adds evidence

1. Extract questions and reuse the course folder's established topic names.
2. Judge every tested topic, including existing topics, using this paper's evidence.
   Infer background assumptions from the paper; no manual prerequisites are used.
3. Store the independent observations in `parsed/<paper>.json`, under
   `topic_judgments`. Quotes, question IDs, reasoning, and the contract version are retained.
4. When new names appear, review connections in earlier current-contract papers using
   the expanded vocabulary. Store the latest edges under `connection_review`, preserving
   the original judgments. This adds model calls when the taxonomy grows.
5. Recompute taxonomy.json from the accumulated evidence, then export the ranking.

The taxonomy is a summary, not a permanent copy of the first paper's scores.
Reparsing an existing paper replaces its contribution, including obsolete edges.
Rebuild repeats the summary calculation without calling the model. Paper observations
and human overrides remain separate from automatically calculated estimates.

## Connection grows with supported relationships

An edge means **prerequisite topic → dependent topic**. Each edge needs a question ID,
exact source quote, and reason. Mere co-occurrence is insufficient.

For example, paper 1 tests A alone: Conn=1 provisionally. Paper 2 shows B requires A:
A's Conn becomes 2, even if A is not directly tested there. If later papers establish
that C and D also require A, its Conn becomes 3. Further evidence of A → B does not
increase the count again. Supporting paper IDs remain attached to the edge.

The bands are: no supported direct dependent topics = 1; one or two = 2; three or
more = 3. Conn is computed from the combined edges, not averaged or summed from
per-paper Conn scores. A later paper with no edge does not erase evidence in another
paper. Correcting the source paper can remove an edge. Cyclic dependencies are kept
as conflicts for review and excluded from the count until corrected.

Earlier papers are reviewed when the topic vocabulary expands. This allows an old
question to support A → B even if A received its canonical name only in a later paper.
The newest connection review replaces that paper's active edges. It does not alter
its original difficulty observations. More data can improve coverage; it does not
by itself prove the judgments are correct.

## Difficulty accumulates too

Within each paper/topic, take the lower median of question levels. Across papers,
take the lower median of those summaries, giving each distinct paper equal weight.
Keep the observed range. A spread of two or more levels requires review.

Group evidence by inferred background assumptions; do not average incompatible
groups. Use the group supported by most papers, breaking ties by the alphabetically
sorted assumption list. Preserve all groups in `difficulty_groups` and flag differing
groups for review. A topic with only new connection evidence keeps its earlier Diff
with a review flag until compatible difficulty evidence is available.

The model supplies `assumed_prerequisites` and `prerequisite_evidence` from exam text.
Each assumption requires a quote and reason. These are estimates of what the paper
expects, not official course entry requirements or personal study history.

## Human corrections and historical records

Use `edit-topic TOPIC --diff 4 --conn 2` to protect an explicit correction. The taxonomy
retains the override while `model_estimate` shows the updated automatic values.
Direct edits to managed scores are detected by comparison with the previous automatic
estimate and preserved as overrides. Unmarked edits in older taxonomies cannot be
identified reliably: use `edit-topic` before reevaluation to protect a specific value.
Spreadsheet edits are not read back into canonical state.

Contract 1.2.0 introduces per-paper connection edges and cumulative summaries.
Earlier contracts and records remain intact. Older papers are listed in
`excluded_legacy_exam_ids`; their old numeric scores are not treated as new evidence.
Reprocess their source papers once with `add-exam --force` to bring them into the
current analysis. This calls the model. `rebuild` alone cannot infer missing evidence.
Old duration fields are ignored and omitted from exports.

New analyses record `evaluation_contract_version` and `evaluation_contract_sha256`.
A version records which rules were used; it is not an independent approval status.

## Ranking arithmetic

`Priority = 100 × Freq × G_Marks × Conn / (Diff × Fmt)`

| Variable | Meaning |
|---|---|
| Freq | Containing papers / all stored papers; distinct sittings in one year remain separate. |
| G_Marks | Mean allocated mark fraction across containing papers. |
| Conn | Supported direct dependency count mapped to the 1–3 bands above. |
| Diff | Qualitative reasoning complexity, 1–6, summarized from compatible evidence. |
| Fmt | Mark-weighted response-mode weight within a paper, then the equal mean across containing papers. |

Format weights remain `mcq=1`, `short_answer=2`, `explain_derive=2`, and
`write_code_or_proof=3`. Difficulty is independent of these categories.
For a mandatory additive paper, an inseparable two-topic question contributes half
its marks to each topic. This is a stated approximation. Optional-paper and full mark
validation remain separate reliability work; prompt instructions alone do not enforce it.

Priority is a relative heuristic, not predicted marks or a rate of learning.
There is no PageRank or recency weighting. Tier 1 takes
`max(1, round(topic_count * .2))` topics, using Python's round-to-even behavior.
Existing ranking arithmetic is unchanged. Legacy papers can still contribute mark
statistics, so exclusions from qualitative evidence are shown in review notes.

JSON exports include contributing paper IDs, connection evidence, automatic estimates,
human overrides, and review notes. XLSX shows the resulting scores and review notes.
Both exports use the same recomputed taxonomy.

## Validation and persistence limits

Run `python -m unittest discover -s pipeline/tests -v` from the repository root
with openpyxl installed. Offline checks cover cumulative dependencies, old-topic
updates, discovery order, repeated edges, replacement, cycles, assumption groups,
overrides, exports, and legacy compatibility. They do not measure live-model accuracy;
independent human calibration remains ticket 9.

Judgments and refreshed edges are validated before writes. Rebuild can reconstruct an
outdated taxonomy from saved observations. Multi-file transactional recovery and
concurrent writers remain ticket 7; independent review and acceptance gating remain
later tickets. These are not implemented merely by refreshing the taxonomy.
