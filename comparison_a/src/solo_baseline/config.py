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

    def __post_init__(self):
        if not isinstance(self.api_key, str) or any(
            ord(char) < 32 or ord(char) == 127 for char in self.api_key
        ):
            raise ValueError("API key must be a string without control characters")
        try:
            parsed = urlsplit(self.base_url)
            port = parsed.port
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid OpenAI API base URL") from exc
        if (
            parsed.scheme != "https"
            or parsed.hostname != "api.openai.com"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path.rstrip("/") != "/v1"
            or port not in (None, 443)
        ):
            raise ValueError("Base URL must be the official HTTPS OpenAI API endpoint /v1")
        if not isinstance(self.analysis_model, str) or not self.analysis_model.strip():
            raise ValueError("Analysis model identifier must not be empty")
        if not isinstance(self.search_model, str) or not self.search_model.strip():
            raise ValueError("Search model identifier must not be empty")
        if isinstance(self.timeout_seconds, bool) or not isinstance(self.timeout_seconds, int) or self.timeout_seconds <= 0:
            raise ValueError("Timeout must be a positive integer")
        if isinstance(self.search_max_output_tokens, bool) or not isinstance(self.search_max_output_tokens, int) or self.search_max_output_tokens <= 0:
            raise ValueError("Search output token cap must be a positive integer")
        if isinstance(self.analysis_max_output_tokens, bool) or not isinstance(self.analysis_max_output_tokens, int) or self.analysis_max_output_tokens <= 0:
            raise ValueError("Analysis output token cap must be a positive integer")
        if isinstance(self.input_safety_margin_tokens, bool) or not isinstance(self.input_safety_margin_tokens, int) or self.input_safety_margin_tokens < 0:
            raise ValueError("Input safety margin must be a non-negative integer")
        if self.search_context_size not in {"low", "medium", "high"}:
            raise ValueError("Search context size must be low, medium, or high")

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
        context = os.getenv("RAVE_SEARCH_CONTEXT_SIZE", "low").lower()
        analysis_model = os.getenv("RAVE_MODEL", "gpt-4.1-mini").strip()
        search_model = os.getenv("RAVE_SEARCH_MODEL", "gpt-5-search-api").strip()
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
