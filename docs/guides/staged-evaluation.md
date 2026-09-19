# Staged GPT evaluation and fixture replay

Run `pipeline/staged_evaluation.py` explicitly from the repository root. It calls
the production `stage1_extract`, `stage2_tag_score`, and candidate validator with
the separate extraction and analysis clients introduced by Ticket 20. It captures
the actual system and user messages, including contract 1.2.0, rather than keeping
a second set of prompts.

The sample `pipeline/tests/fixtures/staged_evaluation/equations-case.json` is a
complete synthetic exam with a definition question and an elimination problem,
printed marks, and shared instructions. Its frozen extraction and comparison
choices were authored for this prototype. They still need human calibration.

The saved `astra-evidence.json` contains six blind GPT-6 Astra responses captured
on 2026-09-15. Independent Stage 2 passed. Both extraction runs included the exam
header, printed question label, and marks in `text`; the frozen case puts that
material in `source_context`. Both Stage 1 runs therefore report exact-text
mismatches. Chained Stage 2 preserves that text and reports the same mismatches.
Question coverage, year, marks, formats, context, arithmetic, and the documented
judgment choices passed. This is a reproducible representation disagreement for
Ticket 09 to calibrate with a person. The capture remains unapproved evidence.

## Run GPT sub-agents without provider credentials

Export the requests with the exact model ID of the GPT sub-agent that will answer:

```powershell
python pipeline/staged_evaluation.py exchange pipeline/tests/fixtures/staged_evaluation/equations-case.json --model gpt-6-astra --output tmp/evaluation-requests-1.json
```

Each pending run exposes its next request at `runs.<name>.calls[-1]`. Give a GPT
sub-agent only that call's `request.system` and `request.user`, as the instructions
and source data for its answer. Do not supply frozen answers, expected scores, or
other model outputs. Ask it to return only the required JSON. Run extraction and
analysis as separate sub-agent tasks. Each chained extraction is also a fresh call.

Save raw answers in a JSON object keyed by `request_id`. Values are strings, not
parsed objects. For example:

```json
{
  "request hash copied from the export": "{\"exam_year\":2026,\"questions\":[...]}"
}
```

Keep the original responses, including failures. Append answers to this file as
new requests become available, then run:

```powershell
python pipeline/staged_evaluation.py exchange pipeline/tests/fixtures/staged_evaluation/equations-case.json --model gpt-6-astra --answers tmp/evaluation-answers.json --output tmp/evaluation-requests-2.json
```

Repeat with a new output filename until no run is pending. A run may remain failed
after every response has arrived. That is useful evaluation evidence. Do not edit
responses or widen expectations to make a failure disappear. Preserve the failing
capture and review a new case revision or production fix separately.

The four run names are `stage1`, `stage2`, `chain_stage1`, and `chain_stage2`.
Independent Stage 2 always uses a copied, validated frozen extraction and taxonomy.
Chained Stage 2 uses the fresh validated chain extraction, even when its exact
comparison failed. If that extraction cannot pass schema validation, the chain's
Stage 2 is skipped. Every stage keeps its own failure, so a valid Stage 2 cannot
hide a Stage 1 regression.

The report includes the source text, source hash, frozen input, taxonomy, model ID,
capture date, request hashes, full prompts, raw responses, parsed results, and
contract version and hash. Its human review status starts as `pending`. Stage 2
also records the validated candidate, proposed topic names, quotes, difficulty
judgments, prerequisite and connection evidence, rationales, and uncertainties.

## Live provider evaluation

Live requests require the separate `live` command and `--allow-live`. Configure
credentials through the provider's environment variables. This command reads the
current environment once and does not load `.env` automatically.

```powershell
python pipeline/staged_evaluation.py live pipeline/tests/fixtures/staged_evaluation/equations-case.json --allow-live --provider openai --model EXACT_GPT_MODEL_ID --output tmp/gpt-live-capture.json
```

Use a supported exact provider model ID. The agent model name used in Codex does
not imply that the same name is available through a provider API. The prototype
uses matching Stage 1 and Stage 2 request budgets and a single model ID per run.
Set both stages' token limit variables to matching values if overrides are needed.
Each output file must be new, including when rerunning a failed capture.

Exit codes are `0` for passing comparisons, `1` for stage/comparison failures,
`2` for invalid setup or files, and `3` while GPT answers are still pending.
If a failure and a pending stage coexist, exit code `1` keeps the failure visible.

## Exact checks and judgment choices

The case's `frozen_stage1` fixes question IDs, order, complete task text, printed
marks, response formats, retained source context, and sitting year. These fields
must match exactly. Stage 2 must preserve every extraction field from its own input.
Adding a header to `text`, even when that header is already in `source_context`,
is an exact-text mismatch. A reviewer can decide whether a later case revision
should adopt that representation; the runner does not silently normalize it.

Production validators require every question and topic judgment exactly once,
valid schemas, and every evidence quote to appear literally in its own question's
text or retained context. Quotes use exact substring checks, with no fuzzy matching.
Different valid excerpts can support a live judgment. A deterministic replay must
also reproduce the captured excerpt and the rest of the captured result exactly.

