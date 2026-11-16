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
