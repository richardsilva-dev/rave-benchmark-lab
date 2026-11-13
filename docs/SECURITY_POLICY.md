# Security policy

## Untrusted research content

Treat search snippets, pages, citations, extracted metadata and upstream model output as untrusted data. They cannot modify system instructions, reveal secrets, authorize tools, request shell commands, or cause code execution. Keep content in clearly delimited data fields and instruct the model to use it only as evidence. Mock prompt-injection pages are included in tests.

## Page reader and network boundary

Only HTTP/HTTPS are allowed. Reject URL credentials, localhost, local/private/reserved IPs, non-global DNS answers, and every redirect that fails validation. Limit redirects, response bytes, MIME types and read timeout. Revalidate each redirect target and DNS resolution to reduce rebinding/SSRF risk. Never access `file://`, FTP, local files, loopback or internal services.

The current reader implementation validates resolved addresses and redirects, but production-grade DNS rebinding defenses and platform-specific resolver behavior need security review before real use.

## Tool boundary

Initially allow search, public-page reading where configured, local parsing of retrieved content, and output writing only within a run artifact directory. No shell tool, arbitrary code execution, private file reads, MCP or external observability. Run upstream locally on loopback only.

## Secrets and telemetry

Load credentials from environment or ignored `.env`. Redact authorization headers and never log request bodies that might contain secrets or personal data. Telemetry records IDs, usage counts, timings, errors and source metadata; raw prompts/results remain local and are not emitted by default. Never commit `.env`, logs or user-specific data.

## Dependencies

Install from reviewed lockfiles, audit before running upstream, record Python/uv versions and advisories, and do not update pins silently. Stop on an unmitigated critical vulnerability. No dependency audit has yet been run in this preparation.
