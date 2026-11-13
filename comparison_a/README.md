# Comparison A — solo baseline

One sequential researcher, one memory and no delegated agents. Uses a separate Python project/venv. Model/search defaults match the frozen RAVE reference (`gpt-4.1-mini`, `gpt-5-search-api`) when enabled. API execution is opt-in: `solo-baseline research ... --live`.

```powershell
cd comparison_a
uv sync --locked --extra dev
Copy-Item .env.example .env
uv run --locked --extra dev pytest -p no:cacheprovider -q
```

Live execution requires an API key and explicit limits; no numeric defaults are selected:

```powershell
uv run --locked --extra dev solo-baseline research "QUESTION" --scope "SCOPE" --live --max-tokens 50000 --max-searches 5 --max-seconds 300 --max-model-calls 12
```

The numbers above are command examples only, not approved benchmark budgets. Set limits before an experiment and keep them fixed in its manifest. Every model API attempt, including retry attempts, counts toward `--max-model-calls`.

A USD cost cap is intentionally not exposed by the CLI until a dated model/search price schedule and cost estimator exist. Unknown cost is recorded as `null`, never zero. Token usage is checked after each provider response; a single in-flight response can exceed the remaining token allowance, so this is a stop-on-observed-usage limit, not yet a strict pre-call token reservation.

The controlled research loop is intentionally sequential. Search uses the same hosted OpenAI web search path observed in RAVE. The optional page reader has stricter network controls but is not enabled in the default equivalent path. No live API call is made by tests; the first real call is an installation probe, not benchmark data.
