# Comparison A — solo baseline

One sequential researcher, one memory and no delegated agents. Uses a separate Python project/venv. Model/search defaults match the frozen RAVE reference (`gpt-4.1-mini`, `gpt-5-search-api`) when enabled. API execution is opt-in: `solo-baseline research ... --live`.

```powershell
cd comparison_a
uv sync --extra dev
Copy-Item .env.example .env
uv run pytest
```

No numeric research limits are set yet. `--live` refuses to run unless every budget limit is supplied. The controlled research loop is intentionally sequential. Search uses the same hosted OpenAI web search path observed in RAVE. The optional page reader has stricter network controls but is not enabled in the default equivalent path.
