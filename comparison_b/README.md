# Comparison B — external solo research reference

**Status: selected candidate, hardening incomplete.** The user-created fork exists at https://github.com/richardsilva-dev/local-deep-research, branch `rave-benchmark-hardened-solo`, commit `ba68db827e0430a7e8b15c9af62918482049b805`, with draft PR #1. No external environment has been installed or executed.

## Previous candidate: Open Deep Research

Upstream project: [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research), pinned submodule at commit 1b7d2e80db9faa586165c60e09096dbbfd483a64 (MIT). The dependency preflight is intentionally fail-closed: the frozen lock audit reported 89 known advisories in 242 packages and two archived/adverse dependency statuses. The architecture also uses a supervisor and subagents, so it is not a clean solo baseline without substantial refactoring. Do not install or run this submodule.

## Preferred candidate for next review: Local Deep Research

[LearningCircuit/local-deep-research](https://github.com/LearningCircuit/local-deep-research) at the reviewed commit 8717d257c234d23a687b8c66c4e5174b4d7e2ea7 (MIT) appears to be a stronger candidate for hardening. Its LangGraph strategy can disable sub-research by setting LDR_LANGGRAPH_AGENT_INCLUDE_SUB_RESEARCH=false. However, its upstream explicitly documents an unresolved unstructured URL-partition SSRF advisory, an LLM SDK DNS boundary, and search-provider differences from RAVE. It is not approved yet.

The next B work must finish on the existing fork: fresh dependency audit, runtime proof of exactly one agent/no child tasks, enforced disabling of document uploads and unrelated surfaces, and tested OS/container-level egress restrictions. The lock still contains vulnerable `unstructured==0.18.32`; the upstream tripwire is only a compensating source-level guard. The new single-agent tests currently exercise the resolver helper, not the instantiated runtime strategy. No CI run exists for this fork branch yet.

See [external reference review](../docs/EXTERNAL_REFERENCE_REVIEW.md) for the findings and hardening criteria. No official benchmark questions or scoring protocol have been started.
