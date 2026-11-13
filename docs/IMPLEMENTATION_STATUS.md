# Implementation status

Updated 2026-11-13. Private remote: https://github.com/richardsilva-dev/rave-benchmark-lab. The RAVE main repository was not modified.

## Completed in published preparation commits

- Separate lab repository created and published privately.
- Frozen RAVE branch and commit verified; architecture, modes, models, provider, and dependency facts documented from that revision.
- Comparison A has its own Python project, `uv.lock`, and `.venv`; config validation, one sequential agent, hosted search matching the RAVE provider, budget controller, telemetry, schema validation, source provenance, and SSRF-conscious optional page reader are implemented.
- Comparison A dependency audit found no known vulnerabilities or adverse package statuses.
- Initial Comparison A installation completed with `uv sync --locked --extra dev`; 21 tests passed in the Codex environment. Subsequent budget-guard PR run 43426091579 passed 24 tests plus offline smoke checks and schema parsing.
- Common contracts, adapters, protocol docs, and security docs exist. JSON contract syntax and Python byte-compilation passed.
- Open Deep Research is pinned as a submodule at `1b7d2e80db9faa586165c60e09096dbbfd483a64` (MIT); its original lock remains unchanged.

## Current continuation branch: sami-token-guard-searchclaw-audit

This branch adds a pre-call token reservation to Comparison A. Every network attempt reserves serialized request bytes plus a configured safety margin and the request's maximum output-token cap before calling the provider. Successful usage reconciles the reservation; rejected 4xx releases it; unknown outcomes (timeout, network/5xx failure or missing usage metadata) conservatively charge the full reservation. A provider output-cap violation stops the run. The CLI and metadata expose input/output tokens, unknown usage, remaining reservations and the estimate method.

Important limitation: UTF-8 request bytes plus a safety margin are not an exact tokenizer and cannot reveal hidden hosted-tool prompt framing. This is stronger than a post-response-only limit but is not described as a mathematical hard cap. A real provider response can still exceed the estimate; post-call reconciliation detects and stops after that response.

These changes have not yet been validated by GitHub Actions. The workflow must be updated to run on this continuation branch and must pass before treating the changes as verified.

## Security gate: external reference

- Open Deep Research's frozen lock audit reported 89 known advisories across 242 packages and adverse archived statuses for `langchain-community` and `rsa`; the audit output did not provide severity scores. The upstream lock has not been changed, and that environment has not been installed or executed.
- A separate alternative review is underway. SearchClaw appears to support OpenAI through LiteLLM and has SSRF checks, but has no committed dependency lock in the inspected branch; redirect revalidation and optional tools/memory/skills need hardening and its dependencies need lock+audit before installation. It is only a candidate, not an approved safe baseline.
- No external reference system has been installed or executed. No fork has been created.
- Comparison A's real installation/API probe still requires a local `.env` with a valid `RAVE_API_KEY`; no credentials were read or logged and no paid API call was made.

## Before benchmark preparation can be considered complete

1. Pass GitHub Actions for the pre-call reservation branch.
2. Run the local Comparison A tests and offline smoke checks; then, when the user configures credentials locally, run one small real installation probe. This is not benchmark data.
3. Choose and harden an external B reference only after a pinned commit, dependency lock, audit, static security review, and tests pass.
4. Complete the adapter/metadata validation and document model/search differences.
5. Ask the user before beginning the formal benchmark protocol (question set, repetitions, rubric and statistical plan). No official questions or benchmark have been created.
