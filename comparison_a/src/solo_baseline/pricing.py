"""Conservative OpenAI API price table for reproducible benchmark cost estimates.

Rates are USD per 1M tokens, standard uncached input/output. Review against the
official pricing page before each benchmark campaign; unknown models fail closed.
Web-search tool fee is USD 0.01 per 1,000 calls.
"""
from .budget import BudgetExceeded

PRICE_VERSION = "2026-11-13"
MODEL_RATES = {
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-5-search-api": {"input": 1.25, "output": 10.00},
}
WEB_SEARCH_USD_PER_CALL = 0.01 / 1000


def estimate_cost(model: str, input_tokens: int, output_tokens: int, web_search: bool = False) -> float:
    rates = MODEL_RATES.get(model)
    if rates is None:
        raise BudgetExceeded(f"no_published_price_configured_for_model:{model}")
    token_cost = (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
    return token_cost + (WEB_SEARCH_USD_PER_CALL if web_search else 0.0)


def actual_cost(model: str, input_tokens: int, output_tokens: int, web_search: bool = False) -> float:
    return estimate_cost(model, input_tokens, output_tokens, web_search)
