"""Tests for transport module."""

import pytest

from mcp_cli.core.transport import (
    TransportError,
    TransportTimeoutError,
    TransportConnectionError,
    TransportFactory,
    StdioTransport,
    SSETransport,
)


def test_transport_factory_stdio():
    """Test TransportFactory creates StdioTransport."""
    transport = TransportFactory.create({"type": "stdio", "command": "echo"})
    assert isinstance(transport, StdioTransport)


def test_transport_factory_sse():
    """Test TransportFactory creates SSETransport."""
    transport = TransportFactory.create({"type": "sse", "url": "http://localhost"})
    assert isinstance(transport, SSETransport)


def test_transport_factory_http():
    """Test TransportFactory creates SSETransport for HTTP type."""
    transport = TransportFactory.create({"type": "http", "url": "http://localhost"})
    assert isinstance(transport, SSETransport)


def test_transport_factory_unknown():
    """Test TransportFactory raises ValueError for unknown type."""
    with pytest.raises(ValueError, match="Unsupported transport type"):
        TransportFactory.create({"type": "unknown"})


def test_transport_error_chain():
    """Test TransportError can wrap a cause."""
    cause = ValueError("original error")
    err = TransportError("wrapped", cause=cause)
    assert err.cause is cause
    assert str(err) == "wrapped"


def test_transport_timeout_error():
    """Test TransportTimeoutError is a TransportError."""
    err = TransportTimeoutError("timed out")
    assert isinstance(err, TransportError)


def test_transport_connection_error():
    """Test TransportConnectionError is a TransportError."""
    err = TransportConnectionError("connection failed")
    assert isinstance(err, TransportError)
