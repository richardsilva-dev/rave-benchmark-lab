# Comparison B — Open Deep Research

Upstream project: [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research), submodule pinned to `1b7d2e80db9faa586165c60e09096dbbfd483a64` (MIT). Its upstream `pyproject.toml` and `uv.lock` define the independent environment.

The scripts in `scripts/` verify the pinned checkout and run a fail-closed dependency preflight. The pinned lock currently reports 89 known advisories across 242 packages and two archived dependency statuses, so the preflight intentionally refuses installation or launch pending security review. See `../docs/DEPENDENCY_AUDIT.md`. Do not update upstream dependency pins as a silent repair.
