# Implementation status

Updated 2026-11-13. Private lab: https://github.com/richardsilva-dev/rave-benchmark-lab. The RAVE main repository was not modified.

## Scope and alignment

This lab prepares three comparable systems: frozen RAVE/Hive, an in-house single-agent baseline (Comparison A), and a separately hardened external single-agent reference (Comparison B). Comparison A has no subagents, MessageBus, delegated research or Hive integration. Comparison B must prove the same single-agent runtime property. The lab has not created official questions, a scoring rubric, repetitions, blind evaluators or a statistical plan.

The frozen RAVE reference is branch independent_research, commit d5a7b2397bc50796ab83ee22ed326fdc087b84b2. Models observed in its valid Nov 11/12 runs are gpt-4.1-mini for analysis and gpt-5-search-api for hosted web search. Comparison A is now pinned to those model identifiers and the official OpenAI HTTPS API endpoint.

## Comparison A — implemented, automated validation in progress

Comparison A has its own Python project, uv.lock and isolated environment. The current hardening branch is sami-token-guard-searchclaw-audit.

Implemented controls:
- One sequential researcher with one in-memory run history; no delegated agents.
- Model identifiers pinned to the frozen RAVE model pair; environment overrides are rejected.
- Provider endpoint restricted to the official HTTPS OpenAI API origin.
- Before every HTTP attempt: reserve serialized request bytes, an explicit input safety margin and the complete max_completion_tokens cap. The request output cap is mandatory.
- Every HTTP attempt, including retries, consumes the total model-call budget. Logical research searches are counted once; retries are separately counted as search attempts.
- Usage reconciliation replaces reservations when the provider reports usage. Rejected HTTP 4xx requests release reservations. Unknown outcomes (timeout, transport error, 5xx, missing usage metadata or unusable response envelope) are charged conservatively as unknown usage.
- Retry only provider-classified transient 429 rate limits, at most three attempts, honoring Retry-After/token-reset headers only when the requested wait fits the remaining wall-clock budget and the 420-second ceiling.
- Telemetry stores per-attempt duration/accounting, provider usage, unknown usage, and separate provider-returned versus model-reported sources.
- JSON output contract is validated. Invalid first output is INVALID and contains no unvalidated answer; a later invalid output preserves prior validated text only as PARTIAL.
- URLs are normalized for identity (scheme/host casing, default ports, fragments, common tracking parameters) while the original URL is retained. Model-reported URLs are candidates, never provider-confirmed citations. A run without structured provider-returned citations cannot be COMPLETED.
- Offline tests cover retry, token reservation, model drift, malformed usage/output, provenance, URL deduplication, result status and config validation.

Budget limitations are explicit: serialized UTF-8 bytes are a conservative estimate for visible request input, not the exact model tokenizer. Hidden provider/tool framing is not observable. Provider usage can exceed the estimate; the run then stops after the response and is marked incomplete. A request already in flight may exceed the wall-clock target. USD budget is fail-closed/disabled until a dated price schedule and estimator exist; unknown cost is null, never zero.

GitHub Actions run 43438587507 passed on exact HEAD 6e9cbb8f0023f5234ddffcc7c8738e5cf1fa1731: isolated installation from uv.lock succeeded, all 58 pytest tests passed, all 10 offline security smoke checks passed, and the three shared JSON Schemas parsed successfully. The run made no live API calls. This validates the current branch head at that checkpoint; subsequent documentation-only commits must still retain green CI.

No real API call has been made. The local .env with RAVE_API_KEY is absent; no key was requested in chat or read, and no paid API call was made. Once the user has configured the key locally, one small explicitly capped integration probe is still required.

## Comparison B — Open Deep Research blocked; Local Deep Research under review

Open Deep Research remains pinned as a submodule at 1b7d2e80db9faa586165c60e09096dbbfd483a64 (MIT). Its frozen lock audit reported 89 advisories across 242 packages and adverse archived-package statuses for two dependencies. No severity scores were present in that audit output. Its supervisor/subagent architecture is also not a clean solo baseline. It was not installed or executed.

SearchClaw is not selected: the inspected upstream lacked a Python lockfile and had fail-open DNS error handling plus automatic redirects without hop-by-hop revalidation. Its optional Jina, browser/CDP, skills and persistent-memory features would need to be removed or disabled, and its search provider differs from RAVE.

Local Deep Research (LDR) is the preferred next candidate for a hardened B review because it has a PDM lockfile, dedicated SSRF/egress controls and tests, and a supported include_sub_research=false mode. It is not approved yet: the upstream explicitly records an unresolved unstructured URL-partitioning SSRF advisory and the LLM SDK endpoint path retains a DNS resolve/connect limitation. Its search provider is not the same hosted gpt-5-search-api route. See docs/EXTERNAL_REFERENCE_REVIEW.md.

No external candidate has been installed or executed. No fork has been created. The available GitHub actions can edit and inspect repository branches but do not expose a GitHub repository-fork operation. If we proceed with LDR, the user must create the fork through GitHub first; we can then work against that repository and pin a reviewed commit.

## Current branch and repository state

- Current work: branch sami-token-guard-searchclaw-audit.
- Draft PR #1 remains unmerged and is superseded by the current continuation branch; do not merge PR #1. The current branch is the authoritative review snapshot.
- Main remains unchanged.
- RAVE main repository remains unchanged.
- No official benchmark question set or evaluation rubric exists yet.

## User intervention required

1. Configure comparison_a/.env locally from comparison_a/.env.example and set RAVE_API_KEY. Do not paste or send the key in chat. Once configured, tell us only that the key is ready; the first live call will be a single, explicitly capped installation probe, not benchmark data.
2. If proceeding with LDR as Comparison B, create a GitHub fork of LearningCircuit/local-deep-research under the user's account and share the fork URL. No fork will be simulated or claimed before it exists.

## Stop point before the definitive benchmark protocol

The next formal stage is the definitive benchmark protocol: official question set, fixed repetitions, objective evaluation rubric, blind evaluation procedure and statistical analysis plan. This stage has not started. Stop and notify the user for approval before creating any of those materials or collecting benchmark results.
