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
