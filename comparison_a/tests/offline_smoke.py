"""Dependency-free safety and contract checks; run with python tests/offline_smoke.py."""
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from solo_baseline.agent import SoloResearchAgent
from solo_baseline.budget import BudgetController, BudgetExceeded, Limits
from solo_baseline.config import Settings
from solo_baseline.schemas import ResearchResult
from solo_baseline.tools.page_reader import _validate
from adapters.result_normalizer import normalize_result


class OfflineSmoke(unittest.TestCase):
    def test_reference_models(self):
        s = Settings.from_env()
        self.assertEqual((s.analysis_model, s.search_model), ("gpt-4.1-mini", "gpt-5-search-api"))

    def test_budget_reserves_before_call(self):
        budget = BudgetController(Limits(100, 1, 10, 0.1))
        with self.assertRaises(BudgetExceeded):
            budget.reserve("search", 80, 30, 0.01)
        self.assertEqual(budget.calls, 0)

    def test_budget_reconciles_usage(self):
        budget = BudgetController(Limits(1000, 1, 10, 0.1))
        reservation = budget.reserve("analysis", 100, 50, 0.02)
        budget.record_usage(20, 10, reservation, 0.001)
        self.assertEqual(budget.tokens, 30)
        self.assertEqual(budget.reserved_tokens, 0)

    def test_ssrf_blocking(self):
        for url in ("file:///secret", "ftp://example.org", "http://localhost", "http://127.0.0.1", "http://10.0.0.1", "http://[::1]"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _validate(url)

    def test_completed_needs_answer(self):
        with self.assertRaises(ValueError):
            ResearchResult("1.0", "r", "solo_baseline", "COMPLETED", "", [], []).validate()

    def test_no_agents_or_bus(self):
        agent = SoloResearchAgent(Settings(""), BudgetController(Limits(1000, 1, 10, 0.1)))
        self.assertFalse(hasattr(agent, "agents"))
        self.assertFalse(hasattr(agent, "message_bus"))

    def test_mocked_run_is_single_pass_and_keeps_provider_sources(self):
        agent = SoloResearchAgent(Settings("unused"), BudgetController(Limits(10000, 2, 30, 0.1)))
        sequence = []
        class MockSearch:
            def __init__(self, *args):
                pass
            def search(self, *args):
                sequence.append("search")
                return {"content": "untrusted evidence", "citations": [{"url": "https://example.org", "title": "Example", "provenance": "provider_returned"}]}
        with patch("solo_baseline.agent.OpenAIHostedSearch", MockSearch), patch.object(
            agent, "_analysis", side_effect=lambda *args: (
                sequence.append("analysis") or {"summary": "Evidence-based answer", "findings": [],
                    "limitations": ["uncertain"], "open_questions": []}
            )
        ):
            result, telemetry = agent.run({"request_id": "req-1", "question": "question", "scope": "scope"})
        self.assertEqual(sequence, ["search", "analysis"])
        self.assertEqual(result.status, "COMPLETED")
        self.assertEqual(result.sources[0]["provenance"], "provider_returned")
        self.assertEqual(result.limitations, ["uncertain"])
        self.assertEqual(telemetry.status, "COMPLETED")

    def test_normalizer_keeps_source_provenance_and_limits(self):
        result = normalize_result("r", "rave", "COMPLETED", "Answer",
            [{"url": "https://example.org", "provenance": "model_reported"}], ["uncertain"])
        self.assertEqual(result["sources"][0]["provenance"], "model_reported")
        self.assertEqual(result["limitations"], ["uncertain"])

    def test_normalizer_blocks_local_urls(self):
        with self.assertRaises(ValueError):
            normalize_result("r", "rave", "COMPLETED", "Answer", [{"url": "file:///etc/passwd"}], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
