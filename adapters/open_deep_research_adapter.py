from .result_normalizer import normalize_result


def normalize_open_deep_research_output(request_id: str, raw: dict):
    # Upstream shape can vary by pinned version. Caller must provide source mapping explicitly.
    sources=raw.get("sources",[])
    answer=raw.get("answer",raw.get("final_report",""))
    if not answer and isinstance(raw.get("messages"),str): answer=raw["messages"]
    return normalize_result(request_id,"open_deep_research",raw.get("status","INVALID"),answer,sources,raw.get("limitations",[]),{"native_keys":sorted(raw.keys())})
