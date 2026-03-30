"""
Envelope encryption using Fernet (symmetric authenticated encryption).

Structure is designed so the get_fernet() call can be swapped for a KMS-backed
implementation without changing call sites.
"""

from cryptography.fernet import Fernet

from app.settings import settings


def _get_fernet() -> Fernet:
    key = settings.APP_ENCRYPTION_KEY
    if not key:
        raise RuntimeError("APP_ENCRYPTION_KEY is not configured")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string, returning a URL-safe base64 ciphertext token."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a ciphertext token produced by encrypt()."""
    return _get_fernet().decrypt(ciphertext.encode()).decode()
