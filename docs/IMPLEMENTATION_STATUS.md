# Implementation status

Updated 2026-11-13. Private remote: https://github.com/richardsilva-dev/rave-benchmark-lab, branch `main`. Local commits have been published. The RAVE main repository was not modified.

## Completed

- Separate lab repository created and published privately.
- Frozen RAVE branch and commit verified; architecture, modes, models, provider, and dependency facts documented from that revision.
- Comparison A has its own Python project, `uv.lock`, and `.venv`; config validation, single sequential agent, hosted search matching the RAVE provider, budget controller, telemetry, schema validation, source provenance, and SSRF-conscious page reader are implemented.
- Comparison A dependency audit found no known vulnerabilities or adverse package statuses.
- Comparison A `uv sync --locked --extra dev` completed. `uv run --locked --extra dev pytest -p no:cacheprovider -q`: 21 passed. Offline smoke checks passed. No real API call was made because neither a local `.env` nor `RAVE_API_KEY` was present.
- Common contracts, adapters, protocol docs, and security docs exist. JSON contract syntax and Python byte-compilation passed.
- Open Deep Research is an actual git submodule at `1b7d2e80db9faa586165c60e09096dbbfd483a64`; the upstream MIT license is preserved. Config fields and model/search mapping are inspected and documented.

## Security gate and remaining work

- `uv audit --locked` on the Open Deep Research lock reported 89 known advisories across 242 packages and archived statuses for `langchain-community` and `rsa`. The audit output contained no severity scores. Per the lab's security rule, Comparison B installation, startup, and smoke test are stopped pending review. The upstream lock has not been edited. See [DEPENDENCY_AUDIT.md](DEPENDENCY_AUDIT.md).
- Comparison B has no installed independent virtual environment, so the lab is not ready for a benchmark.
- Comparison A's real installation probe awaits a locally configured API key; no credentials were read or logged and no paid calls were made.
- No numeric budgets, official questions, scoring rubric, evaluator, or benchmark run were created.
- Model/search equality is imperfect: Open Deep Research `search_api="openai"` uses `web_search_preview`, while frozen RAVE uses `gpt-5-search-api` via Chat Completions. This is documented as a confound.

## Before any benchmark

Assess and resolve Comparison B's dependency security findings without silently changing the frozen upstream reference; prepare and audit its independent environment; verify local loopback startup, models/search, source retention, and metadata; run the Comparison A live installation probe when credentials are configured; complete adapter compatibility tests; then define the formal experimental protocol in a later stage. Do not start official comparisons while these items remain pending.
