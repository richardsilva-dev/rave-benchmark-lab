import pytest
from adapters.result_normalizer import normalize_result

def test_normalizer_preserves_provenance_and_limitations():
    out=normalize_result("r1","rave","COMPLETED","answer",[{"url":"https://example.org","provenance":"model_reported"}],["uncertainty"])
    assert out["sources"][0]["provenance"]=="model_reported" and out["limitations"]==["uncertainty"]

def test_normalizer_rejects_bad_citation():
    with pytest.raises(ValueError): normalize_result("r1","rave","COMPLETED","answer",[{"url":"file:///x"}],[])

def test_completed_requires_answer():
    with pytest.raises(ValueError): normalize_result("r1","solo_baseline","COMPLETED","",[],[])
