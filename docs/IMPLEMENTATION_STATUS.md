# Implementation status

Updated 2026-11-13. Private lab: https://github.com/richardsilva-dev/rave-benchmark-lab. The RAVE main repository was not modified.

## Scope and alignment

This lab prepares three comparable systems: frozen RAVE/Hive, an in-house single-agent baseline (Comparison A), and a separately hardened external single-agent reference (Comparison B). Comparison A has no subagents, MessageBus, delegated research or Hive integration. Comparison B must prove the same single-agent runtime property. The lab has not created official questions, a scoring rubric, repetitions, blind evaluators or a statistical plan.

The frozen RAVE reference is branch independent_research, commit d5a7b2397bc50796ab83ee22ed326fdc087b84b2. Models observed in its valid Nov 11/12 runs are gpt-4.1-mini for analysis and gpt-5-search-api for hosted web search. Comparison A is now pinned to those model identifiers and the official OpenAI HTTPS API endpoint.

## Comparison A — implemented, automated validation in progress

Comparison A has its own Python project, uv.lock and isolated environment. The current hardening branch is sami-token-guard-searchclaw-audit.

Implemented controls:
- Authenticated HTTP requests use a no-redirect opener; 3xx responses fail closed so the bearer API key is not forwarded to a redirect target. Dedicated regression tests cover the handler and transport seam.
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

GitHub Actions runs 43449308048 and 43449301945 passed on exact HEAD 444534af2369ce9602ef002b7a75c8a0bbf748e4: isolated installation from uv.lock succeeded, all 60 pytest tests passed, all 10 offline security smoke checks passed, and the three shared JSON Schemas parsed successfully. No live API call was made by CI. This checkpoint also includes a no-redirect HTTP transport: authenticated API requests now refuse 3xx redirects rather than allowing urllib's default redirect behavior.

The user reports that comparison_a/.env and RAVE_API_KEY are now configured on their local machine. The local filesystem is not accessible through the GitHub connection, so the secret was neither read nor transmitted. No live API call has been made. A single explicitly capped local integration probe is still required; the user can run it locally without sharing the key.

## Comparison B — Open Deep Research blocked; Local Deep Research forked and hardening

Open Deep Research remains pinned as a submodule at 1b7d2e80db9faa586165c60e09096dbbfd483a64 (MIT). Its frozen lock audit reported 89 advisories across 242 packages and adverse archived-package statuses for two dependencies. No severity scores were present in that audit output. Its supervisor/subagent architecture is also not a clean solo baseline. It was not installed or executed.

SearchClaw is not selected: the inspected upstream lacked a Python lockfile and had fail-open DNS error handling plus automatic redirects without hop-by-hop revalidation. Its optional Jina, browser/CDP, skills and persistent-memory features would need to be removed or disabled, and its search provider differs from RAVE.

Local Deep Research (LDR) fork confirmed at https://github.com/richardsilva-dev/local-deep-research. Its main branch currently matches upstream commit 8717d257c234d23a687b8c66c4e5174b4d7e2ea7. A separate branch, rave-benchmark-hardened-solo, now contains an explicit process-level override that forces include_sub_research=false, tests for the override, and a benchmark security profile. Draft PR #1 is open: https://github.com/richardsilva-dev/local-deep-research/pull/1. No merge has occurred. The code change has not yet been run through CI; the PR remains draft.

The upstream source documents a critical SSRF in unstructured's URL-taking APIs, but also maintains a static test contract that production code never passes URLs to those APIs (only local file paths). The benchmark profile forbids document uploads/URL partitioning. The LLM SDK's DNS re-resolution limitation remains; an OS/container firewall or strict egress proxy is mandatory. The LDR search provider is not yet shown to match gpt-5-search-api. See docs/EXTERNAL_REFERENCE_REVIEW.md.

No external candidate has been installed or executed. No real API request has been made.

## Current branch and repository state

- Current work in the lab: branch sami-token-guard-searchclaw-audit; last fully validated CI checkpoint: 7c25f6d0701e1d7c2c91a65309440704b40ac199. The latest documentation commit is newer and should have CI rechecked before merge.
- Comparison B fork branch: https://github.com/richardsilva-dev/local-deep-research/tree/rave-benchmark-hardened-solo; draft PR #1 is open and unmerged.
- Draft PR #1 remains unmerged and is superseded by the current continuation branch; do not merge PR #1. The current branch is the authoritative review snapshot.
- Main remains unchanged.
- RAVE main repository remains unchanged.
- No official benchmark question set or evaluation rubric exists yet.

## User intervention required

1. Comparison A key is reported configured locally. Run the capped local smoke probe when instructed; do not paste or send the key in chat. The assistant cannot access the local filesystem or inspect that .env through GitHub.
2. Comparison B still requires an exact search-provider choice/key if the selected LDR search integration needs one, and approval of the OS/container egress boundary. Do not provide API secrets in chat.

## Stop point before the definitive benchmark protocol

The next formal stage is the definitive benchmark protocol: official question set, fixed repetitions, objective evaluation rubric, blind evaluation procedure and statistical analysis plan. This stage has not started. Stop and notify the user for approval before creating any of those materials or collecting benchmark results.


