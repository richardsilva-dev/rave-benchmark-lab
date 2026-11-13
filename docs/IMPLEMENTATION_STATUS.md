# Implementation status

Updated 2026-11-13. Private remote: https://github.com/richardsilva-dev/rave-benchmark-lab. The RAVE main repository was not modified.

## Completed in published preparation commits

- Separate lab repository created and published privately.
- Frozen RAVE branch and commit verified; architecture, modes, models, provider, and dependency facts documented from that revision.
- Comparison A has its own Python project, `uv.lock`, and `.venv`; config validation, single sequential agent, hosted search matching the RAVE provider, budget controller, telemetry, schema validation, source provenance, and SSRF-conscious page reader are implemented.
- Comparison A dependency audit found no known vulnerabilities or adverse package statuses.
- Comparison A `uv sync --locked --extra dev` completed. `uv run --locked --extra dev pytest -p no:cacheprovider -q`: 21 passed. Offline smoke checks passed. No real API call was made because neither a local `.env` nor `RAVE_API_KEY` was present.
- Common contracts, adapters, protocol docs, and security docs exist. JSON contract syntax and Python byte-compilation passed.
- Open Deep Research is an actual git submodule at `1b7d2e80db9faa586165c60e09096dbbfd483a64`; the upstream MIT license is preserved. Config fields and model/search mapping are inspected and documented.

## Continuation branch: sami-review-budget-guards

This review branch was created from published commit `ea72c080f1edea48d968e4fd0a46d10aaef5003e`. It adds an explicit max-model-call cap (counting retry attempts) and fails closed if a USD budget is supplied without a cost estimator. Three focused budget tests were added. GitHub Actions run `43426091579` completed successfully: 24 pytest tests passed, the offline security smoke suite passed, and all three shared JSON schemas parsed successfully. These changes are not yet merged.

The current token limit is checked after provider-reported usage. One in-flight response can exceed the remaining allowance; do not describe the token limit as a strict hard cap until prompt estimation/output reservation is implemented.

## Security gate and remaining work

- `uv audit --locked` on the Open Deep Research lock reported 89 known advisories across 242 packages and archived statuses for `langchain-community` and `rsa`. The audit output contained no severity scores. Per the lab's security rule, Comparison B installation, startup, and smoke test are stopped pending review. The upstream lock has not been edited. See [DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md).
- Comparison B has no installed independent virtual environment, so the lab is not ready for a benchmark.
- Comparison A's real installation probe awaits a locally configured API key; no credentials were read or logged and no paid calls were made.
- No official questions, scoring rubric, evaluator, or benchmark run were created.
- Model/search equality is imperfect: Open Deep Research `search_api="openai"` uses `web_search_preview`, while frozen RAVE uses `gpt-5-search-api` via Chat Completions. This is documented as a confound.
- The Open Deep Research runner is intentionally not configured: its preflight fails closed while the pinned upstream lock has known advisories. Do not bypass this gate or silently patch upstream.

## Before any benchmark

Assess and resolve Comparison B's dependency security findings without silently changing the frozen upstream reference; prepare and audit its independent environment; verify local loopback startup, models/search, source retention, and metadata; run the Comparison A live installation probe when credentials are configured; complete adapter compatibility tests; then define the formal experimental protocol in a later stage. Confirm the continuation branch tests before merging it. Do not start official comparisons while these items remain pending.
