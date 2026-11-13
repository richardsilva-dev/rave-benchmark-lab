import argparse
import json
from pathlib import Path
import uuid

from .agent import SoloResearchAgent
from .budget import BudgetController, Limits
from .config import Settings


def main():
    parser = argparse.ArgumentParser(prog="solo-baseline")
    sub = parser.add_subparsers(dest="command", required=True)
    research = sub.add_parser("research")
    research.add_argument("question")
    research.add_argument("--scope", default="")
    research.add_argument("--live", action="store_true")
    research.add_argument("--max-tokens", type=int)
    research.add_argument("--max-searches", type=int)
    research.add_argument("--max-seconds", type=float)
    research.add_argument("--max-model-calls", type=int)
    args = parser.parse_args()

    if not args.live:
        parser.error("No API calls are made unless --live is explicit")
    if not all(value is not None for value in (
        args.max_tokens, args.max_searches, args.max_seconds, args.max_model_calls
    )):
        parser.error("Live mode requires explicit --max-tokens, --max-searches, --max-seconds, and --max-model-calls; no defaults are chosen")

    settings = Settings.from_env()
    if not settings.api_key:
        parser.error("RAVE_API_KEY is required")
    budget = BudgetController(Limits(
        max_tokens=args.max_tokens,
        max_searches=args.max_searches,
        max_seconds=args.max_seconds,
        max_cost_usd=None,
        max_model_calls=args.max_model_calls,
        input_safety_margin_tokens=settings.input_safety_margin_tokens,
    ))
    request = {
        "schema_version": "1.0",
        "request_id": "req-" + uuid.uuid4().hex[:12],
        "question": args.question,
        "scope": args.scope,
    }
    result, telemetry = SoloResearchAgent(settings, budget).run(request)
    output_dir = Path(__file__).resolve().parents[3] / "artifacts" / "runs" / telemetry.run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "result.json").write_text(
        json.dumps(result.__dict__, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    metadata = telemetry.to_dict()
    metadata.update({
        "system_id": "solo_baseline",
        "request_id": request["request_id"],
        "budget_remaining": budget.remaining(),
        "tokens_total": budget.tokens,
        "tokens_input": budget.tokens_input,
        "tokens_output": budget.tokens_output,
        "tokens_unknown_usage_charged": budget.unknown_usage_tokens,
        "token_input_estimation": "serialized_utf8_request_bytes_plus_configured_safety_margin",
        "token_budget_is_provider_exact": False,
    })
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "run_id": telemetry.run_id,
        "status": telemetry.status,
        "artifact_dir": str(output_dir),
    }, ensure_ascii=False))
    if telemetry.status != "COMPLETED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
