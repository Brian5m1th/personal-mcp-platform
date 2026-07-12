"""
Authorization engine — multi-dimensional permission evaluation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger


class AuthorizationDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    PENDING_APPROVAL = "pending_approval"


class ToolRiskLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServerTrustLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNTRUSTED = "untrusted"


TOOL_RISK_MAP: dict[str, ToolRiskLevel] = {
    # Read operations
    "filesystem_read": ToolRiskLevel.LOW,
    "filesystem_search": ToolRiskLevel.NONE,
    "github_list_issues": ToolRiskLevel.LOW,
    "postgres_query": ToolRiskLevel.LOW,
    "docker_list_containers": ToolRiskLevel.LOW,
    # Write operations
    "filesystem_write": ToolRiskLevel.MEDIUM,
    "filesystem_edit": ToolRiskLevel.MEDIUM,
    "github_create_pr": ToolRiskLevel.MEDIUM,
    "postgres_execute": ToolRiskLevel.MEDIUM,
    # Destructive operations
    "filesystem_delete": ToolRiskLevel.HIGH,
    "docker_stop": ToolRiskLevel.MEDIUM,
    "docker_rm": ToolRiskLevel.HIGH,
    "postgres_drop_table": ToolRiskLevel.CRITICAL,
    # Critical
    "docker_destroy": ToolRiskLevel.CRITICAL,
    "docker_destroy_all": ToolRiskLevel.CRITICAL,
    "shell_exec": ToolRiskLevel.CRITICAL,
}


SERVER_TRUST_MAP: dict[str, ServerTrustLevel] = {
    "context7": ServerTrustLevel.HIGH,
    "serena": ServerTrustLevel.MEDIUM,
    "github": ServerTrustLevel.HIGH,
    "playwright": ServerTrustLevel.HIGH,
    "filesystem": ServerTrustLevel.HIGH,
    "sequential-thinking": ServerTrustLevel.HIGH,
    "postgres": ServerTrustLevel.HIGH,
    "docker": ServerTrustLevel.HIGH,
    "fetch": ServerTrustLevel.HIGH,
    "memory": ServerTrustLevel.HIGH,
    "qdrant": ServerTrustLevel.MEDIUM,
    "obsidian": ServerTrustLevel.MEDIUM,
    "n8n": ServerTrustLevel.MEDIUM,
    "cloudflare": ServerTrustLevel.MEDIUM,
}


@dataclass
class AuthorizationContext:
    agent_id: str
    user_id: str = "default"
    workspace: str = "."
    profile: str = "full-stack"


@dataclass
class AuthorizationResult:
    decision: AuthorizationDecision
    reason: str = ""
    context: AuthorizationContext | None = None
    server_id: str = ""
    tool_name: str = ""
    tool_args: dict = field(default_factory=dict)
    evaluated_at: float = 0.0


class AuthorizationEngine:
    """Multi-dimensional permission evaluation engine."""

    def __init__(self):
        self._tool_risk_overrides: dict[str, ToolRiskLevel] = {}
        self._server_trust_overrides: dict[str, ServerTrustLevel] = {}
        self._approval_rules: list[dict] = []

    def evaluate(
        self,
        context: AuthorizationContext,
        server_id: str,
        tool_name: str,
        tool_args: dict | None = None,
    ) -> AuthorizationResult:
        """Evaluate whether a tool call should be allowed."""
        from mcp_cli.core.config import PlatformConfig
        import time

        cfg = PlatformConfig()
        profile = cfg.active_profile.get("active_profiles", ["full-stack"])[0]

        # 1. Determine server trust level
        trust = self._server_trust_overrides.get(
            server_id, SERVER_TRUST_MAP.get(server_id, ServerTrustLevel.LOW)
        )

        # 2. Determine tool risk level
        risk = self._tool_risk_overrides.get(
            tool_name, TOOL_RISK_MAP.get(tool_name, ToolRiskLevel.MEDIUM)
        )

        # 3. Check if server is enabled in the current profile
        enabled_servers = cfg.get_enabled_servers()
        enabled_ids = [s.get("id") for s in enabled_servers]
        if server_id not in enabled_ids:
            return AuthorizationResult(
                decision=AuthorizationDecision.DENY,
                reason=f"Server '{server_id}' not enabled in profile '{profile}'",
                server_id=server_id,
                tool_name=tool_name,
                context=context,
                evaluated_at=time.time(),
            )

        # 4. Apply permission matrix
        if trust == ServerTrustLevel.HIGH:
            if risk in (ToolRiskLevel.NONE, ToolRiskLevel.LOW):
                return AuthorizationResult(
                    decision=AuthorizationDecision.ALLOW,
                    reason=f"High trust + {risk.value} risk = ALLOW",
                    server_id=server_id,
                    tool_name=tool_name,
                    context=context,
                    evaluated_at=time.time(),
                )
            elif risk == ToolRiskLevel.MEDIUM:
                return AuthorizationResult(
                    decision=AuthorizationDecision.ALLOW,
                    reason=f"High trust + medium risk = ALLOW",
                    server_id=server_id,
                    tool_name=tool_name,
                    context=context,
                    evaluated_at=time.time(),
                )
            elif risk == ToolRiskLevel.HIGH:
                return AuthorizationResult(
                    decision=AuthorizationDecision.PENDING_APPROVAL,
                    reason=f"High trust + high risk = REQUIRES APPROVAL",
                    server_id=server_id,
                    tool_name=tool_name,
                    context=context,
                    evaluated_at=time.time(),
                )
            else:  # CRITICAL
                return AuthorizationResult(
                    decision=AuthorizationDecision.DENY,
                    reason=f"High trust + critical risk = DENY (override in config)",
                    server_id=server_id,
                    tool_name=tool_name,
                    context=context,
                    evaluated_at=time.time(),
                )

        elif trust == ServerTrustLevel.MEDIUM:
            if risk in (ToolRiskLevel.NONE, ToolRiskLevel.LOW):
                return AuthorizationResult(
                    decision=AuthorizationDecision.ALLOW,
                    reason=f"Medium trust + {risk.value} risk = ALLOW",
                    server_id=server_id,
                    tool_name=tool_name,
                    context=context,
                    evaluated_at=time.time(),
                )
            elif risk == ToolRiskLevel.MEDIUM:
                return AuthorizationResult(
                    decision=AuthorizationDecision.PENDING_APPROVAL,
                    reason=f"Medium trust + medium risk = REQUIRES APPROVAL",
                    server_id=server_id,
                    tool_name=tool_name,
                    context=context,
                    evaluated_at=time.time(),
                )
            else:
                return AuthorizationResult(
                    decision=AuthorizationDecision.DENY,
                    reason=f"Medium trust + {risk.value} risk = DENY",
                    server_id=server_id,
                    tool_name=tool_name,
                    context=context,
                    evaluated_at=time.time(),
                )

        else:  # LOW or UNTRUSTED
            return AuthorizationResult(
                decision=AuthorizationDecision.DENY,
                reason=f"Low trust server '{server_id}' = DENY (all tools)",
                server_id=server_id,
                tool_name=tool_name,
                context=context,
                evaluated_at=time.time(),
            )

    def get_tool_risk(self, tool_name: str) -> ToolRiskLevel:
        """Classify a tool's risk level based on its name."""
        return self._tool_risk_overrides.get(
            tool_name, TOOL_RISK_MAP.get(tool_name, ToolRiskLevel.MEDIUM)
        )

    def get_server_trust(self, server_id: str) -> ServerTrustLevel:
        """Get the trust level for a server."""
        return self._server_trust_overrides.get(
            server_id, SERVER_TRUST_MAP.get(server_id, ServerTrustLevel.LOW)
        )
