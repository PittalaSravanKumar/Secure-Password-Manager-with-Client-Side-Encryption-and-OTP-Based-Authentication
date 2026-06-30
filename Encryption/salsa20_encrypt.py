from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import os
import base64

def encrypt(plaintext: str, key: str) -> str:
    key_bytes = key.encode('utf-8').ljust(32, b'\0')[:32]
    nonce = os.urandom(12)
    chacha = ChaCha20Poly1305(key_bytes)
    ciphertext = chacha.encrypt(nonce, plaintext.encode('utf-8'), None)
    return base64.b64encode(nonce + ciphertext).decode('utf-8')