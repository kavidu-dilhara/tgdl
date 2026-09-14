"""Cryptography utilities for secure credential storage."""

import os
import base64
import logging
from pathlib import Path
from typing import Optional, Tuple
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# Expected length of a valid Fernet key (44 URL-safe base64 chars = 32 raw bytes)
_FERNET_KEY_LENGTH = 44


def harden_file_permissions(path: Path, mode: int = 0o600) -> None:
    """Best-effort chmod hardening.

    Fix #3: restrict access to the config directory and sensitive files on
    POSIX systems. chmod semantics differ (or don't apply at all) on
    Windows, so this is skipped there rather than attempted and failed.
    Any OS-level error here (e.g. exotic filesystems that reject chmod) is
    swallowed — permission hardening is defense-in-depth, not something
    that should crash the CLI — and the error text is logged at debug
    level only so it can never leak a path-adjacent secret.

    Lives here (rather than in config.py, which needs it too) because
    config.py already imports CredentialEncryption from this module;
    putting the shared helper in config.py would create a circular import.
    """
    if os.name == 'nt':
        return
    try:
        os.chmod(path, mode)
    except OSError as e:
        logger.debug(f"Could not set permissions on {path.name}: {e}")


class CredentialEncryption:
    """Handle encryption/decryption of sensitive credentials.

    Threat model note: this encrypts the stored api_id/api_hash at rest using
    a key derived from machine-specific data (hostname + username) plus a
    per-install random salt, both stored alongside the encrypted data in
    ~/.tgdl. This protects against casual disclosure (e.g. the config file
    being copied to a USB drive, committed to a repo, or read by an
    unrelated process that doesn't also have access to the rest of ~/.tgdl)
    and against someone reading config.json in isolation. It does NOT
    protect against an attacker who already has full read access to the
    ~/.tgdl directory itself — the key and salt live right next to the data
    they protect, and the Telegram .session file (which grants live account
    access) is not encrypted by this module at all. File permissions
    (0700/0600, see config.py) are the actual security boundary; this
    encryption layer is a secondary measure against the credentials leaking
    outside that directory.
    """

    def __init__(self, config_dir: Path):
        """
        Initialize encryption handler.

        Args:
            config_dir: Directory to store encryption key and salt
        """
        self.config_dir = config_dir
        self.key_file = config_dir / ".key"
        self.salt_file = config_dir / ".salt"
        self._cipher = None

    def _get_or_create_salt(self) -> bytes:
        """Load the per-install random salt, creating it on first run."""
        if self.salt_file.exists():
            try:
                with open(self.salt_file, 'rb') as f:
                    salt = f.read()
                if len(salt) == 32:
                    return salt
                logger.warning("Salt file has unexpected length; regenerating.")
            except (IOError, OSError) as e:
                logger.warning(f"Failed to read salt file: {e}")

        salt = os.urandom(32)
        try:
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            harden_file_permissions(self.salt_file, 0o600)
        except Exception as e:
            raise RuntimeError(f"Failed to save encryption salt: {e}")
        return salt

    def _generate_key(self) -> bytes:
        """Generate a new encryption key derived from machine-specific data."""
        try:
            import socket
            import getpass
            machine_id = f"{socket.gethostname()}-{getpass.getuser()}".encode()
        except Exception as e:
            logger.warning(f"Failed to get machine ID, using random: {e}")
            machine_id = os.urandom(32)

        salt = self._get_or_create_salt()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id))
        return key

    def _get_or_create_key(self) -> bytes:
        """Get existing key or create a new one.

        Fix #19: validate the key after loading so a truncated or corrupted
        .key file is detected here with a clear error, not later as a cryptic
        Fernet/binascii exception.
        """
        if self.key_file.exists():
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read().strip()
                # Validate: a Fernet key must be exactly 44 URL-safe base64 chars
                if len(key) == _FERNET_KEY_LENGTH:
                    try:
                        Fernet(key)  # raises ValueError if malformed
                        return key
                    except ValueError:
                        pass
                logger.warning(
                    "Key file is malformed or wrong length; regenerating. "
                    "Previously encrypted credentials will become unreadable — "
                    "you may need to run 'tgdl login' again."
                )
            except (IOError, OSError) as e:
                logger.warning(f"Failed to read key file: {e}")

        logger.info(
            "Generating new encryption key. If you had previously saved "
            "credentials, run 'tgdl login' to re-authenticate."
        )
        key = self._generate_key()
        try:
            with open(self.key_file, 'wb') as f:
                f.write(key)
            harden_file_permissions(self.key_file, 0o600)
        except Exception as e:
            raise RuntimeError(f"Failed to save encryption key: {e}")

        return key

    def _get_cipher(self) -> Fernet:
        """Get Fernet cipher instance."""
        if self._cipher is None:
            key = self._get_or_create_key()
            self._cipher = Fernet(key)
        return self._cipher

    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data.

        Fix #11: Fernet.encrypt() already returns URL-safe base64 bytes.
        The previous code wrapped it in a second base64.urlsafe_b64encode()
        call, producing double-encoded output.  We now just decode the Fernet
        bytes directly to a string.

        Args:
            data: Plain text data to encrypt

        Returns:
            Fernet-encrypted string (URL-safe base64, single-encoded)
        """
        if not data:
            return ""
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(data.encode('utf-8'))
        # Fernet output is already URL-safe base64 — just decode to str
        return encrypted.decode('utf-8')

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """
        Decrypt encrypted data.

        Fix #12: matching the encrypt() fix — we no longer base64-decode the
        input before handing it to Fernet, since Fernet expects its own
        base64-encoded token directly.

        Args:
            encrypted_data: Fernet token string returned by encrypt()

        Returns:
            Decrypted plain text or None if decryption fails
        """
        if not encrypted_data:
            return None
        try:
            cipher = self._get_cipher()
            decrypted = cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except InvalidToken:
            # Wrong/rotated key or tampered/corrupted ciphertext.
            logger.debug("Decryption failed: invalid token (wrong key or corrupted data)")
            return None
        except (ValueError, TypeError) as e:
            # Malformed base64/UTF-8 input rather than a cryptographic failure.
            logger.debug(f"Decryption failed: malformed input ({type(e).__name__})")
            return None

    def encrypt_credentials(self, api_id: int, api_hash: str) -> Tuple[str, str]:
        """
        Encrypt API credentials.

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash

        Returns:
            Tuple of (encrypted_api_id, encrypted_api_hash)
        """
        encrypted_id = self.encrypt(str(api_id))
        encrypted_hash = self.encrypt(api_hash)
        return encrypted_id, encrypted_hash

    def decrypt_credentials(self, encrypted_id: str, encrypted_hash: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Decrypt API credentials.

        Args:
            encrypted_id: Encrypted API ID string
            encrypted_hash: Encrypted API hash string

        Returns:
            Tuple of (api_id, api_hash) or (None, None) if decryption fails
        """
        try:
            decrypted_id = self.decrypt(encrypted_id)
            decrypted_hash = self.decrypt(encrypted_hash)
            if decrypted_id and decrypted_hash:
                return int(decrypted_id), decrypted_hash
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to decrypt credentials: {e}")
        return None, None
