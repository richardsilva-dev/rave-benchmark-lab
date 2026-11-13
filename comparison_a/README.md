# Comparison A — solo baseline

One sequential researcher, one memory and no delegated agents. Uses a separate Python project/venv. Model/search defaults match the frozen RAVE reference (`gpt-4.1-mini`, `gpt-5-search-api`) when enabled. API execution is opt-in: `solo-baseline research ... --live`.

```powershell
cd comparison_a
uv sync --locked --extra dev
Copy-Item .env.example .env
uv run --locked --extra dev pytest -p no:cacheprovider -q
```

Live execution requires an API key and explicit limits; no numeric run-budget defaults are selected:

```powershell
uv run --locked --extra dev solo-baseline research "QUESTION" --scope "SCOPE" --live --max-tokens 50000 --max-searches 5 --max-seconds 300 --max-model-calls 12
```

The numbers above are command examples only, not approved benchmark budgets. Set limits before an experiment and keep them fixed in its manifest. Every model API attempt, including retry attempts, counts toward `--max-model-calls`.

## Token budget enforcement

Before every HTTP attempt, the client reserves:

- UTF-8 byte length of the serialized request as a conservative input-token estimate;
- the configured `RAVE_INPUT_SAFETY_MARGIN_TOKENS`;
- the request's explicit `max_completion_tokens` output cap.

Search and analysis output caps are separate settings. A provider response replaces the reservation with reported usage. A rejected HTTP 4xx releases the reservation. A timeout, 5xx, transport failure, oversized response or missing usage metadata conservatively charges the reservation as unknown usage, so later calls cannot reuse that budget.

This is a **pre-call conservative budget guard**, not an exact provider token ceiling: UTF-8 request bytes are not a model tokenizer, and hosted tools may add provider-side prompt/tool framing that is not visible to the client. Actual provider usage is reconciled after every successful response; if it exceeds the budget, the run stops and is marked incomplete. The metadata explicitly distinguishes actual token usage from unknown usage charged at the reserved estimate.

A USD cost cap is intentionally not exposed by the CLI until a dated model/search price schedule and cost estimator exist. Unknown cost is recorded as `null`, never zero.

The controlled research loop is intentionally sequential. Search uses the same hosted OpenAI Chat Completions web-search path observed in the frozen RAVE. The optional page reader has stricter network controls but is not enabled in the default equivalent path. No live API call is made by tests; a real API probe requires a locally configured `.env` and explicit `--live`.
