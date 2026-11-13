from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit


@dataclass
class Source:
    url: str
    title: str = ""
    provenance: str = "provider_returned"


@dataclass
class ResearchResult:
    schema_version: str
    request_id: str
    system_id: str
    status: str
    answer: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.schema_version != "1.0" or not self.request_id or self.system_id != "solo_baseline":
            raise ValueError("Invalid result identity or schema version")
        if self.status not in {"COMPLETED", "PARTIAL", "INVALID", "FAILED"}:
            raise ValueError("Invalid run status")
        if self.status == "COMPLETED" and not self.answer.strip():
            raise ValueError("Completed result must contain a non-empty answer")
        for source in self.sources:
            u = urlsplit(str(source.get("url", "")))
            if u.scheme not in {"http", "https"} or not u.hostname or u.username or u.password:
                raise ValueError("Invalid citation URL")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_dict(value):
    return asdict(value) if hasattr(value, "__dataclass_fields__") else value
