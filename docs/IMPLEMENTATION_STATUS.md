# Implementation status — RAVE paired pilot

Updated 2026-11-18. No live RAVE research request has been sent during this preparation.

## Completed

- Preserved Comparison A run `solo-5b3dc0590dfc`: `COMPLETED`, 8 provider-returned sources, estimated cost USD 0.06093635, duration about 54.9 seconds. Its original artifacts remain unchanged.
- Merged the guarded lab runner into `rave-benchmark-lab` `main` (merge commit `687a3c597bef2851d282cc929a33bccda8883d0b`).
- The runner validates the preserved A artifact and exact question/scope, checks model mapping, search provider, pricing assumptions and budget limits, performs a non-billable `GET /models` authentication preflight, then runs only RAVE. It does not rerun Comparison A.
- The runner clones RAVE into ignored `.cache/project_RAVE`, pins an exact commit, and leaves the user's separate local RAVE checkout untouched.
- Pair artifacts are local and ignored. `blind_responses.json` contains randomly ordered responses normalized to the same schema; `system_key.json` stores the mapping separately.

## RAVE candidate implementation

- Repository: `richardsilva-dev/project_RAVE`
- Candidate branch: `benchmark-a-current-hive-budget-guard`
- Pinned code commit: `0f7ad66f43eb427bcb66d21a08421b243f6ca0e5` (PRs #6 and #7 merged into the candidate branch)
- Base/frozen architecture: `independent_research` at `d5a7b2397bc50796ab83ee22ed326fdc087b84b2`
- PR #7 corrigiu a reserva conservadora de tokens (estimativa por bytes UTF-8 / 3, arredondada para cima); o uso informado pelo provedor continua sendo a fonte autoritativa na reconciliação do orçamento.
- GitHub Actions run `44353374252` on the exact pinned commit `0f7ad66f43eb427bcb66d21a08421b243f6ca0e5`: 43 tests passed on Python 3.11.
- The candidate preserves the current three-specialist Hive, peer refinement, evidence provenance, independent/shared research modes, partial-run handling, single-agent command and research reuse. It is not the older budget branch based directly on `main`.
- Run-wide guard: 80,000 tokens, 3 search attempts, 12 model-call attempts, 180 seconds and USD 0.50 estimated-cost ceiling. Search input reservation for the paired lab profile: 8,192 tokens, matching the preserved baseline metadata.
- Shared pilot mode: one shared search; hosted search output cap 512 tokens; specialist analysis/refinement cap 4,096 tokens per call; final synthesis cap 8,192 tokens.
- Specialist output is bounded to 3 findings per agent, 3 evidence items per finding, 120 summary words and 250 characters per evidence excerpt.
- Retries count as separate attempts. Transient failures retain reservations conservatively; definitive 401/403 failures release reservations. Authenticated HTTP redirects are refused. JSON repair is budgeted and output schemas are validated.
- PR #5 is still an independent review item against the frozen `independent_research` branch. The frozen branch itself has not been changed. PR #6 (bounded synthesis context) was merged into `benchmark-a-current-hive-budget-guard`; it did not target `independent_research` or `main`.

## Historical diagnostics

- `solo-1e01244d0f41`: HTTP 401 `invalid_api_key`; no research sources returned. The client correctly did not retry authentication failure.
- `solo-45ec415605c5`: blocked before network I/O by token-budget reservation.
- `solo-cbd344a619ea`: search completed, but analysis/JSON-repair output hit the 4,096-token ceiling and final JSON remained invalid.
- `solo-5b3dc0590dfc`: successful integration pilot described above.

## Remaining account-side gate

The local `.env` key used in the failed run may still be invalid. The runner first calls `GET /models`; if it receives HTTP 401/403, it stops before any paid research request and instructs the user to replace `RAVE_API_KEY` in the ignored local `comparison_a/.env`. Never paste the key into chat or commit it.

The GPT-5 Search API token rates (USD 1.25 input / USD 10.00 output per million tokens) are user-configured estimates carried from the historical A run. The runner requires them to match the A metadata and they must be verified against the applicable billing record. The USD 0.50 run ceiling is a local estimate, not a provider-enforced cap; retain an independent OpenAI project spend limit.

## Local execution

From the lab repository root, with the preserved A artifact present and `comparison_a/.env` configured:

```powershell
python scripts/run_rave_pilot.py --live
```

The script requires the local files `artifacts/runs/solo-5b3dc0590dfc/metadata.json` and `result.json`. If either is missing, it stops without a research request. New pair outputs are written under ignored `artifacts/pairs/`.

The preserved A run already incurred approximately USD 0.06093635. The new RAVE run has a local estimated ceiling of USD 0.50; the estimated maximum total for this preserved pair is approximately USD 0.56093635.

## Evaluation limits

This is a one-question A-versus-C pilot, not the full A/B/C design or ten-question benchmark in Notion. Condition B (multiple simple agents with basic integration) is not implemented, so this pair cannot isolate the value of peer cooperation from the value of multi-agent decomposition. The independent source-based map in `REFERENCE_MAP_PILOT.md` was prepared before the RAVE output but is retrospective relative to the already observed A output; this run is exploratory, not preregistered. The historical A artifact does not record its exact source commit or resolved output cap; RAVE uses a different internal per-call output allocation even though the run-wide ceiling is matched. No blind independent quality scoring has been performed. A completed pair is preliminary evidence only and cannot establish general superiority. Share only `blind_responses.json` for blinded evaluation; keep `system_key.json` separate until scoring is complete. Use [EVALUATION_RUBRIC.md](EVALUATION_RUBRIC.md).

## Comparison B

Comparison B remains blocked. Its upstream lock audit reported 89 known vulnerabilities and two archived dependency statuses. The environment was not installed or executed; do not launch it until the dependency findings are reviewed.
