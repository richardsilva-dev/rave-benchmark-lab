# External research-agent reference review

**Review date:** 2026-11-13  
**Status:** Local Deep Research has a user-created fork and a draft hardening branch, but is still not approved for installation or execution.  
**Purpose:** Select a genuinely solo external research agent for Comparison B without weakening RAVE or confusing a multi-agent system with a single-agent baseline.

## Decision summary

| Candidate | Solo suitability | Security / dependency posture | Decision |
|---|---|---|---|
| Open Deep Research | Not a clean solo baseline: its frozen architecture uses a supervisor and subagents | Frozen lock audit reported 89 advisories in 242 packages and adverse archived-package statuses for two dependencies | Blocked; do not install or run |
| SearchClaw | One central research agent with tools, but tool calls may run concurrently | No committed Python dependency lock at the reviewed commit; DNS resolution errors fail open in its URL validator; web fetch follows redirects automatically; optional Jina, browser/CDP, skills and memory enlarge the attack surface | Not selected; do not install or run upstream |
| Local Deep Research | Its LangGraph agent can be run without the sub-research tool when include_sub_research=false | Stronger documented SSRF/egress controls and active security automation, but one known suppressed dependency advisory and a residual LLM-SDK DNS boundary remain | Preferred candidate for the next hardening review; still not approved |

This is a source-code and repository review, not a penetration test. No candidate environment was installed or executed during this review. A green CI/security scan is evidence about the scanned revision and configured checks; it is not proof that the whole application is vulnerability-free.

## 1. Open Deep Research — blocked

Frozen reference: langchain-ai/open_deep_research commit 1b7d2e80db9faa586165c60e09096dbbfd483a64 (MIT).

The dependency audit already recorded in DEPENDENCY_AUDIT.md reported **89 known advisories across 242 packages**, together with archived/adverse package statuses for langchain-community and rsa. The audit output did not provide severity scores, so this review does not label all findings critical or exploitable.

The upstream implementation uses a supervisor/subagent research graph. Treating it as a single-agent baseline would require an architectural flattening, not merely a configuration switch. That would also make the benchmark reference a locally modified derivative rather than an unmodified upstream agent.

A fork by itself would not resolve the findings. A proper fork would need reviewed dependency upgrades, a newly generated immutable lock, a fresh vulnerability audit, regression tests, and a documented architecture change. The frozen upstream environment remains uninstalled and blocked.

**Fork status update (2026-11-13):** The user created https://github.com/richardsilva-dev/local-deep-research. Its branch `rave-benchmark-hardened-solo` is six commits ahead of `main` at `ba68db827e0430a7e8b15c9af62918482049b805`; draft PR #1 is open. The branch adds a benchmark profile, a fail-closed environment switch that suppresses the `research_subtopic` tool, and unit tests for the switch. This is a real fork, not an upstream modification.

## 2. SearchClaw — reviewed, not selected

Reviewed upstream commit: RUC-NLPIR/SearchClaw 818c43fdfd20368074ba020ea133e3844b500314 (MIT).

SearchClaw has a single central research loop with planning, search/fetch tools and quality hooks. It is therefore closer to a solo-agent reference than Open Deep Research's supervisor/subagent architecture. Its documented defaults and optional features are not suitable for this benchmark without narrowing.

Blocking findings in the reviewed source:

1. **DNS fail-open:** the URL validator's DNS resolver returns None on resolution errors; the common validator only checks resolved addresses when results exist, and otherwise can permit the URL. A DNS outage must not silently skip SSRF checks.
2. **Redirect validation:** the web fetch client follows redirects automatically after validating the initial URL. Redirect destinations need to be checked on every hop; validating only the first URL leaves a redirect path to a private or metadata address.
3. **Unpinned dependency graph:** the inspected upstream tree has no committed Python lockfile, and its pyproject.toml uses broad minimum-version constraints. A reproducible lock and an advisory/license audit are prerequisites.
4. **Unnecessary attack surface for this experiment:** the upstream offers Jina Reader, browser/CDP access, skills that can run Python, persistent memory, and several search providers. CDP can inherit a user's browser session. These features must be disabled or removed from the benchmark build.
5. **Provider mismatch:** the default path uses external search services (for example Serper and Jina), not the frozen RAVE gpt-5-search-api Chat Completions search path. Using it as B would measure the package and its search providers together, not isolate agent orchestration.

SearchClaw is not approved for install, execution, or benchmark comparison in its upstream state. It could only be reconsidered after a real fork/patch, fail-closed DNS validation, per-hop redirect validation, an immutable lock, audited dependencies, and an offline security test suite.

## 3. Local Deep Research — preferred candidate for the next review

Reviewed upstream commit: LearningCircuit/local-deep-research 8717d257c234d23a687b8c66c4e5174b4d7e2ea7 (MIT, Python >=3.12,<3.15, PDM lockfile).

### Why it is the stronger candidate

- The project maintains a detailed SECURITY.md, explicit security tests and automation for OSV-Scanner, CodeQL, Semgrep and dependency review. The latest observed successful security workflows were on commit d6c81c5dcf6327ed32ec80b74fd0d885190b49dd; this differs from the commit pinned above and is not treated as a scan of the pinned reference.
- Its safe_requests path validates destinations and uses DNS pinning for the outbound connection, including re-pinning across redirect hops. Its security documentation explains the remaining boundaries.
- Its LangGraph strategy exposes include_sub_research; setting it to false removes the research_subtopic subagent tool. The codebase includes tests for this configuration.

