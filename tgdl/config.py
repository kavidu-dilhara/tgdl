"""Configuration management for tgdl."""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

from tgdl.crypto import CredentialEncryption, harden_file_permissions

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".tgdl"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        harden_file_permissions(self.config_dir, 0o700)
        self.config_file = self.config_dir / "config.json"
        self.session_file = self.config_dir / "tgdl.session"
        self.progress_file = self.config_dir / "progress.json"
        self.lock_file = self.config_dir / ".state.lock"
        self.crypto = CredentialEncryption(self.config_dir)
        self._config = self._load_mapping(self.config_file, "config")
        self._progress = self._load_mapping(self.progress_file, "progress")
        for existing in (self.config_file, self.session_file, self.progress_file):
            if existing.exists():
                harden_file_permissions(existing, 0o600)

    @staticmethod
    def _load_mapping(path: Path, label: str) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as stream:
                value = json.load(stream)
            if not isinstance(value, dict):
                raise ValueError(f"{label} must contain a JSON object")
            return value
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.warning("Failed to load %s file: %s", label, exc)
            return {}

    def _atomic_save(self, path: Path, value: dict[str, Any]) -> None:
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=self.config_dir)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(value, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            harden_file_permissions(temporary_path, 0o600)
            os.replace(temporary_path, path)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    def _save_config(self):
        try:
            import fcntl
        except ImportError:
            fcntl = None
        self.lock_file.touch(exist_ok=True)
        with self.lock_file.open("r+", encoding="utf-8") as lock:
            if fcntl:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            current = self._load_mapping(self.config_file, "config")
            current.update(self._config)
            self._config = current
            self._atomic_save(self.config_file, current)
            if fcntl:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def save_progress(self):
        # Reload under a local advisory lock so parallel processes merge updates.
        try:
            import fcntl
        except ImportError:  # pragma: no cover - Windows fallback
            fcntl = None
        self.lock_file.touch(exist_ok=True)
        with self.lock_file.open("r+", encoding="utf-8") as lock:
            if fcntl:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            current = self._load_mapping(self.progress_file, "progress")
            current.update(self._progress)
            self._progress = current
            self._atomic_save(self.progress_file, current)
            if fcntl:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value
        self._save_config()

    def get_progress(self, entity_id: str) -> int:
        value = self._progress.get(str(entity_id), 0)
        return value if isinstance(value, int) and value >= 0 else 0

    def set_progress(self, entity_id: str, message_id: int):
        if not isinstance(message_id, int) or message_id < 0:
            raise ValueError("message_id must be a non-negative integer")
        self._progress[str(entity_id)] = message_id
        self.save_progress()

    def get_api_credentials(self) -> tuple[Optional[int], Optional[str]]:
        self.credentials_error = None
        encrypted_id = self.get("api_id_enc")
        encrypted_hash = self.get("api_hash_enc")
        if isinstance(encrypted_id, str) and isinstance(encrypted_hash, str):
            api_id, api_hash = self.crypto.decrypt_credentials(encrypted_id, encrypted_hash)
            if api_id and api_hash:
                return api_id, api_hash
            self.credentials_error = "Stored credentials could not be decrypted. Run 'tgdl login' again."
        api_id = self.get("api_id")
        api_hash = self.get("api_hash")
        if api_id and isinstance(api_hash, str):
            try:
                api_id_int = int(api_id)
                self.set_api_credentials(api_id_int, api_hash)
                self._config.pop("api_id", None)
                self._config.pop("api_hash", None)
                self._save_config()
                self.credentials_error = None
                return api_id_int, api_hash
            except (ValueError, TypeError):
                self.credentials_error = "Stored credentials are invalid. Run 'tgdl login' again."
        return None, None

    def set_api_credentials(self, api_id: int, api_hash: str):
        encrypted_id, encrypted_hash = self.crypto.encrypt_credentials(api_id, api_hash)
        self._config["api_id_enc"] = encrypted_id
        self._config["api_hash_enc"] = encrypted_hash
        self._config.pop("api_id", None)
        self._config.pop("api_hash", None)
        self._save_config()

    def is_authenticated(self) -> bool:
        try:
            return self.session_file.exists() and self.session_file.stat().st_size > 0
        except OSError:
            return False

    def get_session_path(self) -> str:
        return str(self.config_dir / "tgdl")


_config_holder: dict[str, Optional[Config]] = {"value": None}


def get_config() -> Config:
    if _config_holder["value"] is None:
        _config_holder["value"] = Config()
    return _config_holder["value"]
