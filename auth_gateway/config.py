from __future__ import annotations

import os
import ipaddress
import secrets
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
AUTH_ROOT = Path(__file__).resolve().parent


def _read_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key.replace('_', '').isalnum():
            os.environ.setdefault(key, value)


def _session_secret() -> str:
    value = os.environ.get('AUTH_SESSION_SECRET', '').strip()
    production = os.environ.get('AUTH_ENV', 'local').lower() == 'production'
    if value and value.lower() != 'auto':
        if len(value) < 32:
            raise RuntimeError('AUTH_SESSION_SECRET doit contenir au moins 32 caractères.')
        return value
    if production:
        raise RuntimeError('En production, fournissez AUTH_SESSION_SECRET via le gestionnaire de secrets.')
    secret_file = AUTH_ROOT / 'data' / 'session.secret'
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    if secret_file.exists():
        value = secret_file.read_text(encoding='ascii').strip()
    else:
        value = secrets.token_urlsafe(48)
        secret_file.write_text(value, encoding='ascii')
    if len(value) < 32:
        raise RuntimeError('Le secret local de session est invalide.')
    return value


def load_config() -> dict:
    env_path = Path(os.environ.get('AUTH_CONFIG_FILE', AUTH_ROOT / '.env.auth')).expanduser()
    _read_env_file(env_path)
    profile = os.environ.get('AUTH_PROFILE', 'demo').strip().lower()
    if profile not in {'demo', 'private', 'multi_user'}:
        raise RuntimeError('AUTH_PROFILE accepte demo, private ou multi_user.')
    db_url = os.environ.get('AUTH_DATABASE_URL', 'sqlite:///auth_gateway/data/auth_users.db').strip()
    backend_port = int(os.environ.get('AUTH_BACKEND_PORT', '5101'))
    backend_url = os.environ.get('AUTH_BACKEND_URL', f'http://127.0.0.1:{backend_port}').rstrip('/')
    parsed = urlparse(backend_url)
    if parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        if os.environ.get('AUTH_TRUSTED_PRIVATE_BACKEND', '').lower() != 'true':
            raise RuntimeError('Le backend distant doit être un service privé explicitement approuvé; un backend public est refusé.')
    if os.environ.get('AUTH_ENV', 'local').lower() == 'production' and parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        host = (parsed.hostname or '').lower().rstrip('.')
        try:
            address = ipaddress.ip_address(host)
            private_host = address.is_private or address.is_loopback or address.is_link_local
        except ValueError:
            private_host = '.' not in host or host.endswith(('.internal', '.local', '.localhost', '.private'))
        if not private_host:
            raise RuntimeError('Backend refusé : en production, utilisez une adresse privée/interne et une règle réseau qui interdit son accès Internet.')
    allow_registration = os.environ.get('AUTH_ALLOW_REGISTRATION', 'true' if profile == 'multi_user' else 'false').lower() == 'true'
    if profile != 'multi_user' and allow_registration:
        raise RuntimeError('L’inscription générale exige le profil multi_user et des bases isolées par compte.')
    if profile == 'multi_user' and os.environ.get('AUTH_ENV', 'local').lower() != 'local':
        raise RuntimeError('Le profil multi_user est réservé au lancement local avec stockage durable isolé.')
    if profile == 'multi_user' and not allow_registration:
        raise RuntimeError('Le profil multi_user exige AUTH_ALLOW_REGISTRATION=true et des espaces SQLite isolés.')
    if profile == 'private' and not os.environ.get('AUTH_ADMIN_EMAIL', '').strip():
        raise RuntimeError('AUTH_ADMIN_EMAIL est requis pour le profil privé à administrateur unique.')
    port = int(os.environ.get('AUTH_GATEWAY_PORT', '5000'))
    if not (1 <= port <= 65535 and 1 <= backend_port <= 65535 and port != backend_port):
        raise RuntimeError('Les ports de la passerelle et du backend sont invalides ou identiques.')
    ttl = int(os.environ.get('AUTH_SESSION_TTL_SECONDS', '28800'))
    attempts = int(os.environ.get('AUTH_MAX_LOGIN_ATTEMPTS', '5'))
    login_window = int(os.environ.get('AUTH_LOGIN_WINDOW_SECONDS', '900'))
    if not (300 <= ttl <= 86400 and 1 <= attempts <= 20 and 60 <= login_window <= 86400):
        raise RuntimeError('La durée de session ou les limites de connexion sont hors des bornes sûres.')
    cookie_secure = os.environ.get('AUTH_COOKIE_SECURE', 'false').lower() == 'true'
    allowed_hosts = tuple(host.strip().lower() for host in os.environ.get('AUTH_ALLOWED_HOSTS', '').split(',') if host.strip())
    proxy_hops = int(os.environ.get('AUTH_TRUSTED_PROXY_HOPS', '0'))
    if os.environ.get('AUTH_ENV', 'local').lower() == 'production':
        if not cookie_secure:
            raise RuntimeError('AUTH_COOKIE_SECURE=true est obligatoire en production sous HTTPS.')
        if db_url.startswith('sqlite:'):
            raise RuntimeError('SQLite locale/éphémère est refusée en production; configurez PostgreSQL persistant.')
        if db_url.startswith(('postgresql://', 'postgres://')):
            sslmode = parse_qs(urlparse(db_url).query).get('sslmode', [''])[0].lower()
            if sslmode not in {'require', 'verify-ca', 'verify-full'}:
                raise RuntimeError('PostgreSQL de production exige sslmode=require ou une validation de certificat.')
        if proxy_hops < 1 or not allowed_hosts:
            raise RuntimeError('Production exige AUTH_TRUSTED_PROXY_HOPS et une liste AUTH_ALLOWED_HOSTS explicite.')
    return {
        'ROOT': ROOT,
        'AUTH_ENV': os.environ.get('AUTH_ENV', 'local').lower(),
        'AUTH_PROFILE': profile,
        'AUTH_DATABASE_URL': db_url,
        'AUTH_BACKEND_URL': backend_url,
        'AUTH_BACKEND_PORT': backend_port,
        'AUTH_APP_DATABASE': os.environ.get('AUTH_APP_DATABASE',
            'database/stages_marrakech_public_demo.db' if profile == 'demo' else 'database/stages_marrakech.db'),
        'AUTH_USER_DATA_ROOT': os.environ.get('AUTH_USER_DATA_ROOT', str(ROOT / 'private' / 'user_data')),
        'AUTH_GATEWAY_PORT': port,
        'AUTH_INTERNAL_SECRET': os.environ.get('AUTH_INTERNAL_SECRET', ''),
        'AUTH_ALLOW_REGISTRATION': allow_registration,
        'AUTH_ADMIN_EMAIL': os.environ.get('AUTH_ADMIN_EMAIL', '').strip().casefold(),
        'AUTH_BOOTSTRAP_ADMIN_PASSWORD': os.environ.get('AUTH_BOOTSTRAP_ADMIN_PASSWORD', ''),
        'AUTH_SESSION_SECRET': _session_secret(),
        'AUTH_SESSION_TTL_SECONDS': ttl,
        'AUTH_COOKIE_SECURE': cookie_secure,
        'AUTH_ALLOWED_HOSTS': allowed_hosts,
        'AUTH_TRUSTED_PROXY_HOPS': proxy_hops,
        'AUTH_MAX_LOGIN_ATTEMPTS': attempts,
        'AUTH_LOGIN_WINDOW_SECONDS': login_window,
        'AUTH_MAX_CONTENT_LENGTH': 1024 * 1024,
        'TESTING': os.environ.get('AUTH_TESTING', 'false').lower() == 'true',
    }
