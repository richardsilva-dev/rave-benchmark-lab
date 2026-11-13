from dataclasses import dataclass, field
import time


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class Limits:
    max_tokens: int
    max_searches: int
    max_seconds: float
    max_cost_usd: float | None
    max_model_calls: int | None = None

    def __post_init__(self):
        if self.max_tokens <= 0 or self.max_searches <= 0 or self.max_seconds <= 0:
            raise ValueError("All required budget limits must be positive")
        if self.max_cost_usd is not None and self.max_cost_usd <= 0:
            raise ValueError("Cost limit must be positive")
        if self.max_model_calls is not None and self.max_model_calls <= 0:
            raise ValueError("Model-call limit must be positive")


@dataclass
class BudgetController:
    limits: Limits
    started: float = field(default_factory=time.monotonic)
    tokens: int = 0
    searches: int = 0
    estimated_cost_usd: float | None = None
    calls: int = 0

    def reserve(self, kind: str, attempt: int = 1) -> None:
        """Reserve before every network attempt, including retries."""
        if time.monotonic() - self.started >= self.limits.max_seconds:
            raise BudgetExceeded("time_limit")
        if self.limits.max_model_calls is not None and self.calls >= self.limits.max_model_calls:
            raise BudgetExceeded("model_call_limit")
        if self.limits.max_cost_usd is not None and self.estimated_cost_usd is None:
            raise BudgetExceeded("cost_estimation_unavailable")
        if kind == "search" and self.searches >= self.limits.max_searches:
            raise BudgetExceeded("search_limit")
        if self.calls and self.tokens >= self.limits.max_tokens:
            raise BudgetExceeded("token_limit")
        self.calls += 1
        if kind == "search":
            self.searches += 1

    def record_usage(self, input_tokens: int, output_tokens: int, cost_usd: float | None = None) -> None:
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token usage cannot be negative")
        self.tokens += input_tokens + output_tokens
        if cost_usd is not None:
            if cost_usd < 0:
                raise ValueError("Cost cannot be negative")
            self.estimated_cost_usd = (self.estimated_cost_usd or 0.0) + cost_usd

    def check_after_call(self) -> None:
        if time.monotonic() - self.started > self.limits.max_seconds:
            raise BudgetExceeded("time_limit_reached_during_call")
        if self.tokens > self.limits.max_tokens:
            raise BudgetExceeded("token_limit_reached_after_call")
        if self.limits.max_cost_usd is not None and self.estimated_cost_usd is not None and self.estimated_cost_usd > self.limits.max_cost_usd:
            raise BudgetExceeded("cost_limit_reached_after_call")

    def remaining(self) -> dict:
        return {"tokens": max(0, self.limits.max_tokens - self.tokens),
                "searches": max(0, self.limits.max_searches - self.searches),
                "model_calls": None if self.limits.max_model_calls is None else max(0, self.limits.max_model_calls - self.calls),
                "seconds": max(0.0, self.limits.max_seconds - (time.monotonic() - self.started)),
                "cost_usd": None if self.limits.max_cost_usd is None or self.estimated_cost_usd is None else max(0.0, self.limits.max_cost_usd - self.estimated_cost_usd)}
