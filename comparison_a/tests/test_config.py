import pytest
from solo_baseline.config import Settings

def test_model_defaults_match_rave(monkeypatch):
    monkeypatch.delenv("RAVE_BASE_URL",raising=False); monkeypatch.delenv("RAVE_MODEL",raising=False); monkeypatch.delenv("RAVE_SEARCH_MODEL",raising=False)
    s=Settings.from_env(); assert s.analysis_model=="gpt-4.1-mini" and s.search_model=="gpt-5-search-api"

def test_no_search_provider_fallback(monkeypatch):
    monkeypatch.setenv("RAVE_BASE_URL","https://example.com/v1")
    with pytest.raises(ValueError): Settings.from_env()

def test_local_env_file_loads_without_overriding_process_environment(monkeypatch,tmp_path):
    (tmp_path/".env").write_text("RAVE_API_KEY=file-key\nRAVE_MODEL=file-model\n",encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("RAVE_API_KEY",raising=False)
    monkeypatch.setenv("RAVE_MODEL","process-model")
    settings=Settings.from_env()
    assert settings.api_key=="file-key" and settings.analysis_model=="process-model"
