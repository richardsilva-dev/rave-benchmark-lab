def test_baseline_is_single_pass_without_peer_or_followup_loop():
    import inspect
    from solo_baseline.agent import SoloResearchAgent
    source = inspect.getsource(SoloResearchAgent.run)
    assert "range(" not in source
    assert "gather(" not in source and "create_task(" not in source
    assert source.count("OpenAIHostedSearch") == 1
    assert source.count("_analysis") == 1
