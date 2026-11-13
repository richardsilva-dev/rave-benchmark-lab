import pytest
from solo_baseline.schemas import ResearchResult
from solo_baseline.tools.page_reader import _validate

@pytest.mark.parametrize("url",["file:///etc/passwd","ftp://example.com","http://localhost/","http://127.0.0.1/","http://10.1.2.3/","http://[::1]/"])
def test_reader_blocks_local_and_non_http(url):
    with pytest.raises(ValueError): _validate(url)

def test_schema_rejects_invalid_citation():
    x=ResearchResult("1.0","r","solo_baseline","COMPLETED","answer",[{"url":"file:///secret"}],[])
    with pytest.raises(ValueError): x.validate()
