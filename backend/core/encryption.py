import hashlib
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Must be set in the environment. No fallback — a dev key would silently weaken all encryption.
SECRET_KEY = os.environ["ENCRYPTION_SECRET_KEY"]

def _get_fernet() -> Fernet:
    """Generates a consistent Fernet instance based on the secret key."""
    # We use PBKDF2 to derive a secure 32-byte key from whatever string is in the env var
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=hashlib.sha256(SECRET_KEY.encode()).digest(),
        iterations=600000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return Fernet(key)

_fernet_instance = _get_fernet()

def encrypt_data(data: str) -> str:
    """Encrypts a string and returns a base64 encoded string."""
    if not data:
        return data
    return _fernet_instance.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str | None:
    """Decrypts a base64 encoded encrypted string."""
    if not encrypted_data:
        return encrypted_data
    try:
        return _fernet_instance.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return None
