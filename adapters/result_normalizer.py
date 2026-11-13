from urllib.parse import urlsplit

VALID_STATUS={"COMPLETED","PARTIAL","INVALID","FAILED"}
VALID_PROVENANCE={"provider_returned","model_reported","system_reported","unknown"}


def normalize_result(request_id: str, system_id: str, status: str, answer: str,
                     sources: list[dict], limitations: list[str], system_details: dict | None=None):
    if status not in VALID_STATUS: raise ValueError("Unknown execution status")
    normalized=[]
    for src in sources:
        url=str(src.get("url", "")); p=urlsplit(url)
        if p.scheme not in {"http","https"} or not p.hostname or p.username or p.password:
            raise ValueError("Invalid source URL")
        provenance=src.get("provenance", "unknown")
        if provenance not in VALID_PROVENANCE: raise ValueError("Invalid source provenance")
        normalized.append({"url":url,"title":str(src.get("title", "")),"provenance":provenance})
    if status=="COMPLETED" and not answer.strip(): raise ValueError("Completed output cannot be empty")
    return {"schema_version":"1.0","request_id":request_id,"system_id":system_id,"status":status,"answer":answer,
            "sources":normalized,"limitations":list(limitations),"system_details":system_details or {}}
