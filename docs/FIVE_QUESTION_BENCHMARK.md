# Five-question paired benchmark

This additive runner preserves the original one-question pilot and its artifacts. It does not change the RAVE architecture or research mode.

## Question set

The initial batch is in [questions_v1.json](../benchmark/questions_v1.json). It covers:

1. Factual research using official time-series data.
2. Comparison of institutional and regulatory frameworks.
3. Deep investigation of causal mechanisms.
4. Conflicting empirical evidence.
5. Multidimensional analysis across environmental, economic and social dimensions.

The runner accepts any non-empty JSON question list with unique IDs, a question, and an optional scope. The five prompts are a starting benchmark set, not a claim that five tasks represent all research domains.

## Execution

From the repository root, with \`comparison_a/.env\` configured locally and the RAVE private repository accessible through local Git authentication:

\`\`\`powershell
uv run --project comparison_a --locked --extra dev python scripts/run_question_batch.py --live
\`\`\`

To use another question set:

\`\`\`powershell
uv run --project comparison_a --locked --extra dev python scripts/run_question_batch.py --questions-file benchmark/my_questions.json --live
\`\`\`

The script runs Solo Baseline and then RAVE for each question. It stops at the first incomplete or failed run to avoid spending the remaining budget after a failure. Existing pilot artifacts are not reused, overwritten or modified.

## Resource controls

Both systems receive the same run-wide ceilings:

- 120,000 tokens
- 3 search attempts
- 16 model-call attempts
- 360 seconds
- USD 0.50 estimated cost

Both use \`gpt-4.1-mini\`, \`gpt-5-search-api\`, low search context, a 512-token search-output cap, temperature 0.2 and an 8,192-token hosted-search input reservation. Internal per-call allocation remains architecture-specific: Solo uses an 8,192-token analysis cap; RAVE uses 4,096-token specialist calls and an 8,192-token synthesis cap. These are equal global ceilings, not equal resource consumption.

The configured cost ceiling is a local estimate, not a provider-enforced billing cap. Verify the search pricing values in the applicable billing record and maintain an independent provider spend limit. Five questions mean ten research runs; the combined configured per-run ceiling is USD 5.00.

## Artifacts and evaluation

Artifacts are written under \`artifacts/batches/<batch_id>/<question_id>/\`. Each completed pair contains:

- \`solo_result.json\` and \`solo_metadata.json\`
- \`rave_run.json\` and \`rave_cli_output.json\`
- \`blind_responses.json\`
- \`system_key.json\`
- command stdout/stderr logs
- a batch-level \`batch_manifest.json\`

Score each question from \`blind_responses.json\` using the same six common criteria in [EVALUATION_RUBRIC.md](../docs/EVALUATION_RUBRIC.md). Keep each \`system_key.json\` separate until the scores and written justifications for that question are finalized. Report RAVE-specific collective indicators separately. A single run per question is exploratory; it does not establish statistical reliability or general superiority.

This batch keeps \`shared_research\` enabled. Independent per-agent research is a separate experiment and must not be mixed into this version's results.
