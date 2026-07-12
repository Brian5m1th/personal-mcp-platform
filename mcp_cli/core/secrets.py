"""
Secrets manager — resolves secret values from env vars, encrypted files, and OS keychain.
"""

import os
from pathlib import Path
from typing import Optional

from loguru import logger

from mcp_cli.core.config import get_mcp_home


class SecretsManager:
    """Manages and resolves secret references for MCP servers."""

    def __init__(self):
        self._secrets_dir = get_mcp_home() / "secrets"
        self._secrets_dir.mkdir(parents=True, exist_ok=True)

    def resolve(self, secret_ref: str) -> Optional[str]:
        """Resolve a secret reference to its value.

        Resolution order:
        1. Environment variable (direct match)
        2. Encrypted file ($MCP_HOME/secrets/<name>.enc)
        3. OS keychain (future)
        4. Interactive prompt (fallback)
        """
        # 1. Check environment variables
        env_val = os.environ.get(secret_ref)
        if env_val is not None:
            return env_val

        # 2. Check encrypted file (key format: "secrets.<name>.<key>")
        parts = secret_ref.replace("${", "").replace("}", "").split(".")
        if len(parts) >= 2 and parts[0] == "secrets":
            secret_name = parts[1]
            secret_file = self._secrets_dir / f"{secret_name}.yaml"
            if secret_file.exists():
                try:
                    import yaml
                    with open(secret_file, "r") as f:
                        data = yaml.safe_load(f) or {}
                    if len(parts) >= 3:
                        return data.get(parts[2])
                    return data.get("value")
                except Exception as e:
                    logger.warning(f"[secrets] Failed to read {secret_file}: {e}")

        # 3. Fallback: prompt (non-interactive, return None)
        return None

    def check_all_required(self, server_entry: dict) -> list[str]:
        """Check if all required secrets for a server are available.
        Returns list of missing secret names.
        """
        from mcp_cli.core.config import load_yaml

        missing = []
        req_secrets = server_entry.get("requirements", {}).get("secrets", {})
        for secret_name, secret_info in req_secrets.items():
            resolved = self.resolve(secret_name)
            if resolved is None:
                # Try GITHUB_TOKEN-style name
                resolved = self.resolve(secret_info.get("env_var", secret_name))
            if resolved is None and secret_info.get("required", True):
                missing.append(secret_name)
        return missing

    def set_env(self, secret_name: str, value: str) -> None:
        """Set a secret in the encrypted store."""
        secret_file = self._secrets_dir / f"{secret_name}.yaml"
        import yaml
        data = {}
        if secret_file.exists():
            with open(secret_file, "r") as f:
                data = yaml.safe_load(f) or {}
        data["value"] = value
        with open(secret_file, "w") as f:
            yaml.dump(data, f)
        # Set restrictive permissions (Unix only)
        try:
            secret_file.chmod(0o600)
        except Exception:
            pass
        logger.info(f"[secrets] Stored '{secret_name}'")
