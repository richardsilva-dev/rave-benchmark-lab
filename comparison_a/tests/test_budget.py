import pytest

from solo_baseline.budget import BudgetController, BudgetExceeded, Limits


def make_budget(max_tokens=1000, max_searches=3, max_calls=10, margin=0):
    return BudgetController(
        Limits(
            max_tokens,
            max_searches,
            60,
            None,
            max_model_calls=max_calls,
            input_safety_margin_tokens=margin,
        )
    )


def test_search_retries_count_as_one_logical_search():
    budget = make_budget(max_searches=1, max_calls=3)
    budget.reserve("search", 1, estimated_input_tokens=10, reserved_output_tokens=10)
    budget.reserve("search", 2, estimated_input_tokens=10, reserved_output_tokens=10)

    assert budget.searches == 1
    assert budget.search_attempts == 2
    assert budget.calls == 2
    assert budget.remaining()["searches"] == 0

    with pytest.raises(BudgetExceeded, match="search_limit"):
        budget.reserve("search", 1, estimated_input_tokens=10, reserved_output_tokens=10)


def test_model_call_limit_counts_every_retry_attempt():
    budget = make_budget(max_calls=2)
    budget.reserve("search", 1, estimated_input_tokens=10, reserved_output_tokens=10)
    budget.reserve("search", 2, estimated_input_tokens=10, reserved_output_tokens=10)

    with pytest.raises(BudgetExceeded, match="model_call_limit"):
        budget.reserve("search", 3, estimated_input_tokens=10, reserved_output_tokens=10)

    assert budget.calls == 2
    assert budget.search_attempts == 2
    assert budget.searches == 1


def test_cancel_before_send_retry_does_not_undo_search_operation():
    budget = make_budget(max_searches=1, max_calls=3)
    first = budget.reserve("search", 1, estimated_input_tokens=10, reserved_output_tokens=10)
    second = budget.reserve("search", 2, estimated_input_tokens=10, reserved_output_tokens=10)
    budget.cancel_before_send(second, "search", 2)

    assert budget.searches == 1
    assert budget.search_attempts == 1
    assert budget.calls == 1
    assert first in budget.reservations


def test_cancel_before_send_first_attempt_undoes_unsubmitted_search():
    budget = make_budget(max_searches=1, max_calls=3)
    first = budget.reserve("search", 1, estimated_input_tokens=10, reserved_output_tokens=10)
    budget.cancel_before_send(first, "search", 1)

    assert budget.searches == 0
    assert budget.search_attempts == 0
    assert budget.calls == 0


def test_pre_call_reservation_rejects_request_before_budget_is_exceeded():
    budget = make_budget(max_tokens=100, margin=10)
    with pytest.raises(BudgetExceeded, match="token_reservation_limit"):
        budget.reserve("analysis", estimated_input_tokens=70, reserved_output_tokens=30)

    assert budget.calls == 0
    assert budget.reserved_tokens == 0


def test_success_reconciles_reservation_with_provider_usage():
    budget = make_budget(max_tokens=200, margin=10)
    reservation = budget.reserve(
        "analysis", estimated_input_tokens=50, reserved_output_tokens=40
    )
    assert budget.reserved_tokens == 100

    budget.commit_usage(reservation, 32, 12)

    assert budget.reserved_tokens == 0
    assert budget.tokens == 44
    assert budget.remaining()["tokens"] == 156


def test_unknown_usage_charges_reserved_upper_estimate():
    budget = make_budget(max_tokens=200, margin=10)
    reservation = budget.reserve(
        "search", estimated_input_tokens=50, reserved_output_tokens=40
    )
    charged = budget.commit_unknown_usage(reservation)

    assert charged == 100
    assert budget.unknown_usage_tokens == 100
    assert budget.reserved_tokens == 0
    assert budget.remaining()["tokens"] == 100


def test_release_rejected_request_does_not_charge_tokens():
    budget = make_budget(max_tokens=200, margin=10)
    reservation = budget.reserve(
        "analysis", estimated_input_tokens=50, reserved_output_tokens=40
    )
    budget.release(reservation)

    assert budget.tokens == 0
    assert budget.reserved_tokens == 0


def test_invalid_numeric_limits_rejected():
    with pytest.raises(ValueError):
        Limits(0, 1, 1, None)
    with pytest.raises(ValueError):
        Limits(100, True, 1, None)
    with pytest.raises(ValueError):
        Limits(100, 1, float("nan"), None)
    with pytest.raises(ValueError):
        Limits(100, 1, 1, None, max_model_calls=True)
    with pytest.raises(ValueError):
        Limits(100, 1, 1, None, input_safety_margin_tokens=1.5)


def test_cost_limit_fails_closed_without_pricing_estimator():
    budget = BudgetController(
        Limits(100, 3, 10, 1.0, max_model_calls=3, input_safety_margin_tokens=0)
    )
    with pytest.raises(BudgetExceeded, match="cost_estimation_unavailable"):
        budget.reserve("search", estimated_input_tokens=1, reserved_output_tokens=1)

    assert budget.calls == 0
