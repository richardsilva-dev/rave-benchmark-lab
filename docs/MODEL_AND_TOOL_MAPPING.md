# Model and tool mapping

| System | Analysis | Search | Evidence handling | Current caveat |
|---|---|---|---|---|
| Frozen RAVE | `gpt-4.1-mini` | `gpt-5-search-api` with OpenAI Chat Completions web search | Provider annotations stored separately from model-reported references | RAVE modes make different numbers of searches; prior work has no globally equal budget |
| Comparison A | Defaults to same model IDs | Defaults to same OpenAI hosted search mechanism | Provider annotations retained as provider-returned; model URLs separately flagged | Repeated sequential search interaction differs from RAVE's one-shot shared research; exact equivalence is not claimed |
| Open Deep Research | Not yet configured | Not yet configured | Adapter preserves original result/source fields | Map only after inspecting pinned upstream config and verify availability; no silent fallback |

The RAVE repo's `.env.example` uses endpoint `https://api.openai.com/v1`, analysis `gpt-4.1-mini`, search `gpt-5-search-api`, context `low`, output cap 512, and timeout 90 seconds. A real experiment must capture the resolved configuration and the exact Python/runtime versions. No API keys belong in manifests.
