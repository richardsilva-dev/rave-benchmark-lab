from .result_normalizer import normalize_result


def normalize_solo_output(request_id: str, result: dict):
    return normalize_result(request_id,"solo_baseline",result.get("status","INVALID"),result.get("answer",""),result.get("sources",[]),result.get("limitations",[]))
