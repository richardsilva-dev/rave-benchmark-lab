import pytest
from solo_baseline.budget import BudgetController, BudgetExceeded, Limits


def test_search_budget_counts_retry_attempts():
    b=BudgetController(Limits(100,1,10,None)); b.reserve("search")
    with pytest.raises(BudgetExceeded): b.reserve("search",2)


def test_token_limit_stops_next_call():
    b=BudgetController(Limits(10,2,10,None)); b.reserve("analysis"); b.record_usage(8,3)
    with pytest.raises(BudgetExceeded): b.check_after_call()


def test_invalid_numeric_limits_rejected():
    with pytest.raises(ValueError): Limits(0,1,1,None)


def test_model_call_limit_counts_search_and_analysis_attempts():
    b=BudgetController(Limits(100,3,10,None,max_model_calls=2))
    b.reserve("search",1)
    b.reserve("analysis",1)
    with pytest.raises(BudgetExceeded, match="model_call_limit"):
        b.reserve("analysis",2)
    assert b.calls == 2


def test_model_call_limit_must_be_positive():
    with pytest.raises(ValueError):
        Limits(100,3,10,None,max_model_calls=0)


def test_cost_limit_fails_closed_without_pricing_estimator():
    b=BudgetController(Limits(100,3,10,1.0,max_model_calls=3))
    with pytest.raises(BudgetExceeded, match="cost_estimation_unavailable"):
        b.reserve("search")
    assert b.calls == 0
