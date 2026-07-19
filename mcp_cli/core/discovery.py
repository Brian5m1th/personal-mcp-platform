"""
MCP Server Discovery Engine — searches npm, GitHub, PyPI, Smithery, and awesome lists.
"""

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from loguru import logger

from mcp_cli.core.config import get_mcp_home


@dataclass
class DiscoveredServer:
    id: str
    name: str
    description: str
    source: str
    source_url: str
    package: str
    install_method: str = "npx"
    version: str = "0.0.0"
    confidence: float = 0.0
    tags: list[str] = field(default_factory=list)
    maintainer: str = ""
    license: str = ""


DISCOVERY_CACHE_FILE = get_mcp_home() / "cache" / "discovery" / "results.json"
DISCOVERY_TIMEOUT = 15.0


class NpmSource:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def search(self, query: str = "") -> list[DiscoveredServer]:
        results = []
        search_url = "https://registry.npmjs.org/-/v1/search"
        params = {"text": query or "keywords:mcp-server", "size": 250}
        try:
            resp = await self._client.get(search_url, params=params, timeout=DISCOVERY_TIMEOUT)
            if resp.status_code != 200:
                return results
            data = resp.json()
            for obj in data.get("objects", []):
                pkg = obj.get("package", {})
                name = pkg.get("name", "")
                description = pkg.get("description", "")
                keywords = pkg.get("keywords", [])
                if not self._is_mcp_package(name, description, keywords):
                    continue
                results.append(DiscoveredServer(
                    id=name.split("/")[-1] if "/" in name else name,
                    name=pkg.get("name", name),
                    description=description,
                    source="npm",
                    source_url=pkg.get("links", {}).get("npm", f"https://www.npmjs.com/package/{name}"),
                    package=name,
                    install_method="npx",
                    version=pkg.get("version", "0.0.0"),
                    confidence=self._compute_confidence(name, description, keywords),
                    tags=keywords[:5],
                    maintainer=pkg.get("publisher", {}).get("username", ""),
                    license=pkg.get("license", ""),
                ))
        except Exception as e:
            logger.warning(f"[discovery] npm search failed: {e}")
        return results

    def _is_mcp_package(self, name: str, description: str, keywords: list[str]) -> bool:
        text = f"{name} {description} {' '.join(keywords)}".lower()
        if "mcp" not in text:
            return False
        if "modelcontextprotocol" in text or "mcp-server" in text or "mcp server" in text:
            return True
        return False

    def _compute_confidence(self, name: str, description: str, keywords: list[str]) -> float:
        text = f"{name} {description} {' '.join(keywords)}".lower()
        score = 0.5
        if "modelcontextprotocol" in text:
            score += 0.3
        if "mcp-server" in keywords or "mcp-server" in name:
            score += 0.2
        if "@modelcontextprotocol/" in name:
            score += 0.2
        return min(score, 1.0)


class GitHubSource:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def search(self, query: str = "") -> list[DiscoveredServer]:
        results = []
        search_url = "https://api.github.com/search/repositories"
        params = {
            "q": query or "topic:mcp-server",
            "sort": "updated",
            "per_page": 100,
        }
        try:
            resp = await self._client.get(
                search_url, params=params,
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=DISCOVERY_TIMEOUT,
            )
            if resp.status_code != 200:
                return results
            data = resp.json()
            for item in data.get("items", []):
                topics = item.get("topics", [])
                description = item.get("description") or ""
                full_name = item.get("full_name", "")
                if not self._is_mcp_repo(full_name, description, topics):
                    continue
                default_branch = item.get("default_branch", "main")
                install_method, package = self._detect_install_method(item)
                results.append(DiscoveredServer(
                    id=full_name.split("/")[-1] if "/" in full_name else full_name,
                    name=item.get("name", full_name),
                    description=description,
                    source="github",
                    source_url=item.get("html_url", f"https://github.com/{full_name}"),
                    package=package or full_name,
                    install_method=install_method,
                    version=item.get("default_branch", "main"),
                    confidence=self._compute_confidence(topics, description),
                    tags=topics[:5],
                    maintainer=item.get("owner", {}).get("login", ""),
                    license=item.get("license", {}).get("spdx_id", "") if item.get("license") else "",
                ))
        except Exception as e:
            logger.warning(f"[discovery] GitHub search failed: {e}")
        return results

    def _is_mcp_repo(self, name: str, description: str, topics: list[str]) -> bool:
        if "mcp-server" in topics or "mcp" in topics:
            return True
        text = f"{name} {description}".lower()
        return "mcp" in text or "modelcontextprotocol" in text

    def _detect_install_method(self, repo: dict) -> tuple[str, str]:
        full_name = repo.get("full_name", "")
        topics = repo.get("topics", [])
        if any(t in topics for t in ("python", "pypi")) or repo.get("language") == "Python":
            return "pip", full_name
        if repo.get("language") in ("TypeScript", "JavaScript"):
            return "npx", full_name
        return "npx", full_name

    def _compute_confidence(self, topics: list[str], description: str) -> float:
        score = 0.5
        if "mcp-server" in topics:
            score += 0.3
        if "modelcontextprotocol" in topics:
            score += 0.2
        text = description.lower()
        if "mcp" in text:
            score += 0.1
        return min(score, 1.0)


