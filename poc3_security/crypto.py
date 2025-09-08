
from cryptography.fernet import Fernet
import os

KEY_FILE = os.getenv("CRYPTO_KEY_FILE", ".devkey")

def load_key():
    if not os.path.exists(KEY_FILE):
        with open(KEY_FILE, "wb") as f: f.write(Fernet.generate_key())
    with open(KEY_FILE, "rb") as f: return f.read()

FERNET = Fernet(load_key())

def encrypt_field(plain: str) -> str:
    return FERNET.encrypt(plain.encode()).decode()

def decrypt_field(cipher: str) -> str:
    return FERNET.decrypt(cipher.encode()).decode()
