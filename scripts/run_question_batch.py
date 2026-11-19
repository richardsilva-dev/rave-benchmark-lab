from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts import run_rave_pilot as pilot

LAB_ROOT = pilot.LAB_ROOT
COMPARISON_A_ROOT = LAB_ROOT / "comparison_a"
DEFAULT_QUESTIONS = LAB_ROOT / "benchmark" / "questions_v1.json"
BATCH_ROOT = LAB_ROOT / "artifacts" / "batches"


def load_questions(path: Path) -> list[dict[str, str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read questions file: {path}") from exc
    if not isinstance(payload, list) or not payload:
        raise ValueError("Questions file must contain a non-empty JSON array")
    if len(payload) > 50:
        raise ValueError("A batch may contain at most 50 questions")
    questions: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Question {index} must be a JSON object")
        question_id = item.get("id")
        category = item.get("category", "General")
        question = item.get("question")
        scope = item.get("scope", pilot.QUESTION_SCOPE_DEFAULT)
        if not isinstance(question_id, str) or not question_id.strip():
            raise ValueError(f"Question {index} has no valid id")
        if any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in question_id):
            raise ValueError(f"Question id {question_id!r} may contain only letters, numbers, '-' and '_'")
        if question_id in seen:
            raise ValueError(f"Duplicate question id: {question_id}")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Question {question_id} has no valid question text")
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"Question {question_id} has no valid category")
        if not isinstance(scope, str) or not scope.strip():
            raise ValueError(f"Question {question_id} has no valid scope")
        seen.add(question_id)
        questions.append({
            "id": question_id,
            "category": category.strip(),
            "question": question.strip(),
            "scope": scope.strip(),
        })
    return questions


def build_solo_command(question: str, scope: str) -> list[str]:
    budget = pilot.BUDGET
    return [
        sys.executable, "-m", "solo_baseline.cli", "research", question,
        "--scope", scope,
        "--live",
        "--max-tokens", str(budget["max_tokens"]),
        "--max-searches", str(budget["max_searches"]),
        "--max-seconds", str(budget["max_seconds"]),
        "--max-cost-usd", str(budget["max_cost_usd"]),
        "--max-model-calls", str(budget["max_model_calls"]),
    ]