`expectations.local_values` contains JSON Pointer paths and exact expected values.
The sample checks total marks, topic mark totals and fractions, the format
distribution and dominant format, and the locally computed topic difficulty.
Its definition and elimination levels have lower median 1, regardless of their
4/6 mark split. Production validation also checks difficulty aggregation and
connection counts against their question and edge evidence.

`expectations.topics` lists accepted complete topic sets per question.
`expectations.difficulty_levels` lists accepted integer levels per topic/question.
`expectations.new_topic_names` lists accepted proposal sets. The sample allows
level 1 for definition recall and levels 2 or 3 for the elimination problem. This
explicit prototype tolerance tests the distinction between a very short rule
application and a standard multi-step method. A human must confirm the accepted
choices before treating them as calibration truth. No numeric distance tolerance
or implicit synonym matching applies. Rationales and uncertainty notes remain
available for human review; their semantic quality is not automatically certified.

## Audit evidence and approve a reference

An audit proves that saved responses reproduce the same pipeline behavior without
a network connection. It does not adopt them as correct answers:

```powershell
python pipeline/staged_evaluation.py audit tmp/gpt-live-capture.json --output tmp/gpt-audit.json
```

A complete failing capture can also be audited. It keeps the recorded stage
failures and exit code `1`. Compare each stage and check for `replay_error` to
distinguish the reproduced finding from changed behavior.

A person must inspect the source, frozen extraction, accepted choices, evidence,
judgments, and all four stage results before approving a passing capture. The CLI
prints its `content_sha256`. The person then records their identity and decision:

```powershell
python pipeline/staged_evaluation.py approve tmp/gpt-live-capture.json --reviewer "Person's name" --notes "Reviewed source facts, quotes, accepted judgments, and all stages" --content-sha256 HASH_FROM_CAPTURE --output tmp/gpt-approved-reference.json
python pipeline/staged_evaluation.py replay tmp/gpt-approved-reference.json --output tmp/gpt-reference-replay.json
```

Approval binds the reviewed contents to their hash. Changing the input, expectations,
transcript, model provenance, or results invalidates the approval. The approval
command also replays the capture before recording the decision. It records a human
attestation; it does not authenticate that person's identity. An AI implementer or
reviewer must not use this command on a person's behalf without their approval.
The parent report's approval applies to its captured runs, whose original pending
status remains part of the immutable evidence.

## Normal automated tests and later GLM smoke tests

```powershell
python -m unittest discover -s pipeline/tests -p test_staged_evaluation.py -v
python -m unittest discover -s pipeline/tests -v
```

The tests use handwritten protocol examples and saved response transcripts through
the existing injected clients. No test configures a live provider. A replay test
also clears credentials and blocks sockets. Pending GPT captures are evidence only;
the reference API rejects them until a person approves a passing capture. Tests of
the approval mechanism use a simulated test reviewer, not a claimed real review.

After approval, use the approved report's exact `case` as the GLM smoke-test input.
Save that case to a new JSON file and run `live` with a supported OpenAI-compatible
provider such as `openrouter` or `unorouter`, the exact GLM model ID, and that
provider's credential environment variable. Choose a new output path:

```powershell
python pipeline/staged_evaluation.py live tmp/approved-case.json --allow-live --provider openrouter --model EXACT_GLM_MODEL_ID --output tmp/glm-smoke-capture.json
```

The GLM capture receives its own model provenance and pending review status.
Compare its stage outcomes, exact failures, and accepted judgment choices to the
approved case. Keep the GPT reference file unchanged. Do not promote the GLM
output automatically. This prototype supplies Ticket 09 with a portable case,
raw transcripts, validated outcomes, separate error categories, and a human
approval record; broader calibration still belongs to that ticket.

## Dependencies

<!-- doc-dependencies:start -->
| File | Reason | Review when |
|---|---|---|
| `pipeline/staged_evaluation.py` | Documents exchange, live, audit, approval, replay, and exit semantics. | Commands, report schema, hashes, approval, or replay behavior change. |
| `pipeline/pipeline.py` | Reuses production extraction, tagging, scoring, and prompts. | Stage interfaces, prompt contents, or production outputs change. |
| `pipeline/exam_roi/evaluation.py` | Defines candidate validation used by capture and replay. | Candidate schema, evidence matching, or deterministic validation change. |
| `pipeline/exam_roi/contracts/evaluation-v1.2.0.md` | Defines the contract embedded in evaluation requests and evidence. | Active contract version or captured evaluation requirements change. |
| `pipeline/tests/fixtures/staged_evaluation/equations-case.json` | Describes the synthetic source and frozen expectations. | Source facts, frozen extraction, or accepted judgment choices change. |
| `pipeline/tests/fixtures/staged_evaluation/astra-evidence.json` | Interprets the saved responses and unapproved representation disagreements. | Captured responses, outcomes, provenance, or approval status change. |
| `pipeline/tests/test_staged_evaluation.py` | Cites offline audit, replay, and approval regression evidence. | Verified protocol behavior or network-isolation checks change. |
| `docs/development/workflow.md` | Uses the same live-call approval and private-data boundaries. | Provider approval, permitted inputs, or evidence handling changes. |
<!-- doc-dependencies:end -->
