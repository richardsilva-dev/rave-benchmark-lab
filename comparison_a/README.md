# Comparison A — single-agent baseline

This baseline reproduces the RAVE single-agent control path: one hosted web-search request using the same shared-research instruction, followed by one reasoning-model synthesis request using the RAVE SingleAgent instruction/schema. It has no specialist decomposition, peer messages, or multi-agent refinement. It uses the same JSON-repair strategy if the reasoning response is malformed.

## Offline setup and tests

```powershell
cd comparison_a
uv sync --extra dev
Copy-Item .env.example .env
uv run pytest -v
python tests/offline_smoke.py
```

## Live execution safety

Live mode requires explicit `--max-tokens`, `--max-searches`, `--max-seconds`, and `--max-cost-usd`. The client reserves token and cost capacity before every network attempt, including retries. Failed attempts retain their reservation conservatively. Unknown model prices fail closed.

The token preflight uses UTF-8 byte length as a conservative upper bound for locally supplied prompt text, a per-request completion cap, and a fixed hosted-search context allowance. Search context size is not an exact token count, so the allowance cannot guarantee a provider-side hard token ceiling. Provider-reported usage is reconciled after each successful response. This is a local guardrail, not an account-level billing hard cap; configure an API project spend limit separately.

The official OpenAI pricing page lists gpt-4.1-mini standard uncached input/output rates ($0.40/$1.60 per million tokens) and the web-search call fee ($0.01 per 1,000 calls), but its current model table does not publish a dedicated gpt-5-search-api token-rate row. Therefore live mode requires the user to set `RAVE_SEARCH_INPUT_USD_PER_1M` and `RAVE_SEARCH_OUTPUT_USD_PER_1M` in the local, uncommitted `.env` using the applicable rate shown by their OpenAI billing/pricing source. Do not copy third-party estimates. Until both values are supplied, live execution is blocked.

## Equivalent research behavior

- Models: `gpt-4.1-mini` and `gpt-5-search-api`.
- Search context: `low`.
- Search output cap: 512 tokens.
- Reasoning output cap: 4,096 tokens; the RAVE benchmark branch adds the same cap so both systems can be rerun under the same constraint.
- Temperature: 0.2.
- Search system instruction is aligned with `project_RAVE/rave/research.py`.
- Single-agent system instruction and JSON schema are aligned with `project_RAVE/rave/agents/single.py`.
- Malformed JSON repair follows the RAVE BaseAgent repair strategy and is included in the same token/cost budget.

The historical RAVE run from 2026-11-11 was executed before the shared 4,096-token reasoning output cap was added. It must not be treated as a fully matched Comparison A result. Rerun the RAVE Hive from the `benchmark-a-matched-output-budget` branch and the solo baseline from this branch with the same question, scope, model, context, and limits before interpreting the comparison.
