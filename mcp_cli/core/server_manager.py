"""
Server lifecycle manager — state machine, process management, health tracking.
"""

import asyncio
import time
from enum import Enum
from typing import Callable

from loguru import logger

from mcp_cli.core.config import PlatformConfig, get_server_config_path, save_yaml, load_yaml
from mcp_cli.core.transport import MCPTransport, TransportFactory


class ServerState(str, Enum):
    REGISTERED = "registered"
    INSTALLING = "installing"
    INSTALLED = "installed"
    STARTING = "starting"
    RUNNING = "running"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    UNINSTALLED = "uninstalled"
    FAILED = "failed"


STATE_TRANSITIONS: dict[ServerState, list[ServerState]] = {
    ServerState.REGISTERED: [ServerState.INSTALLING, ServerState.UNINSTALLED],
    ServerState.INSTALLING: [ServerState.INSTALLED, ServerState.FAILED],
    ServerState.INSTALLED: [ServerState.STARTING, ServerState.UNINSTALLED],
    ServerState.STARTING: [ServerState.RUNNING, ServerState.FAILED],
    ServerState.RUNNING: [ServerState.HEALTHY, ServerState.DEGRADED, ServerState.STOPPING, ServerState.FAILED],
    ServerState.HEALTHY: [ServerState.DEGRADED, ServerState.STOPPING, ServerState.FAILED],
    ServerState.DEGRADED: [ServerState.HEALTHY, ServerState.STOPPING, ServerState.FAILED],
    ServerState.STOPPING: [ServerState.STOPPED, ServerState.FAILED],
    ServerState.STOPPED: [ServerState.STARTING, ServerState.UNINSTALLED],
    ServerState.UNINSTALLED: [ServerState.REGISTERED],
    ServerState.FAILED: [ServerState.STOPPED, ServerState.REGISTERED],
}


class LifecycleError(Exception):
    """Raised when a lifecycle transition fails."""
    pass


class ManagedServer:
    """Represents a single MCP server under platform management."""

    def __init__(self, server_id: str, registry_entry: dict):
        self.id = server_id
        self.registry_entry = registry_entry
        self.state: ServerState = ServerState.REGISTERED
        self.transport: MCPTransport | None = None
        self._tools_cache: list[dict] = []
        self._start_attempts: int = 0
        self._max_restarts: int = 3
        self._last_health: dict = {"status": "unknown", "latency_ms": 0, "error": None}
        self._on_state_change: list[Callable] = []

    def on_state_change(self, callback: Callable) -> None:
        self._on_state_change.append(callback)

    def _transition(self, new_state: ServerState) -> None:
        if new_state not in STATE_TRANSITIONS.get(self.state, []):
            raise LifecycleError(
                f"Cannot transition from {self.state.value} to {new_state.value}"
            )
        old_state = self.state
        self.state = new_state
        logger.info(f"[{self.id}] {old_state.value} → {new_state.value}")
        for cb in self._on_state_change:
            cb(self.id, old_state, new_state)

    async def initialize(self) -> bool:
        """Start the server and perform MCP handshake."""
        self._transition(ServerState.STARTING)
        self._start_attempts += 1

        try:
            # Create transport from registry entry
            transport_config = self.registry_entry.get("protocol", {}).get(
                "transports", [{}]
            )[0]
            self.transport = TransportFactory.create(transport_config)
            await self.transport.connect()

            # MCP initialize handshake
            init_result = await self.transport.send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-platform", "version": "0.1.0"},
            })

            # Send initialized notification
            await self.transport.send_notification("notifications/initialized", {})

            # Cache tools list
            tools_result = await self.transport.send_request("tools/list", {})
            self._tools_cache = tools_result.get("tools", [])

            self._transition(ServerState.RUNNING)
            self._last_health = {"status": "healthy", "latency_ms": 0, "error": None}

            # Quick health check
            health = await self.transport.health_check()
            if health.get("status") == "healthy":
                self._transition(ServerState.HEALTHY)
            else:
                self._transition(ServerState.DEGRADED)

            logger.info(f"[{self.id}] Initialized with {len(self._tools_cache)} tools")
            return True

        except Exception as e:
            logger.error(f"[{self.id}] Initialization failed: {e}")
            self._transition(ServerState.FAILED)
            self._last_health = {"status": "error", "latency_ms": 0, "error": str(e)}
            return False

    async def shutdown(self) -> bool:
        """Gracefully shut down the server."""
        self._transition(ServerState.STOPPING)
        try:
            if self.transport:
                await self.transport.disconnect()
            self._transition(ServerState.STOPPED)
            return True
        except Exception as e:
            logger.warning(f"[{self.id}] Shutdown error: {e}")
            self._transition(ServerState.FAILED)
            return False

    async def health_check(self) -> dict:
        """Run a health check and update internal state."""
        if self.transport is None:
            self._last_health = {"status": "stopped", "latency_ms": 0, "error": "Not started"}
            return self._last_health

        health = await self.transport.health_check()
        self._last_health = health

        if health.get("status") == "healthy":
            if self.state in (ServerState.DEGRADED, ServerState.RUNNING):
                self._transition(ServerState.HEALTHY)
        elif health.get("status") == "down":
            if self.state != ServerState.FAILED:
                self._transition(ServerState.FAILED)
                if self._start_attempts < self._max_restarts:
                    logger.info(f"[{self.id}] Attempting restart ({self._start_attempts}/{self._max_restarts})")
                    await self.initialize()
        else:
            if self.state == ServerState.HEALTHY:
                self._transition(ServerState.DEGRADED)

        return health

    def get_tools(self) -> list[dict]:
        return self._tools_cache

    def get_status(self) -> dict:
        return {
            "id": self.id,
            "state": self.state.value,
            "tools_count": len(self._tools_cache),
            "health": self._last_health,
            "start_attempts": self._start_attempts,
        }


