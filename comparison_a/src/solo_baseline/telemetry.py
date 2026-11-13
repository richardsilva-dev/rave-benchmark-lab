from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import time
import uuid


def utc_now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Telemetry:
    run_id: str = field(default_factory=lambda: "solo-" + uuid.uuid4().hex[:12])
    started_at: str = field(default_factory=utc_now)
    completed_at: str | None = None
    question: str = ""
    scope: str = ""
    analysis_model: str = ""
    search_model: str = ""
    search_provider: str = "openai_hosted_web_search"
    calls: list[dict] = field(default_factory=list)
    tokens_input: int = 0
    tokens_output: int = 0
    cost_estimated_usd: float | None = None
    duration_seconds: float = 0.0
    sources_count: int = 0
    model_reported_sources_count: int = 0
    rejected_sources_count: int = 0
    errors: list[str] = field(default_factory=list)
    status: str = "INVALID"
    stop_reason: str | None = None

    def finish(self, start: float):
        self.completed_at = utc_now()
        self.duration_seconds = time.monotonic() - start

    def to_dict(self):
        return asdict(self)
