import pytest

from solo_baseline.pricing import (
    MODEL_RATES,
    WEB_SEARCH_USD_PER_CALL,
    MAX_ALLOWED_RUN_COST_USD,
    estimate_cost,
)


def test_gpt5_search_api_uses_published_gpt5_token_rates():
    assert MODEL_RATES["gpt-5-search-api"]["input"] == 1.25
    assert MODEL_RATES["gpt-5-search-api"]["output"] == 10.00
    assert MODEL_RATES["gpt-5-search-api"]["cached_input"] == 0.125


def test_web_search_fee_is_one_cent_per_call():
    assert WEB_SEARCH_USD_PER_CALL == pytest.approx(0.01)


def test_search_estimate_adds_tool_fee_and_model_tokens():
    cost = estimate_cost("gpt-5-search-api", 1_000_000, 100_000, web_search=True)
    assert cost == pytest.approx(1.25 + 1.00 + 0.01)


def test_initial_per_run_ceiling_is_fifty_cents():
    assert MAX_ALLOWED_RUN_COST_USD == pytest.approx(0.50)
