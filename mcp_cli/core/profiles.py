"""
Profile manager — engineering profiles for focused tool sets.
"""

from pathlib import Path

import yaml
from loguru import logger

from mcp_cli.core.config import (
    get_mcp_home,
    get_profile_path,
    get_active_profile_path,
    load_yaml,
    save_yaml,
)


# Built-in profile definitions
BUILTIN_PROFILES = {
    "backend": {
        "name": "Backend Engineering",
        "description": "Servers for backend development: APIs, databases, containers",
        "enabled_servers": [
            "context7", "github", "postgres", "docker",
            "sequential-thinking", "filesystem", "fetch", "memory",
        ],
        "disabled_servers": ["playwright", "serena"],
    },
    "frontend": {
        "name": "Frontend Engineering",
        "description": "Servers for frontend/UI development: browser, design systems",
        "enabled_servers": [
            "context7", "github", "playwright",
            "filesystem", "sequential-thinking", "fetch", "memory",
        ],
        "disabled_servers": ["postgres", "docker", "serena"],
    },
    "devops": {
        "name": "Infrastructure & DevOps",
        "description": "Servers for cloud, containers, monitoring, and CI/CD",
        "enabled_servers": [
            "github", "docker", "sequential-thinking",
            "filesystem", "fetch", "memory",
        ],
        "disabled_servers": ["playwright", "serena", "context7"],
    },
    "ai-llm": {
        "name": "AI / LLM Engineering",
        "description": "Servers for AI development: RAG, embeddings, models",
        "enabled_servers": [
            "context7", "serena", "github",
            "sequential-thinking", "memory", "fetch",
            "filesystem",
        ],
        "disabled_servers": ["playwright", "docker", "postgres"],
    },
    "security": {
        "name": "Security Engineering",
        "description": "Servers for security auditing and compliance",
        "enabled_servers": [
            "github", "filesystem", "sequential-thinking", "docker", "fetch",
        ],
        "disabled_servers": ["playwright", "serena", "context7", "postgres", "memory"],
    },
    "documentation": {
        "name": "Documentation",
        "description": "Servers for technical writing and documentation",
        "enabled_servers": [
            "context7", "filesystem", "github", "memory",
        ],
        "disabled_servers": ["serena", "playwright", "docker", "postgres", "sequential-thinking"],
    },
    "full-stack": {
        "name": "Full Stack (Default)",
        "description": "All servers with sensible limits",
        "enabled_servers": [
            "context7", "serena", "github", "playwright",
            "filesystem", "sequential-thinking", "postgres", "docker",
            "fetch", "memory",
        ],
        "disabled_servers": [],
    },
    "minimal": {
        "name": "Minimal / Lightweight",
        "description": "Minimal servers for quick coding sessions",
        "enabled_servers": [
            "filesystem", "github", "sequential-thinking",
        ],
        "disabled_servers": [],
    },
}


class ProfileManager:
    """Manages engineering profiles and active profile state."""

    def __init__(self):
        self._profiles_dir = get_mcp_home() / "profiles"
        self._profiles_dir.mkdir(parents=True, exist_ok=True)

    def initialize_builtins(self) -> int:
        """Create all built-in profile files if they don't exist.
        Returns count of profiles created.
        """
        created = 0
        for name, data in BUILTIN_PROFILES.items():
            path = get_profile_path(name)
            if not path.exists():
                save_yaml(path, data)
                created += 1
        return created

    def list_profiles(self) -> list[dict]:
        """List all available profiles."""
        profiles = []
        for name, data in BUILTIN_PROFILES.items():
            profiles.append({
                "id": name,
                "name": data["name"],
                "description": data["description"],
                "server_count": len(data["enabled_servers"]),
            })

        # Also load any custom profiles
        if self._profiles_dir.exists():
            for f in sorted(self._profiles_dir.glob("*.yaml")):
                name = f.stem
                if name not in BUILTIN_PROFILES:
                    data = load_yaml(f)
                    profiles.append({
                        "id": name,
                        "name": data.get("name", name),
                        "description": data.get("description", ""),
                        "server_count": len(data.get("enabled_servers", [])),
                    })
        return profiles

    def get_active(self) -> list[str]:
        """Get the currently active profile(s)."""
        active = load_yaml(get_active_profile_path())
        return active.get("active_profiles", ["full-stack"])

    def set_active(self, profile_name: str) -> bool:
        """Set the active profile."""
        if profile_name not in BUILTIN_PROFILES:
            path = get_profile_path(profile_name)
            if not path.exists():
                logger.error(f"Profile '{profile_name}' not found")
                return False

        import time
        save_yaml(get_active_profile_path(), {
            "active_profiles": [profile_name],
            "set_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": "manual",
        })
        logger.info(f"Active profile set to: {profile_name}")
        return True

    def get_profile_info(self, name: str) -> dict | None:
        """Get details for a specific profile."""
        if name in BUILTIN_PROFILES:
            return {"id": name, **BUILTIN_PROFILES[name]}
        path = get_profile_path(name)
        if path.exists():
            data = load_yaml(path)
            return {"id": name, **data}
        return None

    def auto_detect(self, workspace: str) -> str | None:
        """Detect the appropriate profile based on workspace contents."""
        from pathlib import Path

        ws = Path(workspace)
        if not ws.exists():
            return None

        # Check for indicators
        has_docker = any(ws.glob("Dockerfile")) or any(ws.glob("docker-compose*"))
        has_terraform = any(ws.glob("*.tf"))
        has_package_json = (ws / "package.json").exists()
        has_pyproject = (ws / "pyproject.toml").exists()
        has_cargo = (ws / "Cargo.toml").exists()
        has_docs = any(ws.glob("*.md")) or (ws / "docs").is_dir()

        # Score-based detection
        scores = {
            "backend": (1 if has_cargo else 0) + (1 if has_pyproject else 0),
            "frontend": (2 if has_package_json else 0),
            "devops": (2 if has_docker else 0) + (2 if has_terraform else 0),
            "documentation": (2 if has_docs else 0),
        }

        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
        return None