class ServerManager:
    """Central manager for all MCP server processes."""

    def __init__(self):
        self.config = PlatformConfig()
        self._servers: dict[str, ManagedServer] = {}

    async def start_all(self) -> int:
        """Start all enabled servers. Returns count of successful starts."""
        enabled = self.config.get_enabled_servers()
        started = 0
        for entry in enabled:
            sid = entry.get("id", "unknown")
            if sid in self._servers:
                logger.warning(f"[{sid}] Already managed")
                continue
            server = ManagedServer(sid, entry)
            if await server.initialize():
                self._servers[sid] = server
                started += 1
            else:
                logger.error(f"[{sid}] Failed to start")
        return started

    async def start_one(self, server_id: str) -> bool:
        """Start a single server by ID."""
        entry = self.config.get_server(server_id)
        if entry is None:
            logger.error(f"[{server_id}] Not found in registry")
            return False
        if server_id in self._servers:
            logger.warning(f"[{server_id}] Already running")
            return True
        server = ManagedServer(server_id, entry)
        if await server.initialize():
            self._servers[server_id] = server
            return True
        return False

    async def stop_all(self) -> int:
        """Stop all running servers."""
        stopped = 0
        for sid, server in list(self._servers.items()):
            if await server.shutdown():
                stopped += 1
            del self._servers[sid]
        return stopped

    async def stop_one(self, server_id: str) -> bool:
        """Stop a single server."""
        server = self._servers.get(server_id)
        if server is None:
            return False
        result = await server.shutdown()
        if server_id in self._servers:
            del self._servers[server_id]
        return result

    async def restart_one(self, server_id: str) -> bool:
        """Restart a single server."""
        await self.stop_one(server_id)
        return await self.start_one(server_id)

    async def health_check_all(self) -> list[dict]:
        """Run health checks on all managed servers."""
        results = []
        for sid, server in list(self._servers.items()):
            health = await server.health_check()
            results.append({"id": sid, **health})
        return results

    def get_status_all(self) -> list[dict]:
        """Get status for all managed servers."""
        return [s.get_status() for s in self._servers.values()]

    def get_server(self, server_id: str) -> ManagedServer | None:
        return self._servers.get(server_id)

    async def emergency_stop(self) -> None:
        """Immediately stop all servers (force kill)."""
        for sid, server in list(self._servers.items()):
            logger.warning(f"[emergency] Stopping {sid}")
            await server.shutdown()
            del self._servers[sid]
        logger.info("[emergency] All servers stopped")
