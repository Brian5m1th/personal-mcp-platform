"""
Secrets manager — resolves secret values from env vars, encrypted files, and OS keychain.
"""

import json
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
        self._encryption_key: Optional[bytes] = None

    def _load_encryption_key(self) -> Optional[bytes]:
        """Load the platform encryption key, creating one if needed."""
        key_file = self._secrets_dir / ".key"
        if key_file.exists():
            return key_file.read_bytes()
        try:
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)
            return key
        except ImportError:
            return None

    def _get_fernet(self):
        """Get a Fernet instance using the platform encryption key."""
        if self._encryption_key is None:
            self._encryption_key = self._load_encryption_key()
        if self._encryption_key is None:
            return None
        try:
            from cryptography.fernet import Fernet
            return Fernet(self._encryption_key)
        except ImportError:
            return None

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

        # 2. Check encrypted store
        parts = secret_ref.replace("${", "").replace("}", "").split(".")
        if len(parts) >= 2 and parts[0] == "secrets":
            secret_name = parts[1]
            # Try encrypted file first
            enc_file = self._secrets_dir / f"{secret_name}.enc"
            if enc_file.exists():
                try:
                    encrypted_data = enc_file.read_bytes()
                    fernet = self._get_fernet()
                    if fernet:
                        decrypted = fernet.decrypt(encrypted_data)
                        store = json.loads(decrypted)
                        if len(parts) >= 3:
                            return store.get(parts[2])
                        return store.get("value")
                except Exception as e:
                    logger.warning(f"[secrets] Failed to decrypt {enc_file}: {e}")

            # Fallback to plain YAML (legacy)
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
                resolved = self.resolve(secret_info.get("env_var", secret_name))
            if resolved is None and secret_info.get("required", True):
                missing.append(secret_name)
        return missing

    def set_env(self, secret_name: str, value: str) -> None:
        """Set a secret in the encrypted store. Raises if encryption unavailable."""
        fernet = self._get_fernet()
        if fernet is None:
            raise ImportError(
                "cryptography library not found. Run: pip install mcp-platform[encryption]"
            )
        enc_file = self._secrets_dir / f"{secret_name}.enc"
        store = {"value": value}
        encrypted = fernet.encrypt(json.dumps(store).encode())
        enc_file.write_bytes(encrypted)
        enc_file.chmod(0o600)
        logger.info(f"[secrets] Stored '{secret_name}' (encrypted)")

    def migrate_legacy_secrets(self) -> None:
        """Migrate existing plaintext YAML secrets to encrypted format."""
        for legacy_file in self._secrets_dir.glob("*.yaml"):
            secret_name = legacy_file.stem
            enc_file = self._secrets_dir / f"{secret_name}.enc"
            if enc_file.exists():
                continue
            try:
                import yaml
                with open(legacy_file, "r") as f:
                    data = yaml.safe_load(f) or {}
                value = data.get("value")
                if value:
                    self.set_env(secret_name, value)
                    legacy_file.unlink()
                    logger.info(f"[secrets] Migrated '{secret_name}' from plaintext to encrypted")
            except Exception as e:
                logger.warning(f"[secrets] Failed to migrate '{secret_name}': {e}")
