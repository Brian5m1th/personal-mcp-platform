"""Unit tests for the discovery engine."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_cli.core.discovery import (
    AwesomeSource,
    DiscoveredServer,
    DiscoveryEngine,
    GitHubSource,
    NpmSource,
)


class TestNpmSource:
    @pytest.mark.asyncio
    async def test_filters_non_mcp_packages(self):
        mock_client = AsyncMock()
        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "objects": [
                    {
                        "package": {
                            "name": "@modelcontextprotocol/server-github",
                            "description": "MCP server for GitHub API",
                            "keywords": ["mcp-server", "github"],
                            "version": "1.0.0",
                            "links": {"npm": "https://www.npmjs.com/package/@modelcontextprotocol/server-github"},
                            "publisher": {"username": "mcp"},
                            "license": "MIT",
                        }
                    },
                    {
                        "package": {
                            "name": "lodash",
                            "description": "A modern JavaScript utility library",
                            "keywords": ["utility", "javascript"],
                            "version": "4.17.21",
                            "links": {},
                        }
                    },
                ]
            },
        )
        source = NpmSource(mock_client)
        results = await source.search("mcp-server")
        assert len(results) == 1
        assert results[0].id == "server-github"
        assert results[0].confidence >= 0.8

    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        mock_client = AsyncMock()
        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "objects": [
                    {
                        "package": {
                            "name": "@modelcontextprotocol/server-test",
                            "description": "Official MCP server",
                            "keywords": ["mcp-server", "modelcontextprotocol"],
                            "version": "1.0.0",
                            "links": {},
                            "publisher": {"username": "test"},
                            "license": "MIT",
                        }
                    }
                ]
            },
        )
        source = NpmSource(mock_client)
        results = await source.search()
        assert len(results) == 1
        assert results[0].confidence >= 0.9

    @pytest.mark.asyncio
    async def test_handles_http_error(self):
        mock_client = AsyncMock()
        mock_client.get.return_value = MagicMock(status_code=500)
        source = NpmSource(mock_client)
        results = await source.search()
        assert results == []


class TestGitHubSource:
    @pytest.mark.asyncio
    async def test_detects_mcp_repos(self):
        mock_client = AsyncMock()
        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "items": [
                    {
                        "full_name": "modelcontextprotocol/server-github",
                        "name": "server-github",
                        "description": "MCP server for GitHub",
                        "topics": ["mcp-server", "github", "modelcontextprotocol"],
                        "html_url": "https://github.com/modelcontextprotocol/server-github",
                        "owner": {"login": "modelcontextprotocol"},
                        "language": "TypeScript",
                        "license": {"spdx_id": "MIT"},
                        "default_branch": "main",
                    }
                ]
            },
        )
        source = GitHubSource(mock_client)
        results = await source.search()
        assert len(results) == 1
        assert results[0].id == "server-github"
        assert results[0].install_method == "npx"
        assert results[0].confidence >= 0.8

    @pytest.mark.asyncio
    async def test_detects_python_mcp(self):
        mock_client = AsyncMock()
        mock_client.get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "items": [
                    {
                        "full_name": "user/mcp-server-python",
                        "name": "mcp-server-python",
                        "description": "A Python MCP server",
                        "topics": ["mcp-server", "python"],
                        "html_url": "https://github.com/user/mcp-server-python",
                        "owner": {"login": "user"},
                        "language": "Python",
                        "license": None,
                        "default_branch": "main",
                    }
                ]
            },
        )
        source = GitHubSource(mock_client)
        results = await source.search()
        assert len(results) == 1
        assert results[0].install_method == "pip"

    @pytest.mark.asyncio
    async def test_handles_empty_response(self):
        mock_client = AsyncMock()
        mock_client.get.return_value = MagicMock(status_code=403, json=lambda: {"message": "rate limit"})
        source = GitHubSource(mock_client)
        results = await source.search()
        assert results == []


class TestAwesomeSource:
    @pytest.mark.asyncio
    async def test_parses_readme_links(self):
        text = '''# Awesome MCP Servers
- [GitHub MCP Server](https://github.com/modelcontextprotocol/server-github) - Official GitHub integration
- [Filesystem MCP](https://github.com/modelcontextprotocol/server-filesystem) - File system access
'''
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[
            MagicMock(status_code=200, text=text),
            MagicMock(status_code=404),
        ])
        source = AwesomeSource(mock_client)
        results = await source.search()
        assert len(results) == 2
        assert results[0].source == "awesome"
        assert results[0].confidence == 0.7

    @pytest.mark.asyncio
    async def test_filters_by_query(self):
        text = '''# Awesome MCP Servers
- [GitHub MCP](https://github.com/modelcontextprotocol/server-github) - GitHub API
- [Docker MCP](https://github.com/modelcontextprotocol/server-docker) - Docker management
'''
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[
            MagicMock(status_code=200, text=text),
            MagicMock(status_code=404),
        ])
        source = AwesomeSource(mock_client)
        results = await source.search("docker")
        assert len(results) == 1
        assert "docker" in results[0].name.lower()

    @pytest.mark.asyncio
    async def test_handles_http_error(self):
        mock_client = AsyncMock()
        mock_client.get.return_value = MagicMock(status_code=404)
        source = AwesomeSource(mock_client)
        results = await source.search()
        assert results == []


class TestDiscoveryEngine:
    @pytest.mark.asyncio
    async def test_merges_results_from_multiple_sources(self):
        engine = DiscoveryEngine()

        with patch.object(NpmSource, "search", new=AsyncMock(return_value=[
            DiscoveredServer(
                id="server-a", name="Server A", description="desc",
                source="npm", source_url="url", package="pkg-a",
                confidence=0.8,
            )
        ])):
            with patch.object(GitHubSource, "search", new=AsyncMock(return_value=[
                DiscoveredServer(
                    id="server-b", name="Server B", description="desc",
                    source="github", source_url="url", package="pkg-b",
                    confidence=0.7,
                )
            ])):
                with patch.object(AwesomeSource, "search", new=AsyncMock(return_value=[])):
                    results = await engine.search(sources=["npm", "github"])
                    assert len(results) == 2

    @pytest.mark.asyncio
    async def test_dedup_by_package_highest_confidence_wins(self):
        engine = DiscoveryEngine()

        with patch.object(NpmSource, "search", new=AsyncMock(return_value=[
            DiscoveredServer(
                id="server-a", name="Server A", description="from npm",
                source="npm", source_url="url1", package="pkg-a",
                confidence=0.6,
            )
        ])):
            with patch.object(GitHubSource, "search", new=AsyncMock(return_value=[
                DiscoveredServer(
                    id="server-a", name="Server A", description="from github",
                    source="github", source_url="url2", package="pkg-a",
                    confidence=0.9,
                )
            ])):
                with patch.object(AwesomeSource, "search", new=AsyncMock(return_value=[])):
                    results = await engine.search(sources=["npm", "github"])
                    assert len(results) == 1
                    assert results[0].source == "github"
                    assert results[0].confidence == 0.9

    def test_cache_age_negative_when_no_cache(self):
        engine = DiscoveryEngine()
        engine.clear_cache()
        age = engine.get_cache_age_hours()
        assert age == -1

    def test_clear_cache_does_not_raise(self):
        engine = DiscoveryEngine()
        engine.clear_cache()
        cached = engine.get_cached_results()
        assert cached == []
