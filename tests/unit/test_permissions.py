"""Tests for permissions module."""

from mcp_cli.core.permissions import (
    AuthorizationEngine,
    AuthorizationContext,
    AuthorizationDecision,
    ServerTrustLevel,
    ToolRiskLevel,
    TOOL_RISK_MAP,
    SERVER_TRUST_MAP,
)


def test_tool_risk_map_contains_common_tools():
    """Test that common tools are classified."""
    assert TOOL_RISK_MAP["filesystem_read"] == ToolRiskLevel.LOW
    assert TOOL_RISK_MAP["filesystem_delete"] == ToolRiskLevel.HIGH
    assert TOOL_RISK_MAP["docker_destroy"] == ToolRiskLevel.CRITICAL
    assert TOOL_RISK_MAP["shell_exec"] == ToolRiskLevel.CRITICAL


def test_server_trust_map_contains_common_servers():
    """Test that common servers have trust levels."""
    assert SERVER_TRUST_MAP["github"] == ServerTrustLevel.HIGH
    assert SERVER_TRUST_MAP["docker"] == ServerTrustLevel.HIGH


def test_engine_default_trust():
    """Test that unknown servers get LOW trust by default."""
    engine = AuthorizationEngine()
    trust = engine.get_server_trust("unknown-server")
    assert trust == ServerTrustLevel.LOW


def test_engine_default_risk():
    """Test that unknown tools get MEDIUM risk by default."""
    engine = AuthorizationEngine()
    risk = engine.get_tool_risk("unknown_tool")
    assert risk == ToolRiskLevel.MEDIUM


def test_engine_high_trust_low_risk_allows():
    """Test that high trust + low risk = ALLOW."""
    engine = AuthorizationEngine()
    context = AuthorizationContext(agent_id="test", profile="full-stack")
    result = engine.evaluate(context, "github", "filesystem_read")
    assert result.decision == AuthorizationDecision.ALLOW


def test_engine_critical_tool_denies():
    """Test that critical risk tools get DENY even for high-trust servers."""
    engine = AuthorizationEngine()
    context = AuthorizationContext(agent_id="test", profile="full-stack")
    result = engine.evaluate(context, "docker", "docker_destroy")
    assert result.decision == AuthorizationDecision.DENY


def test_engine_tool_risk_classification():
    """Test tool risk classification returns correct level."""
    engine = AuthorizationEngine()
    assert engine.get_tool_risk("filesystem_read") == ToolRiskLevel.LOW
    assert engine.get_tool_risk("docker_rm") == ToolRiskLevel.HIGH
