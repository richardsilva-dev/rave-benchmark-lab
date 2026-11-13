# Comparison A — controlled solo researcher

## Question

Can RAVE's collective architecture produce better research results than one agent when models, tools, scope, and experimental limits are controlled? The baseline is one researcher, one decision loop and one run memory. It has no supervisor, subagents, MessageBus, peer communication or delegated research instances.

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
