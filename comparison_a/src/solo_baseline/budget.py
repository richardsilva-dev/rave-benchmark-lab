from dataclasses import dataclass, field
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
        if self.max_tokens <= 0 or self.max_searches <= 0 or self.max_seconds <= 0:
            raise ValueError("All required budget limits must be positive")
        if self.max_cost_usd is not None and self.max_cost_usd <= 0:
            raise ValueError("Cost limit must be positive")
        if self.max_model_calls is not None and self.max_model_calls <= 0:
            raise ValueError("Model-call limit must be positive")
        if self.input_safety_margin_tokens < 0:
            raise ValueError("Input safety margin cannot be negative")


@dataclass
class BudgetController:
    limits: Limits
    started: float = field(default_factory=time.monotonic)
    tokens_input: int = 0
    tokens_output: int = 0
    unknown_usage_tokens: int = 0
    reserved_tokens: int = 0
    searches: int = 0
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
        """Reserve input plus maximum output before every network attempt.

        The input estimate is supplied by the transport from serialized request
        bytes plus a configured safety margin. It is deliberately conservative;
        it is not an exact tokenizer or a provider-side hard guarantee.
        """
        if kind not in {"search", "analysis"}:
            raise ValueError(f"Unsupported call kind: {kind}")
        if estimated_input_tokens < 0 or reserved_output_tokens <= 0:
            raise ValueError("Token estimates must be non-negative and output reservation positive")
        if time.monotonic() - self.started >= self.limits.max_seconds:
            raise BudgetExceeded("time_limit")
        if self.limits.max_model_calls is not None and self.calls >= self.limits.max_model_calls:
            raise BudgetExceeded("model_call_limit")
        if self.limits.max_cost_usd is not None and self.estimated_cost_usd is None:
            raise BudgetExceeded("cost_estimation_unavailable")
        if kind == "search" and self.searches >= self.limits.max_searches:
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
            self.searches += 1
        return reservation_id

    def release(self, reservation_id: int) -> int:
        """Release a reservation for a request known to have been rejected."""
        amount = self.reservations.pop(reservation_id, None)
        if amount is None:
            raise ValueError("Unknown or already finalized token reservation")
        self.reserved_tokens -= amount
        return amount

    def cancel_before_send(self, reservation_id: int, kind: str) -> int:
        """Cancel a reserved attempt only when no network request was submitted."""
        amount = self.release(reservation_id)
        self.calls -= 1
        if kind == "search":
            self.searches -= 1
        return amount

    def commit_usage(self, reservation_id: int, input_tokens: int, output_tokens: int) -> None:
        """Replace a pre-call reservation with usage reported by the provider."""
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token usage cannot be negative")
        self.release(reservation_id)
        self.tokens_input += input_tokens
        self.tokens_output += output_tokens

    def commit_unknown_usage(self, reservation_id: int) -> int:
        """Conservatively charge the full reservation when outcome/usage is unknown."""
        amount = self.release(reservation_id)
        self.unknown_usage_tokens += amount
        return amount

    def record_usage(self, input_tokens: int, output_tokens: int, cost_usd: float | None = None) -> None:
        """Record provider usage for offline tools/tests that have no reservation."""
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token usage cannot be negative")
        self.tokens_input += input_tokens
        self.tokens_output += output_tokens
        if cost_usd is not None:
            if cost_usd < 0:
                raise ValueError("Cost cannot be negative")
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
            "model_calls": None if self.limits.max_model_calls is None else max(0, self.limits.max_model_calls - self.calls),
            "seconds": max(0.0, self.limits.max_seconds - (time.monotonic() - self.started)),
            "cost_usd": None if self.limits.max_cost_usd is None or self.estimated_cost_usd is None else max(0.0, self.limits.max_cost_usd - self.estimated_cost_usd),
        }
