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
    "commit": "b3b1b687947f646110ebaedff48e10f975bcf1f9",
    "checked_at": "2026-09-16T19:56:54+00:00",
    "criteria_digest": "e0c2d57c0ede5fe6f286e0a173252a494b87efe446251fd82ca4ad9657c20ef6",
    "checker": "Codex",
    "result": "still_valid",
    "evidence": [
      "At commit b3b1b68, add-exam configures both ModelClient objects but prints no provider, model, or effective limits. RequestLimits still applies generic 128,000 context and 32,000 output defaults to the requested UnoRouter GLM 5.3 models unless environment overrides are supplied."
    ],
    "provisional": false
  },
  "closure": null
}
```

**What to build:** Print the effective LLM provider, model, and request limits before an `add-exam` run starts, and use the selected GLM 5.3 models' supported budgets for long exam papers.

- [ ] Print one LLM settings block before processing exam files.
- [ ] Show the Stage 1 and Stage 2 model IDs.
- [ ] Show each stage's context, maximum output, and framing-overhead limits.
- [ ] Never print API keys or other credentials.
- [ ] Keep dry runs and commands that do not call an LLM free of the settings block.
- [ ] Default UnoRouter `glm-5.3-flash` and `glm-5.3` to a 1,000,000-token context and a 128,000-token maximum output.
- [ ] Preserve explicit `LLM_CONTEXT_TOKENS_STAGE1/STAGE2` and `LLM_MAX_OUTPUT_TOKENS_STAGE1/STAGE2` overrides.
- [ ] Cover a normalized 20-page exam request under the configured Stage 1 budget.
- [ ] Add an offline CLI test for the exact output and credential exclusion.

**Architecture:** Select known model defaults while constructing each `ModelClient`, then render the summary from those configured clients after environment validation and before course processing. Do not reread environment variables or duplicate provider defaults in the renderer.

## Evidence and history

Created to make live MVP runs self-describing when different providers, models, or token budgets are selected. UnoRouter's current catalog lists both requested GLM 5.3 variants with a 1,000,000-token context; their model specifications list a 128,000-token maximum output.