class PyPISource:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def search(self, query: str = "") -> list[DiscoveredServer]:
        results = []
        search_url = "https://pypi.org/search/"
        params = {"q": query or "mcp server", "o": ""}
        try:
            resp = await self._client.get(search_url, params=params, timeout=DISCOVERY_TIMEOUT)
            if resp.status_code != 200:
                return results
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for package in soup.select(".package-snippet"):
                name_el = package.select_one(".package-snippet__name")
                desc_el = package.select_one(".package-snippet__description")
                if not name_el:
                    continue
                name = name_el.text.strip()
                description = desc_el.text.strip() if desc_el else ""
                if not self._is_mcp(name, description):
                    continue
                results.append(DiscoveredServer(
                    id=name,
                    name=name,
                    description=description,
                    source="pypi",
                    source_url=f"https://pypi.org/project/{name}/",
                    package=name,
                    install_method="pip",
                    version="latest",
                    confidence=0.6,
                    tags=["python", "mcp"],
                ))
        except ImportError:
            logger.warning("[discovery] beautifulsoup4 not installed, skipping PyPI (pip install beautifulsoup4)")
        except Exception as e:
            logger.warning(f"[discovery] PyPI search failed: {e}")
        return results

    def _is_mcp(self, name: str, description: str) -> bool:
        text = f"{name} {description}".lower()
        return "mcp" in text


class SmitherySource:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def search(self, query: str = "") -> list[DiscoveredServer]:
        results = []
        urls = [
            "https://registry.smithery.ai/api/v1/packages",
            "https://registry.smithery.ai/packages",
        ]
        for url in urls:
            try:
                resp = await self._client.get(url, timeout=DISCOVERY_TIMEOUT)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                packages = data if isinstance(data, list) else data.get("packages", data.get("data", []))
                for pkg in packages:
                    if not isinstance(pkg, dict):
                        continue
                    name = pkg.get("name") or pkg.get("id") or pkg.get("package", "")
                    if not name:
                        continue
                    description = pkg.get("description", "")
                    if query and query.lower() not in f"{name} {description}".lower():
                        continue
                    results.append(DiscoveredServer(
                        id=name,
                        name=pkg.get("displayName", name),
                        description=description,
                        source="smithery",
                        source_url=pkg.get("homepage", pkg.get("url", f"https://smithery.ai/package/{name}")),
                        package=pkg.get("packageName", name),
                        install_method="npx",
                        version=pkg.get("version", "0.0.0"),
                        confidence=0.9,
                        tags=pkg.get("categories", [])[:5],
                        maintainer=pkg.get("author", ""),
                    ))
                if results:
                    break
            except Exception:
                continue
        return results


class AwesomeSource:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def search(self, query: str = "") -> list[DiscoveredServer]:
        results = []
        urls = [
            "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md",
            "https://raw.githubusercontent.com/homanp/awesome-mcp/main/README.md",
        ]
        for url in urls:
            try:
                resp = await self._client.get(url, timeout=DISCOVERY_TIMEOUT)
                if resp.status_code != 200:
                    continue
                text = resp.text
                for line in text.split("\n"):
                    if "- [" not in line or "](http" not in line:
                        continue
                    name = line.split("[", 1)[1].split("]", 1)[0] if "[" in line else ""
                    url_part = line.split("(", 1)[1].split(")", 1)[0] if "(" in line else ""
                    desc_part = line.split(") - ", 1)[1] if ") - " in line else ""
                    if not name:
                        continue
                    if query and query.lower() not in f"{name} {desc_part}".lower():
                        continue
                    results.append(DiscoveredServer(
                        id=name.lower().replace(" ", "-").replace("(", "").replace(")", ""),
                        name=name,
                        description=desc_part[:200],
                        source="awesome",
                        source_url=url_part,
                        package=name.lower().replace(" ", "-"),
                        install_method="npx",
                        version="0.0.0",
                        confidence=0.7,
                        tags=["curated"],
                    ))
            except Exception as e:
                logger.warning(f"[discovery] Awesome list failed: {e}")
        return results


class DiscoveryEngine:
    def __init__(self):
        self._cache_file = get_mcp_home() / "cache" / "discovery" / "results.json"
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)

    async def search(self, query: str = "", sources: list[str] | None = None) -> list[DiscoveredServer]:
        async with httpx.AsyncClient() as client:
            source_instances = self._build_sources(client, sources)
            tasks = [src.search(query) for src in source_instances]
            all_results = await asyncio.gather(*tasks, return_exceptions=True)

        merged: dict[str, DiscoveredServer] = {}
        for results in all_results:
            if isinstance(results, Exception):
                logger.warning(f"[discovery] Source failed: {results}")
                continue
            for server in results:
                key = server.package or server.id
                if key not in merged or server.confidence > merged[key].confidence:
                    merged[key] = server

        result_list = sorted(merged.values(), key=lambda s: s.confidence, reverse=True)
        self._cache_results(result_list)
        return result_list

    def _build_sources(self, client: httpx.AsyncClient, sources: list[str] | None) -> list:
        all_sources = {
            "npm": NpmSource(client),
            "github": GitHubSource(client),
            "pypi": PyPISource(client),
            "smithery": SmitherySource(client),
            "awesome": AwesomeSource(client),
        }
        if sources:
            return [all_sources[s] for s in sources if s in all_sources]
        return list(all_sources.values())

    def _cache_results(self, results: list[DiscoveredServer]) -> None:
        try:
            data = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "count": len(results),
                "servers": [asdict(s) for s in results],
            }
            self._cache_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"[discovery] Failed to cache results: {e}")

    def get_cached_results(self) -> list[dict]:
        if not self._cache_file.exists():
            return []
        try:
            data = json.loads(self._cache_file.read_text(encoding="utf-8"))
            return data.get("servers", [])
        except Exception:
            return []

    def get_cache_age_hours(self) -> float:
        if not self._cache_file.exists():
            return -1
        age = time.time() - self._cache_file.stat().st_mtime
        return age / 3600

    def clear_cache(self) -> None:
        if self._cache_file.exists():
            self._cache_file.unlink()
            logger.info("[discovery] Cache cleared")
