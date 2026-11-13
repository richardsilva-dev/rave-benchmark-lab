def test_baseline_is_single_pass_without_peer_or_followup_loop():
    import inspect
    from solo_baseline.agent import SoloResearchAgent
    src = inspect.getsource(SoloResearchAgent.run)
    assert "for " not in src
    assert "gather(" not in src and "create_task(" not in src
    assert "OpenAIHostedSearch" in src and "_analysis" in src
