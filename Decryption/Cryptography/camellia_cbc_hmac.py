from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import base64
import hashlib


def encrypt(plaintext: str, key: str) -> str:
    key_bytes = key.encode('utf-8').ljust(32, b'\0')[:32]
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
    algorithm = algorithms.Camellia(key_bytes)
    cipher = Cipher(algorithm, modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    hmac_key = hashlib.sha256(key_bytes + b'hmac').digest()
    hmac_value = hashlib.sha256(hmac_key + iv + ciphertext).digest()
    return base64.b64encode(iv + ciphertext + hmac_value).decode('utf-8')


def decrypt(ciphertext_b64: str, key: str) -> str:
    key_bytes = key.encode('utf-8').ljust(32, b'\0')[:32]
    data = base64.b64decode(ciphertext_b64)
    iv = data[:16]
    hmac_value = data[-32:]
    ciphertext = data[16:-32]
    hmac_key = hashlib.sha256(key_bytes + b'hmac').digest()
    expected_hmac = hashlib.sha256(hmac_key + iv + ciphertext).digest()
    if hmac_value != expected_hmac:
        raise ValueError("HMAC verification failed")
    algorithm = algorithms.Camellia(key_bytes)
    cipher = Cipher(algorithm, modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    return plaintext.decode('utf-8')