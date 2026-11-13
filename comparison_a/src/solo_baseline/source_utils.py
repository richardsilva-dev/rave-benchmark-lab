"""Safe source URL validation and conservative deduplication helpers."""
from urllib.parse import unquote_plus, urlsplit, urlunsplit


_TRACKING_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref_src",
    "igshid",
    "yclid",
}


def canonical_source_url(value: str) -> str | None:
    """Return a stable identity for an HTTP(S) citation URL, or None.

    The original URL is retained in result records. This identity lowercases
    the scheme/host, removes default ports and fragments, and drops known
    tracking parameters. It does not merge www/non-www hosts or rewrite paths.
    """
    if not isinstance(value, str) or not value or len(value) > 4096:
        return None
    if any(ord(char) < 32 or char.isspace() for char in value):
        return None

    try:
        parsed = urlsplit(value)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None

    if scheme not in {"http", "https"} or not hostname:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None

    hostname = hostname.lower().rstrip(".")
    if not hostname:
        return None
    try:
        hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return None

    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    if port is not None and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{hostname}:{port}"
    else:
        netloc = hostname

    path = parsed.path or "/"
    query_parts = []
    if parsed.query:
        for part in parsed.query.split("&"):
            key = part.split("=", 1)[0]
            decoded_key = unquote_plus(key).lower()
            if decoded_key.startswith("utm_") or decoded_key in _TRACKING_KEYS:
                continue
            query_parts.append(part)
    query = "&".join(query_parts)

    return urlunsplit((scheme, netloc, path, query, ""))


def validate_source_record(source: object) -> None:
    """Validate a normalized source dictionary without trusting model fields."""
    if not isinstance(source, dict):
        raise ValueError("Each source must be an object")
    if canonical_source_url(source.get("url")) is None:
        raise ValueError("Each source must contain a valid HTTP(S) URL without credentials")
    title = source.get("title", "")
    if not isinstance(title, str) or len(title) > 1000:
        raise ValueError("Source title must be a string of at most 1000 characters")
    provenance = source.get("provenance", "provider_returned")
    if not isinstance(provenance, str) or provenance not in {"provider_returned", "model_reported"}:
        raise ValueError("Source provenance must be provider_returned or model_reported")
