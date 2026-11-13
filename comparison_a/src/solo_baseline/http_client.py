"""OpenAI Chat Completions transport with pre-call resource reservations.

The input estimate is serialized UTF-8 request bytes plus a safety margin.
This is a conservative local estimate, not an exact tokenizer or a guarantee
about hidden provider-side prompts/tool framing. Output is capped explicitly.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import re
import time
import urllib.error
import urllib.request

from .budget import BudgetExceeded


MAX_REQUEST_BYTES = 1_100_000
MAX_RESPONSE_BYTES = 4_000_000


def _safe_error_fields(exc):
    try:
        payload = json.loads(exc.read(64_000).decode("utf-8", errors="replace"))
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        if not isinstance(error, dict):
            return "", ""
        values = []
        for field in ("code", "type"):
            value = error.get(field, "")
            values.append(
                value[:80]
                if isinstance(value, str)
                and value.replace("_", "").replace("-", "").isalnum()
                else ""
            )
        return tuple(values)
    except (AttributeError, OSError, ValueError, TypeError):
        return "", ""


def _retry_after_seconds(value):
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        duration = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", value)
        if duration and any(duration.groups()):
            hours, minutes, seconds_part = duration.groups()
            return max(0.0, int(hours or 0) * 3600 + int(minutes or 0) * 60 + float(seconds_part or 0))
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return None
    return max(0.0, seconds)


def _finalize_unknown(budget, reservation_id):
    if reservation_id in budget.reservations:
        return budget.commit_unknown_usage(reservation_id)
    return 0


def post_chat_completion(settings, budget, telemetry, kind, payload):
    if not settings.api_key:
        raise RuntimeError("RAVE_API_KEY is missing")
    output_cap = payload.get("max_completion_tokens")
    if not isinstance(output_cap, int) or isinstance(output_cap, bool) or output_cap <= 0:
        raise ValueError("Every provider request must declare a positive max_completion_tokens cap")

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_REQUEST_BYTES:
        raise ValueError("LLM request exceeds the configured safety limit")
    estimated_input_tokens = len(body)
    req = urllib.request.Request(
        settings.base_url + "/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.monotonic()
    last_attempt = 0

    for attempt in range(1, 4):
        last_attempt = attempt
        reservation_id = None
        try:
            reservation_id = budget.reserve(
                kind,
                attempt,
                estimated_input_tokens=estimated_input_tokens,
                reserved_output_tokens=output_cap,
            )
        except BudgetExceeded as exc:
            telemetry.calls.append({
                "kind": kind,
                "status": "BLOCKED_BUDGET",
                "duration_seconds": time.monotonic() - started,
                "attempt": attempt,
                "request_bytes": len(body),
                "estimated_input_tokens": estimated_input_tokens,
                "reserved_output_tokens": output_cap,
                "reserved_total_tokens": None,
                "input_tokens": None,
                "output_tokens": None,
                "token_accounting": "not_sent",
                "cost_usd": None,
                "stop_reason": str(exc),
            })
            raise

        reserved_total = (
            estimated_input_tokens
            + budget.limits.input_safety_margin_tokens
            + output_cap
        )
        try:
            remaining_seconds = budget.remaining()["seconds"]
            if remaining_seconds <= 0:
                raise BudgetExceeded("time_limit")
            timeout = min(settings.timeout_seconds, max(0.001, remaining_seconds))
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                unknown = _finalize_unknown(budget, reservation_id)
                telemetry.calls.append({
                    "kind": kind, "status": "FAILED", "duration_seconds": time.monotonic() - started,
                    "attempt": attempt, "request_bytes": len(body),
                    "estimated_input_tokens": estimated_input_tokens,
                    "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                    "input_tokens": None, "output_tokens": None,
                    "unknown_usage_tokens_charged": unknown,
                    "token_accounting": "reservation_charged_unknown",
                    "cost_usd": None, "error": "ResponseTooLarge",
                })
                raise RuntimeError("LLM provider response exceeded the configured size limit")

            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Provider response root must be an object")
            usage = data.get("usage")
            if not isinstance(usage, dict) or "prompt_tokens" not in usage or "completion_tokens" not in usage:
                unknown = _finalize_unknown(budget, reservation_id)
                telemetry.calls.append({
                    "kind": kind, "status": "FAILED", "duration_seconds": time.monotonic() - started,
                    "attempt": attempt, "request_bytes": len(body),
                    "estimated_input_tokens": estimated_input_tokens,
                    "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                    "input_tokens": None, "output_tokens": None,
                    "unknown_usage_tokens_charged": unknown,
                    "token_accounting": "reservation_charged_unknown",
                    "cost_usd": None, "error": "MissingUsageMetadata",
                })
                raise RuntimeError("LLM provider omitted required token usage metadata")

            try:
                input_tokens = int(usage["prompt_tokens"])
                output_tokens = int(usage["completion_tokens"])
            except (TypeError, ValueError) as exc:
                unknown = _finalize_unknown(budget, reservation_id)
                telemetry.calls.append({
                    "kind": kind, "status": "FAILED", "duration_seconds": time.monotonic() - started,
                    "attempt": attempt, "request_bytes": len(body),
                    "estimated_input_tokens": estimated_input_tokens,
                    "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                    "input_tokens": None, "output_tokens": None,
                    "unknown_usage_tokens_charged": unknown,
                    "token_accounting": "reservation_charged_unknown",
                    "cost_usd": None, "error": "InvalidUsageMetadata",
                })
                raise RuntimeError("LLM provider returned invalid token usage metadata") from exc
            if input_tokens < 0 or output_tokens < 0:
                unknown = _finalize_unknown(budget, reservation_id)
                telemetry.calls.append({
                    "kind": kind, "status": "FAILED", "duration_seconds": time.monotonic() - started,
                    "attempt": attempt, "request_bytes": len(body),
                    "estimated_input_tokens": estimated_input_tokens,
                    "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                    "input_tokens": None, "output_tokens": None,
                    "unknown_usage_tokens_charged": unknown,
                    "token_accounting": "reservation_charged_unknown",
                    "cost_usd": None, "error": "NegativeUsageMetadata",
                })
                raise RuntimeError("LLM provider returned negative token usage metadata")

            budget.commit_usage(reservation_id, input_tokens, output_tokens)
            telemetry.tokens_input += input_tokens
            telemetry.tokens_output += output_tokens

            choices = data.get("choices")
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                telemetry.calls.append({
                    "kind": kind, "status": "FAILED", "duration_seconds": time.monotonic() - started,
                    "attempt": attempt, "request_bytes": len(body),
                    "estimated_input_tokens": estimated_input_tokens,
                    "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                    "input_tokens": input_tokens, "output_tokens": output_tokens,
                    "token_accounting": "provider_usage_committed",
                    "cost_usd": None, "error": "InvalidChoices",
                })
                raise RuntimeError("LLM provider returned no choices")
            message = choices[0].get("message")
            if not isinstance(message, dict) or not isinstance(message.get("content"), str):
                telemetry.calls.append({
                    "kind": kind, "status": "FAILED", "duration_seconds": time.monotonic() - started,
                    "attempt": attempt, "request_bytes": len(body),
                    "estimated_input_tokens": estimated_input_tokens,
                    "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                    "input_tokens": input_tokens, "output_tokens": output_tokens,
                    "token_accounting": "provider_usage_committed",
                    "cost_usd": None, "error": "MissingTextContent",
                })
                raise RuntimeError("LLM provider returned no text content")

            telemetry.calls.append({
                "kind": kind, "status": "COMPLETED",
                "duration_seconds": time.monotonic() - started,
                "attempt": attempt, "request_bytes": len(body),
                "estimated_input_tokens": estimated_input_tokens,
                "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                "input_tokens": input_tokens, "output_tokens": output_tokens,
                "token_accounting": "provider_usage_committed",
                "cost_usd": None,
            })
            budget.check_after_call()
            return data, message

        except urllib.error.HTTPError as exc:
            code, error_type = _safe_error_fields(exc)
            retry_values = [
                _retry_after_seconds(exc.headers.get(header))
                for header in ("Retry-After", "x-ratelimit-reset-tokens")
            ]
            retry_after = max((value for value in retry_values if value is not None), default=None)
            transient = exc.code == 429 and (
                code in {"rate_limit_exceeded", "slow_down"} or error_type == "rate_limit_error"
            )
            rejected = 400 <= exc.code < 500
            unknown = 0 if rejected else _finalize_unknown(budget, reservation_id)
            if rejected and reservation_id in budget.reservations:
                budget.release(reservation_id)
            details = []
            if code:
                details.append(f"code={code}")
            if error_type:
                details.append(f"type={error_type}")
            if retry_after is not None:
                details.append(f"retry_after={retry_after:g}s")
            suffix = f" ({', '.join(details)})" if details else ""
            telemetry.calls.append({
                "kind": kind, "status": "FAILED",
                "duration_seconds": time.monotonic() - started,
                "attempt": attempt, "request_bytes": len(body),
                "estimated_input_tokens": estimated_input_tokens,
                "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                "input_tokens": None, "output_tokens": None,
                "unknown_usage_tokens_charged": unknown,
                "token_accounting": "released_rejected_request" if rejected else "reservation_charged_unknown",
                "cost_usd": None, "error": f"HTTP {exc.code}",
            })
            if transient and attempt < 3:
                delay = retry_after if retry_after is not None else 2 ** (attempt - 1)
                if delay <= 420:
                    time.sleep(delay)
                    continue
            raise RuntimeError(f"LLM provider returned HTTP {exc.code}{suffix}") from exc

        except urllib.error.URLError as exc:
            unknown = _finalize_unknown(budget, reservation_id)
            reason = type(exc.reason).__name__
            telemetry.calls.append({
                "kind": kind, "status": "FAILED",
                "duration_seconds": time.monotonic() - started,
                "attempt": attempt, "request_bytes": len(body),
                "estimated_input_tokens": estimated_input_tokens,
                "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                "input_tokens": None, "output_tokens": None,
                "unknown_usage_tokens_charged": unknown,
                "token_accounting": "reservation_charged_unknown",
                "cost_usd": None, "error": reason,
            })
            if isinstance(exc.reason, TimeoutError):
                raise TimeoutError("LLM request timed out") from exc
            raise RuntimeError("Could not reach LLM provider") from exc

        except TimeoutError as exc:
            unknown = _finalize_unknown(budget, reservation_id)
            telemetry.calls.append({
                "kind": kind, "status": "FAILED",
                "duration_seconds": time.monotonic() - started,
                "attempt": attempt, "request_bytes": len(body),
                "estimated_input_tokens": estimated_input_tokens,
                "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                "input_tokens": None, "output_tokens": None,
                "unknown_usage_tokens_charged": unknown,
                "token_accounting": "reservation_charged_unknown",
                "cost_usd": None, "error": "TimeoutError",
            })
            raise TimeoutError("LLM request timed out") from exc

        except BudgetExceeded:
            raise

        except Exception as exc:
            unknown = _finalize_unknown(budget, reservation_id)
            telemetry.calls.append({
                "kind": kind, "status": "FAILED",
                "duration_seconds": time.monotonic() - started,
                "attempt": attempt, "request_bytes": len(body),
                "estimated_input_tokens": estimated_input_tokens,
                "reserved_output_tokens": output_cap, "reserved_total_tokens": reserved_total,
                "input_tokens": None, "output_tokens": None,
                "unknown_usage_tokens_charged": unknown,
                "token_accounting": "reservation_charged_unknown" if unknown else "provider_usage_committed",
                "cost_usd": None, "error": type(exc).__name__,
            })
            raise RuntimeError("LLM provider response could not be validated") from exc

    raise RuntimeError(f"LLM provider call failed after {last_attempt} attempts")
