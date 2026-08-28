import os
import json
import hmac
import hashlib
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


APP_SALT = b"localchat_v1_salt_2024"


def derive_key(room_code: str) -> bytes:
    """
    Turns room code like "482901" into a 256 bit AES key.
    Every peer with same room code gets identical key.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,            # 256 bit key
        salt=APP_SALT,
        iterations=10_000,   # slow enough to resist brute force
    )
    return kdf.derive(room_code.upper().encode())


def hash_room_code(room_code: str) -> str:
    """
    One way hash of room code for HELLO discovery packets.
    Peers verify they are in same room without exposing actual code.
    """
    h = hmac.new(APP_SALT, room_code.upper().encode(), hashlib.sha256)
    return h.hexdigest()[:16]


def encrypt_message(payload: dict, key: bytes) -> str:
    """
    Encrypts a dict with AES-GCM.
    Returns base64 string safe to put inside JSON.
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)       # random 12 bytes, unique per message
    plaintext = json.dumps(payload).encode()
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt_message(encrypted_b64: str, key: bytes) -> dict | None:
    """
    Decrypts a base64 AES-GCM payload back to dict.
    Returns None if decryption fails — wrong key or tampered packet.
    """
    try:
        raw = base64.b64decode(encrypted_b64)
        nonce = raw[:12]
        ciphertext = raw[12:]
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(plaintext.decode())
    except Exception:
        return None 
