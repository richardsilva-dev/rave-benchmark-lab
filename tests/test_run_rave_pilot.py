import io
import json
import urllib.error
import urllib.request

import pytest

from scripts import run_rave_pilot as pilot


def test_parse_dotenv_keeps_values_private_and_parses_equals(tmp_path):
    path = tmp_path / ".env"
    path.write_text('RAVE_API_KEY="secret-value"\nRAVE_SEARCH_INPUT_USD_PER_1M=1.25\n# comment\n', encoding="utf-8")
    values = pilot.parse_dotenv(path)
    assert values == {"RAVE_API_KEY": "secret-value", "RAVE_SEARCH_INPUT_USD_PER_1M": "1.25"}


def test_build_child_env_maps_comparison_a_names_to_rave_settings():
    values = {
        "RAVE_API_KEY": "not-a-real-key",
        "RAVE_BASE_URL": "https://api.openai.com/v1",
        "RAVE_MODEL": "gpt-4.1-mini",
        "RAVE_SEARCH_MODEL": "gpt-5-search-api",
        "RAVE_SEARCH_INPUT_USD_PER_1M": "1.25",
        "RAVE_SEARCH_OUTPUT_USD_PER_1M": "10.0",
    }
    env = pilot.build_child_env(values)
    assert env["RAVE_WEB_SEARCH_MODEL"] == "gpt-5-search-api"
    assert env["RAVE_WEB_SEARCH_CONTEXT_SIZE"] == "low"
    assert env["RAVE_RESEARCH_MODE"] == "shared_research"
    assert env["RAVE_ANALYSIS_MAX_OUTPUT_TOKENS"] == "4096"
    assert env["RAVE_SYNTHESIS_MAX_OUTPUT_TOKENS"] == "8192"
    assert env["RAVE_MAX_RUN_TOKENS"] == "80000"


def test_build_child_env_rejects_missing_key():
    with pytest.raises(ValueError, match="RAVE_API_KEY"):
        pilot.build_child_env({
            "RAVE_SEARCH_INPUT_USD_PER_1M": "1.25",
            "RAVE_SEARCH_OUTPUT_USD_PER_1M": "10.0",
        })


def test_auth_preflight_does_not_echo_key_on_401(monkeypatch):
    error = urllib.error.HTTPError(
        "https://api.openai.com/v1/models", 401, "Unauthorized", {}, io.BytesIO(b"")
    )
    monkeypatch.setattr(pilot, "_open_preflight", lambda *args, **kwargs: (_ for _ in ()).throw(error))
    with pytest.raises(RuntimeError) as exc:
        pilot.check_api_auth("https://api.openai.com/v1", "secret-value")
    assert "secret-value" not in str(exc.value)
    assert "No paid research request was sent" in str(exc.value)


def test_validate_baseline_rejects_non_completed_run(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "LAB_ROOT", tmp_path)
    run_dir = tmp_path / "artifacts" / "runs" / "run-1"
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(json.dumps({"status": "FAILED"}), encoding="utf-8")
    (run_dir / "result.json").write_text(json.dumps({"status": "FAILED"}), encoding="utf-8")
    with pytest.raises(ValueError, match="not COMPLETED"):
        pilot.validate_baseline("run-1")



def test_validate_baseline_reuses_the_preserved_completed_run(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "LAB_ROOT", tmp_path)
    run_dir = tmp_path / "artifacts" / "runs" / "pilot"
    run_dir.mkdir(parents=True)
    metadata = {
        "status": "COMPLETED",
        "question": pilot.QUESTION_DEFAULT,
        "scope": pilot.QUESTION_SCOPE_DEFAULT,
        "analysis_model": "gpt-4.1-mini",
        "search_model": "gpt-5-search-api",
        "search_provider": "openai_hosted_web_search",
        "search_input_reservation_tokens": 8192,
        "budget_limits": {
            "max_tokens": 80000,
            "max_searches": 3,
            "max_model_calls": 12,
            "max_seconds": 180,
            "max_cost_usd": 0.50,
        },
        "pricing_rates_usd_per_1m": {"gpt-5-search-api": {"input": 1.25, "output": 10.0}},
    }
    result = {"status": "COMPLETED", "answer": "Preserved answer", "sources": [], "limitations": []}
    (run_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (run_dir / "result.json").write_text(json.dumps(result), encoding="utf-8")
    loaded_meta, loaded_result, loaded_dir = pilot.validate_baseline("pilot")
    assert loaded_meta["question"] == pilot.QUESTION_DEFAULT
    assert loaded_result["answer"] == "Preserved answer"
    assert loaded_dir == run_dir


def test_validate_baseline_rejects_a_different_question(tmp_path, monkeypatch):
    monkeypatch.setattr(pilot, "LAB_ROOT", tmp_path)
    run_dir = tmp_path / "artifacts" / "runs" / "other"
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(json.dumps({
        "status": "COMPLETED", "question": "different", "scope": pilot.QUESTION_SCOPE_DEFAULT,
    }), encoding="utf-8")
    (run_dir / "result.json").write_text(json.dumps({
        "status": "COMPLETED", "answer": "answer",
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="question/scope"):
        pilot.validate_baseline("other")



def test_compose_rave_answer_keeps_all_comparable_final_sections():
    answer = pilot.compose_rave_answer({
        "executive_answer": "Executive",
        "integrated_analysis": "Analysis",
        "collective_integration": "Collective",
        "conclusions": "Conclusion",
        "gaps_and_limitations": ["Not part of answer body"],
    })
    assert answer == "Executive\n\nAnalysis\n\nCollective\n\nConclusion"


def test_blinded_response_order_is_randomizable_and_key_is_separate():
    baseline = {"answer": "A", "sources": [{"url": "https://a.example"}], "limitations": []}
    rave = {"answer": "B", "sources": [{"url": "https://b.example"}], "limitations": []}
    responses, key = pilot.build_blinded_responses(baseline, rave, ("rave_hive", "solo_baseline"))
    assert [item["response_id"] for item in responses] == ["response_01", "response_02"]
    assert [item["answer"] for item in responses] == ["B", "A"]
    assert key == {"response_01": "rave_hive", "response_02": "solo_baseline"}
    assert all(set(item) == {"response_id", "answer", "sources", "limitations"} for item in responses)


def test_model_reported_sources_are_marked_without_changing_provider_sources():
    sources = pilot.normalize_rave_sources(
        [{"url": "https://provider.example", "title": "Provider"}],
        ["https://model.example"],
    )
    assert sources[0]["provenance"] == "provider_returned"
    assert sources[1] == {"url": "https://model.example", "provenance": "model_reported"}


def test_build_child_env_rejects_untrusted_base_url():
    values = {
        "RAVE_API_KEY": "not-a-real-key",
        "RAVE_BASE_URL": "https://attacker.example/v1",
        "RAVE_SEARCH_INPUT_USD_PER_1M": "1.25",
        "RAVE_SEARCH_OUTPUT_USD_PER_1M": "10.0",
    }
    with pytest.raises(ValueError, match="RAVE_BASE_URL"):
        pilot.build_child_env(values)


def test_preflight_redirect_handler_refuses_redirects():
    handler = pilot._NoRedirectHandler()
    request = urllib.request.Request("https://api.openai.com/v1/models")
    assert handler.redirect_request(request, None, 302, "Found", {}, "https://attacker.example/collect") is None
