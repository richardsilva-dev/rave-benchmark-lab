"""Explicit boundary for calling RAVE; deliberately has no import of RAVE internals."""
from .result_normalizer import normalize_result


def normalize_rave_output(request_id: str, raw: dict):
    sources=[]
    for item in raw.get("web_sources", []):
        sources.append({"url":item.get("source_url", item.get("url", "")),"title":item.get("source_title", item.get("title", "")),"provenance":"provider_returned"})
    for item in raw.get("model_reported_references", []):
        sources.append({"url":item.get("url", ""),"title":item.get("title", ""),"provenance":"model_reported"})
    return normalize_result(request_id,"rave",raw.get("status","INVALID"),raw.get("answer",raw.get("summary","")),sources,raw.get("limitations",[]),{"native_status":raw.get("status"),"raw_run_id":raw.get("run_id")})
