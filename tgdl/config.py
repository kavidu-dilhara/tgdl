"""Configuration management for tgdl."""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Iterable, Set, Union
from tgdl.crypto import CredentialEncryption

logger = logging.getLogger(__name__)


class Config:
    """Manage tgdl configuration and user data."""

    def __init__(self):
        """Initialize configuration paths."""
        self.config_dir = Path.home() / ".tgdl"
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.session_file = self.config_dir / "tgdl.session"
        self.progress_file = self.config_dir / "progress.json"
        
        # Initialize encryption handler
        self.crypto = CredentialEncryption(self.config_dir)
        
        self._config = self._load_config()
        self._progress = self._load_progress()

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
        """Save configuration to file."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2)

    def _load_progress(self) -> Dict[str, Any]:
        """Load download progress from file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load progress file: {e}")
        return {}
        return {}

    def save_progress(self):
        """Save download progress to file."""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self._progress, f, indent=2)

    def _coerce_message_id(self, value: Any) -> int:
        """Convert a value to a valid message ID."""
        should_warn = value not in (None, "", 0, "0")
        try:
            message_id = int(value)
        except (TypeError, ValueError):
            if should_warn:
                logger.warning("Invalid message ID in progress data: %r", value)
            return 0
        if message_id <= 0:
            if should_warn:
                logger.warning("Non-positive message ID in progress data: %r", value)
            return 0
        return message_id

    def _coerce_message_ids(self, values: Any) -> Set[int]:
        """Convert a list of values to a set of valid message IDs."""
        message_ids: Set[int] = set()
        if isinstance(values, (list, tuple, set)):
            for value in values:
                message_id = self._coerce_message_id(value)
                if message_id:
                    message_ids.add(message_id)
        return message_ids

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value and save."""
        self._config[key] = value
        self._save_config()

    def get_progress(self, entity_id: Union[str, int]) -> int:
        """Get last downloaded message ID for entity."""
        entry = self._progress.get(str(entity_id), 0)
        if isinstance(entry, dict):
            return self._coerce_message_id(entry.get("last_message_id", 0))
        return self._coerce_message_id(entry)

    def get_downloaded_ids(self, entity_id: Union[str, int]) -> Set[int]:
        """Get downloaded message IDs tracked in the progress file."""
        entry = self._progress.get(str(entity_id))
        if isinstance(entry, dict):
            return self._coerce_message_ids(entry.get("downloaded_ids", []))
        if isinstance(entry, list):
            return self._coerce_message_ids(entry)
        return set()

    def set_progress(self, entity_id: Union[str, int], message_id: int):
        """Set last downloaded message ID for entity."""
        key = str(entity_id)
        entry = self._progress.get(key)
        if isinstance(entry, dict):
            entry["last_message_id"] = message_id
            self._progress[key] = entry
        elif isinstance(entry, list):
            self._progress[key] = {
                "last_message_id": message_id,
                "downloaded_ids": entry,
            }
        else:
            self._progress[key] = message_id
        self.save_progress()

    def add_downloaded_ids(self, entity_id: Union[str, int], message_ids: Iterable[int]):
        """Track additional downloaded message IDs for an entity."""
        ids_to_add = self._coerce_message_ids(message_ids)
        if not ids_to_add:
            return

        key = str(entity_id)
        entry = self._progress.get(key)
        last_message_id = 0

        if isinstance(entry, dict):
            downloaded_ids = self._coerce_message_ids(entry.get("downloaded_ids", []))
            last_message_id = self._coerce_message_id(entry.get("last_message_id", 0))
        elif isinstance(entry, list):
            downloaded_ids = self._coerce_message_ids(entry)
        else:
            downloaded_ids = set()
            last_message_id = self._coerce_message_id(entry)

        downloaded_ids.update(ids_to_add)
        self._progress[key] = {
            "last_message_id": last_message_id,
            "downloaded_ids": list(downloaded_ids),
        }
        self.save_progress()

    def get_api_credentials(self) -> tuple[Optional[int], Optional[str]]:
        """Get API credentials from config (with decryption)."""
        encrypted_id = self.get('api_id_enc')
        encrypted_hash = self.get('api_hash_enc')
        
        if encrypted_id and encrypted_hash:
            # Try to decrypt encrypted credentials
            api_id, api_hash = self.crypto.decrypt_credentials(encrypted_id, encrypted_hash)
            if api_id and api_hash:
                return api_id, api_hash
        
        # Fallback: check for old plaintext credentials (for migration)
        api_id = self.get('api_id')
        api_hash = self.get('api_hash')
        
        if api_id and api_hash:
            # Migrate to encrypted storage
            try:
                api_id_int = int(api_id)
                self.set_api_credentials(api_id_int, api_hash)
                # Remove old plaintext credentials
                if 'api_id' in self._config:
                    del self._config['api_id']
                if 'api_hash' in self._config:
                    del self._config['api_hash']
                self._save_config()
                return api_id_int, api_hash
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to migrate credentials: {e}")
        
        return None, None

    def set_api_credentials(self, api_id: int, api_hash: str):
        """Save API credentials to config (with encryption)."""
        # Encrypt credentials
        encrypted_id, encrypted_hash = self.crypto.encrypt_credentials(api_id, api_hash)
        
        # Save encrypted credentials
        self.set('api_id_enc', encrypted_id)
        self.set('api_hash_enc', encrypted_hash)
        
        # Remove old plaintext credentials if they exist
        if 'api_id' in self._config:
            del self._config['api_id']
        if 'api_hash' in self._config:
            del self._config['api_hash']
        self._save_config()

    def is_authenticated(self) -> bool:
        """Check if user has valid session file."""
        return self.session_file.exists()

    def get_session_path(self) -> str:
        """Get session file path."""
        # Return without extension - Telethon adds .session
        return str(self.config_dir / "tgdl")


# Global config instance
_config = None


def get_config() -> Config:
    """Get global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
