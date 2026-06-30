from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import hashlib

def decrypt(ciphertext: str, key: str) -> str:
    key_bytes = key.encode('utf-8').ljust(32, b'\0')[:32]
    data = base64.b64decode(ciphertext)
    nonce = data[:16]
    hmac_received = data[-32:]
    ciphertext_bytes = data[16:-32]
    hmac_key = hashlib.sha256(key_bytes + b'hmac').digest()
    hmac_calculated = hashlib.sha256(hmac_key + nonce + ciphertext_bytes).digest()
    if hmac_received != hmac_calculated:
        raise ValueError("Authentication failed")
    algorithm = algorithms.AES(key_bytes)
    cipher = Cipher(algorithm, modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    return (decryptor.update(ciphertext_bytes) + decryptor.finalize()).decode('utf-8')