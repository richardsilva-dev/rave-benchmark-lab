import pytest

from solo_baseline.budget import BudgetExceeded
from solo_baseline.pricing import (
    MODEL_RATES,
    WEB_SEARCH_USD_PER_CALL,
    MAX_ALLOWED_RUN_COST_USD,
    configured_model_rates,
    estimate_cost,
)


def test_gpt41_mini_uses_official_uncached_rates():
    assert MODEL_RATES["gpt-4.1-mini"]["input"] == 0.40
    assert MODEL_RATES["gpt-4.1-mini"]["output"] == 1.60


def test_gpt5_search_api_requires_explicit_user_rate(monkeypatch):
    monkeypatch.delenv("RAVE_SEARCH_INPUT_USD_PER_1M", raising=False)
    monkeypatch.delenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", raising=False)
    with pytest.raises(BudgetExceeded, match="missing_or_invalid_price_setting"):
        configured_model_rates()


def test_gpt5_search_api_uses_explicit_configured_rate(monkeypatch):
    monkeypatch.setenv("RAVE_SEARCH_INPUT_USD_PER_1M", "1.25")
    monkeypatch.setenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", "10.00")
    rates = configured_model_rates()
    assert rates["gpt-5-search-api"]["input"] == 1.25
    assert rates["gpt-5-search-api"]["output"] == 10.00


def test_web_search_fee_is_one_cent_per_call():
    assert WEB_SEARCH_USD_PER_CALL == pytest.approx(0.01)


def test_search_estimate_adds_tool_fee_and_configured_model_tokens(monkeypatch):
    monkeypatch.setenv("RAVE_SEARCH_INPUT_USD_PER_1M", "1.25")
    monkeypatch.setenv("RAVE_SEARCH_OUTPUT_USD_PER_1M", "10.00")
    cost = estimate_cost("gpt-5-search-api", 1_000_000, 100_000, web_search=True)
    assert cost == pytest.approx(1.25 + 1.00 + 0.01)


def test_initial_per_run_ceiling_is_fifty_cents():
    assert MAX_ALLOWED_RUN_COST_USD == pytest.approx(0.50)
