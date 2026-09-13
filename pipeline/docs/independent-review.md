# Independent candidate review

Use `--review` with `add-exam` to challenge an analysis against the full extracted
source and the evaluation contract before saving it as a candidate.

```powershell
$env:LLM_REVIEW_PROVIDER = "openai"
$env:LLM_REVIEW_MODEL = "your-reviewer-model-id"
python pipeline/pipeline.py Courses/Example_Course add-exam paper.txt --review
```

The reviewer provider defaults to `LLM_PROVIDER`. The model ID must be explicitly
set. The reviewer uses that provider's existing API key environment variable and
SDK. It can use a different provider from extraction and scoring. Every review is
a fresh request with no analyzer conversation history. Using the same model is
allowed, but its agreement does not prove correctness.

Review is off unless `--review` is supplied. Candidates record this explicitly as
`independent_review.enabled: false` and `disposition: disabled`.

## Evidence and outcomes

The reviewer receives the complete extracted source, its references in candidate
provenance, the candidate including canonical topic names and proposed taxonomy
changes, and the full contract matching the candidate's version and hash.

It returns one structured assessment for each of these categories:

- Extraction omissions, including missing subparts.
- Claims unsupported by the source.
- Mark allocation, totals, double counting, and optional or bonus questions.
- Topic consistency with canonical labels.
- Difficulty rubric application.
- Connection rubric application.

Each assessment requires a disposition, severity, rationale, and exact source
quotes. This includes assessments reporting no issue. Python checks completeness,
quote membership, and consistent dispositions and records source character
offsets. Quotes establish traceability; their presence cannot establish that the
model's reasoning is correct. Repeated quotes use their first source occurrence.

`no_issue` means the reviewer reported no issue. `correction_required` asks the
analyzer to reconsider supported defects. `needs_review` records ambiguity or an
unresolved disagreement. Review results are separate from `candidate_status` and
never accept a candidate, change accepted taxonomy, or trigger an export.
Existing deterministic validation still applies, and a clean review does not
clear a candidate's existing `needs-review` status.

Malformed JSON, missing assessments, invented quotes, contradictory dispositions,
truncation, unavailable credentials/providers, and oversized requests all produce
a saved `needs-review` candidate with a failed review attempt and a recorded error.
The CLI prints the review disposition and failure reason.

## Corrections and history

The default correction budget is zero. Findings that need correction therefore
leave a visible `needs-review` candidate for inspection. To permit one analyzer
correction attempt, add `--review-corrections 1`. The hard maximum is two.

The analyzer receives the findings as observations to check against the source.
It reruns extraction, tagging, scoring, deterministic validation, and taxonomy
proposal construction against the same source snapshot. The reviewer cannot
return a replacement candidate. Every valid revised candidate gets a fresh review
before it is saved. A human-review disposition stops automated correction.

The saved review record includes reviewer provider/model, contract version/hash,
source text hash, correction budget/count, and each reviewed candidate snapshot,
candidate hash, findings, and errors. Failed correction retains the last valid
candidate. Exhausted correction attempts leave `needs-review`. Use `--force` with
`--review` to reprocess a candidate through this workflow; it starts a new run and
replaces the previous candidate file under the existing force behavior.

## Request limits and injected clients

| Environment variable | Default |
|---|---:|
| `LLM_REVIEW_CONTEXT_TOKENS` | 128000 |
| `LLM_REVIEW_MAX_OUTPUT_TOKENS` | 32000 |
| `LLM_REVIEW_OVERHEAD_TOKENS` | 1024 |

These are local budgets. Configure values supported by the selected model. Review
includes the entire source and candidate in one request because omission and
consistency checks need the complete paper. It never trims evidence to fit. Use a
larger supported context budget or review the saved candidate manually if needed.
Provider transport retries use the existing maximum of three attempts per request.
Malformed reviews are not retried as though they had passed.

`process_exam_file` accepts `review_enabled`, `reviewer_client`, `reviewer_limits`,
and `max_corrections`. An injected `ModelClient` supplies its own model, provider,
token counter, and limits. A plain callable accepts `system`, `user`, and
`max_tokens`; its provenance is labeled `injected-callable`.

`exam_roi.review.review_candidate` returns a candidate and a separate review
record. Its optional correction callback must return a complete candidate rebuilt
and validated through the evaluation interface. The module performs no file writes
or acceptance decisions.

Offline tests use fake reviewers to verify routing and failure behavior. They do
not measure a live model's ability to detect defects. Ticket 03's deterministic
mark/scoring checks remain separate work and are not replaced by model review.
