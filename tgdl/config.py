"""Configuration management for tgdl."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Manage tgdl configuration and user data."""

    def __init__(self):
        """Initialize configuration paths."""
        self.config_dir = Path.home() / ".tgdl"
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.session_file = self.config_dir / "tgdl.session"
        self.progress_file = self.config_dir / "progress.json"
        
        self._config = self._load_config()
        self._progress = self._load_progress()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
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
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def save_progress(self):
        """Save download progress to file."""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self._progress, f, indent=2)

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

    def get_api_credentials(self) -> tuple[Optional[int], Optional[str]]:
        """Get API credentials from config."""
        api_id = self.get('api_id')
        api_hash = self.get('api_hash')
        
        if api_id is not None:
            try:
                api_id = int(api_id)
            except (ValueError, TypeError):
                api_id = None
        
        return api_id, api_hash

    def set_api_credentials(self, api_id: int, api_hash: str):
        """Save API credentials to config."""
        self.set('api_id', api_id)
        self.set('api_hash', api_hash)

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
