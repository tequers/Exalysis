# Model request limits and question context

Extraction, tagging, and topic scoring check request size before dispatch. The
check includes the system prompt and evaluation contract, source evidence,
canonical topic labels, framing overhead, and the entire reserved output budget.

Set these variables in the repository `.env` or process environment. Stage 1 is
extraction. Stage 2 is tagging and scoring. The defaults are local budgets, not
verified limits for the model named in `LLM_MODEL_STAGE1` or `LLM_MODEL_STAGE2`.
Choose values supported by the models you use.

| Variable | Default | Meaning |
|---|---:|---|
| `LLM_CONTEXT_TOKENS_STAGE1` | 128000 | Total extraction context budget |
| `LLM_MAX_OUTPUT_TOKENS_STAGE1` | 32000 | Extraction output cap and reservation |
| `LLM_OVERHEAD_TOKENS_STAGE1` | 1024 | Extraction framing reservation |
| `LLM_CONTEXT_TOKENS_STAGE2` | 128000 | Total tagging/scoring context budget |
| `LLM_MAX_OUTPUT_TOKENS_STAGE2` | 32000 | Tagging/scoring output cap and reservation |
| `LLM_OVERHEAD_TOKENS_STAGE2` | 1024 | Tagging/scoring framing reservation |

Values must be positive integers. Context must exceed output plus overhead.
The default input estimate counts UTF-8 bytes. This is deliberately conservative
for ordinary text and avoids assuming English token density for other languages.
An injected `ModelClient` can supply its model's token counter. The check cannot
correct a deployment limit that is larger than the provider actually supports.

## What is preserved

Question `text` is no longer cut after 500 characters. New extractions also store
`source_context`, copied from the source by Python. It includes the question's
complete source block, its parent instructions and subparts, and the paper's
opening instructions. Explicit references to other questions bring their source
blocks along, including chains of references. Page markers inside these blocks
are retained. Tagging and scoring receive both fields, and evidence quotes may
match either. Existing records without `source_context` remain readable.

Difficulty uses the current evaluation contract's course baseline: infer assumed
background from the exam and support it with quotes. This change does not add a
manual prerequisites list or change the difficulty scale.

## Splitting and failure behavior

Extraction recognizes unique top-level headings such as `Q1`, `Question 1`,
`Pregunta 1`, and `Ejercicio 1`. It splits between those headings, never at a page
boundary or a fixed character count. A question that continues onto another page
stays intact. Subparts keep IDs such as `Q2a`; numbering does not restart in later
batches. Each source heading must have a returned question or subquestion. Merged
results reject duplicate IDs and conflicting sitting years.

Bare numbered lists and repeated question numbers are ambiguous. Such papers stay
one source unit. If that unit cannot fit, use a model with a larger supported
budget, or prepare a text copy with unique explicit question headings and all its
instructions. Structural coverage checks do not prove that a model identified
every semantic subpart correctly.

Tagging splits by complete question. Scoring splits by topic, then by complete
question if a single topic has too much evidence. Each response must cover exactly
its requested IDs or topics before it can join the result. Merging retains all
question judgments and dependency evidence. Python calculates difficulty from all
question levels and connectivity from the union of supported downstream labels.
New topic labels carry forward to later tagging batches. Canonical labels are
never silently trimmed to make a request fit.

Output-size estimates can also trigger splitting. Provider-reported truncation
rejects the entire response, even if it contains syntactically valid JSON. Recovery
halves the batch until a complete answer arrives or only one question remains.
Each batch tree has at most `2*n-1` completion attempts, excluding transient network
retries. A single question that still exceeds a limit or produces truncated output
fails with a remedy. Malformed JSON fails validation; it is not repaired into a
partial candidate. Failed analysis never overwrites the candidate with partial
results.

## Injecting clients

`stage1_extract`, `_stage2_tag`, `_stage2_score_topics`, and `stage2_tag_score`
accept keyword arguments `client` and `limits`. A fake callable accepts
`system`, `user`, and `max_tokens` and returns complete response text.

For a real provider, construct `exam_roi.llm.ModelClient` with an SDK client,
SDK family, model ID, and `RequestLimits`. It owns response completion checks.
Its optional `provider` identifies an OpenAI-compatible host in provenance, and
`count_tokens` supplies a tokenizer. Explicit limits must match the injected
client's limits.

`process_exam_file` accepts separate `extraction_client`, `analysis_client`,
`extraction_limits`, and `analysis_limits`. Saved provenance identifies injected
models and providers. The existing CLI still configures course paths; the broader
course-state and startup refactor belongs to ticket 20. Importing the new
`exam_roi.llm` and `exam_roi.question_context` modules has no CLI side effects.

## Offline verification

Run from the repository root with the project's Python dependencies installed:

```powershell
python -m unittest discover -s pipeline/tests -q
```

`test_request_limits.py` covers long introductions, decisive tail text, source
context persistence, page continuations, cross-question references, input and
output budgets, large topic sets, merge coverage, and truncated responses. It uses
fake clients and makes no live API calls.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `pipeline/exam_roi/llm.py` | Explains request budgets, token counting, completion checks, and injected clients. | Limit defaults, interfaces, retries, or truncation handling change. |
| `pipeline/exam_roi/question_context.py` | Explains complete question groups and retained evidence context. | Heading recognition, cross-references, or context construction changes. |
| `pipeline/pipeline.py` | Explains per-stage limits, batching, and configuration integration. | Stage signatures, environment defaults, or splitting behavior change. |
| `pipeline/exam_roi/contracts/evaluation-v1.2.0.md` | Preserves the difficulty baseline and evidence requirements during batching. | Contract text, evidence rules, or background-assumption requirements change. |
| `pipeline/tests/test_request_limits.py` | Cites offline coverage of limits, context retention, and batch recovery. | Regression cases or the behavior those checks establish change. |
| `.env.example` | Exposes the documented per-stage request budget settings. | Budget variable names, examples, or defaults change. |
<!-- doc-dependencies:end -->
