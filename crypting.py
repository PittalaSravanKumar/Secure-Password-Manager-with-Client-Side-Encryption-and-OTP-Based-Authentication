import sys
sys.path.append('Encryption')
sys.path.append('Decryption')
sys.path.append('Cryptography')

from aes_ctr_encrypt import encrypt as aes_ctr_enc
from aes_gcm_encrypt import encrypt as aes_gcm_enc
from camellia_encrypt import encrypt as camellia_enc
from chacha20_encrypt import encrypt as chacha20_enc
from salsa20_encrypt import encrypt as salsa20_enc
from xchacha20_encrypt import encrypt as xchacha20_enc

from aes_ctr_decrypt import decrypt as aes_ctr_dec
from aes_gcm_decrypt import decrypt as aes_gcm_dec
from camellia_decrypt import decrypt as camellia_dec
from chacha20_decrypt import decrypt as chacha20_dec
from salsa20_decrypt import decrypt as salsa20_dec
from xchacha20_decrypt import decrypt as xchacha20_dec

import aes_ctr_hmac
import aes_gcm
import camellia_cbc_hmac
import chacha20_poly1305
import xchacha20_poly1305


def char_to_number(char: str) -> int:
    char_upper = char.upper()
    if 'A' <= char_upper <= 'Z':
        return ord(char_upper) - ord('A') + 1
    else:
        return ord(char)


def get_algorithm_remainder(email: str, modulo: int) -> int:
    total = 0
    for i in range(0, len(email), 2):
        total += char_to_number(email[i])
    return total % modulo


def extract_key(email: str, key_length: int) -> str:
    if key_length == 6:
        remainder = get_algorithm_remainder(email, 6)
    else:
        remainder = get_algorithm_remainder(email, 5)
    
    key = []
    email_len = len(email)
    current_pos = remainder
    
    while len(key) < key_length:
        key.append(email[current_pos % email_len])
        current_pos += 2
    
    return ''.join(key)


def encrypt_with_email_6char(email: str, password: str) -> str:
    remainder = get_algorithm_remainder(email, 6)
    key = extract_key(email, 6)
    password = password.ljust(6, '0')[:6]
    
    if remainder == 0:
        return aes_ctr_enc(password, key)
    elif remainder == 1:
        return camellia_enc(password, key)
    elif remainder == 2:
        return aes_gcm_enc(password, key)
    elif remainder == 3:
        return xchacha20_enc(password, key)
    elif remainder == 4:
        return chacha20_enc(password, key)
    else:
        return salsa20_enc(password, key)


def decrypt_with_email_6char(email: str, ciphertext: str) -> str:
    remainder = get_algorithm_remainder(email, 6)
    key = extract_key(email, 6)
    
    if remainder == 0:
        return aes_ctr_dec(ciphertext, key)
    elif remainder == 1:
        return camellia_dec(ciphertext, key)
    elif remainder == 2:
        return aes_gcm_dec(ciphertext, key)
    elif remainder == 3:
        return xchacha20_dec(ciphertext, key)
    elif remainder == 4:
        return chacha20_dec(ciphertext, key)
    else:
        return salsa20_dec(ciphertext, key)


def encrypt_with_email_8char(email: str, password: str) -> str:
    remainder = get_algorithm_remainder(email, 5)
    key = extract_key(email, 8)
    password_normalized = password.ljust(8, '0')[:8]
    
    if remainder == 0:
        return aes_ctr_hmac.encrypt(password_normalized, key)
    elif remainder == 1:
        return camellia_cbc_hmac.encrypt(password_normalized, key)
    elif remainder == 2:
        return aes_gcm.encrypt(password_normalized, key)
    elif remainder == 3:
        return xchacha20_poly1305.encrypt(password_normalized, key)
    else:
        return chacha20_poly1305.encrypt(password_normalized, key)


def decrypt_with_email_8char(email: str, ciphertext: str) -> str:
    remainder = get_algorithm_remainder(email, 5)
    key = extract_key(email, 8)
    
    if remainder == 0:
        return aes_ctr_hmac.decrypt(ciphertext, key)
    elif remainder == 1:
        return camellia_cbc_hmac.decrypt(ciphertext, key)
    elif remainder == 2:
        return aes_gcm.decrypt(ciphertext, key)
    elif remainder == 3:
        return xchacha20_poly1305.decrypt(ciphertext, key)
    else:
        return chacha20_poly1305.decrypt(ciphertext, key)