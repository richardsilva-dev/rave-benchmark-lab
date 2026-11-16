# Architecture and frozen references

## Purpose and boundary

The lab compares the frozen RAVE baseline against two separately managed systems. It lives outside `project_RAVE`; no experiment code is added to or merged into RAVE. The two Python projects do not share installed dependencies. Shared JSON contracts define only the outer request, result, and run metadata; adapters retain system-specific details and limitations.

## Frozen RAVE reference

- Repository: https://github.com/richardsilva-dev/project_RAVE
- Branch: `independent_research`
- Commit: `d5a7b2397bc50796ab83ee22ed326fdc087b84b2`
- Reference date: 2026-11-12 (commit authored 2026-11-12 15:47:47 UTC)
- Python: `pyproject.toml` requires Python `>=3.11`; exact runtime used by prior experiment is not established by the repository and must be measured before a run.
- Analysis model: `gpt-4.1-mini`
- Web search model: `gpt-5-search-api`, through OpenAI Chat Completions `/chat/completions` with `web_search_options.search_context_size=low` and max 512 completion tokens in the checked-in example configuration.
- Modes: `shared_research` and `independent_research`. Shared research performs one search then supplies its material to three specialist agents. Independent research has each of three specialists search, then analyze. The existing solo baseline uses one search then a single analysis. This lab's A baseline uses a single decision-making agent and must document where its controlled loop differs.
- Dependencies: the RAVE `pyproject.toml` declares no runtime dependencies (stdlib client); dev extra `pytest>=8.0`. The RAVE lockfile is not a lab dependency lock.
- Relevant implementation: `rave/research.py`, `rave/llm.py`, `rave/config.py`, `rave/agents/single.py` at the frozen commit.
- Later changes: never move this reference. Any later RAVE revision is a separate experimental manifest/version.

The frozen RAVE repository's `docs/IMPLEMENTATION_STATUS.md` describes prior v3 runs as exploratory, without blind factual evaluation and with no globally matched budget. The v3 artifacts are historical context only, not this lab's benchmark data.

## Components

`contracts/` holds versioned JSON Schemas. `comparison_a/` is a stand-alone solo research program with sequential control, bounded tools, explicit budget accounting and telemetry. `comparison_b/` contains scripts and configuration for the upstream project pinned as a submodule. `adapters/` normalize outputs while preserving source provenance and system limitations. `manifests/` is reserved for future immutable run manifests; no official benchmark manifest is created in this stage. `artifacts/` is ignored except for its README.

## Data flow

One `ResearchRequest` is sent independently to each system adapter. The adapter returns the original output plus a normalized `ResearchResult` and `RunMetadata`. Normalization does not imply equal internal methods, factual validity, or causal comparability. Model, search mechanism, parameters, budget, runtime and source provenance must accompany any later comparison.

## Reproducibility

Before any formal run, record exact code refs, Python/uv versions, resolved lockfiles, model IDs, endpoint class, search settings, environment variable names (never values), budgets, start/end times and status. Store per-run artifacts locally and keep them out of Git unless explicitly reviewed for secrets and privacy.


## Candidate RAVE build for the first paired pilot

The frozen reference above remains unchanged. The first live pilot uses a separate candidate build from `project_RAVE`:
- Branch `benchmark-a-current-hive-budget-guard`
- Commit `ee45023a64f637e80095e08c4aab56f97d6cc835`
- GitHub Actions: 40 tests passed at run `43923968510`

This candidate adds a run-wide budget and reliability fixes. The lab runner checks out this exact commit in an ignored local cache, leaving the user's other RAVE checkout untouched. It reuses the existing successful Comparison A artifact and runs only the Hive candidate. The candidate is not the frozen reference and must not be described as the same code version as the historical RAVE results.
