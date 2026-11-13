import io
import json
import urllib.error
from unittest.mock import patch

import pytest

from solo_baseline.budget import BudgetController, BudgetExceeded, Limits
from solo_baseline.config import Settings
from solo_baseline.http_client import _NoRedirectHandler, post_chat_completion
from solo_baseline.telemetry import Telemetry


class FakeResponse:
    def __init__(self, obj):
        self.raw = json.dumps(obj).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.raw if size < 0 else self.raw[:size]


def setup_client(max_tokens=1000, max_seconds=60, max_searches=3, max_calls=10):
    settings = Settings("local-test-key", input_safety_margin_tokens=0)
    budget = BudgetController(
        Limits(
            max_tokens,
            max_searches,
            max_seconds,
            None,
            max_model_calls=max_calls,
            input_safety_margin_tokens=0,
        )
    )
    telemetry = Telemetry()
    payload = {"model": "gpt-4.1-mini", "max_completion_tokens": 64, "messages": []}
    return settings, budget, telemetry, payload


def test_retries_only_provider_rate_limit_and_respects_retry_after():
    settings, budget, telemetry, payload = setup_client(max_searches=1, max_calls=3)
    payload["model"] = settings.search_model
    body = json.dumps({
        "error": {
            "type": "rate_limit_error",
            "code": "rate_limit_exceeded",
            "message": "do not log me",
        }
    }).encode()
    limited = urllib.error.HTTPError(
        "https://api.openai.com/v1/chat/completions",
        429,
        "rate limited",
        {"Retry-After": "0"},
        io.BytesIO(body),
    )
    ok = FakeResponse({
        "choices": [{"message": {"content": "answer"}}],
        "usage": {"prompt_tokens": 4, "completion_tokens": 2},
    })

    with (
        patch("solo_baseline.http_client.urllib.request.urlopen", side_effect=[limited, ok]) as call,
        patch("solo_baseline.http_client.time.sleep") as sleep,
    ):
        _, message = post_chat_completion(settings, budget, telemetry, "search", payload)

    assert message["content"] == "answer"
    assert call.call_count == 2
    sleep.assert_called_once_with(0.0)
    assert [x["status"] for x in telemetry.calls] == ["FAILED", "COMPLETED"]
    assert budget.calls == 2
    assert budget.searches == 1
    assert budget.search_attempts == 2
    assert budget.tokens == 6
    assert budget.reserved_tokens == 0
    assert "do not log me" not in str(telemetry.calls)


@pytest.mark.parametrize("status,error", [
    (429, {"type": "invalid_request_error", "code": "insufficient_quota"}),
    (500, {"type": "server_error", "code": "internal_error"}),
])
def test_non_transient_errors_are_not_retried(status, error):
    settings, budget, telemetry, payload = setup_client()
    exc = urllib.error.HTTPError(
        "https://api.openai.com/v1/chat/completions",
        status,
        "failure",
        {},
        io.BytesIO(json.dumps({"error": error}).encode()),
    )

    with patch("solo_baseline.http_client.urllib.request.urlopen", side_effect=exc) as call:
        with pytest.raises(RuntimeError):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)

    assert call.call_count == 1
    assert len(telemetry.calls) == 1
    if status == 429:
        assert telemetry.calls[0]["token_accounting"] == "released_rejected_request"
        assert budget.unknown_usage_tokens == 0
    else:
        assert telemetry.calls[0]["token_accounting"] == "reservation_charged_unknown"
        assert budget.unknown_usage_tokens > 0
    assert budget.reserved_tokens == 0


def test_timeout_is_logged_once_and_reservation_charged_as_unknown():
    settings, budget, telemetry, payload = setup_client()

    with patch(
        "solo_baseline.http_client.urllib.request.urlopen",
        side_effect=TimeoutError("private details"),
    ) as call:
        with pytest.raises(TimeoutError):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)

    assert call.call_count == 1
    assert len(telemetry.calls) == 1
    assert telemetry.calls[0]["status"] == "FAILED"
    assert telemetry.calls[0]["token_accounting"] == "reservation_charged_unknown"
    assert budget.unknown_usage_tokens == telemetry.calls[0]["reserved_total_tokens"]
    assert "private details" not in str(telemetry.calls)


def test_pre_call_token_reservation_blocks_before_urlopen():
    settings, budget, telemetry, payload = setup_client(max_tokens=10)

    with patch("solo_baseline.http_client.urllib.request.urlopen") as call:
        with pytest.raises(BudgetExceeded, match="token_reservation_limit"):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)

    call.assert_not_called()
    assert budget.calls == 0
    assert telemetry.calls[0]["status"] == "BLOCKED_BUDGET"
    assert telemetry.calls[0]["token_accounting"] == "not_sent"


