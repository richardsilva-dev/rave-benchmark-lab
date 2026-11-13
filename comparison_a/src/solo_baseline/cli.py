import argparse
import json
from pathlib import Path
import uuid
from .budget import BudgetController, Limits
from .config import Settings
from .agent import SoloResearchAgent


def main():
    p=argparse.ArgumentParser(prog="solo-baseline")
    sub=p.add_subparsers(dest="command",required=True)
    r=sub.add_parser("research"); r.add_argument("question"); r.add_argument("--scope",default=""); r.add_argument("--live",action="store_true")
    r.add_argument("--max-tokens",type=int); r.add_argument("--max-searches",type=int); r.add_argument("--max-seconds",type=float); r.add_argument("--max-model-calls",type=int)
    args=p.parse_args()
    if not args.live:
        p.error("No API calls are made unless --live is explicit")
    if not all(v is not None for v in (args.max_tokens,args.max_searches,args.max_seconds,args.max_model_calls)):
        p.error("Live mode requires explicit --max-tokens, --max-searches, --max-seconds, and --max-model-calls; no defaults are chosen")
    settings=Settings.from_env()
    if not settings.api_key: p.error("RAVE_API_KEY is required")
    budget=BudgetController(Limits(args.max_tokens,args.max_searches,args.max_seconds,None,args.max_model_calls))
    request={"schema_version":"1.0","request_id":"req-"+uuid.uuid4().hex[:12],"question":args.question,"scope":args.scope}
    result,meta=SoloResearchAgent(settings,budget).run(request)
    out=Path(__file__).resolve().parents[3] / "artifacts" / "runs" / meta.run_id; out.mkdir(parents=True,exist_ok=True)
    (out/"result.json").write_text(json.dumps(result.__dict__,ensure_ascii=False,indent=2),encoding="utf-8")
    md=meta.to_dict(); md.update({"system_id":"solo_baseline","request_id":request["request_id"],"budget_remaining":budget.remaining(),"tokens_total":budget.tokens})
    (out/"metadata.json").write_text(json.dumps(md,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"run_id":meta.run_id,"status":meta.status,"artifact_dir":str(out)},ensure_ascii=False))
    if meta.status != "COMPLETED": raise SystemExit(2)
