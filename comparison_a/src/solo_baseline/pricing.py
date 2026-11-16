"""Conservative local cost estimator for the Comparison A pilot.

The official OpenAI pricing page publishes GPT-4.1-mini rates and the Web
Search tool fee. It does not publish a distinct GPT-5 Search API token-rate
row. Therefore GPT-5 Search rates MUST be supplied explicitly in the user's
uncommitted .env from the applicable billing/pricing record; no proxy rate is
silently treated as an official rate.

Rates are USD per 1M tokens. Search fee is USD per 1,000 search calls.
"""
import math
import os

from .budget import BudgetExceeded

PRICE_VERSION = "2026-11-13-user-configured-search-rate"
WEB_SEARCH_USD_PER_CALL = 10.00 / 1000
MAX_ALLOWED_RUN_COST_USD = 0.50

MODEL_RATES = {
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60, "cached_input": 0.10},
}


def _positive_rate(name: str) -> float:
    raw = os.getenv(name, "").strip()
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise BudgetExceeded(f"missing_or_invalid_price_setting:{name}") from exc
    if not math.isfinite(value) or value <= 0:
        raise BudgetExceeded(f"missing_or_invalid_price_setting:{name}")
    return value


def model_rate(model: str) -> dict:
    if model == "gpt-5-search-api":
        return {
            "input": _positive_rate("RAVE_SEARCH_INPUT_USD_PER_1M"),
            "output": _positive_rate("RAVE_SEARCH_OUTPUT_USD_PER_1M"),
            "cached_input": 0.0,
        }
    try:
        return MODEL_RATES[model]
    except KeyError as exc:
        raise BudgetExceeded(f"no_price_configured_for_model:{model}") from exc


def configured_model_rates() -> dict:
    return {name: dict(model_rate(name)) for name in (*MODEL_RATES, "gpt-5-search-api")}


def estimate_cost(model: str, input_tokens: int, output_tokens: int, web_search: bool = False) -> float:
    rates = model_rate(model)
    token_cost = (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
    return token_cost + (WEB_SEARCH_USD_PER_CALL if web_search else 0.0)


def actual_cost(model: str, input_tokens: int, output_tokens: int, web_search: bool = False) -> float:
    return estimate_cost(model, input_tokens, output_tokens, web_search)
