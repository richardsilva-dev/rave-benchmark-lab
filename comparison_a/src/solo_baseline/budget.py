from dataclasses import dataclass, field
import math
import time


class BudgetExceeded(RuntimeError):
    """Raised when an execution would exceed a declared resource limit."""


@dataclass
class Limits:
    max_tokens: int
    max_searches: int
    max_seconds: float
    max_cost_usd: float | None
    max_model_calls: int | None = None
    input_safety_margin_tokens: int = 1024

    def __post_init__(self):
        for name, value in (
            ("max_tokens", self.max_tokens),
            ("max_searches", self.max_searches),
            ("input_safety_margin_tokens", self.input_safety_margin_tokens),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
        if self.max_tokens <= 0 or self.max_searches <= 0:
            raise ValueError("Token and logical-search limits must be positive")
        if self.input_safety_margin_tokens < 0:
            raise ValueError("Input safety margin cannot be negative")
        if isinstance(self.max_seconds, bool) or not isinstance(self.max_seconds, (int, float)):
            raise ValueError("Time limit must be a finite positive number")
        if not math.isfinite(self.max_seconds) or self.max_seconds <= 0:
            raise ValueError("Time limit must be a finite positive number")
        if self.max_model_calls is not None:
            if isinstance(self.max_model_calls, bool) or not isinstance(self.max_model_calls, int) or self.max_model_calls <= 0:
                raise ValueError("Model-call limit must be a positive integer")
        if self.max_cost_usd is not None:
            if isinstance(self.max_cost_usd, bool) or not isinstance(self.max_cost_usd, (int, float)):
                raise ValueError("Cost limit must be a finite positive number")
            if not math.isfinite(self.max_cost_usd) or self.max_cost_usd <= 0:
                raise ValueError("Cost limit must be a finite positive number")


@dataclass
class BudgetController:
    limits: Limits
    started: float = field(default_factory=time.monotonic)
    tokens_input: int = 0
    tokens_output: int = 0
    unknown_usage_tokens: int = 0
    reserved_tokens: int = 0
    searches: int = 0
    search_attempts: int = 0
    estimated_cost_usd: float | None = None
    calls: int = 0
    reservations: dict[int, int] = field(default_factory=dict)
    _next_reservation_id: int = 1

    @property
    def tokens(self) -> int:
        """Committed token use, including conservative charges for unknown usage."""
        return self.tokens_input + self.tokens_output + self.unknown_usage_tokens

    def reserve(
        self,
        kind: str,
        attempt: int = 1,
        *,
        estimated_input_tokens: int,
        reserved_output_tokens: int,
    ) -> int:
        """Reserve input and maximum output before every network attempt.

        A logical search is counted once (attempt 1). Retries are separate
        model-call attempts but do not consume additional logical-search slots.
        The input estimate is serialized request bytes plus a safety margin;
        it is not an exact tokenizer or provider-side hard guarantee.
        """
        if kind not in {"search", "analysis"}:
            raise ValueError(f"Unsupported call kind: {kind}")
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
            raise ValueError("Attempt number must be a positive integer")
        if (
            isinstance(estimated_input_tokens, bool)
            or not isinstance(estimated_input_tokens, int)
            or estimated_input_tokens < 0
        ):
            raise ValueError("Estimated input tokens must be a non-negative integer")
        if (
            isinstance(reserved_output_tokens, bool)
            or not isinstance(reserved_output_tokens, int)
            or reserved_output_tokens <= 0
        ):
            raise ValueError("Reserved output tokens must be a positive integer")
        if time.monotonic() - self.started >= self.limits.max_seconds:
            raise BudgetExceeded("time_limit")
        if self.limits.max_model_calls is not None and self.calls >= self.limits.max_model_calls:
            raise BudgetExceeded("model_call_limit")
        if self.limits.max_cost_usd is not None and self.estimated_cost_usd is None:
            raise BudgetExceeded("cost_estimation_unavailable")
        if kind == "search" and attempt == 1 and self.searches >= self.limits.max_searches:
            raise BudgetExceeded("search_limit")

        reservation = (
            estimated_input_tokens
            + self.limits.input_safety_margin_tokens
            + reserved_output_tokens
        )
        committed_and_reserved = self.tokens + self.reserved_tokens
        if committed_and_reserved + reservation > self.limits.max_tokens:
            raise BudgetExceeded("token_reservation_limit")

        reservation_id = self._next_reservation_id
        self._next_reservation_id += 1
        self.reservations[reservation_id] = reservation
        self.reserved_tokens += reservation
        self.calls += 1
        if kind == "search":
            self.search_attempts += 1
            if attempt == 1:
                self.searches += 1
        return reservation_id

    def release(self, reservation_id: int) -> int:
        """Release a reservation for a request known to have been rejected."""
        amount = self.reservations.pop(reservation_id, None)
        if amount is None:
            raise ValueError("Unknown or already finalized token reservation")
        self.reserved_tokens -= amount
        return amount

    def cancel_before_send(self, reservation_id: int, kind: str, attempt: int = 1) -> int:
        """Undo a reservation only when no network request was submitted."""
        amount = self.release(reservation_id)
        self.calls -= 1
        if kind == "search":
            self.search_attempts -= 1
            if attempt == 1:
                self.searches -= 1
        return amount

    def commit_usage(self, reservation_id: int, input_tokens: int, output_tokens: int) -> None:
        """Replace a pre-call reservation with usage reported by the provider."""
        for name, value in (("input_tokens", input_tokens), ("output_tokens", output_tokens)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        self.release(reservation_id)
        self.tokens_input += input_tokens
        self.tokens_output += output_tokens

    def commit_unknown_usage(self, reservation_id: int) -> int:
        """Conservatively charge the full reservation when usage is unknown."""
        amount = self.release(reservation_id)
        self.unknown_usage_tokens += amount
        return amount

    def record_usage(self, input_tokens: int, output_tokens: int, cost_usd: float | None = None) -> None:
        """Record provider usage for offline tools/tests that have no reservation."""
        for name, value in (("input_tokens", input_tokens), ("output_tokens", output_tokens)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        self.tokens_input += input_tokens
        self.tokens_output += output_tokens
        if cost_usd is not None:
            if isinstance(cost_usd, bool) or not isinstance(cost_usd, (int, float)):
                raise ValueError("Cost must be a finite non-negative number")
            if not math.isfinite(cost_usd) or cost_usd < 0:
                raise ValueError("Cost must be a finite non-negative number")
            self.estimated_cost_usd = (self.estimated_cost_usd or 0.0) + cost_usd

    def check_after_call(self) -> None:
        if time.monotonic() - self.started > self.limits.max_seconds:
            raise BudgetExceeded("time_limit_reached_during_call")
        if self.tokens + self.reserved_tokens > self.limits.max_tokens:
            raise BudgetExceeded("token_limit_reached_after_call")
        if self.limits.max_cost_usd is not None and self.estimated_cost_usd is not None and self.estimated_cost_usd > self.limits.max_cost_usd:
            raise BudgetExceeded("cost_limit_reached_after_call")

    def remaining(self) -> dict:
        spent_or_reserved = self.tokens + self.reserved_tokens
        return {
            "tokens": max(0, self.limits.max_tokens - spent_or_reserved),
            "tokens_committed": self.tokens,
            "tokens_reserved": self.reserved_tokens,
            "tokens_unknown_usage": self.unknown_usage_tokens,
            "searches": max(0, self.limits.max_searches - self.searches),
            "searches_used": self.searches,
            "search_attempts": self.search_attempts,
            "model_calls": None if self.limits.max_model_calls is None else max(0, self.limits.max_model_calls - self.calls),
            "model_calls_used": self.calls,
            "seconds": max(0.0, self.limits.max_seconds - (time.monotonic() - self.started)),
            "cost_usd": None if self.limits.max_cost_usd is None or self.estimated_cost_usd is None else max(0.0, self.limits.max_cost_usd - self.estimated_cost_usd),
        }
