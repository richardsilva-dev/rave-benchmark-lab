# Implementation status

Updated 2026-11-16. Active correction branch: `fix/comparison-a-json-output-and-validation`, based on `comparison-a-budget-and-methodology-hardening`.

## Findings from the four recorded pilot runs

- `solo-1e01244d0f41`: failed before useful work; hosted search returned HTTP 401 with `invalid_api_key`. This is a credential/account configuration failure, not a prompt or retry bug. The client correctly does not retry 401.
- `solo-45ec415605c5`: blocked before network I/O because the configured reservation exceeded the run token budget.
- `solo-5b3dc0590dfc`: completed successfully; 8 provider-returned sources; estimated cost USD 0.06093635; duration about 54.9 seconds.
- `solo-cbd344a619ea`: search succeeded, but both analysis and JSON-repair output hit the 4,096-token completion ceiling and the final response remained invalid JSON. This is consistent with output truncation, not an authentication failure.

## Changes in this correction branch

- Raise the analysis/JSON-repair completion-token floor to 8,192 because the failed run exhausted 4,096 output tokens.
- Tighten the output contract: concise summary, at most 10 findings, and at most 3 evidence items per finding. This reduces malformed/truncated output while preserving the research structure.
- Add the correction branch to GitHub Actions so the locked offline tests and security smoke checks run against the actual repository commit.
- Preserve fail-closed authentication: HTTP 401/403 are not retried and their reservations are released. No key is written to source control or workflow logs.

## Remaining user-only gate

A 401 caused by `invalid_api_key` cannot be repaired by changing Python code. The credential must be replaced or re-authorized by the account owner. The secure next path is a GitHub Actions repository secret named `RAVE_API_KEY` for any future remote live workflow; never commit the key or paste it into chat. The existing local `.env` remains local and ignored.

## Experimental status

The successful solo run is an integration pilot, not a matched benchmark. Before claiming that RAVE's collective architecture outperforms a single researcher, Comparison A must be paired with a RAVE run using the same question, scope, model/tool mapping, output limits and run-wide budgets. Comparison B remains blocked by its dependency audit and must not be installed or launched until the findings are reviewed.


## RAVE candidate readiness — 2026-11-16

A separate candidate implementation is available in `richardsilva-dev/project_RAVE`:
- Branch: `benchmark-a-global-budget-guard`
- Candidate commit: `bf107f1b72ec7723ec586308532bde10f134af97`
- Run-wide guard: 80,000 tokens, 3 search attempts, 12 model-call attempts, 180 seconds, and USD 0.50 estimated cost.
- Shared search fails closed; no silent fallback to individual agent searches.
- Agent analysis and JSON-repair output cap: 8,192 tokens; final synthesis cap: 8,192 tokens; hosted search cap: 512 tokens.
- Search tool fee is estimated at USD 0.01 per call (USD 10 per 1,000 calls), matching Comparison A.
- A definitive 401/403 releases its token/cost reservation but still counts the failed attempt; timeouts and ambiguous failures retain reservations conservatively.
- Request timeout is bounded by the remaining run-wide wall-clock budget.
- The API key is never committed, printed, or included in telemetry.

The candidate branch remains separate from `main` until its CI checks pass. It does not replace the frozen RAVE reference in [ARCHITECTURE.md](ARCHITECTURE.md).

## Paired pilot readiness

`scripts/run_rave_pilot.py` now creates a fresh Comparison A run and then a RAVE Hive run with the same question and scope. It no longer reuses the historical `solo-5b3dc0590dfc` artifact as if it were a newly matched baseline.

Before sending paid research requests, the runner:
1. verifies that the lab checkout is clean and records its commit;
2. prepares the exact RAVE candidate commit and refuses to overwrite a dirty RAVE checkout;
3. checks the local ignored `comparison_a/.env` configuration and performs a non-billable `GET /models` authentication preflight;
4. applies the same run-wide caps to both systems: 80,000 tokens, 3 searches, 12 model calls, 180 seconds, and USD 0.50 estimated cost per system;
5. runs Comparison A first and stops without launching RAVE if A is not `COMPLETED`;
6. verifies question, scope, model mapping, search price assumptions, and persisted artifacts before creating a pair manifest.

The run is a one-question pilot, not the ten-question protocol. It creates blinded response files and a separate system key, but no blind independent quality scoring has yet been performed. A completed pair is preliminary evidence, not proof of general superiority. Comparison B remains blocked by its dependency audit and must not be installed or launched.
