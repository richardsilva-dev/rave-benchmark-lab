def test_research_loop_is_sequential_by_design():
    import inspect
    from solo_baseline.agent import SoloResearchAgent
    src=inspect.getsource(SoloResearchAgent.run)
    assert "for _ in range" in src and "gather(" not in src and "create_task(" not in src
