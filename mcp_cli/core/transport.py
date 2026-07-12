"""
Transport abstraction layer — STDIO, HTTP/SSE, and WebSocket transports.
"""

import asyncio
import json
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx
from loguru import logger


class TransportError(Exception):
    """Base exception for transport errors."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause


class TransportTimeoutError(TransportError):
    """Raised when a transport operation times out."""
    pass


class TransportConnectionError(TransportError):
    """Raised when a connection cannot be established."""
    pass


# ── Abstract Transport ──────────────────────────────────────────


class MCPTransport(ABC):
    """Abstract transport layer for MCP communication."""

    @abstractmethod
    async def connect(self) -> bool:
        """Establish the transport connection. Returns True if successful."""
        ...

    @abstractmethod
    async def disconnect(self) -> bool:
        """Gracefully close the transport connection."""
        ...

    @abstractmethod
    async def send_request(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC request and wait for the response."""
        ...

    @abstractmethod
    async def send_notification(self, method: str, params: dict) -> None:
        """Send a JSON-RPC notification (fire-and-forget)."""
        ...

    @abstractmethod
    def get_server_info(self) -> dict:
        """Return transport-level server information."""
        ...

    @abstractmethod
    async def health_check(self) -> dict:
        """Check if the transport is healthy."""
        ...


# ── STDIO Transport ────────────────────────────────────────────


class StdioTransport(MCPTransport):
    """STDIO-based transport using subprocess stdin/stdout."""

    def __init__(self, config: dict):
        self._command: str = config.get("command", "")
        self._args: list[str] = config.get("args", [])
        self._env_overrides: dict = config.get("env", {})
        self._process: subprocess.Popen | None = None
        self._connected_at: float | None = None
        self._pending_requests: dict[int, asyncio.Future] = {}

    async def connect(self) -> bool:
        if not self._command:
            raise TransportConnectionError("No command configured")

        resolved = shutil.which(self._command)
        if not resolved:
            raise TransportConnectionError(
                f"Executable '{self._command}' not found in PATH"
            )

        env = dict(subprocess.__dict__) if False else None  # placeholder
        env = None  # Will implement properly

        try:
            self._process = subprocess.Popen(
                [resolved, *self._args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**dict(subprocess.os.environ), **self._env_overrides}
                if self._env_overrides
                else None,
            )
            self._connected_at = time.time()
            logger.info(f"[stdio] Connected to {self._command} (pid={self._process.pid})")
            return True
        except (OSError, subprocess.SubprocessError) as e:
            raise TransportConnectionError(f"Failed to start process: {e}")

    async def disconnect(self) -> bool:
        if self._process is None:
            return True
        try:
            self._process.terminate()
            self._process.wait(timeout=5)
            self._process = None
            self._connected_at = None
            logger.info("[stdio] Disconnected")
            return True
        except Exception as e:
            logger.warning(f"[stdio] Force kill: {e}")
            if self._process:
                self._process.kill()
                self._process = None
            return False

    async def send_request(self, method: str, params: dict) -> dict:
        if not self._process or not self._process.stdin:
            raise TransportConnectionError("Not connected")

        req_id = int(time.time() * 1000)
        req = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}

        try:
            req_str = json.dumps(req) + "\n"
            self._process.stdin.write(req_str.encode("utf-8"))
            self._process.stdin.flush()

            while True:
                line = self._process.stdout.readline()
                if not line:
                    raise TransportConnectionError("Connection closed by server")
                try:
                    resp = json.loads(line.decode("utf-8"))
                    if resp.get("id") == req_id:
                        if "error" in resp:
                            raise TransportError(
                                f"Server error: {resp['error']}"
                            )
                        return resp.get("result", {})
                except json.JSONDecodeError:
                    continue
        except TransportError:
            raise
        except Exception as e:
            raise TransportError(f"STDIO request failed: {e}")

    async def send_notification(self, method: str, params: dict) -> None:
        if not self._process or not self._process.stdin:
            return
        notif = {"jsonrpc": "2.0", "method": method, "params": params}
        try:
            self._process.stdin.write((json.dumps(notif) + "\n").encode("utf-8"))
            self._process.stdin.flush()
        except Exception:
            pass

    def get_server_info(self) -> dict:
        return {
            "type": "stdio",
            "pid": self._process.pid if self._process else None,
            "command": self._command,
            "args": self._args,
            "connected_at": self._connected_at,
        }

    async def health_check(self) -> dict:
        t0 = time.monotonic()
        if self._process is None:
            return {"status": "down", "latency_ms": 0, "error": "Not connected"}
        ret = self._process.poll()
        latency_ms = int((time.monotonic() - t0) * 1000)
        if ret is not None:
            self._process = None
            return {"status": "down", "latency_ms": latency_ms, "error": f"Exited with code {ret}"}
        return {"status": "healthy", "latency_ms": latency_ms, "error": None}


# ── HTTP/SSE Transport ─────────────────────────────────────────


class SSETransport(MCPTransport):
    """HTTP/SSE-based transport for remote MCP servers."""

    def __init__(self, config: dict):
        self._url: str = config.get("url", "")
        self._headers: dict = config.get("headers", {})
        self._client: httpx.AsyncClient | None = None
        self._connected_at: float | None = None
        self._session_id: str | None = None

    async def connect(self) -> bool:
        if not self._url:
            raise TransportConnectionError("No URL configured")
        self._client = httpx.AsyncClient(
            headers=self._headers,
            timeout=30.0,
        )
        self._connected_at = time.time()
        logger.info(f"[sse] Connected to {self._url}")
        return True

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected_at = None
        return True

    async def send_request(self, method: str, params: dict) -> dict:
        if not self._client:
            raise TransportConnectionError("Not connected")
        try:
            resp = await self._client.post(
                self._url,
                json={"jsonrpc": "2.0", "method": method, "params": params},
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise TransportError(f"Server error: {data['error']}")
            return data.get("result", {})
        except httpx.HTTPStatusError as e:
            raise TransportError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        except httpx.TimeoutException:
            raise TransportTimeoutError("Request timed out")
        except Exception as e:
            raise TransportError(f"SSE request failed: {e}")

    async def send_notification(self, method: str, params: dict) -> None:
        # For SSE, notifications are fire-and-forget POST requests
        if self._client:
            try:
                await self._client.post(
                    self._url + "/notification",
                    json={"jsonrpc": "2.0", "method": method, "params": params},
                )
            except Exception:
                pass

    def get_server_info(self) -> dict:
        return {
            "type": "sse",
            "url": self._url,
            "connected_at": self._connected_at,
        }

    async def health_check(self) -> dict:
        t0 = time.monotonic()
        try:
            result = await self.send_request("ping", {})
            latency_ms = int((time.monotonic() - t0) * 1000)
            return {"status": "healthy", "latency_ms": latency_ms, "error": None}
        except Exception as e:
            latency_ms = int((time.monotonic() - t0) * 1000)
            return {"status": "down", "latency_ms": latency_ms, "error": str(e)}


# ── Transport Factory ──────────────────────────────────────────


class TransportFactory:
    """Creates transport instances based on configuration."""

    @staticmethod
    def create(transport_config: dict) -> MCPTransport:
        transport_type = transport_config.get("type", "stdio")
        if transport_type == "stdio":
            return StdioTransport(transport_config)
        elif transport_type == "sse":
            return SSETransport(transport_config)
        elif transport_type == "http":
            # HTTP transport (direct request-response, no SSE)
            return SSETransport(transport_config)
        else:
            raise ValueError(f"Unsupported transport type: {transport_type}")
