from __future__ import annotations

import base64
import hashlib
import hmac
import os

SCRYPT_N = 1 << 14
SCRYPT_R = 8
SCRYPT_P = 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32)
    return '$'.join(('scrypt', str(SCRYPT_N), str(SCRYPT_R), str(SCRYPT_P),
                     base64.urlsafe_b64encode(salt).decode('ascii'),
                     base64.urlsafe_b64encode(digest).decode('ascii')))


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_text, digest_text = encoded.split('$', 5)
        if scheme != 'scrypt':
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode('ascii'))
        expected = base64.urlsafe_b64decode(digest_text.encode('ascii'))
        actual = hashlib.scrypt(password.encode('utf-8'), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def valid_password(password: str) -> bool:
    if not isinstance(password, str) or not (12 <= len(password) <= 128) or len(password.encode('utf-8')) > 256:
        return False
    return any(ch.isalpha() for ch in password) and any(ch.isdigit() for ch in password)
