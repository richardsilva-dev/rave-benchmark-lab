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
- Pinned candidate commit: `831b5b45321ec827d9383d9a73c685740315badf`
- Validation: GitHub Actions run `43920287460` completed successfully (25 tests).
- Run-wide guard: 80,000 tokens, 3 search attempts, 12 model-call attempts, 180 seconds, and USD 0.50 estimated cost.
- Shared search fails closed; no silent fallback to individual agent searches.
- Agent analysis cap: 4,096 tokens; final synthesis cap: 8,192 tokens; hosted search cap: 512 tokens.
- JSON code fences on one line and response-read connection failures now have regression coverage.

The candidate branch is not merged into `main` and does not replace the frozen RAVE reference in [ARCHITECTURE.md](ARCHITECTURE.md). The branch is pinned by the lab runner for this pilot.

## Next live gate

The lab runner `scripts/run_rave_pilot.py` validates and reuses the completed A artifact `solo-5b3dc0590dfc`, checks the local pricing configuration, performs a non-billable `GET /models` authentication preflight, and only then launches one RAVE Hive run with the same question and scope. It does not rerun or modify Comparison A. An HTTP 401 stops before any paid research request; the only required intervention in that case is replacing the local `RAVE_API_KEY`.

The run is still a one-question pilot. The historical A artifact does not record its exact source commit, and no blind independent quality scoring has been performed. A completed pair is preliminary evidence only, not proof of general superiority. Comparison B remains blocked by the dependency audit.
