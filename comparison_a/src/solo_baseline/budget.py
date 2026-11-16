from dataclasses import dataclass, field
import time


class BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class Limits:
    max_tokens: int
    max_searches: int
    max_seconds: float
    max_cost_usd: float
    max_model_calls: int | None = None

    def __post_init__(self):
        if self.max_tokens <= 0 or self.max_searches <= 0 or self.max_seconds <= 0:
            raise ValueError("Token, search and time limits must be positive")
        if self.max_cost_usd <= 0:
            raise ValueError("A positive cost ceiling is mandatory for live execution")
        if self.max_model_calls is not None and self.max_model_calls <= 0:
            raise ValueError("Model-call limit must be positive")


@dataclass
class BudgetController:
    limits: Limits
    started: float = field(default_factory=time.monotonic)
    tokens: int = 0
    searches: int = 0
    estimated_cost_usd: float = 0.0
    calls: int = 0
    reserved_tokens: int = 0
    reserved_cost_usd: float = 0.0

    def reserve(self, kind: str, estimated_input_tokens: int, max_output_tokens: int,
                estimated_cost_usd: float, attempt: int = 1) -> tuple[int, float]:
        """Fail closed before each network attempt; retries consume the same global budget."""
        if time.monotonic() - self.started >= self.limits.max_seconds:
            raise BudgetExceeded("time_limit")
        if self.limits.max_model_calls is not None and self.calls >= self.limits.max_model_calls:
            raise BudgetExceeded("model_call_limit")
        if kind == "search" and self.searches >= self.limits.max_searches:
            raise BudgetExceeded("search_limit")
        if estimated_input_tokens < 0 or max_output_tokens <= 0 or estimated_cost_usd < 0:
            raise ValueError("Invalid token or cost reservation")
        token_reservation = estimated_input_tokens + max_output_tokens
        if token_reservation <= 0:
            raise ValueError("A positive token reservation is required")
        if self.tokens + self.reserved_tokens + token_reservation > self.limits.max_tokens:
            raise BudgetExceeded("token_budget_reservation_exceeded")
        if self.estimated_cost_usd + self.reserved_cost_usd + estimated_cost_usd > self.limits.max_cost_usd:
            raise BudgetExceeded("cost_budget_reservation_exceeded")
        self.calls += 1
        if kind == "search":
            self.searches += 1
        self.reserved_tokens += token_reservation
        self.reserved_cost_usd += estimated_cost_usd
        return token_reservation, estimated_cost_usd

    def release_reservation(self, reservation: tuple[int, float]) -> None:
        """Release a reservation only when the provider definitively rejected the request."""
        reserved_tokens, reserved_cost = reservation
        self.reserved_tokens = max(0, self.reserved_tokens - reserved_tokens)
        self.reserved_cost_usd = max(0.0, self.reserved_cost_usd - reserved_cost)

    def record_usage(self, input_tokens: int, output_tokens: int, reservation: tuple[int, float],
                     actual_cost_usd: float) -> None:
        if input_tokens < 0 or output_tokens < 0 or actual_cost_usd < 0:
            raise ValueError("Usage and cost cannot be negative")
        reserved_tokens, reserved_cost = reservation
        self.reserved_tokens = max(0, self.reserved_tokens - reserved_tokens)
        self.reserved_cost_usd = max(0.0, self.reserved_cost_usd - reserved_cost)
        self.tokens += input_tokens + output_tokens
        self.estimated_cost_usd += actual_cost_usd
        if self.tokens + self.reserved_tokens > self.limits.max_tokens:
            raise BudgetExceeded("provider_usage_exceeded_reserved_token_budget")
        if self.estimated_cost_usd + self.reserved_cost_usd > self.limits.max_cost_usd:
            raise BudgetExceeded("provider_usage_exceeded_reserved_cost_budget")

    def check_after_call(self) -> None:
        if time.monotonic() - self.started > self.limits.max_seconds:
            raise BudgetExceeded("time_limit_reached_during_call")

    def remaining(self) -> dict:
        elapsed = time.monotonic() - self.started
        return {
            "tokens": max(0, self.limits.max_tokens - self.tokens - self.reserved_tokens),
            "searches": max(0, self.limits.max_searches - self.searches),
            "model_calls": None if self.limits.max_model_calls is None else max(0, self.limits.max_model_calls - self.calls),
            "seconds": max(0.0, self.limits.max_seconds - elapsed),
            "cost_usd": max(0.0, self.limits.max_cost_usd - self.estimated_cost_usd - self.reserved_cost_usd),
            "reserved_tokens": self.reserved_tokens,
            "reserved_cost_usd": round(self.reserved_cost_usd, 8),
        }
