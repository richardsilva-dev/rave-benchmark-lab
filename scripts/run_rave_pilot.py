from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

LAB_ROOT = Path(__file__).resolve().parents[1]
RAVE_REPOSITORY = "https://github.com/richardsilva-dev/project_RAVE.git"
RAVE_BRANCH = "benchmark-a-current-hive-budget-guard"
RAVE_COMMIT = "ee45023a64f637e80095e08c4aab56f97d6cc835"
BASELINE_RUN_ID = "solo-5b3dc0590dfc"
QUESTION_DEFAULT = "Quais são os benefícios, riscos e recomendações atuais para o uso de inteligência artificial generativa na educação? Compare fontes institucionais e apresente limites e divergências."
QUESTION_SCOPE_DEFAULT = "Investigar a pergunta sem expandir além do necessário."
BUDGET = {
    "max_tokens": 80000,
    "max_searches": 3,
    "max_model_calls": 12,
    "max_seconds": 180,
    "max_cost_usd": 0.50,
    "search_input_reserve_tokens": 16384,
}


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            values[key] = value.strip().strip("\"'").strip()
    return values


def validate_baseline(run_id: str) -> tuple[dict, dict, Path]:
    artifact_dir = LAB_ROOT / "artifacts" / "runs" / run_id
    metadata_path = artifact_dir / "metadata.json"
    result_path = artifact_dir / "result.json"
    if not metadata_path.is_file() or not result_path.is_file():
        raise ValueError(f"Baseline artifacts are incomplete: {artifact_dir}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if metadata.get("status") != "COMPLETED" or result.get("status") != "COMPLETED":
        raise ValueError("The selected Comparison A run is not COMPLETED")
    if not isinstance(result.get("answer"), str) or not result["answer"].strip():
        raise ValueError("The selected Comparison A run has no answer")
    if metadata.get("question") != QUESTION_DEFAULT or metadata.get("scope") != QUESTION_SCOPE_DEFAULT:
        raise ValueError("The preserved baseline question/scope does not match the approved pilot")
    if metadata.get("analysis_model") != "gpt-4.1-mini":
        raise ValueError("The baseline analysis model does not match the RAVE pilot profile")
    if metadata.get("search_model") != "gpt-5-search-api":
        raise ValueError("The baseline search model does not match the RAVE pilot profile")
    if metadata.get("search_provider") != "openai_hosted_web_search":
        raise ValueError("The baseline search provider does not match the RAVE pilot profile")
    if int(metadata.get("search_input_reservation_tokens", 0)) != BUDGET["search_input_reserve_tokens"]:
        raise ValueError("Baseline hosted-search input reservation does not match the RAVE pilot profile")
    limits = metadata.get("budget_limits", {})
    for key, expected in BUDGET.items():
        if key == "search_input_reserve_tokens":
            continue
        if key not in limits or float(limits[key]) != float(expected):
            raise ValueError(f"Baseline budget mismatch for {key}")
    return metadata, result, artifact_dir


def build_child_env(dotenv: dict[str, str]) -> dict[str, str]:
    env = os.environ.copy()
    env.update(dotenv)
    api_key = env.get("RAVE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("RAVE_API_KEY is missing from comparison_a/.env")
    base_url = env.get("RAVE_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
    parsed = urlsplit(base_url)
    if parsed.scheme != "https" or parsed.hostname != "api.openai.com" or parsed.username or parsed.password:
        raise ValueError("RAVE_BASE_URL must be https://api.openai.com/v1")
    for name in ("RAVE_SEARCH_INPUT_USD_PER_1M", "RAVE_SEARCH_OUTPUT_USD_PER_1M"):
        try:
            rate = float(env.get(name, ""))
        except ValueError as exc:
            raise ValueError(f"{name} must be configured in comparison_a/.env") from exc
        if rate <= 0:
            raise ValueError(f"{name} must be positive")
    analysis_model = env.get("RAVE_MODEL", "gpt-4.1-mini").strip()
    search_model = env.get("RAVE_SEARCH_MODEL", "gpt-5-search-api").strip()
    if analysis_model != "gpt-4.1-mini" or search_model != "gpt-5-search-api":
        raise ValueError("The paired pilot requires gpt-4.1-mini and gpt-5-search-api")
    env.update({
        "RAVE_BASE_URL": base_url,
        "RAVE_MODEL": analysis_model,
        "RAVE_WEB_SEARCH": "true",
        "RAVE_RESEARCH_MODE": "shared_research",
        "RAVE_WEB_SEARCH_MODEL": search_model,
        "RAVE_WEB_SEARCH_CONTEXT_SIZE": "low",
        "RAVE_WEB_SEARCH_MAX_OUTPUT_TOKENS": "512",
        "RAVE_TEMPERATURE": "0.2",
        "RAVE_TIMEOUT_SECONDS": "90",
        "RAVE_MAX_CONCURRENT_REQUESTS": "1",
        "RAVE_ANALYSIS_MAX_OUTPUT_TOKENS": "4096",
        "RAVE_SYNTHESIS_MAX_OUTPUT_TOKENS": "8192",
        "RAVE_MAX_RUN_TOKENS": str(BUDGET["max_tokens"]),
        "RAVE_MAX_RUN_SEARCHES": str(BUDGET["max_searches"]),
        "RAVE_MAX_RUN_MODEL_CALLS": str(BUDGET["max_model_calls"]),
        "RAVE_MAX_RUN_SECONDS": str(BUDGET["max_seconds"]),
        "RAVE_MAX_RUN_COST_USD": str(BUDGET["max_cost_usd"]),
        "RAVE_SEARCH_INPUT_RESERVE_TOKENS": str(BUDGET["search_input_reserve_tokens"]),
    })
    return env


def check_api_auth(base_url: str, api_key: str) -> None:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise RuntimeError(f"OpenAI authentication preflight returned HTTP {response.status}")
            response.read(1024)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise RuntimeError(
                f"OpenAI authentication preflight failed with HTTP {exc.code}. "
                "No paid research request was sent. Replace RAVE_API_KEY in comparison_a/.env."
            ) from exc
        raise RuntimeError(
            f"OpenAI authentication preflight could not complete (HTTP {exc.code}); no research request was sent."
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            f"OpenAI authentication preflight could not reach the provider ({type(exc).__name__}); "
            "no research request was sent."
        ) from exc


def run_git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout.strip()


def ensure_rave_checkout(target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        try:
            subprocess.run(
                ["git", "clone", "--filter=blob:none", "--single-branch", "--branch",
                 RAVE_BRANCH, RAVE_REPOSITORY, str(target)],
                check=True, capture_output=True, text=True, encoding="utf-8",
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                "Could not clone the private Project RAVE repository. Confirm local GitHub authentication."
            ) from exc
    elif not (target / ".git").exists():
        raise RuntimeError(f"RAVE_PROJECT_PATH is not a Git checkout: {target}")
    else:
        dirty = run_git(["status", "--porcelain"], target)
        if dirty:
            raise RuntimeError(
                f"The RAVE checkout has local changes; refusing to overwrite or switch it: {target}"
            )
        run_git(["fetch", "--no-tags", "origin", RAVE_BRANCH], target)
    run_git(["checkout", "--detach", RAVE_COMMIT], target)
    actual = run_git(["rev-parse", "HEAD"], target)
    if actual != RAVE_COMMIT:
        raise RuntimeError("The RAVE checkout does not match the pinned candidate commit")
    return target


def compose_rave_answer(final_output: dict) -> str:
    fields = ("executive_answer", "integrated_analysis", "collective_integration", "conclusions")
    return "\\n\\n".join(
        value.strip() for key in fields
        if isinstance((value := final_output.get(key)), str) and value.strip()
    )


def build_baseline_command(question: str, scope: str) -> list[str]:
    return [
        "uv", "run", "--project", str(LAB_ROOT / "comparison_a"), "--locked", "--extra", "dev",
        "solo-baseline", "research", question, "--scope", scope, "--live",
        "--max-tokens", str(BUDGET["max_tokens"]),
        "--max-searches", str(BUDGET["max_searches"]),
        "--max-model-calls", str(BUDGET["max_model_calls"]),
        "--max-seconds", str(BUDGET["max_seconds"]),
        "--max-cost-usd", str(BUDGET["max_cost_usd"]),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run RAVE against the preserved, completed Comparison A pilot."
    )
    parser.add_argument("--live", action="store_true", help="Required opt-in for the paid RAVE request")
    parser.add_argument("--baseline-run-id", default=BASELINE_RUN_ID)
    parser.add_argument("--rave-project-path", default=os.getenv("RAVE_PROJECT_PATH", ""))
    args = parser.parse_args()
    if not args.live:
        parser.error("No API request is made unless --live is explicitly supplied")

    try:
        baseline_meta, baseline_result, baseline_dir = validate_baseline(args.baseline_run_id)
        dotenv_path = LAB_ROOT / "comparison_a" / ".env"
        if not dotenv_path.is_file():
            raise ValueError("Create comparison_a/.env from comparison_a/.env.example first")
        child_env = build_child_env(parse_dotenv(dotenv_path))

        search_rates = baseline_meta.get("pricing_rates_usd_per_1m", {}).get("gpt-5-search-api")
        if not isinstance(search_rates, dict) or "input" not in search_rates or "output" not in search_rates:
            raise ValueError("The preserved Comparison A run has no complete search pricing record")
        if float(child_env["RAVE_SEARCH_INPUT_USD_PER_1M"]) != float(search_rates["input"]):
            raise ValueError("Search input price differs from the preserved Comparison A run")
        if float(child_env["RAVE_SEARCH_OUTPUT_USD_PER_1M"]) != float(search_rates["output"]):
            raise ValueError("Search output price differs from the preserved Comparison A run")

        # This GET is non-billable and occurs before any paid research request.
        check_api_auth(child_env["RAVE_BASE_URL"], child_env["RAVE_API_KEY"])

        rave_path = Path(args.rave_project_path).expanduser().resolve() if args.rave_project_path else (
            LAB_ROOT / ".cache" / "project_RAVE"
        )
        rave_path = ensure_rave_checkout(rave_path)
        child_env["RAVE_OUTPUT_DIR"] = str(rave_path / "data" / "runs")

        command = [
            "uv", "run", "--project", str(rave_path), "--locked",
            "rave", "hive", baseline_meta["question"], "--scope", baseline_meta["scope"],
        ]
        completed = subprocess.run(
            command, cwd=rave_path, env=child_env, capture_output=True, text=True,
            encoding="utf-8", timeout=300,
        )
        try:
            rave_output = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            detail = completed.stderr[-2000:].strip()
            raise RuntimeError(
                "RAVE CLI did not return valid JSON. "
                + (f"Diagnostic: {detail}" if detail else "Inspect the local CLI output.")
            ) from exc

        rave_run_id = rave_output.get("run_id", "unknown")
        rave_artifact_path = Path(rave_output.get("result_path", ""))
        if not rave_artifact_path.is_absolute():
            rave_artifact_path = rave_path / rave_artifact_path
        if not rave_artifact_path.is_file():
            raise RuntimeError("RAVE did not persist its run artifact; the pair cannot be evaluated")

        pair_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + rave_run_id
        pair_dir = LAB_ROOT / "artifacts" / "pairs" / pair_id
        pair_dir.mkdir(parents=True, exist_ok=True)
        (pair_dir / "rave_cli_output.json").write_text(
            json.dumps(rave_output, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        shutil.copy2(rave_artifact_path, pair_dir / "rave_run.json")
        try:
            rave_payload = json.loads(rave_artifact_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError("RAVE persisted an invalid JSON run artifact") from exc

        rave_budget = rave_payload.get("run_budget", rave_output.get("run_budget", {}))
        rave_meta = rave_payload.get("metadata", rave_output.get("metadata", {}))
        rave_status = rave_payload.get("execution_status", rave_output.get("execution_status", "INVALID"))
        rave_final = rave_payload.get("final_output", rave_output.get("final_output", {}))
        rave_answer = compose_rave_answer(rave_final) if isinstance(rave_final, dict) else ""
        integration = rave_payload.get("integration", {})
        rave_sources = integration.get("web_sources", [])
        rave_model_refs = integration.get("model_reported_references", [])
        rave_limitations = rave_final.get("gaps_and_limitations", []) if isinstance(rave_final, dict) else []

        blind_responses = [
            {
                "response_id": "response_01",
                "answer": baseline_result["answer"],
                "sources": baseline_result.get("sources", []),
                "limitations": baseline_result.get("limitations", []),
            },
            {
                "response_id": "response_02",
                "answer": rave_answer,
                "sources": rave_sources,
                "model_reported_references": rave_model_refs,
                "limitations": rave_limitations,
            },
        ]
        (pair_dir / "blind_responses.json").write_text(
            json.dumps(blind_responses, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (pair_dir / "system_key.json").write_text(
            json.dumps({"response_01": "solo_baseline", "response_02": "rave_hive"}, indent=2),
            encoding="utf-8"
        )

        pair_status = (
            "COMPLETED" if completed.returncode == 0 and rave_status == "COMPLETED"
            and isinstance(rave_answer, str) and rave_answer.strip() else "INELIGIBLE"
        )
        baseline_cost = float(baseline_meta.get("cost_estimated_usd", 0.0))
        manifest = {
            "schema_version": "1.0",
            "pair_id": pair_id,
            "pair_status": pair_status,
            "question": baseline_meta["question"],
            "scope": baseline_meta["scope"],
            "baseline": {
                "system_id": "solo_baseline",
                "run_id": args.baseline_run_id,
                "artifact_dir": str(baseline_dir.relative_to(LAB_ROOT)),
                "status": baseline_result["status"],
                "duration_seconds": baseline_meta.get("duration_seconds"),
                "tokens_total": baseline_meta.get("tokens_total"),
                "estimated_cost_usd_already_incurred": baseline_cost,
                "sources_count": baseline_meta.get("sources_count"),
                "analysis_model": baseline_meta.get("analysis_model"),
                "search_model": baseline_meta.get("search_model"),
                "code_commit": "not recorded in the historical pilot metadata",
            },
            "rave": {
                "system_id": "rave_hive",
                "run_id": rave_run_id,
                "status": rave_status,
                "code_commit": RAVE_COMMIT,
                "code_branch": RAVE_BRANCH,
                "duration_seconds": rave_meta.get("duration_seconds"),
                "run_budget": rave_budget,
                "agent_count": len(rave_payload.get("agent_results", rave_output.get("agent_results", []))),
                "message_count": len(rave_payload.get("messages", [])),
                "sources_count": len(rave_sources),
                "artifact": "rave_run.json",
                "blind_responses": "blind_responses.json",
                "system_key": "system_key.json",
            },
            "shared_profile": {
                "analysis_model": "gpt-4.1-mini",
                "search_model": "gpt-5-search-api",
                "search_context": "low",
                "search_output_tokens": 512,
                "run_budget": BUDGET,
                "rave_agent_analysis_output_tokens": 4096,
                "rave_final_synthesis_output_tokens": 8192,
            },
            "cost_guard": {
                "historical_baseline_cost_usd_already_incurred": baseline_cost,
                "maximum_new_rave_estimated_cost_usd": BUDGET["max_cost_usd"],
                "maximum_total_estimated_cost_including_baseline_usd": round(
                    baseline_cost + BUDGET["max_cost_usd"], 8
                ),
                "note": "Local estimate, not a provider-enforced billing cap.",
            },
            "limitations": [
                "This is a one-question pilot, not the ten-question benchmark in the 30-day protocol.",
                "The historical Comparison A artifact does not record its exact source commit or resolved per-call output cap.",
                "RAVE uses a different internal allocation of per-call output tokens; the run-wide budget is capped equally.",
                "No blind independent quality scoring has been performed yet.",
            ],
        }
        (pair_dir / "pair_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary = {
            "pair_id": pair_id,
            "pair_status": pair_status,
            "baseline_run_id": args.baseline_run_id,
            "rave_run_id": rave_run_id,
            "rave_status": rave_status,
            "artifact_dir": str(pair_dir),
        }
        print(json.dumps(summary, ensure_ascii=False))
        return 0 if pair_status == "COMPLETED" else 2
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"RAVE pilot stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
