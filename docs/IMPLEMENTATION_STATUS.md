# Implementation status

Updated 2026-11-13. Private repository: https://github.com/richardsilva-dev/rave-benchmark-lab. Current preparation work is isolated on branch `comparison-a-budget-and-methodology-hardening`; no changes are merged into `main` or the RAVE production repository.

## Comparison A hardening on this branch

- One-agent baseline aligned to RAVE's shared search, analysis schema and JSON repair strategy.
- Token and estimated-cost reservations occur before each outbound request; retries retain reservations conservatively.
- A global model-call-attempt limit is now supported and counts retries and JSON repair calls.
- CLI requires explicit token, search, wall-time, cost and model-call limits; maximum allowed local run-cost argument is USD 0.50.
- GPT-4.1-mini rates and Web Search fee are configured from the official OpenAI pricing page. GPT-5 Search API has no distinct token-rate row on that page, so live execution requires explicit local input/output rates; unknown rates fail closed.
- Suggested first pilot limits: 80,000 tokens, 3 search attempts, 12 model-call attempts, 180 seconds and USD 0.50 estimated cost.
- Metadata records configured limits, pricing version/rates, reserved search context and estimated cost.

## Important limitations

- Local cost and token ceilings are estimates. Provider-supplied search context is variable, and no local estimator can guarantee a hard provider billing cap. Configure an OpenAI project spend limit independently.
- The GPT-5 Search API token rates must be verified in the user's billing/pricing context or explicitly marked as a proxy assumption before the run.
- GitHub source edits are not equivalent to a local test run. Run the locked test suite in the local VS Code checkout before any paid API call.
- The RAVE runtime itself still needs a matching run-wide token/cost budget implementation before a fully budget-matched paired experiment. This pilot only validates the solo baseline.
- Comparison B remains blocked by the documented dependency/security findings. Do not install or execute it.

## First paid pilot gate

1. Configure the two GPT-5 Search API rate variables in the local ignored `.env`.
2. Verify the OpenAI project spend limit is enabled.
3. Run locked pytest and offline smoke checks.
4. Execute exactly one capped Comparison A pilot with the documented prior question and scope.
5. Inspect both `result.json` and `metadata.json`; only `COMPLETED` is a valid integration result.

This pilot is not official benchmark data and must not be used for a comparative claim.
