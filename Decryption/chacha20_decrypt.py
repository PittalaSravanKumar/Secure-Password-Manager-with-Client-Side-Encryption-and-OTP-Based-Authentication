from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import base64

def decrypt(ciphertext: str, key: str) -> str:
    key_bytes = key.encode('utf-8').ljust(32, b'\0')[:32]
    data = base64.b64decode(ciphertext)
    nonce, ciphertext_bytes = data[:12], data[12:]
    chacha = ChaCha20Poly1305(key_bytes)
    return chacha.decrypt(nonce, ciphertext_bytes, None).decode('utf-8')