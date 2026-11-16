import io
import json
import urllib.error

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
    assert env["RAVE_ANALYSIS_MAX_OUTPUT_TOKENS"] == "8192"
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
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(error))
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



def test_paired_pilot_builds_fresh_baseline_with_full_shared_budget():
    command = pilot.build_baseline_command("same question", "same scope")
    assert command[command.index("research") + 1] == "same question"
    assert command[command.index("--scope") + 1] == "same scope"
    assert command[command.index("--max-tokens") + 1] == "80000"
    assert command[command.index("--max-searches") + 1] == "3"
    assert command[command.index("--max-model-calls") + 1] == "12"
    assert command[command.index("--max-seconds") + 1] == "180"
    assert command[command.index("--max-cost-usd") + 1] == "0.5"
    assert "--live" in command


def test_compose_rave_answer_keeps_all_comparable_final_sections():
    answer = pilot.compose_rave_answer({
        "executive_answer": "Executive",
        "integrated_analysis": "Analysis",
        "collective_integration": "Collective",
        "conclusions": "Conclusion",
        "gaps_and_limitations": ["Not part of answer body"],
    })
    assert answer == "Executive\\n\\nAnalysis\\n\\nCollective\\n\\nConclusion"
