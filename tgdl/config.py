"""Configuration management for tgdl."""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from tgdl.crypto import CredentialEncryption, harden_file_permissions

logger = logging.getLogger(__name__)


class Config:
    """Manage tgdl configuration and user data."""

    def __init__(self):
        """Initialize configuration paths."""
        self.config_dir = Path.home() / ".tgdl"
        self.config_dir.mkdir(exist_ok=True)
        # Fix #3: the directory itself should not be group/world accessible —
        # it holds the Telegram session, encryption key, and salt.
        harden_file_permissions(self.config_dir, 0o700)

        self.config_file = self.config_dir / "config.json"
        self.session_file = self.config_dir / "tgdl.session"
        self.progress_file = self.config_dir / "progress.json"

        # Initialize encryption handler
        self.crypto = CredentialEncryption(self.config_dir)

        self._config = self._load_config()
        self._progress = self._load_progress()

        # Fix #3: harden any of these files that already existed before this
        # version started enforcing permissions (e.g. upgrades from an older
        # tgdl release). Newly created files are also hardened at write time
        # in _save_config/save_progress and in crypto.py.
        for existing in (self.config_file, self.session_file, self.progress_file):
            if existing.exists():
                harden_file_permissions(existing, 0o600)

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config file: {e}")
        return {}

    def _save_config(self):
        """Save configuration to file atomically.

        Fix #17: write to a temp file then os.replace() so a crash mid-write
        never corrupts config.json.
        """
        tmp = self.config_file.with_suffix('.tmp')
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
            harden_file_permissions(tmp, 0o600)  # Fix #3: harden before the rename is visible
            os.replace(tmp, self.config_file)
        except Exception:
            # Broad catch is intentional here: this is a cleanup-then-reraise
            # (remove the temp file, then propagate whatever went wrong —
            # bad data in json.dump, a full disk, a permission error, etc.)
            # rather than a handler that swallows the error.
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
            raise

    def _load_progress(self) -> Dict[str, Any]:
        """Load download progress from file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load progress file: {e}")
        return {}

    def save_progress(self):
        """Save download progress to file atomically.

        Fix #18: write to a temp file then os.replace() so a crash mid-write
        never corrupts progress.json.
        """
        tmp = self.progress_file.with_suffix('.tmp')
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self._progress, f, indent=2)
            harden_file_permissions(tmp, 0o600)  # Fix #3: harden before the rename is visible
            os.replace(tmp, self.progress_file)
        except Exception:
            # Broad catch intentional: cleanup-then-reraise (see _save_config).
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value and save."""
        self._config[key] = value
        self._save_config()

    def get_progress(self, entity_id: str) -> int:
        """Get last downloaded message ID for entity."""
        return self._progress.get(str(entity_id), 0)

    def set_progress(self, entity_id: str, message_id: int):
        """Set last downloaded message ID for entity."""
        self._progress[str(entity_id)] = message_id
        self.save_progress()

    def get_api_credentials(self) -> Tuple[Optional[int], Optional[str]]:
        """Get API credentials from config (with decryption).

        Fix #4: use typing.Tuple instead of built-in tuple[] (PEP 585) so this
        works on Python 3.7 and 3.8 as advertised in setup.py.

        Fix #4/#5: if encrypted credentials are present but fail to decrypt
        (corrupted/regenerated .key, tampered config.json, etc.), that is a
        distinct condition from "never logged in" — set self.credentials_error
        so callers can surface an accurate message instead of the misleading
        "Not logged in. Run 'tgdl login' first."
        """
        self.credentials_error: Optional[str] = None
        encrypted_id = self.get('api_id_enc')
        encrypted_hash = self.get('api_hash_enc')

        if encrypted_id and encrypted_hash:
            api_id, api_hash = self.crypto.decrypt_credentials(encrypted_id, encrypted_hash)
            if api_id and api_hash:
                return api_id, api_hash
            # Encrypted credentials exist but could not be decrypted.
            self.credentials_error = (
                "Stored credentials could not be decrypted (the encryption key may have "
                "changed or the config file is corrupted). Run 'tgdl login' again."
            )
            logger.warning("Encrypted API credentials present but decryption failed.")

        # Fallback: check for old plaintext credentials (migration path)
        api_id = self.get('api_id')
        api_hash = self.get('api_hash')

        if api_id and api_hash:
            try:
                api_id_int = int(api_id)
                self.set_api_credentials(api_id_int, api_hash)
                # Remove old plaintext credentials and persist
                self._config.pop('api_id', None)
                self._config.pop('api_hash', None)
                self._save_config()
                self.credentials_error = None
                return api_id_int, api_hash
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to migrate credentials: {type(e).__name__}")
                self.credentials_error = "Stored credentials are invalid. Run 'tgdl login' again."

        return None, None

    def set_api_credentials(self, api_id: int, api_hash: str):
        """Save API credentials to config (with encryption)."""
        encrypted_id, encrypted_hash = self.crypto.encrypt_credentials(api_id, api_hash)
        self._config['api_id_enc'] = encrypted_id
        self._config['api_hash_enc'] = encrypted_hash
        self._config.pop('api_id', None)
        self._config.pop('api_hash', None)
        self._save_config()

    def is_authenticated(self) -> bool:
        """Check if user has a plausible (non-empty) session file."""
        if not self.session_file.exists():
            return False
        try:
            return self.session_file.stat().st_size > 0
        except OSError:
            return False

    def get_session_path(self) -> str:
        """Get session file path (without .session extension — Telethon adds it)."""
        return str(self.config_dir / "tgdl")


# Global config instance — lazily initialized to avoid import-time side effects.
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
