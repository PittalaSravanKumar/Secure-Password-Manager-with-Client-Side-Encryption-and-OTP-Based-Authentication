from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64
import hashlib

def encrypt(plaintext: str, key: str) -> str:
    key_bytes = key.encode('utf-8').ljust(32, b'\0')[:32]
    nonce = os.urandom(16)
    algorithm = algorithms.AES(key_bytes)
    cipher = Cipher(algorithm, modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()
    hmac_key = hashlib.sha256(key_bytes + b'hmac').digest()
    hmac_value = hashlib.sha256(hmac_key + nonce + ciphertext).digest()
    return base64.b64encode(nonce + ciphertext + hmac_value).decode('utf-8')