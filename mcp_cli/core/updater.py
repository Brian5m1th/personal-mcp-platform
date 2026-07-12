"""
Update manager — version checking, compatibility validation, backup/rollback.
"""

import json
import shutil
import time
from datetime import datetime
from pathlib import Path

import httpx
from loguru import logger

from mcp_cli.core.config import get_mcp_home, load_yaml, save_yaml


class UpdateManager:
    """Manages MCP server updates with backup and rollback support."""

    def __init__(self):
        self._backups_dir = get_mcp_home() / "backups"
        self._backups_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self._backups_dir / "manifest.yaml"

    async def check_version(self, server_entry: dict) -> dict:
        """Check the latest available version for a server.
        Returns dict with current_version, latest_version, has_update.
        """
        server_id = server_entry.get("id", "unknown")
        current = server_entry.get("version", "0.0.0")
        update_policy = server_entry.get("install", {}).get("update_policy", "minor")

        # For npm packages, check npm registry
        install_method = server_entry.get("install", {}).get("method", "")
        latest = current  # Default: no update

        if install_method == "npx" or install_method == "npm":
            package_name = self._get_npm_package(server_entry)
            if package_name:
                latest = await self._check_npm_version(package_name)

        return {
            "server_id": server_id,
            "current_version": current,
            "latest_version": latest or current,
            "has_update": latest is not None and latest != current,
            "update_policy": update_policy,
        }

    def _get_npm_package(self, server_entry: dict) -> str | None:
        """Extract npm package name from install command."""
        command = server_entry.get("install", {}).get("command", "")
        # e.g., "npx @modelcontextprotocol/server-github" -> "@modelcontextprotocol/server-github"
        parts = command.split()
        for p in parts:
            if p.startswith("@") or "/" in p:
                return p
        return None

    async def _check_npm_version(self, package: str) -> str | None:
        """Check the latest version of an npm package."""
        try:
            url = f"https://registry.npmjs.org/{package}/latest"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("version")
        except Exception as e:
            logger.warning(f"[updater] Failed to check npm version for {package}: {e}")
        return None

    def create_backup(self, server_id: str, from_version: str, to_version: str) -> str:
        """Create a backup snapshot before updating. Returns backup ID."""
        backup_id = f"bk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{server_id}"
        backup_dir = self._backups_dir / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup server config
        server_config = get_mcp_home() / "servers" / f"{server_id}.yaml"
        if server_config.exists():
            shutil.copy2(server_config, backup_dir / f"{server_id}.yaml")

        # Record in manifest
        manifest = load_yaml(self._manifest_path)
        backups = manifest.get("backups", [])
        backups.append({
            "id": backup_id,
            "date": datetime.utcnow().isoformat(),
            "server": server_id,
            "from_version": from_version,
            "to_version": to_version,
            "files": [str(backup_dir / f"{server_id}.yaml")],
            "status": "completed",
        })
        save_yaml(self._manifest_path, {"backups": backups})

        return backup_id

    def get_backups(self, server_id: str | None = None) -> list[dict]:
        """List available backups."""
        manifest = load_yaml(self._manifest_path)
        backups = manifest.get("backups", [])
        if server_id:
            backups = [b for b in backups if b.get("server") == server_id]
        return backups

    def get_latest_backup(self, server_id: str) -> dict | None:
        """Get the most recent backup for a server."""
        backups = self.get_backups(server_id)
        if not backups:
            return None
        return backups[-1]

    async def rollback(self, server_id: str, target_version: str | None = None) -> bool:
        """Rollback a server to a previous version.
        Returns True if successful.
        """
        backup = self.get_latest_backup(server_id)
        if backup is None:
            logger.error(f"[updater] No backup found for '{server_id}'")
            return False

        if target_version and backup.get("from_version") != target_version:
            logger.error(f"[updater] No backup matching version {target_version}")
            return False

        backup_dir = self._backups_dir / backup["id"]
        if not backup_dir.exists():
            logger.error(f"[updater] Backup directory not found: {backup_dir}")
            return False

        # Restore files from backup
        for file_path_str in backup.get("files", []):
            file_path = Path(file_path_str)
            if file_path.exists() and file_path.parent == backup_dir:
                target = get_mcp_home() / "servers" / file_path.name
                shutil.copy2(file_path, target)
                logger.info(f"[updater] Restored {file_path.name}")

        # Mark backup as rolled back
        manifest = load_yaml(self._manifest_path)
        for b in manifest.get("backups", []):
            if b["id"] == backup["id"]:
                b["status"] = "rolled_back"
                break
        save_yaml(self._manifest_path, manifest)

        logger.info(f"[updater] Rolled back '{server_id}' to version {backup.get('from_version')}")
        return True
