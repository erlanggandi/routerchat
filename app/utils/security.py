import base64
import hashlib
from cryptography.fernet import Fernet
from config.settings import settings


def _get_fernet_key(secret: str) -> bytes:
    """Generate 32 url-safe base64-encoded bytes from any secret key string."""
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(plain_text: str) -> str:
    """Encrypt a secret string (e.g. router password)."""
    if not plain_text:
        return ""
    fernet = Fernet(_get_fernet_key(settings.SECRET_KEY))
    encrypted = fernet.encrypt(plain_text.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_secret(encrypted_text: str) -> str:
    """Decrypt an encrypted secret string."""
    if not encrypted_text:
        return ""
    try:
        fernet = Fernet(_get_fernet_key(settings.SECRET_KEY))
        decrypted = fernet.decrypt(encrypted_text.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception:
        # If decryption fails (e.g. key changed or plain text stored before), fallback safely
        return encrypted_text
