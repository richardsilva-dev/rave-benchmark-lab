# Comparison B — Open Deep Research

Use the upstream LangChain project as an external reference and preserve its internal architecture. Upstream: https://github.com/langchain-ai/open_deep_research. Pinned reference: `1b7d2e80db9faa586165c60e09096dbbfd483a64` (main commit observed 2026-11-13), checked out as a git submodule. The upstream license is MIT and its LICENSE file is preserved in the submodule.

Keep a separate Python project and virtual environment. Do not install its dependencies in Comparison A or RAVE. Keep the server on `127.0.0.1`; disable remote tracing, MCP, public tunnels, and unneeded tools. Disable interactive clarification for automated runs only through documented upstream configuration. Do not patch upstream behavior silently. The pinned `Configuration` supports `allow_clarification=false`, `search_api="openai"`, mapped model fields, and null MCP fields. OpenAI `web_search_preview` differs from RAVE's `gpt-5-search-api`; record this as a confound.

## Dependency security gate

On 2026-11-13, `uv audit --locked` on the pinned upstream lock reported 89 known vulnerability advisories across 242 packages and adverse archived statuses for `langchain-community` and `rsa`. The report includes packages in network/request or server paths, including `aiohttp`, `urllib3`, `certifi`, LangGraph and MCP. The audit output did not provide severity scores. Per this lab's security rule, do not install or execute this dependency set until the findings are assessed and a documented safe resolution is agreed. Do not change the upstream lock or suppress findings in this stage.
