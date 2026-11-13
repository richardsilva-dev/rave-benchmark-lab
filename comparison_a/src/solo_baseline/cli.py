import argparse
import json
from pathlib import Path
import uuid
from .budget import BudgetController, Limits
from .config import Settings
from .agent import SoloResearchAgent
from .pricing import PRICE_VERSION, MODEL_RATES, configured_model_rates, WEB_SEARCH_USD_PER_CALL, MAX_ALLOWED_RUN_COST_USD


def main():
    parser = argparse.ArgumentParser(prog="solo-baseline")
    sub = parser.add_subparsers(dest="command", required=True)
    research = sub.add_parser("research")
    research.add_argument("question")
    research.add_argument("--scope", default="Investigar a pergunta sem expandir além do necessário.")
    research.add_argument("--live", action="store_true")
    research.add_argument("--max-tokens", type=int)
    research.add_argument("--max-searches", type=int)
    research.add_argument("--max-seconds", type=float)
    research.add_argument("--max-cost-usd", type=float)
    research.add_argument("--max-model-calls", type=int)
    args = parser.parse_args()
    if not args.live:
        parser.error("No API calls are made unless --live is explicit")
    if not all(value is not None for value in (args.max_tokens, args.max_searches, args.max_seconds, args.max_cost_usd, args.max_model_calls)):
        parser.error("Live mode requires explicit --max-tokens, --max-searches, --max-seconds and --max-cost-usd and --max-model-calls")
    if args.max_cost_usd > MAX_ALLOWED_RUN_COST_USD:
        parser.error(f"Initial benchmark policy caps each live run at US${MAX_ALLOWED_RUN_COST_USD:.2f}; lower --max-cost-usd")
    settings = Settings.from_env()
    if not settings.api_key:
        parser.error("RAVE_API_KEY is required")
    try:
        rates = configured_model_rates()
    except Exception as exc:
        parser.error(str(exc))
    if settings.analysis_model not in rates or settings.search_model not in rates:
        parser.error("No configured price schedule exists for both models; refusing live execution")
    budget = BudgetController(Limits(args.max_tokens, args.max_searches, args.max_seconds, args.max_cost_usd, args.max_model_calls))
    request = {"schema_version": "1.0", "request_id": "req-" + uuid.uuid4().hex[:12],
               "question": args.question, "scope": args.scope, "constraints": []}
    result, metadata = SoloResearchAgent(settings, budget).run(request)
    output_dir = Path(__file__).resolve().parents[3] / "artifacts" / "runs" / metadata.run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "result.json").write_text(json.dumps(result.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    md = metadata.to_dict()
    md.update({
        "system_id": "solo_baseline", "request_id": request["request_id"],
        "budget_remaining": budget.remaining(), "tokens_total": budget.tokens,
        "budget_limits": {"max_tokens": args.max_tokens, "max_searches": args.max_searches,
                          "max_seconds": args.max_seconds, "max_cost_usd": args.max_cost_usd,
                          "max_model_calls": args.max_model_calls},
        "pricing_version": PRICE_VERSION, "pricing_rates_usd_per_1m": rates,\n        "pricing_source": "user-configured local .env; verify against the applicable OpenAI billing record",
        "web_search_fee_usd_per_call": WEB_SEARCH_USD_PER_CALL,
        "max_allowed_run_cost_usd": MAX_ALLOWED_RUN_COST_USD,
        "search_input_reservation_tokens": settings.search_input_reserve_tokens,
        "budget_note": "Preflight reserves UTF-8 prompt bytes, max completion tokens and the configured hosted-search context allowance. Provider-side search context is variable and may exceed the allowance. GPT-5 Search API token rates are user-configured because no distinct official rate row is published. The local USD 0.50 ceiling is an estimate, not a provider-enforced billing cap; retain account/project spend limits."
    })
    (output_dir / "metadata.json").write_text(json.dumps(md, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"run_id": metadata.run_id, "status": metadata.status, "artifact_dir": str(output_dir),
                      "tokens": budget.tokens, "estimated_cost_usd": round(budget.estimated_cost_usd, 8)}, ensure_ascii=False))
    if metadata.status != "COMPLETED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
