import io
import json
import urllib.error
from unittest.mock import patch

import pytest
from solo_baseline.budget import BudgetController, Limits, BudgetExceeded
from solo_baseline.config import Settings
from solo_baseline.http_client import post_chat_completion
from solo_baseline.telemetry import Telemetry


class FakeResponse:
    def __init__(self, obj):
        self.raw = json.dumps(obj).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self.raw


def setup_client(max_tokens=10000, max_cost=1.0):
    settings = Settings("local-test-key")
    budget = BudgetController(Limits(max_tokens, 3, 60, max_cost))
    telemetry = Telemetry()
    payload = {"model": "gpt-4.1-mini", "max_completion_tokens": 100, "messages": []}
    return settings, budget, telemetry, payload


def test_preflight_token_budget_blocks_before_http():
    settings, budget, telemetry, payload = setup_client(max_tokens=50)
    with patch("solo_baseline.http_client.urllib.request.urlopen") as call:
        with pytest.raises(BudgetExceeded):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)
    call.assert_not_called()


def test_retries_only_provider_rate_limit_and_respects_retry_after():
    settings, budget, telemetry, payload = setup_client()
    body = json.dumps({"error": {"type": "rate_limit_error", "code": "rate_limit_exceeded", "message": "do not log me"}}).encode()
    limited = urllib.error.HTTPError("https://api.openai.com/v1/chat/completions", 429, "rate limited",
                                     {"Retry-After": "0"}, io.BytesIO(body))
    ok = FakeResponse({"choices": [{"message": {"content": "answer"}}],
                       "usage": {"prompt_tokens": 4, "completion_tokens": 2}})
    with patch("solo_baseline.http_client.urllib.request.urlopen", side_effect=[limited, ok]) as call, \
         patch("solo_baseline.http_client.time.sleep") as sleep:
        _, message = post_chat_completion(settings, budget, telemetry, "analysis", payload)
    assert message["content"] == "answer" and call.call_count == 2
    sleep.assert_called_once_with(0.0)
    assert [item["status"] for item in telemetry.calls] == ["FAILED", "COMPLETED"]
    assert budget.calls == 2 and budget.tokens == 6
    assert "do not log me" not in str(telemetry.calls)


@pytest.mark.parametrize("status,error", [
    (429, {"type": "invalid_request_error", "code": "insufficient_quota"}),
    (500, {"type": "server_error", "code": "internal_error"}),
])
def test_non_transient_errors_are_not_retried(status, error):
    settings, budget, telemetry, payload = setup_client()
    exc = urllib.error.HTTPError("https://api.openai.com/v1/chat/completions", status, "failure", {},
                                 io.BytesIO(json.dumps({"error": error}).encode()))
    with patch("solo_baseline.http_client.urllib.request.urlopen", side_effect=exc) as call:
        with pytest.raises(RuntimeError):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)
    assert call.call_count == 1 and len(telemetry.calls) == 1


def test_timeout_is_logged_once_without_retry():
    settings, budget, telemetry, payload = setup_client()
    with patch("solo_baseline.http_client.urllib.request.urlopen", side_effect=TimeoutError("private details")) as call:
        with pytest.raises(TimeoutError):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)
    assert call.call_count == 1 and telemetry.calls[0]["status"] == "FAILED"
    assert "private details" not in str(telemetry.calls)


def test_unknown_model_price_fails_before_http():
    settings, budget, telemetry, payload = setup_client()
    payload["model"] = "unpriced-model"
    with patch("solo_baseline.http_client.urllib.request.urlopen") as call:
        with pytest.raises(BudgetExceeded):
            post_chat_completion(settings, budget, telemetry, "analysis", payload)
    call.assert_not_called()
