"""Dated, fail-closed API pricing inputs.

The official OpenAI pricing page currently publishes gpt-4.1-mini rates and the
web-search call fee, but does not expose a dedicated gpt-5-search-api token row
in its model table. Do not substitute third-party estimates: require explicit
search-model rates from the account's applicable pricing/billing information.
"""
import os
from .budget import BudgetExceeded

PRICE_VERSION = "2026-11-13"
MODEL_RATES = {
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
}
WEB_SEARCH_USD_PER_CALL = 0.01 / 1000


def configured_model_rates() -> dict:
    rates = dict(MODEL_RATES)
    try:
        search_input = float(os.getenv("RAVE_SEARCH_INPUT_USD_PER_1M", ""))
        search_output = float(os.getenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", ""))
    except ValueError as exc:
        raise BudgetExceeded("invalid_search_model_pricing_configuration") from exc
    if search_input <= 0 or search_output <= 0:
        raise BudgetExceeded("official_search_model_token_rates_must_be_configured")
    rates["gpt-5-search-api"] = {"input": search_input, "output": search_output}
    return rates


def estimate_cost(model: str, input_tokens: int, output_tokens: int, web_search: bool = False) -> float:
    rates = configured_model_rates().get(model)
    if rates is None:
        raise BudgetExceeded(f"no_price_configured_for_model:{model}")
    token_cost = (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
    return token_cost + (WEB_SEARCH_USD_PER_CALL if web_search else 0.0)


def actual_cost(model: str, input_tokens: int, output_tokens: int, web_search: bool = False) -> float:
    return estimate_cost(model, input_tokens, output_tokens, web_search)
