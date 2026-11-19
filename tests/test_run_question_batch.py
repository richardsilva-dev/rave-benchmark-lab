import json

import pytest

from scripts import run_question_batch as batch


def test_load_questions_accepts_multiple_arbitrary_questions(tmp_path):
    path = tmp_path / "questions.json"
    path.write_text(json.dumps([
        {"id": "Q1", "category": "factual", "question": "Question one?"},
        {"id": "Q2", "category": "comparison", "question": "Question two?", "scope": "Narrow scope."},
    ]), encoding="utf-8")

    questions = batch.load_questions(path)

    assert len(questions) == 2
    assert questions[0]["question"] == "Question one?"
    assert questions[0]["scope"] == batch.pilot.QUESTION_SCOPE_DEFAULT
    assert questions[1]["scope"] == "Narrow scope."


def test_load_questions_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "questions.json"
    path.write_text(json.dumps([
        {"id": "same", "question": "First?"},
        {"id": "same", "question": "Second?"},
    ]), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate question id"):
        batch.load_questions(path)


def test_load_questions_rejects_empty_question(tmp_path):
    path = tmp_path / "questions.json"
    path.write_text(json.dumps([{"id": "Q1", "question": "  "}]), encoding="utf-8")

    with pytest.raises(ValueError, match="no valid question"):
        batch.load_questions(path)


def test_build_solo_command_uses_the_same_global_budget_as_rave():
    command = batch.build_solo_command("What changed?", "Compare the last five years.")

    assert command[command.index("--max-tokens") + 1] == str(batch.pilot.BUDGET["max_tokens"])
    assert command[command.index("--max-searches") + 1] == str(batch.pilot.BUDGET["max_searches"])
    assert command[command.index("--max-seconds") + 1] == str(batch.pilot.BUDGET["max_seconds"])
    assert command[command.index("--max-model-calls") + 1] == str(batch.pilot.BUDGET["max_model_calls"])
    assert command[command.index("--max-cost-usd") + 1] == str(batch.pilot.BUDGET["max_cost_usd"])
    assert command[command.index("--scope") + 1] == "Compare the last five years."


def test_rave_metrics_extracts_run_usage():
    metrics = batch._rave_metrics({
        "execution_status": "COMPLETED",
        "metadata": {"duration_seconds": 12.5},
        "run_budget": {"used": {
            "tokens": 1000, "estimated_cost_usd": 0.02,
            "model_calls": 4, "searches": 1,
        }},
        "integration": {"web_sources": [{"url": "https://example.org"}]},
        "agent_results": [{}, {}, {}],
        "messages": [{}, {}],
        "research_mode": "shared_research",
    })

    assert metrics["tokens_total"] == 1000
    assert metrics["sources_count"] == 1
    assert metrics["agent_count"] == 3
    assert metrics["message_count"] == 2
