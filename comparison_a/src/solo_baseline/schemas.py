from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .source_utils import canonical_source_url, validate_source_record


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
        if (
            self.schema_version != "1.0"
            or not isinstance(self.request_id, str)
            or not self.request_id.strip()
            or len(self.request_id) > 256
            or self.system_id != "solo_baseline"
        ):
            raise ValueError("Invalid result identity or schema version")
        if self.status not in {"COMPLETED", "PARTIAL", "INVALID", "FAILED"}:
            raise ValueError("Invalid run status")
        if not isinstance(self.answer, str):
            raise ValueError("Result answer must be a string")
        if self.status == "COMPLETED" and not self.answer.strip():
            raise ValueError("Completed result must contain a non-empty answer")
        if self.status == "INVALID" and self.answer.strip():
            raise ValueError("Invalid result must not expose an unvalidated answer")
        if not isinstance(self.sources, list):
            raise ValueError("Result sources must be a list")
        if not isinstance(self.limitations, list) or any(
            not isinstance(item, str) for item in self.limitations
        ):
            raise ValueError("Result limitations must be a list of strings")

        seen = set()
        for source in self.sources:
            validate_source_record(source)
            identity = canonical_source_url(source["url"])
            if identity in seen:
                raise ValueError("Result sources must be deduplicated by canonical URL")
            seen.add(identity)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_dict(value):
    return asdict(value) if hasattr(value, "__dataclass_fields__") else value
