from dataclasses import dataclass
import os
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    analysis_model: str = "gpt-4.1-mini"
    search_model: str = "gpt-5-search-api"
    timeout_seconds: int = 90
    search_context_size: str = "low"
    search_max_output_tokens: int = 512

    @classmethod
    def from_env(cls) -> "Settings":
        try:
            timeout = int(os.getenv("RAVE_TIMEOUT_SECONDS", "90"))
            max_out = int(os.getenv("RAVE_SEARCH_MAX_OUTPUT_TOKENS", "512"))
        except ValueError as exc:
            raise ValueError("Timeout and token limit must be integers") from exc
        base = os.getenv("RAVE_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
        parsed = urlsplit(base)
        context = os.getenv("RAVE_SEARCH_CONTEXT_SIZE", "low").lower()
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("RAVE_BASE_URL must be HTTPS without credentials, query, or fragment")
        if parsed.hostname != "api.openai.com":
            raise ValueError("Hosted web search requires the official OpenAI endpoint; no provider fallback is allowed")
        if timeout <= 0 or max_out <= 0 or context not in {"low", "medium", "high"}:
            raise ValueError("Invalid timeout, search token limit, or context size")
        return cls(os.getenv("RAVE_API_KEY", "").strip(), base,
                   os.getenv("RAVE_MODEL", "gpt-4.1-mini").strip(),
                   os.getenv("RAVE_SEARCH_MODEL", "gpt-5-search-api").strip(),
                   timeout, context, max_out)
