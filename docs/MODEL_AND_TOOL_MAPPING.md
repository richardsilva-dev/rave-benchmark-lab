# Model and tool mapping

| System | Analysis | Search | Evidence handling | Current caveat |
|---|---|---|---|---|
| Frozen RAVE | `gpt-4.1-mini` | `gpt-5-search-api` with OpenAI Chat Completions web search | Provider annotations stored separately from model-reported references | Frozen historical reference; no run-wide budget guard |
| Comparison A | `gpt-4.1-mini` | `gpt-5-search-api` with low context | Provider annotations retained as provider-returned; model URLs separately flagged | Preserved pilot's exact source commit and resolved output cap were not recorded |
| Open Deep Research | `research_model`, `summarization_model`, `compression_model`, `final_report_model` set to `openai:gpt-4.1-mini` | `search_api="openai"` selects OpenAI `web_search_preview` | Adapter preserves original result/source fields | Native web search tool differs from RAVE's `gpt-5-search-api` Chat Completions call; material confound |

The RAVE repo's `.env.example` uses endpoint `https://api.openai.com/v1`, analysis `gpt-4.1-mini`, search `gpt-5-search-api`, context `low`, output cap 512, and timeout 90 seconds. A real experiment must capture the resolved configuration and the exact Python/runtime versions. No API keys belong in manifests.

At the pinned Open Deep Research commit, `Configuration` exposes `allow_clarification`, `search_api`, the model fields above, and optional `mcp_config`/`mcp_prompt`. The example disables clarification and sets MCP fields to null. Its default search provider is Tavily, so `search_api="openai"` must be explicit. Its research workflow is internally multi-agent and concurrent; preserve this as an inherent system difference. No model token caps or budgets are changed here.


## Current RAVE benchmark candidate

The lab runner pins `project_RAVE` branch `benchmark-a-current-hive-budget-guard` at commit `ee45023a64f637e80095e08c4aab56f97d6cc835`, based on the frozen `independent_research` implementation. It preserves the current three-specialist Hive, peer refinement, provenance and partial-run handling. The first pilot uses `shared_research` mode: one shared hosted search followed by three specialists, peer refinement and final synthesis. It has a run-wide ceiling of 80,000 tokens, 3 search attempts, 12 model-call attempts, 180 seconds and USD 0.50 estimated cost. Specialist analysis/refinement is capped at 4,096 tokens; final synthesis at 8,192; hosted search output at 512. These internal allocations differ from the solo system, so the comparison is preliminary even though the global budget is matched.


## Condições experimentais pendentes

A direção atual no Notion especifica A (agente único), B (múltiplos agentes simples com integração básica) e C (RAVE com cooperação, núcleo híbrido, verificação e integração progressiva). O executor atual cobre A e C. B ainda não existe no código e deve ser implementado antes de declarar concluída a comparação completa. O piloto A/C é útil como verificação inicial, mas não isola o ganho específico de peer refinement.
