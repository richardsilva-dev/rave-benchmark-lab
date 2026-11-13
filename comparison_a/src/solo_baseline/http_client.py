"""OpenAI Chat Completions transport with pre-call resource reservations.

The input estimate is serialized UTF-8 request bytes plus a safety margin.
This is not an exact tokenizer or a guarantee about hidden provider-side
prompt/tool framing. Output is capped explicitly by max_completion_tokens.
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
MAX_RETRY_WAIT_SECONDS = 420


class ProviderResponseError(RuntimeError):
    """A provider response was received but failed safe structural validation."""


def _safe_error_fields(exc):
    """Extract only provider error identifiers; never retain the raw message."""
    try:
        body = exc.read(64_000)
        payload = json.loads(body.decode("utf-8", errors="replace"))
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
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    try:
        seconds = float(value)
    except ValueError:
        duration = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", value)
        if duration and any(duration.groups()):
            hours, minutes, seconds_part = duration.groups()
            return max(
                0.0,
                int(hours or 0) * 3600
                + int(minutes or 0) * 60
                + float(seconds_part or 0),
            )
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


def _attempt_record(kind, status, attempt, started, logical_started, **fields):
    record = {
        "kind": kind,
        "status": status,
        "attempt": attempt,
        "duration_seconds": max(0.0, time.monotonic() - started),
        "logical_call_elapsed_seconds": max(0.0, time.monotonic() - logical_started),
    }
    record.update(fields)
    return record


def post_chat_completion(settings, budget, telemetry, kind, payload):
    """Perform one logical API call, logging and budgeting every HTTP attempt."""
    if not settings.api_key:
        raise RuntimeError("RAVE_API_KEY is missing")
    expected_model = settings.search_model if kind == "search" else settings.analysis_model if kind == "analysis" else None
    if expected_model is None or payload.get("model") != expected_model:
        raise ValueError("Provider request model does not match the frozen comparison configuration")
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
    logical_started = time.monotonic()

    for attempt in range(1, 4):
        attempt_started = time.monotonic()
        reservation_id = None
        try:
            reservation_id = budget.reserve(
                kind,
                attempt,
                estimated_input_tokens=estimated_input_tokens,
                reserved_output_tokens=output_cap,
            )
        except BudgetExceeded as exc:
            telemetry.calls.append(_attempt_record(
                kind, "BLOCKED_BUDGET", attempt, attempt_started, logical_started,
                request_bytes=len(body),
                estimated_input_tokens=estimated_input_tokens,
                reserved_output_tokens=output_cap,
                reserved_total_tokens=None,
                input_tokens=None,
                output_tokens=None,
                token_accounting="not_sent",
                cost_usd=None,
                stop_reason=str(exc),
            ))
            raise

        input_tokens = None
        output_tokens = None
        reserved_total = (
            estimated_input_tokens
            + budget.limits.input_safety_margin_tokens
            + output_cap
        )

        try:
            remaining_seconds = budget.remaining()["seconds"]
            if remaining_seconds <= 0.001:
                raise BudgetExceeded("time_limit_before_request")
            timeout = min(float(settings.timeout_seconds), remaining_seconds)

            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ProviderResponseError("LLM provider response exceeded the configured size limit")

            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProviderResponseError("LLM provider returned invalid JSON") from exc
            if not isinstance(data, dict):
                raise ProviderResponseError("LLM provider response root must be an object")

            usage = data.get("usage")
            if not isinstance(usage, dict) or "prompt_tokens" not in usage or "completion_tokens" not in usage:
                raise ProviderResponseError("LLM provider omitted required token usage metadata")

            input_tokens = usage["prompt_tokens"]
            output_tokens = usage["completion_tokens"]
            for name, value in (("prompt_tokens", input_tokens), ("completion_tokens", output_tokens)):
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise ProviderResponseError(f"LLM provider returned invalid {name} usage metadata")

            # Usage is committed before validating the answer envelope so even
            # malformed model responses cannot escape token accounting.
            budget.commit_usage(reservation_id, input_tokens, output_tokens)
            telemetry.tokens_input += input_tokens
            telemetry.tokens_output += output_tokens

            if output_tokens > output_cap:
                telemetry.calls.append(_attempt_record(
                    kind, "FAILED_OUTPUT_CAP_VIOLATION", attempt, attempt_started, logical_started,
                    request_bytes=len(body),
                    estimated_input_tokens=estimated_input_tokens,
                    reserved_output_tokens=output_cap,
                    reserved_total_tokens=reserved_total,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    token_accounting="provider_usage_committed",
                    cost_usd=None,
                    error="ProviderExceededOutputCap",
                ))
                raise BudgetExceeded("provider_output_cap_exceeded")

            choices = data.get("choices")
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                raise ProviderResponseError("LLM provider returned no choices")
            message = choices[0].get("message")
            if not isinstance(message, dict) or not isinstance(message.get("content"), str):
                raise ProviderResponseError("LLM provider returned no text content")

            telemetry.calls.append(_attempt_record(
                kind, "COMPLETED", attempt, attempt_started, logical_started,
                request_bytes=len(body),
                estimated_input_tokens=estimated_input_tokens,
                reserved_output_tokens=output_cap,
                reserved_total_tokens=reserved_total,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                token_accounting="provider_usage_committed",
                cost_usd=None,
            ))
            try:
                budget.check_after_call()
            except BudgetExceeded as exc:
                # The provider call succeeded, but its measured usage or elapsed
                # time exceeded the run budget. Preserve that distinction.
                telemetry.calls[-1]["post_call_budget_status"] = "overrun_detected_after_response"
                telemetry.calls[-1]["stop_reason"] = str(exc)
                raise
            return data, message

        except urllib.error.HTTPError as exc:
            code, error_type = _safe_error_fields(exc)
            headers = exc.headers or {}
            retry_values = [
                _retry_after_seconds(headers.get(header))
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
            telemetry.calls.append(_attempt_record(
                kind, "FAILED", attempt, attempt_started, logical_started,
                request_bytes=len(body),
                estimated_input_tokens=estimated_input_tokens,
                reserved_output_tokens=output_cap,
                reserved_total_tokens=reserved_total,
                input_tokens=None,
                output_tokens=None,
                unknown_usage_tokens_charged=unknown,
                token_accounting="released_rejected_request" if rejected else "reservation_charged_unknown",
                cost_usd=None,
                error=f"HTTP {exc.code}",
            ))

            if transient and attempt < 3:
                delay = retry_after if retry_after is not None else 2 ** (attempt - 1)
                remaining_seconds = budget.remaining()["seconds"]
                if delay > MAX_RETRY_WAIT_SECONDS:
                    raise BudgetExceeded("retry_delay_exceeds_allowed_wait") from exc
                if delay >= remaining_seconds:
                    raise BudgetExceeded("retry_delay_exceeds_remaining_time_budget") from exc
                time.sleep(delay)
                continue
            raise RuntimeError(f"LLM provider returned HTTP {exc.code}{suffix}") from exc

        except urllib.error.URLError as exc:
            unknown = _finalize_unknown(budget, reservation_id)
            reason = type(exc.reason).__name__
            telemetry.calls.append(_attempt_record(
                kind, "FAILED", attempt, attempt_started, logical_started,
                request_bytes=len(body),
                estimated_input_tokens=estimated_input_tokens,
                reserved_output_tokens=output_cap,
                reserved_total_tokens=reserved_total,
                input_tokens=None,
                output_tokens=None,
                unknown_usage_tokens_charged=unknown,
                token_accounting="reservation_charged_unknown",
                cost_usd=None,
                error=reason,
            ))
            if isinstance(exc.reason, TimeoutError):
                raise TimeoutError("LLM request timed out") from exc
            raise RuntimeError("Could not reach LLM provider") from exc

        except TimeoutError as exc:
            unknown = _finalize_unknown(budget, reservation_id)
            telemetry.calls.append(_attempt_record(
                kind, "FAILED", attempt, attempt_started, logical_started,
                request_bytes=len(body),
                estimated_input_tokens=estimated_input_tokens,
                reserved_output_tokens=output_cap,
                reserved_total_tokens=reserved_total,
                input_tokens=None,
                output_tokens=None,
                unknown_usage_tokens_charged=unknown,
                token_accounting="reservation_charged_unknown",
                cost_usd=None,
                error="TimeoutError",
            ))
            raise TimeoutError("LLM request timed out") from exc

        except BudgetExceeded as exc:
            if reservation_id in budget.reservations:
                # Only pre-send budget checks reach here with a live reservation.
                budget.cancel_before_send(reservation_id, kind, attempt)
                telemetry.calls.append(_attempt_record(
                    kind, "BLOCKED_BUDGET", attempt, attempt_started, logical_started,
                    request_bytes=len(body),
                    estimated_input_tokens=estimated_input_tokens,
                    reserved_output_tokens=output_cap,
                    reserved_total_tokens=reserved_total,
                    input_tokens=None,
                    output_tokens=None,
                    token_accounting="not_sent",
                    cost_usd=None,
                    stop_reason=str(exc),
                ))
            raise

        except ProviderResponseError as exc:
            unknown = _finalize_unknown(budget, reservation_id)
            telemetry.calls.append(_attempt_record(
                kind, "FAILED", attempt, attempt_started, logical_started,
                request_bytes=len(body),
                estimated_input_tokens=estimated_input_tokens,
                reserved_output_tokens=output_cap,
                reserved_total_tokens=reserved_total,
                input_tokens=None if unknown else input_tokens,
                output_tokens=None if unknown else output_tokens,
                unknown_usage_tokens_charged=unknown,
                token_accounting="reservation_charged_unknown" if unknown else "provider_usage_committed",
                cost_usd=None,
                error="ProviderResponseError",
                validation_error=str(exc),
            ))
            raise

        except Exception as exc:
            unknown = _finalize_unknown(budget, reservation_id)
            telemetry.calls.append(_attempt_record(
                kind, "FAILED", attempt, attempt_started, logical_started,
                request_bytes=len(body),
                estimated_input_tokens=estimated_input_tokens,
                reserved_output_tokens=output_cap,
                reserved_total_tokens=reserved_total,
                input_tokens=None,
                output_tokens=None,
                unknown_usage_tokens_charged=unknown,
                token_accounting="reservation_charged_unknown" if unknown else "provider_usage_committed",
                cost_usd=None,
                error=type(exc).__name__,
            ))
            raise ProviderResponseError("LLM provider response could not be validated") from exc

    raise RuntimeError("LLM provider call failed after the retry limit")