## Final gate review — 2026-11-13 (after user requested all recommendations be applied)

This section is the current release decision and supersedes any wording above that could be read as approval to start the official benchmark.

### Comparison A
- Current reviewed branch head: `463d312619fb086ed5e4772672f3233c444c9119`.
- GitHub Actions runs `43449538522` and `43449549687` completed successfully on this exact head.
- The recorded CI scope is 60 pytest tests, 10 offline security smoke checks, and parsing of 3 shared JSON Schemas. CI did not exercise a live provider call and cannot validate the user's local API credential.
- **Decision:** eligible for one capped, user-initiated live integration probe only. Not yet eligible for official benchmark runs until a successful probe produces schema-valid result and metadata artifacts and actual provider usage is reconciled.

### Comparison B — Local Deep Research
- Fork branch: `rave-benchmark-hardened-solo`, head `ba68db827e0430a7e8b15c9af62918482049b805`; PR #1 remains draft.
- The lock still contains `unstructured==0.18.32`, affected by GHSA-4mvj-m6j5-pmf7 / CVE-2026-71428. The repository documents that a fixed release currently cannot be locked for its supported Python 3.14 target. A static source tripwire is compensating evidence only; it does not remove the vulnerable dependency.
- The solo-mode flag is wired into the LangGraph strategy and controls whether `research_subtopic` is added. Existing benchmark-solo tests exercise the resolver helper, not a full end-to-end run proving one researcher, no child tasks, and the actual final tool list under production configuration.
- No benchmark-specific enforced upload-disable boundary, reproducible OS/container egress policy with deny tests, or CI run on the fork branch has been demonstrated in this review.
- **Decision:** do not install or execute B. These are hard blockers, not accepted risks.

### Official benchmark release gate
- No official benchmark questions, paired runs, blinded scoring, statistical analysis, or performance claims are authorized by these preparatory checks.
- Keep both PRs in draft. Do not merge either branch into its default branch as a substitute for passing the gates.
- Next safe action: run only the capped Comparison A integration probe locally; separately complete B's dependency and isolation gates before any installation or execution.


## RAVE calibration run evidence received 2026-11-13

The user supplied the execution report for valid RAVE run `rave-86b64f402cfd` (question: generative AI in education). This is a real RAVE/Hive run, not a paired benchmark run.

Recorded reference values:
- frozen RAVE branch: `independent_research` (commit `d5a7b2397bc50796ab83ee22ed326fdc087b84b2`), using the shared-search execution path as described in the supplied report;
- 3 agents completed, 36 inter-agent messages, 18 structured findings, 8 deduplicated provider-returned sources;
- 8 LLM calls: 1 hosted web-search call, 3 initial agent analyses, 3 cross-agent integration calls, 1 final synthesis;
- 49,607 input + 26,160 output = 75,767 reported tokens;
- 200.55 seconds total elapsed time;
- output covered 4 benefits, 6 risks, 5 recommendations and 6 limitations/divergences.

Interpretation limits:
- This run is useful as a calibration/reference artifact only. It is not a comparison because no SOLO A or external B run used the same question, scope, initial context, provider configuration and predeclared resource envelope.
- The run report does not demonstrate a pre-call global token ceiling. Its 75,767 tokens are observed consumption, not an enforceable benchmark budget.
- A's earlier capped smoke command (20,000 tokens, 1 search, 2 model calls, 180 seconds) is intentionally much smaller than this RAVE run and must never be compared for quality or efficiency.
- Before the official protocol, choose one common maximum resource envelope for all systems, instrument RAVE's pre-call limits, and keep observed usage separate from configured ceilings. Match model IDs and search route for A; B remains a system-level reference with declared provider/tool deviations.
- The answer itself must be scored against source documents by blind evaluators; citation presence and model-assigned support labels are not independent fact verification.

This report does not authorize the definitive benchmark protocol or official question set. The user must be notified before that phase begins.


## Follow-up hardening status — 2026-11-13

- Comparison A: the current branch head `6d01a47d8dbf8da7d0c39f05aba5d5b7e9213888` passed GitHub Actions run `43458297674`. This run validates the repository's offline tests/security smoke checks/schema parsing, not a live API call. The user's real RAVE run report is recorded above as calibration evidence only.
- Comparison B LDR fork: a follow-up branch `rave-benchmark-final-hardening` and draft PR #2 were created. The lead LangGraph strategy now fails closed if the effective toolset includes `research_subtopic` in solo mode; its system prompt and strict-egress guidance are aligned with solo mode; focused regression tests and a dedicated CI/dependency-audit workflow were added. Earlier draft PR #1 was closed as superseded by PR #2.
- LDR's known `unstructured 0.18.x` advisory is not resolved. The branch's dependency-audit job is a release gate and must not be bypassed. Comprehensive upload/document-ingestion disablement and tested OS/container egress isolation are also still outstanding. LDR remains unapproved for installation/live execution.
- No paid API call was made from CI. No API key was read or transmitted. No official benchmark question set or scoring protocol has been created.

**Release status:** A is ready only for a user-run, capped integration probe. B is blocked. The official benchmark is not yet ready.
