# Comparison A — controlled solo researcher

## Question

Can RAVE's collective architecture produce better research results than one agent when models, tools, scope, and experimental limits are controlled? This baseline is one researcher with one sequential decision loop and one run memory. It has no supervisor, subagents, MessageBus, peer communication or delegated research instances.

## Reference mapping

Use `gpt-4.1-mini` for analysis and, when technically compatible, `gpt-5-search-api` via OpenAI Chat Completions web search as observed in frozen RAVE. The RAVE search component returns provider annotations; this implementation preserves those citations distinctly from model-written URLs. Search call count and any differences in prompting/search context remain explicit confounds. No alternate provider may be silently substituted.

The shared HTTP client follows the frozen RAVE retry policy: at most three attempts; retries only provider-classified HTTP 429 rate limits; honors `Retry-After` and token-reset headers up to 420 seconds, otherwise uses 1s then 2s; no retries for quota errors, server errors, or timeouts. Each attempt reserves budget and is logged. This policy was checked against the frozen RAVE implementation at the pinned commit.

## Loop

The solo agent plans a query, performs one bounded search, analyzes results and gaps, and may repeat sequentially while budget remains. It synthesizes only after the loop ends, validates structured output and source URLs, and marks exhausted/incomplete runs `PARTIAL`, never `COMPLETED`. Web page contents are not fetched by default: the frozen RAVE search tool exposes provider annotations and summarized result content. The safe page reader is an independently controlled capability for compatible providers and must not be represented as RAVE-equivalent without protocol changes.

## Budgets

No numeric limits are selected in this preparation stage. Every model/search attempt, including retry, must reserve budget before the network call. Enforce max total tokens, searches, wall-clock time, and cost only when a known price schedule is configured. Record unknown cost as null, not zero. A budget stop is explicit and preserves earlier valid results.

## Completion criteria

Unit tests use mocked clients only. A real integration probe requires configured credentials and explicit invocation; it is installation validation, not benchmark data. The official question set and quality rubric belong to a later protocol stage.
