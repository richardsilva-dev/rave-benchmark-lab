import pytest
from solo_baseline.schemas import ResearchResult
from solo_baseline.tools.page_reader import _validate

@pytest.mark.parametrize("url",["file:///etc/passwd","ftp://example.com","http://localhost/","http://127.0.0.1/","http://10.1.2.3/","http://[::1]/"])
def test_reader_blocks_local_and_non_http(url):
    with pytest.raises(ValueError): _validate(url)

def test_schema_rejects_invalid_citation():
    x=ResearchResult("1.0","r","solo_baseline","COMPLETED","answer",[{"url":"file:///secret"}],[])
    with pytest.raises(ValueError): x.validate()


from solo_baseline.source_utils import canonical_source_url


def test_canonical_url_removes_fragments_default_ports_and_tracking():
    first = "HTTPS://Example.ORG:443/path?utm_source=newsletter&item=42#section"
    second = "https://example.org/path?item=42"
    assert canonical_source_url(first) == canonical_source_url(second)


def test_canonical_url_does_not_merge_distinct_hosts_or_query_values():
    assert canonical_source_url("https://www.example.org/a?id=1") != canonical_source_url(
        "https://example.org/a?id=1"
    )
    assert canonical_source_url("https://example.org/a?id=1") != canonical_source_url(
        "https://example.org/a?id=2"
    )


@pytest.mark.parametrize("url", [
    "javascript:alert(1)",
    "https://user:pass@example.org/path",
    "https:///missing-host",
    "not-a-url",
])
def test_canonical_url_rejects_unsafe_or_malformed_values(url):
    assert canonical_source_url(url) is None


def test_schema_rejects_duplicate_canonical_source_urls():
    result = ResearchResult(
        "1.0",
        "r",
        "solo_baseline",
        "COMPLETED",
        "answer",
        [
            {"url": "https://example.org/page?utm_source=a#x", "title": "A", "provenance": "provider_returned"},
            {"url": "https://EXAMPLE.org/page?utm_source=b#y", "title": "B", "provenance": "provider_returned"},
        ],
        [],
    )
    with pytest.raises(ValueError, match="deduplicated"):
        result.validate()


def test_schema_rejects_unknown_source_provenance_and_non_string_limits():
    unknown_provenance = ResearchResult(
        "1.0", "r", "solo_baseline", "COMPLETED", "answer",
        [{"url": "https://example.org", "title": "Example", "provenance": "unverified"}], []
    )
    with pytest.raises(ValueError, match="provenance"):
        unknown_provenance.validate()

    invalid_limitations = ResearchResult(
        "1.0", "r", "solo_baseline", "COMPLETED", "answer", [], ["ok", 7]
    )
    with pytest.raises(ValueError, match="limitations"):
        invalid_limitations.validate()
