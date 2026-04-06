import logging
import os
import warnings

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    warnings.warn(
        "ENCRYPTION_KEY not set! Generating temporary key. Set in .env for production."
    )
    ENCRYPTION_KEY = Fernet.generate_key().decode()

_fernet = Fernet(
    ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
)


def encrypt_token(token: str) -> str:
    return _fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    return _fernet.decrypt(encrypted_token.encode()).decode()
