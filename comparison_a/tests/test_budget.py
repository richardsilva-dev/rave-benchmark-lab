import pytest
from solo_baseline.budget import BudgetController, BudgetExceeded, Limits


def test_reservation_blocks_tokens_before_network_call():
    budget = BudgetController(Limits(100, 2, 10, 1.0))
    with pytest.raises(BudgetExceeded, match="token_budget_reservation_exceeded"):
        budget.reserve("analysis", 80, 21, 0.01)
    assert budget.calls == 0


def test_reservation_blocks_cost_before_network_call():
    budget = BudgetController(Limits(1000, 2, 10, 0.01))
    with pytest.raises(BudgetExceeded, match="cost_budget_reservation_exceeded"):
        budget.reserve("analysis", 10, 10, 0.011)
    assert budget.calls == 0


def test_search_limit_counts_each_attempt():
    budget = BudgetController(Limits(1000, 1, 10, 1.0))
    budget.reserve("search", 10, 10, 0.001)
    with pytest.raises(BudgetExceeded, match="search_limit"):
        budget.reserve("search", 10, 10, 0.001)


def test_usage_reconciles_reservation():
    budget = BudgetController(Limits(1000, 2, 10, 1.0))
    reservation = budget.reserve("analysis", 100, 50, 0.02)
    budget.record_usage(40, 20, reservation, 0.001)
    assert budget.tokens == 60
    assert budget.reserved_tokens == 0
    assert budget.estimated_cost_usd == pytest.approx(0.001)


def test_invalid_numeric_limits_rejected():
    with pytest.raises(ValueError):
        Limits(0, 1, 1, 1.0)
    with pytest.raises(ValueError):
        Limits(100, 1, 1, 0)