def run_json_command(command: list[str], cwd: Path, env: dict[str, str],
                     timeout_seconds: float) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    completed = subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout_seconds,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        detail = completed.stderr[-2000:].strip()
        raise RuntimeError(
            f"Command exited with code {completed.returncode} and did not return valid JSON. "
            + (f"Diagnostic: {detail}" if detail else "Inspect the command output.")
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Command returned JSON with an unexpected top-level type")
    return completed, payload


def write_process_output(directory: Path, prefix: str,
                         completed: subprocess.CompletedProcess[str]) -> None:
    (directory / f"{prefix}_stdout.txt").write_text(completed.stdout or "", encoding="utf-8")
    (directory / f"{prefix}_stderr.txt").write_text(completed.stderr or "", encoding="utf-8")


def _baseline_metrics(metadata: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    calls = metadata.get("calls", [])
    return {
        "status": metadata.get("status", result.get("status")),
        "duration_seconds": metadata.get("duration_seconds"),
        "tokens_total": metadata.get("tokens_total"),
        "estimated_cost_usd": metadata.get("cost_estimated_usd", metadata.get("estimated_cost_usd")),
        "model_calls": len(calls) if isinstance(calls, list) else metadata.get("total_calls"),
        "sources_count": len(result.get("sources", []) or []),
        "analysis_model": metadata.get("analysis_model"),
        "search_model": metadata.get("search_model"),
    }


def _rave_metrics(run: dict[str, Any]) -> dict[str, Any]:
    budget = run.get("run_budget", {})
    used = budget.get("used", {}) if isinstance(budget, dict) else {}
    integration = run.get("integration", {})
    return {
        "status": run.get("execution_status"),
        "duration_seconds": run.get("metadata", {}).get("duration_seconds"),
        "tokens_total": used.get("tokens"),
        "estimated_cost_usd": used.get("estimated_cost_usd"),
        "model_calls": used.get("model_calls"),
        "searches": used.get("searches"),
        "sources_count": len(integration.get("web_sources", []) or []),
        "agent_count": len(run.get("agent_results", []) or []),
        "message_count": len(run.get("messages", []) or []),
        "research_mode": run.get("research_mode"),
    }


def _write_batch_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def run_batch(questions_path: Path) -> int:
    questions = load_questions(questions_path)
    dotenv_path = COMPARISON_A_ROOT / ".env"
    if not dotenv_path.is_file():
        raise ValueError("Create comparison_a/.env from comparison_a/.env.example first")
    child_env = pilot.build_child_env(pilot.parse_dotenv(dotenv_path))

    # Match the global ceilings for both systems. This is a shared ceiling,
    # not a requirement that both architectures consume the same resources.
    budget = pilot.BUDGET
    solo_env = child_env.copy()
    solo_env.update({
        "RAVE_SEARCH_CONTEXT_SIZE": "low",
        "RAVE_SEARCH_MAX_OUTPUT_TOKENS": "512",
        "RAVE_SEARCH_INPUT_RESERVE_TOKENS": str(budget["search_input_reserve_tokens"]),
        "RAVE_ANALYSIS_MAX_OUTPUT_TOKENS": "8192",
        "RAVE_TEMPERATURE": "0.2",
        "RAVE_TIMEOUT_SECONDS": "90",
    })

    # Non-billable authentication check before any paid research request.
    pilot.check_api_auth(child_env["RAVE_BASE_URL"], child_env["RAVE_API_KEY"])
    rave_path = pilot.ensure_rave_checkout(LAB_ROOT / ".cache" / "project_RAVE")
    child_env["RAVE_OUTPUT_DIR"] = str(rave_path / "data" / "runs")

    batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    batch_dir = BATCH_ROOT / batch_id
    batch_dir.mkdir(parents=True, exist_ok=False)
    batch_manifest_path = batch_dir / "batch_manifest.json"
    batch_manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "batch_id": batch_id,
        "batch_status": "RUNNING",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "questions_file": str(questions_path.relative_to(LAB_ROOT)) if questions_path.is_relative_to(LAB_ROOT) else str(questions_path),
        "question_count": len(questions),
        "code": {
            "lab_branch": "benchmark/five-question-batch",
            "rave_branch": pilot.RAVE_BRANCH,
            "rave_commit": pilot.RAVE_COMMIT,
            "research_mode": "shared_research",
        },
        "shared_budget_limits": budget,
        "comparability_notes": [
            "Solo Baseline and RAVE receive identical run-wide ceilings: tokens, search attempts, model-call attempts, wall time and estimated cost.",
            "Both use gpt-4.1-mini analysis, gpt-5-search-api hosted search, low search context, 512 search-output tokens, temperature 0.2 and an 8,192-token hosted-search input reservation.",
            "Internal allocation differs by architecture: Solo uses one analysis call with an 8,192-token output cap; RAVE uses specialist calls capped at 4,096 tokens and final synthesis capped at 8,192 tokens.",
            "RAVE is pinned to the exact candidate commit recorded above. The Solo Baseline code is the version in this benchmark-lab branch.",
            "The estimated USD cost ceiling is local and is not a provider-enforced billing limit. Verify configured search prices and maintain an independent provider spend limit.",
        ],
        "pairs": [],
    }
    _write_batch_manifest(batch_manifest_path, batch_manifest)

    for question in questions:
        pair_dir = batch_dir / question["id"]
        pair_dir.mkdir(parents=True, exist_ok=False)
        pair_record: dict[str, Any] = {
            "question_id": question["id"],
            "category": question["category"],
            "pair_status": "RUNNING",
            "question": question["question"],
            "scope": question["scope"],
            "artifact_dir": str(pair_dir.relative_to(LAB_ROOT)),
        }
        batch_manifest["pairs"].append(pair_record)
        _write_batch_manifest(batch_manifest_path, batch_manifest)

        try:
            solo_command = build_solo_command(question["question"], question["scope"])
            solo_completed, solo_cli = run_json_command(
                solo_command, COMPARISON_A_ROOT, solo_env, budget["max_seconds"] + 90
            )
            write_process_output(pair_dir, "solo_cli", solo_completed)
            if solo_completed.returncode != 0:
                raise RuntimeError(f"Solo Baseline exited with code {solo_completed.returncode}")
            (pair_dir / "solo_cli_output.json").write_text(
                json.dumps(solo_cli, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            solo_artifact_dir = Path(solo_cli["artifact_dir"])
            if not solo_artifact_dir.is_absolute():
                solo_artifact_dir = COMPARISON_A_ROOT / solo_artifact_dir
            solo_metadata_path = solo_artifact_dir / "metadata.json"
            solo_result_path = solo_artifact_dir / "result.json"
            if not solo_metadata_path.is_file() or not solo_result_path.is_file():
                raise RuntimeError("Solo Baseline did not persist both run artifacts")
            solo_metadata = json.loads(solo_metadata_path.read_text(encoding="utf-8"))
            solo_result = json.loads(solo_result_path.read_text(encoding="utf-8"))
            if solo_metadata.get("status") != "COMPLETED" or solo_result.get("status") != "COMPLETED":
                raise RuntimeError("Solo Baseline did not complete; RAVE was not started for this question")
            if solo_metadata.get("question") != question["question"] or solo_metadata.get("scope") != question["scope"]:
                raise RuntimeError("Solo Baseline artifact question/scope mismatch")
            shutil.copy2(solo_metadata_path, pair_dir / "solo_metadata.json")
            shutil.copy2(solo_result_path, pair_dir / "solo_result.json")
            pair_record["solo_baseline"] = _baseline_metrics(solo_metadata, solo_result)
            pair_record["solo_run_id"] = solo_metadata.get("run_id")

            rave_command = [
                "uv", "run", "--project", str(rave_path), "--locked",
                "rave", "hive", question["question"], "--scope", question["scope"],
            ]
            rave_completed, rave_cli = run_json_command(
                rave_command, rave_path, child_env, budget["max_seconds"] + 90
            )
            write_process_output(pair_dir, "rave_cli", rave_completed)
            if rave_completed.returncode != 0:
                raise RuntimeError(f"RAVE CLI exited with code {rave_completed.returncode}")
            (pair_dir / "rave_cli_output.json").write_text(
                json.dumps(rave_cli, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            rave_run_id = rave_cli.get("run_id", "unknown")
            rave_artifact_path = Path(rave_cli.get("result_path", ""))
            if not rave_artifact_path.is_absolute():
                rave_artifact_path = rave_path / rave_artifact_path
            if not rave_artifact_path.is_file():
                raise RuntimeError("RAVE did not persist its run artifact")
            shutil.copy2(rave_artifact_path, pair_dir / "rave_run.json")
            rave_run = json.loads(rave_artifact_path.read_text(encoding="utf-8"))
            rave_status = rave_run.get("execution_status", rave_cli.get("execution_status"))
            agents = rave_run.get("agent_results", rave_cli.get("agent_results", []))
            completed_agents = [
                item for item in agents
                if isinstance(item, dict) and item.get("status") == "COMPLETED"
            ]
            rave_final = rave_run.get("final_output", rave_cli.get("final_output", {}))
            rave_answer = pilot.compose_rave_answer(rave_final) if isinstance(rave_final, dict) else ""
            if rave_status != "COMPLETED" or len(agents) != 3 or len(completed_agents) != 3 or not rave_answer.strip():
                raise RuntimeError(
                    f"RAVE run is not eligible: status={rave_status}, completed_agents={len(completed_agents)}/3"
                )

            integration = rave_run.get("integration", {})
            rave_sources = integration.get("web_sources", []) or []
            rave_model_refs = integration.get("model_reported_references", []) or []
            rave_limitations = rave_final.get("gaps_and_limitations", []) if isinstance(rave_final, dict) else []
            normalized_rave_sources = pilot.normalize_rave_sources(rave_sources, rave_model_refs)
            blind_responses, system_key = pilot.build_blinded_responses(
                {
                    "answer": solo_result.get("answer", ""),
                    "sources": solo_result.get("sources", []) or [],
                    "limitations": solo_result.get("limitations", []) or [],
                },
                {
                    "answer": rave_answer,
                    "sources": normalized_rave_sources,
                    "limitations": rave_limitations,
                },
            )
            (pair_dir / "blind_responses.json").write_text(
                json.dumps(blind_responses, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (pair_dir / "system_key.json").write_text(
                json.dumps(system_key, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            pair_record["rave_hive"] = _rave_metrics(rave_run)
            pair_record["rave_run_id"] = rave_run_id
            pair_record["pair_status"] = "COMPLETED"
        except Exception as exc:
            pair_record["pair_status"] = "FAILED"
            pair_record["error_type"] = type(exc).__name__
            pair_record["error_message"] = str(exc)[:2000]
            batch_manifest["batch_status"] = "FAILED"
            _write_batch_manifest(batch_manifest_path, batch_manifest)
            print(f"[{question['id']}] FAILED: {exc}", file=sys.stderr)
            return 1

        _write_batch_manifest(batch_manifest_path, batch_manifest)
        print(f"[{question['id']}] COMPLETED")

    batch_manifest["batch_status"] = "COMPLETED"
    batch_manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
    _write_batch_manifest(batch_manifest_path, batch_manifest)
    print(json.dumps({
        "batch_id": batch_id,
        "batch_status": batch_manifest["batch_status"],
        "completed_pairs": len(batch_manifest["pairs"]),
        "artifact_dir": str(batch_dir),
    }, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run paired Solo Baseline vs RAVE research for a JSON question batch."
    )
    parser.add_argument("--questions-file", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--live", action="store_true", help="Required opt-in for paid research requests")
    args = parser.parse_args()
    if not args.live:
        parser.error("No API request is made unless --live is explicitly supplied")
    questions_path = args.questions_file
    if not questions_path.is_absolute():
        questions_path = LAB_ROOT / questions_path
    try:
        return run_batch(questions_path)
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"{parser.prog}: error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
