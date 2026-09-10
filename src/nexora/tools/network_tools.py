"""Network diagnostic tools.

These tools perform real, read-only network checks (DNS resolution, TCP
connect, TLS certificate inspection, HTTP requests) when a live target is
reachable. In sandboxed or offline environments, or in demo mode, they
return an explicit `unavailable` result rather than fabricating data.
"""

from __future__ import annotations

import socket
import ssl
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel

from nexora.tools.base import DEFAULT_TIMEOUT_SECONDS, BaseTool


class HostInput(BaseModel):
    host: str
    port: int | None = None


class DnsLookupTool(BaseTool[HostInput, dict]):
    name = "dns_lookup"
    description = "Resolves a hostname to IP addresses. Read-only."

    def run(self, payload: HostInput) -> dict[str, Any]:
        try:
            results = socket.getaddrinfo(payload.host, None)
            addresses = sorted({r[4][0] for r in results})
            return {"unavailable": False, "host": payload.host, "addresses": addresses}
        except socket.gaierror as exc:
            return {
                "unavailable": True,
                "unavailable_reason": f"DNS resolution failed: {exc}",
                "host": payload.host,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "unavailable": True,
                "unavailable_reason": f"DNS lookup could not be completed: {exc}",
                "host": payload.host,
            }


class TcpConnectTool(BaseTool[HostInput, dict]):
    name = "tcp_connect"
    description = "Attempts a TCP connection to host:port to check reachability. Read-only."
    timeout_seconds = 4.0

    def run(self, payload: HostInput) -> dict[str, Any]:
        if not payload.port:
            return {"unavailable": True, "unavailable_reason": "No port specified."}
        try:
            with socket.create_connection((payload.host, payload.port), timeout=self.timeout_seconds):
                return {"unavailable": False, "host": payload.host, "port": payload.port, "reachable": True}
        except (TimeoutError, OSError) as exc:
            return {
                "unavailable": False,
                "host": payload.host,
                "port": payload.port,
                "reachable": False,
                "detail": str(exc),
            }


class TlsCertificateInput(BaseModel):
    host: str
    port: int = 443


class TlsCertificateTool(BaseTool[TlsCertificateInput, dict]):
    name = "tls_certificate_inspection"
    description = "Inspects the TLS certificate presented by a host for expiry and validity. Read-only."
    timeout_seconds = 5.0

    def run(self, payload: TlsCertificateInput) -> dict[str, Any]:
        context = ssl.create_default_context()
        try:
            with socket.create_connection(
                (payload.host, payload.port), timeout=self.timeout_seconds
            ) as sock, context.wrap_socket(sock, server_hostname=payload.host) as tls_sock:
                cert = tls_sock.getpeercert()
            not_after = cert.get("notAfter") if cert else None
            expired = False
            if isinstance(not_after, str):
                expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
                    tzinfo=UTC
                )
                expired = expiry < datetime.now(UTC)
            return {
                "unavailable": False,
                "host": payload.host,
                "not_after": not_after,
                "expired": expired,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "unavailable": True,
                "unavailable_reason": f"Could not inspect certificate: {exc}",
                "host": payload.host,
            }


class HttpRequestInput(BaseModel):
    url: str
    method: str = "GET"


class HttpRequestTool(BaseTool[HttpRequestInput, dict]):
    name = "http_request"
    description = "Performs a read-only HTTP request and reports status code, headers, and timing."
    timeout_seconds = DEFAULT_TIMEOUT_SECONDS

    def run(self, payload: HttpRequestInput) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = client.request(payload.method, payload.url)
            return {
                "unavailable": False,
                "url": payload.url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "elapsed_ms": response.elapsed.total_seconds() * 1000,
            }
        except httpx.TimeoutException:
            return {
                "unavailable": True,
                "unavailable_reason": "HTTP request timed out.",
                "url": payload.url,
            }
        except httpx.HTTPError as exc:
            return {
                "unavailable": True,
                "unavailable_reason": f"HTTP request failed: {exc}",
                "url": payload.url,
            }
