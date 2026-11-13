from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlsplit


def _load_dotenv(path: str = ".env") -> None:
    """Load simple KEY=VALUE entries without overriding the process environment."""
    file = Path(path)
    if not file.is_file():
        return
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    analysis_model: str = "gpt-4.1-mini"
    search_model: str = "gpt-5-search-api"
    timeout_seconds: int = 90
    search_context_size: str = "low"
    search_max_output_tokens: int = 512
    analysis_max_output_tokens: int = 2048
    input_safety_margin_tokens: int = 1024

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        try:
            timeout = int(os.getenv("RAVE_TIMEOUT_SECONDS", "90"))
            search_max_out = int(os.getenv("RAVE_SEARCH_MAX_OUTPUT_TOKENS", "512"))
            analysis_max_out = int(os.getenv("RAVE_ANALYSIS_MAX_OUTPUT_TOKENS", "2048"))
            input_margin = int(os.getenv("RAVE_INPUT_SAFETY_MARGIN_TOKENS", "1024"))
        except ValueError as exc:
            raise ValueError("Timeout, output token caps and input safety margin must be integers") from exc
        base = os.getenv("RAVE_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
        parsed = urlsplit(base)
        context = os.getenv("RAVE_SEARCH_CONTEXT_SIZE", "low").lower()
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("RAVE_BASE_URL must be HTTPS without credentials, query, or fragment")
        if parsed.hostname != "api.openai.com":
            raise ValueError("Hosted web search requires the official OpenAI endpoint; no provider fallback is allowed")
        if timeout <= 0 or search_max_out <= 0 or analysis_max_out <= 0 or input_margin < 0 or context not in {"low", "medium", "high"}:
            raise ValueError("Invalid timeout, output token caps, input safety margin, or search context size")
        analysis_model = os.getenv("RAVE_MODEL", "gpt-4.1-mini").strip()
        search_model = os.getenv("RAVE_SEARCH_MODEL", "gpt-5-search-api").strip()
        if not analysis_model or not search_model:
            raise ValueError("Analysis and search model identifiers must not be empty")
        return cls(
            api_key=os.getenv("RAVE_API_KEY", "").strip(),
            base_url=base,
            analysis_model=analysis_model,
            search_model=search_model,
            timeout_seconds=timeout,
            search_context_size=context,
            search_max_output_tokens=search_max_out,
            analysis_max_output_tokens=analysis_max_out,
            input_safety_margin_tokens=input_margin,
        )
