"""Official OpenAI rates used for the Comparison A cost estimate.

GPT-5 Search API is the Chat Completions search-model path. The GPT-5 model
page publishes the GPT-5 token rates; OpenAI pricing lists Web Search at
$10/1,000 calls, plus search-content tokens at model rates.
Rates are USD per 1M tokens, except WEB_SEARCH_USD_PER_CALL.
Reviewed against official pricing/model docs on 2026-11-13.
"""
from .budget import BudgetExceeded

PRICE_VERSION = "2026-11-13"
MODEL_RATES = {
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60, "cached_input": 0.10},
    # GPT-5 Search API uses the GPT-5 search-model path. Apply GPT-5 published
    # token rates; search tool call fees are added separately below.
    "gpt-5-search-api": {"input": 1.25, "output": 10.00, "cached_input": 0.125},
}
WEB_SEARCH_USD_PER_CALL = 10.00 / 1000
MAX_ALLOWED_RUN_COST_USD = 0.50


def model_rate(model: str) -> dict:
    try:
        return MODEL_RATES[model]
    except KeyError as exc:
        raise BudgetExceeded(f"no_price_configured_for_model:{model}") from exc


def configured_model_rates() -> dict:
    return {name: dict(rates) for name, rates in MODEL_RATES.items()}


def estimate_cost(model: str, input_tokens: int, output_tokens: int, web_search: bool = False) -> float:
    rates = model_rate(model)
    token_cost = (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
    return token_cost + (WEB_SEARCH_USD_PER_CALL if web_search else 0.0)


def actual_cost(model: str, input_tokens: int, output_tokens: int, web_search: bool = False) -> float:
    return estimate_cost(model, input_tokens, output_tokens, web_search)
