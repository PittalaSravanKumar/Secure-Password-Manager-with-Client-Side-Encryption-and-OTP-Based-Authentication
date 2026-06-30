from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import base64

def hchacha20(key: bytes, nonce: bytes) -> bytes:
    constants = b"expand 32-byte k"
    def bytes_to_words(b):
        return [int.from_bytes(b[i:i+4], 'little') for i in range(0, len(b), 4)]
    def words_to_bytes(words):
        return b''.join(w.to_bytes(4, 'little') for w in words)
    def rotl32(v, c):
        return ((v << c) & 0xffffffff) | (v >> (32 - c))
    def quarter_round(x, a, b, c, d):
        x[a] = (x[a] + x[b]) & 0xffffffff
        x[d] ^= x[a]
        x[d] = rotl32(x[d], 16)
        x[c] = (x[c] + x[d]) & 0xffffffff
        x[b] ^= x[c]
        x[b] = rotl32(x[b], 12)
        x[a] = (x[a] + x[b]) & 0xffffffff
        x[d] ^= x[a]
        x[d] = rotl32(x[d], 8)
        x[c] = (x[c] + x[d]) & 0xffffffff
        x[b] ^= x[c]
        x[b] = rotl32(x[b], 7)
    state = (bytes_to_words(constants) + bytes_to_words(key) + bytes_to_words(nonce))
    for _ in range(10):
        quarter_round(state, 0, 4, 8, 12)
        quarter_round(state, 1, 5, 9, 13)
        quarter_round(state, 2, 6, 10, 14)
        quarter_round(state, 3, 7, 11, 15)
        quarter_round(state, 0, 5, 10, 15)
        quarter_round(state, 1, 6, 11, 12)
        quarter_round(state, 2, 7, 8, 13)
        quarter_round(state, 3, 4, 9, 14)
    return words_to_bytes(state[0:4] + state[12:16])

def decrypt(ciphertext: str, key: str) -> str:
    key_bytes = key.encode('utf-8').ljust(32, b'\0')[:32]
    data = base64.b64decode(ciphertext)
    nonce = data[:24]
    ciphertext_bytes = data[24:]
    subkey = hchacha20(key_bytes, nonce[:16])
    chacha_nonce = b'\x00\x00\x00\x00' + nonce[16:]
    chacha = ChaCha20Poly1305(subkey)
    return chacha.decrypt(chacha_nonce, ciphertext_bytes, None).decode('utf-8')