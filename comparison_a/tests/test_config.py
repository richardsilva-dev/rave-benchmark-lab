import pytest

from solo_baseline.config import Settings


def test_model_defaults_match_rave(monkeypatch):
    for key in (
        "RAVE_BASE_URL", "RAVE_MODEL", "RAVE_SEARCH_MODEL",
        "RAVE_SEARCH_MAX_OUTPUT_TOKENS", "RAVE_ANALYSIS_MAX_OUTPUT_TOKENS",
        "RAVE_INPUT_SAFETY_MARGIN_TOKENS",
    ):
        monkeypatch.delenv(key, raising=False)
    settings = Settings.from_env()
    assert settings.analysis_model == "gpt-4.1-mini"
    assert settings.search_model == "gpt-5-search-api"
    assert settings.search_max_output_tokens == 512
    assert settings.analysis_max_output_tokens == 2048
    assert settings.input_safety_margin_tokens == 1024


def test_no_search_provider_fallback(monkeypatch):
    monkeypatch.setenv("RAVE_BASE_URL", "https://example.com/v1")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_invalid_output_limit_rejected(monkeypatch):
    monkeypatch.setenv("RAVE_ANALYSIS_MAX_OUTPUT_TOKENS", "0")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_invalid_negative_safety_margin_rejected(monkeypatch):
    monkeypatch.setenv("RAVE_INPUT_SAFETY_MARGIN_TOKENS", "-1")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_local_env_file_loads_without_overriding_process_environment(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("RAVE_API_KEY='file-key'\nRAVE_MODEL=file-model\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("RAVE_API_KEY", raising=False)
    monkeypatch.setenv("RAVE_MODEL", "process-model")
    settings = Settings.from_env()
    assert settings.api_key == "file-key"
    assert settings.analysis_model == "process-model"


@pytest.mark.parametrize("base_url", [
    "http://api.openai.com/v1",
    "https://api.openai.com",
    "https://api.openai.com/v1?redirect=https://example.org",
    "https://api.openai.com:8443/v1",
    "https://user:pass@api.openai.com/v1",
])
def test_manual_settings_cannot_override_official_provider_boundary(base_url):
    with pytest.raises(ValueError):
        Settings("test-key", base_url=base_url)


def test_api_key_cannot_contain_header_control_characters():
    with pytest.raises(ValueError):
        Settings("secret\r\nX-Injected: true")


@pytest.mark.parametrize("name,value", [
    ("RAVE_MODEL", "gpt-4.1"),
    ("RAVE_SEARCH_MODEL", "gpt-5-search-preview"),
])
def test_comparison_models_cannot_drift_through_environment(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError, match="pinned"):
        Settings.from_env()
