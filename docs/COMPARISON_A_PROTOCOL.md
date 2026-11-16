# Comparison A — controlled solo researcher

## Question

Can RAVE's collective architecture produce better research results than one agent when models, tools, scope, and experimental limits are controlled? The baseline is one researcher, one decision loop and one run memory. It has no supervisor, subagents, MessageBus, peer communication or delegated research instances. The historical 2026-11-11 RAVE report preserves the question but not a literal scope string; using the shared CLI default is a provisional pilot setting, not proof of exact historical scope equality.

## Reference mapping

Use `gpt-4.1-mini` for analysis and `gpt-5-search-api` for hosted web search through OpenAI Chat Completions, matching the frozen RAVE configuration. Preserve provider-returned citations separately from model-reported URLs. Search-call count, prompt differences and the single-agent versus multi-agent architecture remain explicit methodological variables.

The HTTP client follows the frozen RAVE retry policy: at most three attempts; retry only provider-classified HTTP 429 rate limits; honor `Retry-After` and token-reset headers up to 420 seconds, otherwise use 1s then 2s; do not retry quota errors, server errors or timeouts. Every attempt reserves budget before the network call and is recorded.

## Pilot limits

The initial live integration pilot is limited to one run with:
- 80,000 total reserved/observed tokens
- 3 search attempts, including retries
- 12 total model-call attempts, including retries and JSON repair
- 180 seconds wall time
- USD 0.50 estimated cost ceiling

All limits are mandatory CLI inputs. The run must fail closed before a request when a reservation would exceed a limit. Failed attempts retain reservations conservatively. The search reservation includes the configured 16,384-token allowance for provider-supplied search context, plus local prompt bytes and max completion tokens. Since provider-side context size is variable, this local estimate is not a strict provider-side token or billing cap. An OpenAI project spend limit is an additional required safeguard.

## Pricing

GPT-4.1-mini rates and the Web Search call fee are based on the official OpenAI pricing page. The pricing page does not expose a distinct GPT-5 Search API token-rate row. The local program therefore requires explicit `RAVE_SEARCH_INPUT_USD_PER_1M` and `RAVE_SEARCH_OUTPUT_USD_PER_1M` values in the ignored local `.env`. Record whether these are directly confirmed rates or an explicitly accepted proxy. Unknown prices block live execution; no third-party estimate is silently substituted.

## Pilot versus benchmark

The first capped live run validates integration, authentication, usage reporting, source extraction, output schema and artifact writing. It is not benchmark data. Formal paired comparisons, a question set, blind evaluation and comparative claims remain gated on the later benchmark protocol. A result is eligible for later evaluation only when status is `COMPLETED`, the exact question/scope and code references are recorded, and all budget fields are present.


## First paired pilot profile (2026-11-16)

The current Notion direction defines three conditions: A — one agent; B — multiple simple agents with basic integration; C — the full RAVE Hive. This first pilot covers A versus C only; condition B is not implemented yet. It therefore cannot isolate the incremental value of peer cooperation from the value of multi-agent decomposition.

The first pilot reuses the already completed Comparison A run `solo-5b3dc0590dfc` and executes only the pinned RAVE Hive candidate. It does not rerun or modify A. Both outputs use the same recorded question and scope, `gpt-4.1-mini` analysis, `gpt-5-search-api` hosted search, and low search context.

- Shared run-wide limits: 80,000 tokens, 3 search attempts, 12 model-call attempts, 180 seconds and USD 0.50 estimated cost for the new RAVE run.
- Hosted-search input reservation: 16,384 tokens; hosted-search output cap: 512 tokens.
- Current Comparison A code uses an 8,192-token analysis cap, but the preserved historical A artifact does not record its exact source commit or resolved cap.
- The pinned RAVE candidate uses a 4,096-token cap for each specialist analysis/refinement and an 8,192-token cap for final synthesis. Each agent is limited to 3 findings, 3 evidence items per finding, a 120-word summary and 250-character evidence excerpts.
- RAVE runs in `shared_research` mode: one shared search, three specialist agents, peer refinement and final synthesis. The internal call/output allocation therefore differs from the solo system; the global run-wide ceiling is shared.
- The preserved A run already incurred approximately USD 0.06093635. The new RAVE run has a local estimated ceiling of USD 0.50, giving an estimated maximum total of approximately USD 0.56093635 for this pair. This is not a provider-enforced billing cap; retain an independent OpenAI project spend limit.
- GPT-5 Search API token rates (USD 1.25 input / USD 10.00 output per million tokens) remain user-configured estimates and must be verified against the applicable billing record.

The runner performs a non-billable `GET /models` authentication preflight before any paid RAVE request. It randomizes response order, normalizes both outputs to the same schema, preserves source provenance and stores the system key separately. A pair is eligible only if the RAVE artifact reports `execution_status=COMPLETED`, the final answer is non-empty, and the budget snapshot is present.

This is a one-question A-versus-C pilot, not the ten-question benchmark or the full A/B/C design. The independent reference checklist is retrospective relative to the already observed A output and must be labeled exploratory. The historical A artifact does not record its exact source commit or resolved output cap, RAVE uses a different internal per-call allocation, and no blind independent quality scoring has been performed yet. Results are preliminary and cannot establish general superiority. See [EVALUATION_RUBRIC.md](EVALUATION_RUBRIC.md) for the fixed scoring criteria.
