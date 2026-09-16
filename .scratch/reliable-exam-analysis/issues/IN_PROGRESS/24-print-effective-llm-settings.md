# 24: Print effective LLM settings

```json
{
  "schema_version": 1,
  "id": "24",
  "priority": "P2",
  "queue_order": 24,
  "areas": [
    "configuration"
  ],
  "depends_on": [
    "20"
  ],
  "related_to": [
    "23"
  ],
  "references": [
    "pipeline/pipeline.py",
    "pipeline/exam_roi/llm.py",
    "pipeline/tests/test_explicit_configuration.py"
  ],
  "verification": {
    "commit": "ef5e69c30b52ffe1ea60b090109b83ffafc1ba71",
    "checked_at": "2026-09-16T20:01:58+00:00",
    "criteria_digest": "e0c2d57c0ede5fe6f286e0a173252a494b87efe446251fd82ca4ad9657c20ef6",
    "checker": "Codex",
    "result": "already_resolved",
    "evidence": [
      "At commit ef5e69c, live add-exam startup prints the effective provider, models, and per-stage limits without credentials. UnoRouter GLM 5.3 defaults use 1,000,000 context and 128,000 output tokens, explicit overrides remain effective, the 307,598-token synthetic 20-page request fits, and all 224 pipeline plus 35 ticket tests pass."
    ],
    "provisional": false
  },
  "closure": null
}
```

**What to build:** Print the effective LLM provider, model, and request limits before an `add-exam` run starts, and use the selected GLM 5.3 models' supported budgets for long exam papers.

- [x] Print one LLM settings block before processing exam files.
- [x] Show the Stage 1 and Stage 2 model IDs.
- [x] Show each stage's context, maximum output, and framing-overhead limits.
- [x] Never print API keys or other credentials.
- [x] Keep dry runs and commands that do not call an LLM free of the settings block.
- [x] Default UnoRouter `glm-5.3-flash` and `glm-5.3` to a 1,000,000-token context and a 128,000-token maximum output.
- [x] Preserve explicit `LLM_CONTEXT_TOKENS_STAGE1/STAGE2` and `LLM_MAX_OUTPUT_TOKENS_STAGE1/STAGE2` overrides.
- [x] Cover a normalized 20-page exam request under the configured Stage 1 budget.
- [x] Add an offline CLI test for the exact output and credential exclusion.

**Architecture:** Select known model defaults while constructing each `ModelClient`, then render the summary from those configured clients after environment validation and before course processing. Do not reread environment variables or duplicate provider defaults in the renderer.

## Evidence and history

Created to make live MVP runs self-describing when different providers, models, or token budgets are selected. UnoRouter's current catalog lists both requested GLM 5.3 variants with a 1,000,000-token context; their model specifications list a 128,000-token maximum output.

Implementation selects known limits for the two requested UnoRouter models while retaining all per-stage environment overrides. A live `add-exam` run now prints the configured provider, model, context, maximum output, and overhead for each stage before course processing. Dry runs and non-LLM commands do not print the block.

Offline verification built a normalized 20-page request whose conservative complete-request estimate was 307,598 tokens, leaving 692,402 tokens of headroom under the new Stage 1 context. All 224 pipeline tests passed, including exact-output, secret-exclusion, override, dry-run, and long-exam coverage tests.
