# Dependency audit — 2026-11-13

Auditor: `uv 0.13.5`; Windows x86_64. Open Deep Research specifies Python 3.11 in `langgraph.json`.

## Comparison A

- `uv audit --locked`: 7 resolved packages, 6 audited non-project packages.
- Result: no known vulnerabilities and no adverse project statuses.
- Installed separately in `comparison_a/.venv` using `uv sync --locked --extra dev`.
- `uv run --locked --extra dev pytest -p no:cacheprovider -q`: 21 passed.

## Comparison B: pinned Open Deep Research

- Upstream commit: `1b7d2e80db9faa586165c60e09096dbbfd483a64`; upstream version `0.0.16`.
- The original upstream `uv.lock` remains unmodified.
- `uv audit --locked`: 89 known vulnerability advisories across 242 packages, plus adverse archived statuses for `langchain-community` and `rsa`. The audit output supplied no severity scores. Examples (locked and fixed versions reported by the audit):

| Package | Locked | Advisories | Fix indicated by audit |
|---|---:|---:|---:|
| aiohttp | 3.14.3 | 8 | 3.14.4 |
| anyio | 4.9.0 | 4 | 4.14.2 |
| certifi | 2025.4.26 | 2 | 2026.10.18 |
| langgraph | 1.2.9 | 1 | 1.2.14 |
| langgraph-api | 0.10.0 | 1 | 0.15.0 |
| langgraph-sdk | 0.4.2 | 3 | 0.4.4 / 0.4.6 (advisory-specific) |
| mcp | 1.28.1 | 4 | 1.30.0 or 2.2.0 (advisory-specific) |
| tornado | 6.5.7 | 10 | 6.5.8 / 6.5.9 / 6.6 (advisory-specific) |
| urllib3 | 2.7.0 | 6 | 2.8.0 |

Examples include advisories about resource exhaustion, unsafe networking behavior, or server handling. Do not treat this as a complete advisory list or severity ranking.

## Decision

Comparison B was not installed, started, or smoke-tested. Under the supplied security rule, dependency installation and execution stop pending assessment of the findings and a documented safe resolution. The upstream commit and lock remain unchanged. A future decision can retain the frozen reference with documented isolation/mitigation evidence, or select a new version as a separate experiment; do not silently patch or retag the reference.
