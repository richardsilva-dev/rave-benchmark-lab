import pytest
from solo_baseline.config import Settings

def test_model_defaults_match_rave(monkeypatch):
    monkeypatch.delenv("RAVE_BASE_URL",raising=False); monkeypatch.delenv("RAVE_MODEL",raising=False); monkeypatch.delenv("RAVE_SEARCH_MODEL",raising=False)
    s=Settings.from_env(); assert s.analysis_model=="gpt-4.1-mini" and s.search_model=="gpt-5-search-api"

def test_no_search_provider_fallback(monkeypatch):
    monkeypatch.setenv("RAVE_BASE_URL","https://example.com/v1")
    with pytest.raises(ValueError): Settings.from_env()
