from solo_baseline.agent import SoloResearchAgent, SINGLE_AGENT_SYSTEM
from solo_baseline.budget import BudgetController, Limits
from solo_baseline.config import Settings


def test_agent_is_single_pass_and_matches_rave_single_agent(monkeypatch):
    agent = SoloResearchAgent(Settings("not-used"), BudgetController(Limits(10000, 2, 30, 1.0)))
    calls = []
    class Search:
        def __init__(self, *args):
            pass
        def search(self, *args):
            calls.append("search")
            return {"content": "untrusted evidence", "citations": [{"url": "https://example.org", "title": "Example", "provenance": "provider_returned"}]}
    monkeypatch.setattr("solo_baseline.agent.OpenAIHostedSearch", Search)
    monkeypatch.setattr(agent, "_analysis", lambda *args: (
        calls.append("analysis") or {"summary": "A sourced answer", "findings": [], "limitations": [], "open_questions": []}
    ))
    result, metadata = agent.run({"request_id": "req-1", "question": "Q", "scope": "S"})
    assert calls == ["search", "analysis"]
    assert result.status == "COMPLETED"
    assert result.answer == "A sourced answer"
    assert result.sources[0]["provenance"] == "provider_returned"
    assert "without specialist decomposition" in SINGLE_AGENT_SYSTEM


def test_agent_fails_closed_when_analysis_json_is_invalid(monkeypatch):
    agent = SoloResearchAgent(Settings("not-used"), BudgetController(Limits(10000, 2, 30, 1.0)))
    class Search:
        def __init__(self, *args):
            pass
        def search(self, *args):
            return {"content": "evidence", "citations": []}
    monkeypatch.setattr("solo_baseline.agent.OpenAIHostedSearch", Search)
    monkeypatch.setattr(agent, "_analysis", lambda *args: (_ for _ in ()).throw(ValueError("invalid json")))
    result, metadata = agent.run({"request_id": "req-2", "question": "Q", "scope": ""})
    assert result.status == "FAILED"
    assert metadata.stop_reason == "invalid json"
