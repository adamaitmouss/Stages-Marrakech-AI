import json
import os
import secrets
import threading
from pathlib import Path
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash

_setup_lock = threading.Lock()


class Vault:
    """Profil CV chiffré au repos ; clé locale séparée, jamais servie par HTTP."""
    def __init__(self, directory):
        self.path = Path(directory)
        self.path.mkdir(parents=True, exist_ok=True)
        key_file = self.path / 'cv.key'
        if not key_file.exists():
            try:
                with key_file.open('xb') as stream:
                    stream.write(Fernet.generate_key())
            except FileExistsError:
                pass
        self.fernet = Fernet(key_file.read_bytes())
        secret_file = self.path / 'session.key'
        if not secret_file.exists():
            try:
                with secret_file.open('xb') as stream:
                    stream.write(secrets.token_bytes(32))
            except FileExistsError:
                pass
        self.session_key = secret_file.read_bytes()
        for f in self.path.iterdir():
            try:
                os.chmod(f, 0o600)
            except OSError:
                pass

    def encrypt(self, data):
        return self.fernet.encrypt(json.dumps(data, ensure_ascii=False).encode())

    def decrypt(self, data):
        return json.loads(self.fernet.decrypt(data))

    @property
    def configured(self):
        return (self.path / 'auth.json').exists()

    def setup(self, password):
        if not isinstance(password, str) or len(password) < 12 or len(password) > 256:
            raise ValueError('Choisissez un mot de passe de 12 à 256 caractères.')
        with _setup_lock:
            with (self.path / 'auth.json').open('x', encoding='utf-8') as f:
                json.dump({'password_hash': generate_password_hash(password)}, f)

    def login(self, password):
        if not self.configured or not isinstance(password, str):
            return False
        auth = json.loads((self.path / 'auth.json').read_text())
        return check_password_hash(auth['password_hash'], password)
