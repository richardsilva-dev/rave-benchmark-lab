from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlsplit


def _load_dotenv(path: str = ".env") -> None:
    file = Path(path)
    if not file.is_file():
        return
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\\"'").strip())


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    analysis_model: str = "gpt-4.1-mini"
    search_model: str = "gpt-5-search-api"
    timeout_seconds: int = 90
    search_context_size: str = "low"
    search_max_output_tokens: int = 512
    analysis_max_output_tokens: int = 8192
    search_input_reserve_tokens: int = 16384

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        try:
            timeout = int(os.getenv("RAVE_TIMEOUT_SECONDS", "90"))
            search_out = int(os.getenv("RAVE_SEARCH_MAX_OUTPUT_TOKENS", "512"))
            # 4,096 repeatedly truncated valid research JSON in the pilot.
            # Keep an 8,192-token floor for both analysis and JSON repair.
            analysis_out = max(8192, int(os.getenv("RAVE_ANALYSIS_MAX_OUTPUT_TOKENS", "8192")))
            search_reserve = int(os.getenv("RAVE_SEARCH_INPUT_RESERVE_TOKENS", "16384"))
        except ValueError as exc:
            raise ValueError("Timeout and token reservation settings must be integers") from exc
        base = os.getenv("RAVE_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
        parsed = urlsplit(base)
        context = os.getenv("RAVE_SEARCH_CONTEXT_SIZE", "low").lower()
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("RAVE_BASE_URL must be HTTPS without credentials, query, or fragment")
        if parsed.hostname != "api.openai.com":
            raise ValueError("Hosted web search requires the official OpenAI endpoint; no provider fallback is allowed")
        if timeout <= 0 or search_out <= 0 or analysis_out <= 0 or search_reserve <= 0 or context not in {"low", "medium", "high"}:
            raise ValueError("Invalid timeout, output cap, search reservation, or context size")
        return cls(
            os.getenv("RAVE_API_KEY", "").strip(), base,
            os.getenv("RAVE_MODEL", "gpt-4.1-mini").strip(),
            os.getenv("RAVE_SEARCH_MODEL", "gpt-5-search-api").strip(),
            timeout, context, search_out, analysis_out, search_reserve,
        )
