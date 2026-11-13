# Comparison A — single-agent baseline

This baseline reproduces the RAVE shared-research control path: one hosted web-search request using the shared-research instruction, followed by one reasoning-model synthesis request using the RAVE SingleAgent instruction/schema. It has no specialist decomposition, peer messages, or multi-agent refinement. It uses the same JSON-repair strategy if the reasoning response is malformed.

## Offline setup and tests

```powershell
cd comparison_a
uv sync --locked --extra dev
Copy-Item .env.example .env
uv run --locked --extra dev pytest -v
python tests/offline_smoke.py
```

## Required local pricing configuration

The official OpenAI pricing page lists GPT-4.1-mini uncached input/output rates ($0.40/$1.60 per million tokens) and Web Search at $10 per 1,000 calls plus search-content tokens billed at model rates. It does not provide a distinct GPT-5 Search API token-rate row. The application therefore refuses live calls until both values below are supplied in the ignored local `.env`, based on the applicable pricing record visible in the user's OpenAI Platform account:

- `RAVE_SEARCH_INPUT_USD_PER_1M`
- `RAVE_SEARCH_OUTPUT_USD_PER_1M`

Do not silently assume a rate from another model. The pricing values and their source must be captured in the run metadata. If the only available rate is the GPT-5 model row from the user's pricing screenshot, treat it as an explicit proxy assumption, not as a confirmed dedicated GPT-5 Search API rate.

## Live pilot safety

Every live invocation requires explicit limits for total tokens, search attempts, wall-clock time, estimated USD cost and total model-call attempts (retries included). The initial per-run estimated cost ceiling is USD 0.50. The pilot profile is:

- max total tokens: 80,000
- max search attempts: 3 (includes retry attempts)
- max wall time: 180 seconds
- max estimated cost: USD 0.50
- max model-call attempts: 5 (includes retries and JSON repair)
- search context: low; search output: 512 tokens; analysis output: 4,096 tokens

The preflight reserves UTF-8 prompt bytes, each request's completion cap and 16,384 additional input tokens for hosted search content. Provider-side search context is variable and can exceed that allowance. After each successful response, provider-reported usage and locally estimated cost are reconciled. Failed attempts retain their reservations conservatively. This is a local guardrail, not a provider-enforced billing cap. Configure a separate OpenAI project spend limit before making paid calls.

## First capped integration probe (not benchmark data)

Use the exact prior RAVE question and scope. Run this only after local pricing variables are configured and the offline tests pass:

```powershell
uv run solo-baseline research "Quais são os benefícios, riscos e recomendações atuais para o uso de inteligência artificial generativa na educação? Compare fontes institucionais e apresente limites e divergências." --scope "Usar o mesmo escopo do RAVE run válido de 2026-11-11; priorizar fontes institucionais; identificar data, evidência, limitações e divergências." --live --max-tokens 80000 --max-searches 3 --max-seconds 180 --max-cost-usd 0.50 --max-model-calls 12
```

The CLI prints the artifact directory. Each run writes `result.json` and `metadata.json` under `artifacts/runs/<run_id>/`. A run must report `COMPLETED`; `PARTIAL` or `FAILED` is not a valid matched output.

## Equivalence limits

- Models: `gpt-4.1-mini` and `gpt-5-search-api`.
- Search context: `low`.
- Search output cap: 512 tokens.
- Analysis output cap: 4,096 tokens.
- Temperature: 0.2.
- Search system instruction is aligned with `project_RAVE/rave/research.py`.
- Single-agent system instruction and JSON schema are aligned with `project_RAVE/rave/agents/single.py`.
- Malformed JSON repair follows the RAVE BaseAgent repair strategy and consumes the same token/cost budget.

The historical RAVE run from 2026-11-11 predates the matched 4,096-token analysis cap. Do not interpret it as a fully matched result until RAVE is rerun with the same cap and experimental limits. This first solo run is an integration pilot only, not an official comparative result.
