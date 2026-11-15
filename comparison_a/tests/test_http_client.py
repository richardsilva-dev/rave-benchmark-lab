import io
import json
import urllib.error
from unittest.mock import patch

import pytest
from solo_baseline.budget import BudgetController, Limits
from solo_baseline.config import Settings
from solo_baseline.http_client import post_chat_completion
from solo_baseline.telemetry import Telemetry


class FakeResponse:
    def __init__(self, obj): self.raw=json.dumps(obj).encode()
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self): return self.raw


def setup_client():
    settings=Settings("local-test-key")
    budget=BudgetController(Limits(1000,3,60,None))
    telemetry=Telemetry()
    return settings,budget,telemetry,{"model":"gpt-4.1-mini","messages":[]}


def test_retries_only_provider_rate_limit_and_respects_retry_after():
    settings,budget,telemetry,payload=setup_client()
    body=json.dumps({"error":{"type":"rate_limit_error","code":"rate_limit_exceeded","message":"do not log me"}}).encode()
    limited=urllib.error.HTTPError("https://api.openai.com/v1/chat/completions",429,"rate limited",{"Retry-After":"0"},io.BytesIO(body))
    ok=FakeResponse({"choices":[{"message":{"content":"answer"}}],"usage":{"prompt_tokens":4,"completion_tokens":2}})
    with patch("solo_baseline.http_client.urllib.request.urlopen",side_effect=[limited,ok]) as call, patch("solo_baseline.http_client.time.sleep") as sleep:
        _,message=post_chat_completion(settings,budget,telemetry,"analysis",payload)
    assert message["content"]=="answer" and call.call_count==2
    sleep.assert_called_once_with(0.0)
    assert [x["status"] for x in telemetry.calls]==["FAILED","COMPLETED"]
    assert budget.calls==2 and budget.tokens==6
    assert "do not log me" not in str(telemetry.calls)


@pytest.mark.parametrize("status,error",[(429,{"type":"invalid_request_error","code":"insufficient_quota"}),(500,{"type":"server_error","code":"internal_error"})])
def test_non_transient_errors_are_not_retried(status,error):
    settings,budget,telemetry,payload=setup_client()
    exc=urllib.error.HTTPError("https://api.openai.com/v1/chat/completions",status,"failure",{},io.BytesIO(json.dumps({"error":error}).encode()))
    with patch("solo_baseline.http_client.urllib.request.urlopen",side_effect=exc) as call:
        with pytest.raises(RuntimeError): post_chat_completion(settings,budget,telemetry,"analysis",payload)
    assert call.call_count==1 and len(telemetry.calls)==1


def test_timeout_is_logged_once_without_retry():
    settings,budget,telemetry,payload=setup_client()
    with patch("solo_baseline.http_client.urllib.request.urlopen",side_effect=TimeoutError("private details")) as call:
        with pytest.raises(TimeoutError): post_chat_completion(settings,budget,telemetry,"analysis",payload)
    assert call.call_count==1 and telemetry.calls[0]["status"]=="FAILED"
    assert "private details" not in str(telemetry.calls)


def test_connection_reset_during_read_is_recorded_and_wrapped():
    settings,budget,telemetry,payload=setup_client()
    class ResetResponse(FakeResponse):
        def read(self): raise ConnectionResetError("reset")
    with patch("solo_baseline.http_client.urllib.request.urlopen",return_value=ResetResponse({})):
        with pytest.raises(RuntimeError,match="Could not reach LLM provider"):
            post_chat_completion(settings,budget,telemetry,"analysis",payload)
    assert [(x["status"],x["error"]) for x in telemetry.calls]==[("FAILED","ConnectionResetError")]
