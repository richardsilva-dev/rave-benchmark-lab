# Model and tool mapping

| System | Analysis | Search | Evidence handling | Current caveat |
|---|---|---|---|---|
| Frozen RAVE | `gpt-4.1-mini` | `gpt-5-search-api` with OpenAI Chat Completions web search | Provider annotations stored separately from model-reported references | RAVE modes make different numbers of searches; prior work has no globally equal budget |
| Comparison A | Defaults to same model IDs | Defaults to same OpenAI hosted search mechanism | Provider annotations retained as provider-returned; model URLs separately flagged | Repeated sequential search interaction differs from RAVE's one-shot shared research; exact equivalence is not claimed |
| Open Deep Research | `research_model`, `summarization_model`, `compression_model`, `final_report_model` set to `openai:gpt-4.1-mini` | `search_api="openai"` selects OpenAI `web_search_preview` | Adapter preserves original result/source fields | Native web search tool differs from RAVE's `gpt-5-search-api` Chat Completions call; material confound |

The RAVE repo's `.env.example` uses endpoint `https://api.openai.com/v1`, analysis `gpt-4.1-mini`, search `gpt-5-search-api`, context `low`, output cap 512, and timeout 90 seconds. A real experiment must capture the resolved configuration and the exact Python/runtime versions. No API keys belong in manifests.

At the pinned Open Deep Research commit, `Configuration` exposes `allow_clarification`, `search_api`, the model fields above, and optional `mcp_config`/`mcp_prompt`. The example disables clarification and sets MCP fields to null. Its default search provider is Tavily, so `search_api="openai"` must be explicit. Its research workflow is internally multi-agent and concurrent; preserve this as an inherent system difference. No model token caps or budgets are changed here.