def test_success_records_pre_call_reservation_and_reconciles_usage():
    settings, budget, telemetry, payload = setup_client()
    ok = FakeResponse({
        "choices": [{"message": {"content": "answer"}}],
        "usage": {"prompt_tokens": 4, "completion_tokens": 2},
    })

    with patch("solo_baseline.http_client.urllib.request.urlopen", return_value=ok) as call:
        _, message = post_chat_completion(settings, budget, telemetry, "analysis", payload)

    assert message["content"] == "answer"
    assert call.call_count == 1
    record = telemetry.calls[0]
    assert record["estimated_input_tokens"] == record["request_bytes"]
    assert record["reserved_output_tokens"] == 64
    assert record["reserved_total_tokens"] == record["request_bytes"] + 64
    assert record["token_accounting"] == "provider_usage_committed"
    assert budget.tokens == 6
    assert budget.reserved_tokens == 0


def test_missing_usage_metadata_charges_unknown_and_preserves_safe_error():
    settings, budget, telemetry, payload = setup_client()
    invalid = FakeResponse({"choices": [{"message": {"content": "answer"}}]})

    with patch("solo_baseline.http_client.urllib.request.urlopen", return_value=invalid):
        with pytest.raises(RuntimeError, match="usage metadata"):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)

    assert len(telemetry.calls) == 1
    assert telemetry.calls[0]["token_accounting"] == "reservation_charged_unknown"
    assert budget.unknown_usage_tokens == telemetry.calls[0]["reserved_total_tokens"]
    assert budget.reserved_tokens == 0


def test_malformed_answer_envelope_keeps_reported_usage():
    settings, budget, telemetry, payload = setup_client()
    invalid = FakeResponse({
        "choices": [],
        "usage": {"prompt_tokens": 12, "completion_tokens": 5},
    })

    with patch("solo_baseline.http_client.urllib.request.urlopen", return_value=invalid):
        with pytest.raises(RuntimeError, match="no choices"):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)

    record = telemetry.calls[0]
    assert record["status"] == "FAILED"
    assert record["input_tokens"] == 12
    assert record["output_tokens"] == 5
    assert record["token_accounting"] == "provider_usage_committed"
    assert budget.tokens == 17
    assert budget.unknown_usage_tokens == 0


def test_retry_wait_cannot_exceed_remaining_wall_clock_budget():
    settings, budget, telemetry, payload = setup_client(max_seconds=60)
    body = json.dumps({
        "error": {"type": "rate_limit_error", "code": "rate_limit_exceeded"}
    }).encode()
    limited = urllib.error.HTTPError(
        "https://api.openai.com/v1/chat/completions",
        429,
        "rate limited",
        {"Retry-After": "2"},
        io.BytesIO(body),
    )

    with (
        patch("solo_baseline.http_client.urllib.request.urlopen", side_effect=limited) as call,
        patch.object(budget, "remaining", side_effect=[
            {"seconds": 10.0},
            {"seconds": 1.0},
        ]),
        patch("solo_baseline.http_client.time.sleep") as sleep,
    ):
        with pytest.raises(BudgetExceeded, match="retry_delay_exceeds_remaining_time_budget"):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)

    assert call.call_count == 1
    sleep.assert_not_called()
    assert telemetry.calls[0]["status"] == "FAILED"
    assert budget.reserved_tokens == 0


def test_usage_fields_must_be_non_boolean_integers():
    for value in (True, 1.5, "3", -1):
        settings, budget, telemetry, payload = setup_client()
        invalid = FakeResponse({
            "choices": [{"message": {"content": "answer"}}],
            "usage": {"prompt_tokens": value, "completion_tokens": 2},
        })
        with patch("solo_baseline.http_client.urllib.request.urlopen", return_value=invalid):
            with pytest.raises(RuntimeError, match="usage metadata"):
                post_chat_completion(settings, budget, telemetry, "analysis", payload)
        assert budget.unknown_usage_tokens > 0


def test_client_rejects_model_drift_before_network_call():
    settings, budget, telemetry, payload = setup_client()
    payload["model"] = "gpt-4.1"

    with patch("solo_baseline.http_client.urllib.request.urlopen") as call:
        with pytest.raises(ValueError, match="frozen comparison configuration"):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)

    call.assert_not_called()
    assert budget.calls == 0
    assert telemetry.calls == []



def test_redirect_handler_refuses_redirect_targets():
    handler = _NoRedirectHandler()
    request = __import__("urllib.request", fromlist=["Request"]).Request(
        "https://api.openai.com/v1/chat/completions",
        data=b"{}",
        headers={"Authorization": "Bearer test-secret"},
        method="POST",
    )
    redirected = handler.redirect_request(
        request, None, 302, "Found", {"Location": "https://attacker.invalid/collect"},
        "https://attacker.invalid/collect",
    )
    assert redirected is None


def test_http_client_uses_no_redirect_opener():
    settings, budget, telemetry, payload = setup_client()
    error = urllib.error.HTTPError(
        "https://api.openai.com/v1/chat/completions",
        302,
        "Found",
        {"Location": "https://attacker.invalid/collect"},
        io.BytesIO(b""),
    )
    fake_opener = __import__("unittest.mock", fromlist=["Mock"]).Mock()
    fake_opener.open.side_effect = error

    with patch("solo_baseline.http_client.urllib.request.build_opener", return_value=fake_opener) as build:
        with pytest.raises(RuntimeError, match="HTTP 302"):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)

    build.assert_called_once()
    fake_opener.open.assert_called_once()
    assert telemetry.calls[0]["token_accounting"] == "reservation_charged_unknown"
