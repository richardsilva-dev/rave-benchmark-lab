# Comparison A — controlled solo researcher

## Question

Can RAVE's collective architecture produce better research results than one agent when models, tools, scope, and experimental limits are controlled? This baseline is one researcher with one sequential decision loop and one run memory. It has no supervisor, subagents, MessageBus, peer communication or delegated research instances.

## Reference mapping

Use `gpt-4.1-mini` for analysis and `gpt-5-search-api` via OpenAI Chat Completions web search as observed in frozen RAVE. The RAVE search component returns provider annotations; this implementation preserves those citations distinctly from model-written URLs. Search call count and any differences in prompting/search context remain explicit confounds. No alternate provider may be silently substituted.

The shared HTTP client follows the frozen RAVE retry policy: at most three attempts; retries only provider-classified HTTP 429 rate limits; honors `Retry-After` and token-reset headers up to 420 seconds, otherwise uses 1s then 2s; no retries for quota errors, server errors, or timeouts. Each network attempt reserves budget and is logged. The solo telemetry records attempts as individual rows; frozen RAVE aggregates retries into a call record with `request_attempts`. Compare normalized attempt totals, not raw telemetry-row counts.

## Loop

The solo agent plans a query, performs one bounded search, analyzes results and gaps, and may repeat sequentially while budget remains. It synthesizes only after the loop ends, validates structured output and source URLs, and marks exhausted/incomplete runs `PARTIAL`, never `COMPLETED`. Web page contents are not fetched by default: the frozen RAVE search tool exposes provider annotations and summarized result content. The safe page reader is an independently controlled capability for compatible providers and must not be represented as RAVE-equivalent without protocol changes.

## Budgets

Live CLI execution requires explicit maximum total tokens, search attempts, wall-clock seconds and model-call attempts. Every network attempt, including retries, reserves a model-call slot and (for search) a search slot before sending.

Before each API request, the client reserves an input estimate based on the serialized UTF-8 request byte length plus `RAVE_INPUT_SAFETY_MARGIN_TOKENS`, and reserves the full request-level `max_completion_tokens` output cap. The search and analysis output caps are explicit configuration values. On success, the reservation is reconciled with provider-reported usage. Rejected HTTP 4xx responses release it. If the request outcome or usage is unknown (for example timeout, transport error, server error or missing usage), the full reservation is conservatively charged as unknown usage and cannot be reused.

This is a conservative **pre-call guard**, not an exact token hard cap. Request bytes are not a model tokenizer, and hosted web-search infrastructure can add provider-side prompt/tool overhead that the client cannot inspect. Provider-reported usage is checked after the call; any overrun stops the run and makes it incomplete. Metadata records input/output usage separately from unknown reservation charges and declares that the budget is not provider-exact.

A USD cost cap is disabled until a dated price schedule and estimator are implemented. Programmatic attempts to set a cost limit without an estimator fail closed with `cost_estimation_unavailable`; unknown cost remains null, not zero.

A budget stop is explicit and preserves earlier valid results. A single in-flight provider response may exceed the estimated reservation if hidden provider-side overhead is larger than the safety margin; record this as a limitation rather than claiming mathematical enforcement.

## Completion criteria

Unit tests use mocked clients only. A real integration probe requires configured credentials and explicit invocation; it is installation validation, not benchmark data. The official question set and quality rubric belong to a later protocol stage.
