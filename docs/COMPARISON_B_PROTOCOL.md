# Comparison B — Open Deep Research

Use the upstream LangChain project as an external reference and preserve its internal architecture. Upstream: https://github.com/langchain-ai/open_deep_research. Pinned reference identified for this preparation: `1b7d2e80db9faa586165c60e09096dbbfd483a64` (main commit observed 2026-11-13). The actual git submodule checkout and license audit remain pending; the SHA is not evidence that a submodule has been installed.

Keep a separate Python project and virtual environment. Do not install its dependencies in Comparison A or RAVE. Keep the server on `127.0.0.1`; disable remote tracing, MCP, public tunnels, and unneeded tools. Disable interactive clarification for automated runs only through documented upstream configuration. Do not patch upstream behavior silently. Model/search mapping, constraints, license, dependency audit and smoke test must be recorded in implementation status before the environment is called prepared.

The current upstream commit and its licensed files require review at checkout time. This stage does not run the project or official questions.
