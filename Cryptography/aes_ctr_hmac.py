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


def decrypt(ciphertext_b64: str, key: str) -> str:
    key_bytes = key.encode('utf-8').ljust(32, b'\0')[:32]
    data = base64.b64decode(ciphertext_b64)
    nonce = data[:16]
    hmac_value = data[-32:]
    ciphertext = data[16:-32]
    hmac_key = hashlib.sha256(key_bytes + b'hmac').digest()
    expected_hmac = hashlib.sha256(hmac_key + nonce + ciphertext).digest()
    if hmac_value != expected_hmac:
        raise ValueError("HMAC verification failed")
    algorithm = algorithms.AES(key_bytes)
    cipher = Cipher(algorithm, modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext.decode('utf-8')