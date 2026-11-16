# Implementation status — RAVE paired pilot

Updated 2026-11-16. Both preparation changes are merged into their respective GitHub default branches. No paid/live API request has been sent during this preparation.

## Merged repository updates

- Project RAVE: merge commit `62ace021acf99745a51760dc13308292867e0801`; candidate implementation commit `7a0032bd81528aa8f69b5beb0f9771b8fc455689`.
- RAVE Benchmark Lab: merge commit `2725ced06d307cbbc8e78f4f4a0e52e208a10b91`.
- Project RAVE GitHub Actions: pytest passed on the merged main commit.
- RAVE Benchmark Lab GitHub Actions: locked tests, offline security smoke checks, schema validation and pilot orchestration tests passed on the PR head; the merged-main workflow is completing separately.
- The RAVE candidate includes run-wide token, search-attempt, model-call, wall-time and estimated-cost reservations; fail-closed shared search; 8,192-token analysis/repair and synthesis caps; at most 10 findings and 3 evidence items per finding; release of reservations on definitive 401/403; and request timeouts bounded by remaining run time.
- The hosted web-search fee is estimated at USD 0.01 per call (USD 10 per 1,000 calls), consistent with the current OpenAI pricing page. The GPT-5 Search API token rates remain explicit user-configured estimates carried forward from the previous pilot (USD 1.25 input / USD 10 output per million tokens); verify against the billing record.

## Historical pilot outcomes

These four earlier runs are diagnostic history, not a matched comparison:
- `solo-1e01244d0f41`: HTTP 401, `invalid_api_key`; no research sources returned.
- `solo-45ec415605c5`: blocked before network I/O by token-budget reservation.
- `solo-5b3dc0590dfc`: completed with 8 provider-returned sources, estimated cost USD 0.06093635, duration about 54.9 seconds.
- `solo-cbd344a619ea`: search completed, but the 4,096-token analysis/repair ceiling was insufficient and the final JSON remained invalid.

The runner no longer reuses the historical successful solo artifact as a matched baseline. It creates a new solo run and then a new RAVE run using the same question, scope, shared-search prompt, model mapping, output bounds and per-system global budget.

## Current pilot profile

- Analysis model: `gpt-4.1-mini`.
- Hosted search model: `gpt-5-search-api`; context `low`; maximum search output 512 tokens.
- Analysis and JSON-repair output cap: 8,192 tokens.
- RAVE final synthesis cap: 8,192 tokens.
- Output bounds: at most 10 findings and 3 evidence items per finding.
- Per-system limits: 80,000 tokens, 3 search attempts, 12 model-call attempts, 180 seconds, USD 0.50 estimated cost.
- Hosted-search input reserve: 16,384 tokens.
- Maximum estimated pair cost: USD 1.00 across the two independent per-system caps. The estimate is not a provider-enforced hard billing limit; an independent OpenAI project spend limit remains necessary.

## Remaining user-only gate

The previous HTTP 401 with `invalid_api_key` is a credential issue, not a code defect. It cannot be repaired by changing repository code. The user must replace the invalid key in the local ignored `comparison_a/.env`; the key must never be pasted into chat or committed. The paired runner performs a non-billable `GET /models` authentication preflight and stops before paid research if authentication fails.

## How the paired pilot runs

From a clean, synchronized local clone of `rave-benchmark-lab`, with a valid key in `comparison_a/.env`:

```powershell
uv run --project comparison_a --locked --extra dev python scripts/run_rave_pilot.py --live
```

The runner verifies the lab checkout is clean, prepares the exact RAVE candidate commit, checks authentication, runs Comparison A first, and does not launch RAVE if A fails. It then runs RAVE with the same question and scope. It saves local-only artifacts under ignored `artifacts/runs/` and `artifacts/pairs/`, including randomly ordered blinded responses with a normalized schema and a separate system key. Give evaluators only `blind_responses.json`; keep `system_key.json` sealed until scoring is complete.

## Interpretation and remaining research

A completed one-question pair is an integration pilot, not proof of general superiority. The blinded responses still require independent scoring against a predeclared rubric. A multi-question evaluation (the broader protocol uses ten questions) is needed before making a general claim. Comparison B remains blocked by the dependency/security audit and must not be installed or launched.
