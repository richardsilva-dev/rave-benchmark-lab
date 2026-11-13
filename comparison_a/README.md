# Comparison A — single-agent baseline

This baseline reproduces the RAVE single-agent control path: one hosted web-search call using the same shared-research instruction, followed by one reasoning-model synthesis call using the RAVE SingleAgent instruction/schema. It has no specialist decomposition, peer messages, or multi-agent refinement.

## Offline setup and tests

```powershell
cd comparison_a
uv sync --extra dev
Copy-Item .env.example .env
uv run pytest -v
```

## Live execution safety

Live mode requires explicit `--max-tokens`, `--max-searches`, `--max-seconds`, and `--max-cost-usd`. The client reserves token and cost capacity before every network attempt, including retries. Failed attempts retain their reservation conservatively. Unknown model prices fail closed.

The token preflight uses UTF-8 byte length as a conservative upper bound for locally supplied prompt text, a per-request completion cap, and a fixed 16,384-token allowance for hosted-search context. Hosted search context size is not an exact token cap, so the local budget is a guardrail, not an account-level hard billing limit. Provider-reported usage is reconciled after each successful response. Check account-level API spend limits separately.

The dated price table is in `src/solo_baseline/pricing.py`; it uses standard uncached rates and includes the hosted web-search call fee. Review it against the official OpenAI pricing page before each benchmark campaign.

## Equivalent research behavior

- Models: `gpt-4.1-mini` and `gpt-5-search-api`.
- Search context: `low`.
- Search output cap: 512 tokens.
- Reasoning output cap: 4,096 tokens (explicit local cap; confirm the RAVE run's actual output setting before interpreting results).
- Temperature: 0.2, matching the RAVE SingleAgent implementation.
- Search prompt and single-agent system instruction are aligned with `project_RAVE/rave/research.py` and `project_RAVE/rave/agents/single.py`.
