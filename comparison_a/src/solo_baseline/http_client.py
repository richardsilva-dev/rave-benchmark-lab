"""Shared OpenAI Chat Completions transport matching the frozen RAVE retry policy."""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import re
import time
import urllib.error
import urllib.request

from .budget import BudgetExceeded


def _safe_error_fields(exc):
    try:
        payload=json.loads(exc.read(64_000).decode("utf-8",errors="replace"))
        error=payload.get("error",{}) if isinstance(payload,dict) else {}
        if not isinstance(error,dict): return "",""
        values=[]
        for field in ("code","type"):
            value=error.get(field," ")
            values.append(value[:80] if isinstance(value,str) and value.replace("_","").replace("-","").isalnum() else "")
        return tuple(values)
    except (AttributeError,OSError,ValueError,TypeError):
        return "",""


def _retry_after_seconds(value):
    if not value: return None
    try: seconds=float(value)
    except ValueError:
        duration=re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?",value)
        if duration and any(duration.groups()):
            h,m,s=duration.groups(); return max(0.0,int(h or 0)*3600+int(m or 0)*60+float(s or 0))
        try:
            retry_at=parsedate_to_datetime(value)
            if retry_at.tzinfo is None: retry_at=retry_at.replace(tzinfo=timezone.utc)
            seconds=(retry_at-datetime.now(timezone.utc)).total_seconds()
        except (TypeError,ValueError,OverflowError): return None
    return max(0.0,seconds)


def post_chat_completion(settings,budget,telemetry,kind,payload):
    if not settings.api_key: raise RuntimeError("RAVE_API_KEY is missing")
    body=json.dumps(payload).encode("utf-8")
    if len(body)>1_100_000: raise ValueError("LLM request exceeds the configured safety limit")
    req=urllib.request.Request(settings.base_url+"/chat/completions",data=body,
        headers={"Authorization":f"Bearer {settings.api_key}","Content-Type":"application/json"},method="POST")
    started=time.monotonic(); last_attempt=0
    for attempt in range(1,4):
        last_attempt=attempt
        try:
            budget.reserve(kind,attempt)
        except BudgetExceeded:
            telemetry.calls.append({"kind":kind,"status":"BLOCKED_BUDGET","duration_seconds":time.monotonic()-started,"attempt":attempt,
                                    "input_tokens":None,"output_tokens":None,"cost_usd":None})
            raise
        try:
            timeout=min(settings.timeout_seconds,max(0.001,budget.remaining()["seconds"]))
            with urllib.request.urlopen(req,timeout=timeout) as response:
                data=json.loads(response.read().decode("utf-8"))
            if not isinstance(data,dict): raise RuntimeError("LLM provider returned an invalid Chat Completions response")
            message=data["choices"][0]["message"]
            content=message["content"]
            if not isinstance(message,dict) or not isinstance(content,str): raise RuntimeError("LLM provider returned no text content")
            usage=data.get("usage") or {}
            if not isinstance(usage,dict): raise RuntimeError("LLM provider returned invalid usage metadata")
            try:
                input_tokens=max(0,int(usage.get("prompt_tokens",0))); output_tokens=max(0,int(usage.get("completion_tokens",0)))
            except (TypeError,ValueError) as exc: raise RuntimeError("LLM provider returned invalid usage metadata") from exc
            budget.record_usage(input_tokens,output_tokens)
            telemetry.tokens_input+=input_tokens; telemetry.tokens_output+=output_tokens
            telemetry.calls.append({"kind":kind,"status":"COMPLETED","duration_seconds":time.monotonic()-started,"attempt":attempt,
                                    "input_tokens":input_tokens,"output_tokens":output_tokens,"cost_usd":None})
            budget.check_after_call()
            return data,message
        except urllib.error.HTTPError as exc:
            code,error_type=_safe_error_fields(exc)
            retry_values=[_retry_after_seconds(exc.headers.get(h)) for h in ("Retry-After","x-ratelimit-reset-tokens")]
            retry_after=max((v for v in retry_values if v is not None),default=None)
            transient=exc.code==429 and (code in {"rate_limit_exceeded","slow_down"} or error_type=="rate_limit_error")
            details=[]
            if code: details.append(f"code={code}")
            if error_type: details.append(f"type={error_type}")
            if retry_after is not None: details.append(f"retry_after={retry_after:g}s")
            suffix=f" ({', '.join(details)})" if details else ""
            telemetry.calls.append({"kind":kind,"status":"FAILED","duration_seconds":time.monotonic()-started,"attempt":attempt,
                                    "input_tokens":None,"output_tokens":None,"cost_usd":None,"error":f"HTTP {exc.code}"})
            if transient and attempt<3:
                delay=retry_after if retry_after is not None else 2**(attempt-1)
                if delay<=420:
                    time.sleep(delay); continue
            raise RuntimeError(f"LLM provider returned HTTP {exc.code}{suffix}") from exc
        except urllib.error.URLError as exc:
            telemetry.calls.append({"kind":kind,"status":"FAILED","duration_seconds":time.monotonic()-started,"attempt":attempt,
                                    "input_tokens":None,"output_tokens":None,"cost_usd":None,"error":type(exc.reason).__name__})
            if isinstance(exc.reason,TimeoutError): raise TimeoutError("LLM request timed out") from exc
            raise RuntimeError("Could not reach LLM provider") from exc
        except TimeoutError as exc:
            telemetry.calls.append({"kind":kind,"status":"FAILED","duration_seconds":time.monotonic()-started,"attempt":attempt,
                                    "input_tokens":None,"output_tokens":None,"cost_usd":None,"error":"TimeoutError"})
            raise TimeoutError("LLM request timed out") from exc
        except BudgetExceeded:
            raise
        except (UnicodeDecodeError,json.JSONDecodeError,KeyError,IndexError,TypeError,ValueError,RuntimeError) as exc:
            telemetry.calls.append({"kind":kind,"status":"FAILED","duration_seconds":time.monotonic()-started,"attempt":attempt,
                                    "input_tokens":None,"output_tokens":None,"cost_usd":None,"error":type(exc).__name__})
            raise RuntimeError("LLM provider returned an invalid Chat Completions response") from exc
    raise RuntimeError(f"LLM provider call failed after {last_attempt} attempts")
