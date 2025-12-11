"""Cryptography utilities for secure credential storage."""

import os
import base64
from pathlib import Path
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialEncryption:
    """Handle encryption/decryption of sensitive credentials."""
    
    def __init__(self, config_dir: Path):
        """
        Initialize encryption handler.
        
        Args:
            config_dir: Directory to store encryption key
        """
        self.config_dir = config_dir
        self.key_file = config_dir / ".key"
        self._cipher = None
    
    def _generate_key(self) -> bytes:
        """Generate a new encryption key based on machine-specific data."""
        # Use machine-specific data as salt (hostname + user)
        try:
            import socket
            import getpass
            machine_id = f"{socket.gethostname()}-{getpass.getuser()}".encode()
        except Exception:
            # Fallback to random if machine ID fails
            machine_id = os.urandom(32)
        
        # Derive key from machine ID using PBKDF2-HMAC
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'tgdl-secure-storage-v1',  # Fixed salt for consistency
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(machine_id))
        return key
    
    def _get_or_create_key(self) -> bytes:
        """Get existing key or create new one."""
        if self.key_file.exists():
            try:
                with open(self.key_file, 'rb') as f:
                    return f.read()
            except (IOError, OSError):
                pass
        
        # Generate new key
        key = self._generate_key()
        
        # Save key with restricted permissions
        try:
            # Write key
            with open(self.key_file, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions (owner read/write only)
            if os.name != 'nt':  # Unix-like systems
                os.chmod(self.key_file, 0o600)
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
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Base64-encoded encrypted data
        """
        if not data:
            return ""
        
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """
        Decrypt encrypted data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted plain text or None if decryption fails
        """
        if not encrypted_data:
            return None
        
        try:
            cipher = self._get_cipher()
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = cipher.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception:
            # Decryption failed (corrupted data or wrong key)
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
            encrypted_id: Encrypted API ID
            encrypted_hash: Encrypted API hash
            
        Returns:
            Tuple of (api_id, api_hash) or (None, None) if decryption fails
        """
        try:
            decrypted_id = self.decrypt(encrypted_id)
            decrypted_hash = self.decrypt(encrypted_hash)
            
            if decrypted_id and decrypted_hash:
                return int(decrypted_id), decrypted_hash
        except (ValueError, TypeError):
            pass
        
        return None, None
