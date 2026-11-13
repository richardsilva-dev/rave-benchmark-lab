"""SSRF-conscious bounded HTTP reader. Not enabled by the equivalent search path."""
from ipaddress import ip_address
import socket
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, build_opener, Request


def _validate(url: str):
    p = urlsplit(url)
    if p.scheme not in {"http", "https"} or not p.hostname or p.username or p.password:
        raise ValueError("Only credential-free HTTP(S) URLs are permitted")
    host = p.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("Local hostnames are not permitted")
    try:
        resolved = {ip_address(host)}
    except ValueError:
        try:
            resolved = {ip_address(row[4][0]) for row in socket.getaddrinfo(host, p.port or (443 if p.scheme == "https" else 80), type=socket.SOCK_STREAM)}
        except OSError as exc:
            raise ValueError("Hostname could not be resolved") from exc
    if not resolved or any(not addr.is_global for addr in resolved):
        raise ValueError("Local, private, reserved, and mixed DNS targets are not permitted")
    return url


class _SafeRedirect(HTTPRedirectHandler):
    def __init__(self, limit):
        super().__init__(); self.limit = limit; self.count = 0
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count += 1
        if self.count > self.limit: raise ValueError("Redirect limit exceeded")
        _validate(urljoin(req.full_url, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def read_page(url: str, timeout: float = 10, max_bytes: int = 1_000_000, max_redirects: int = 3) -> dict:
    original = _validate(url)
    redirect = _SafeRedirect(max_redirects)
    opener = build_opener(redirect)
    req = Request(original, headers={"User-Agent": "RAVE-Benchmark-Lab/0.1"})
    with opener.open(req, timeout=timeout) as response:
        final_url = _validate(response.geturl())
        if response.headers.get_content_type() not in {"text/html", "text/plain", "application/xhtml+xml"}:
            raise ValueError("Unsupported page content type")
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes: raise ValueError("Page exceeds size limit")
        return {"original_url": original, "final_url": final_url,
                "content_type": response.headers.get_content_type(),
                "text": body.decode(response.headers.get_content_charset() or "utf-8", errors="replace")}
