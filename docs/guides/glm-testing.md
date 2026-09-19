# Pipeline testing with GLM

Before a live test, follow the [provider approval and setup](../development/workflow.md#optional-live-provider-setup) instructions. Approve the provider, exact models, and expected cost.

When testing the exam pipeline:

1. Run `pipeline/pipeline.py`; it loads the repository-root `.env` automatically.
2. Before an API call, verify without printing secrets that:
   - `LLM_PROVIDER` is `unorouter`
   - both model variables contain `glm`
   - `UNOROUTER_API_KEY` or its compatibility alias is present
3. Stop if these checks fail. Do not fall back to Anthropic.
4. Use `.scratch/glm-pipeline-smoke/exam_2026.txt` for the first API test.
5. Send personal or copyrighted exams externally only when the user explicitly identifies and authorizes those files.
6. After the run, inspect the candidate JSON and confirm `model_provenance.provider` is `unorouter` and both recorded models are GLM.
7. Never print, commit, or include `.env` contents in logs.

The normal smoke-test command is:

`python pipeline/pipeline.py ".scratch/glm-pipeline-smoke" add-exam "exam_2026.txt"`