### Findings in the user's fork branch

- The branch has not produced a GitHub Actions run in the fork; no CI result is available for the exact branch.
- `pdm.lock` still resolves `unstructured==0.18.32`, within the affected range `>=0.4.7,<0.24.0` for GHSA-4mvj-m6j5-pmf7 / CVE-2026-71428. The upstream source tripwire asserts no URL reaches the unstructured partitioner and documents that current call sites use local file paths. This is a compensating source-level control, not removal of the vulnerable package. The benchmark profile also says uploads must be disabled, but this fork branch does not yet enforce that prohibition at runtime.
- The new test file tests `resolve_include_sub_research()` in isolation. It does not instantiate the actual strategy and assert that the runtime tool list excludes `research_subtopic`, that no child research task starts, or that exactly one agent is created.
- The profile requires OS/container-level egress restrictions, but the fork does not yet provide a reproducible, tested firewall/proxy/container policy or denied-destination integration tests. The in-process egress controls explicitly disclaim being a hard boundary.
- The environment switch is wired into the LangGraph strategy constructor and the tool is appended only when `self.include_sub_research` is true; this is promising source evidence, but it is not a substitute for runtime verification.

### Blocking risks and required restrictions

1. The current pyproject.toml explicitly documents unstructured 0.18.x as affected by GHSA-4mvj-m6j5-pmf7 / CVE-2026-71428, a URL-partitioning SSRF. The upstream maintains a source-level tripwire and scanner suppressions because its Python 3.14 production image cannot currently use the fixed upstream release. This is a known unresolved dependency finding, not a clean bill of health.
2. LDR's own security documentation identifies a DNS resolve-versus-connect window for some LLM SDK endpoint calls because the SDK re-resolves hostnames outside the pinned safe_requests path. The documented operator mitigation is outbound firewall/egress restriction.
3. The research agent has sub-research enabled by default. The benchmark build must set LDR_LANGGRAPH_AGENT_INCLUDE_SUB_RESEARCH=false and verify through tests/telemetry that no subagent tool or child research is created.
4. The project has document-ingestion and server surfaces that are unnecessary for this comparison. A benchmark build must use a CLI/programmatic one-run path, disable upload/document ingestion, browser/CDP, notifications and unrelated integrations, and avoid exposing a web server.
5. The search-engine system does not use the same hosted gpt-5-search-api route as frozen RAVE. Even with the same analysis model, a different search backend is a material experimental confound. The B adapter must record this explicitly; no search provider may be described as equivalent without a dedicated adapter and tests.
6. The PDM lock is large and has not yet been audited independently in this lab. The upstream's successful security workflows are useful evidence, but they do not replace a fresh audit of the exact lock we intend to execute.

### Hardening plan before approval

- Keep the existing dedicated fork and pin its upstream base commit; do not patch upstream silently.
- Use a Python version/build that allows the affected unstructured dependency to be removed or upgraded to a fixed version. If that cannot be resolved with compatible tests, block LDR rather than rely only on the upstream tripwire.
- Generate and commit a clean PDM lock; run a fresh OSV/pip audit and license inventory against that exact lock. Any unresolved high/critical or archived dependency must be explicitly reviewed and accepted or fixed before installation.
- Run only the solo LangGraph strategy with include_sub_research=false; add an assertion/test that research_subtopic and child-run creation are absent.
- Restrict the tool surface to one selected search provider and controlled page fetch. Disable document uploads, PDF ingestion, browser/CDP, memory side effects, notifications, MCP/server exposure and unused providers.
- Enforce OS-level egress allowlisting for the LLM endpoint and chosen search/fetch services. Do not rely on application-level host validation as the only network boundary.
- Add deterministic run limits and telemetry for every provider request, retry, search, token usage, elapsed time, source and final status.
- Run offline security tests, schema/adapter tests, and a clean CI workflow before any live API probe.

## 4. Benchmark integrity constraints

Comparison A remains the in-house sequential solo baseline and is pinned to the frozen RAVE model identifiers. Comparison B must also be exactly one active researcher at runtime. Neither baseline may call RAVE/Hive, use its MessageBus, or inherit its agent outputs.

Comparison B's model, search provider, page-fetch method, parallelism, token budget, retries and prompt/system configuration must be recorded. When those do not match RAVE, the result is a system-level comparison with explicit confounds—not proof that a single architectural feature caused an observed difference.

The formal benchmark protocol (question set, repetitions, rubric, blind assessment and statistical plan) has deliberately not been started. The user must be notified and approve before that stage begins.

## References inspected

- [Open Deep Research upstream](https://github.com/langchain-ai/open_deep_research/tree/1b7d2e80db9faa586165c60e09096dbbfd483a64)
- [SearchClaw upstream](https://github.com/RUC-NLPIR/SearchClaw/tree/818c43fdfd20368074ba020ea133e3844b500314)
- [Local Deep Research upstream](https://github.com/LearningCircuit/local-deep-research/tree/8717d257c234d23a687b8c66c4e5174b4d7e2ea7)
- [Local Deep Research security policy](https://github.com/LearningCircuit/local-deep-research/blob/8717d257c234d23a687b8c66c4e5174b4d7e2ea7/SECURITY.md)
- [Local Deep Research unstructured SSRF tripwire](https://github.com/LearningCircuit/local-deep-research/blob/8717d257c234d23a687b8c66c4e5174b4d7e2ea7/tests/security/test_unstructured_url_partition_tripwire.py)
