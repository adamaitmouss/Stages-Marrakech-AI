from __future__ import annotations

import os
import socket
import sqlite3
import sys
import tempfile
import shutil
import secrets
import threading
import time
from pathlib import Path

import requests
from werkzeug.serving import WSGIRequestHandler, make_server

from .config import AUTH_ROOT, _read_env_file, load_config


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


def port_free(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('127.0.0.1', port))
        return True
    except OSError:
        return False


def ensure_internal_secret() -> str:
    """Create a random shared secret in the ignored local-private directory."""
    configured = os.environ.get('AUTH_INTERNAL_SECRET_FILE', '').strip()
    secret_path = Path(configured).expanduser() if configured else Path(__file__).resolve().parents[1] / 'private' / 'auth_gateway_internal.secret'
    secret_path = secret_path.resolve()
    secret_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(str(secret_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        secret = secret_path.read_text(encoding='ascii').strip()
    else:
        secret = secrets.token_urlsafe(64)
        with os.fdopen(descriptor, 'w', encoding='ascii') as stream:
            stream.write(secret + '\n')
    if len(secret) < 48:
        raise RuntimeError('Le secret interne local est absent ou invalide.')
    os.environ['AUTH_INTERNAL_SECRET'] = secret
    return str(secret_path)


def check_database(cfg: dict) -> dict:
    root = Path(cfg['ROOT'])
    db_path = Path(cfg['AUTH_APP_DATABASE']).expanduser()
    if not db_path.is_absolute():
        db_path = root / db_path
    db_path = db_path.resolve()
    if not db_path.is_file():
        raise RuntimeError(f'Base de données configurée introuvable : {db_path}')
    with sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True, timeout=5) as db:
        integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {'entreprises', 'offres', 'candidatures'}
        if not required.issubset(tables):
            raise RuntimeError('La base configurée ne possède pas le schéma Stages Marrakech attendu.')
        counts = {name: db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in sorted(required)}
        company_columns = {row[1].casefold(): row[1] for row in db.execute('PRAGMA table_info(entreprises)')}
        email_column = next((company_columns[name] for name in ('email', 'emails', 'courriel', 'e-mail')
                             if name in company_columns), None)
        email_count = None
        if email_column is not None:
            quoted_email_column = email_column.replace('"', '""')
            email_count = db.execute(
                f'SELECT COUNT(*) FROM entreprises WHERE trim(COALESCE("{quoted_email_column}", "")) <> ""'
            ).fetchone()[0]
        foreign_keys = len(db.execute('PRAGMA foreign_key_check').fetchall())
        marker = None
        if 'deployment_metadata' in tables:
            row = db.execute("SELECT value FROM deployment_metadata WHERE key='dataset_type'").fetchone()
            marker = row[0] if row else None
    if integrity != 'ok' or foreign_keys:
        raise RuntimeError('La base SQLite n’est pas intègre; aucun serveur n’a été lancé.')
    if cfg['AUTH_PROFILE'] == 'demo' and marker != 'synthetic_public_demo':
        raise RuntimeError('Le profil inscription exige le marqueur synthétique public exact; base historique refusée.')
    if cfg['AUTH_PROFILE'] in {'private', 'multi_user'} and marker == 'synthetic_public_demo':
        raise RuntimeError('Le profil privé ne peut pas démarrer sur la base synthétique.')
    return {'path': db_path, 'integrity': integrity, 'counts': counts,
            'email_count': email_count, 'marker': marker}


def run_gateway_only():
    ensure_internal_secret()
    cfg = load_config()
    if not (AUTH_ROOT / '.env.auth').is_file() and cfg['AUTH_ENV'] != 'production':
        raise SystemExit('Configuration absente : copiez .env.auth.example vers auth_gateway/.env.auth puis modifiez-la.')
    server = make_server('127.0.0.1', cfg['AUTH_GATEWAY_PORT'], __import__('auth_gateway.app', fromlist=['create_app']).create_app(),
                         threaded=True, request_handler=QuietHandler)
    print(f"Passerelle active sur http://127.0.0.1:{cfg['AUTH_GATEWAY_PORT']} (Ctrl+C pour arrêter).", flush=True)
    server.serve_forever()


def main() -> int:
    if str(Path(__file__).resolve().parents[1]) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    config_file = Path(os.environ.get('AUTH_CONFIG_FILE', AUTH_ROOT / '.env.auth')).expanduser()
    _read_env_file(config_file)
    try:
        secret_path = ensure_internal_secret()
    except (OSError, RuntimeError) as exc:
        print(f'ERREUR de préparation du canal local privé : {exc}', flush=True)
        return 5
    cfg = load_config()
    if not (AUTH_ROOT / '.env.auth').is_file():
        print('ERREUR : configuration absente. Le script Windows la prépare depuis .env.auth.example; relancez-le.', flush=True)
        return 2
    db_check = check_database(cfg)
    for port, name in ((cfg['AUTH_GATEWAY_PORT'], 'passerelle'), (cfg['AUTH_BACKEND_PORT'], 'backend')):
        if not port_free(port):
            print(f'ERREUR : port {port} ({name}) déjà occupé. Aucun processus n’a été arrêté et aucun serveur n’a été repris.', flush=True)
            return 3

    scratch = tempfile.TemporaryDirectory(prefix='stages-auth-demo-') if cfg['AUTH_PROFILE'] == 'demo' else None
    backend_database = db_check['path']
    if scratch is not None:
        backend_database = Path(scratch.name) / 'stages_marrakech_public_demo.db'
        shutil.copy2(db_check['path'], backend_database)
    cfg['AUTH_BACKEND_URL'] = f"http://127.0.0.1:{cfg['AUTH_BACKEND_PORT']}"
    os.environ['AUTH_BACKEND_URL'] = cfg['AUTH_BACKEND_URL']
    os.environ['DATABASE'] = str(backend_database)
    os.environ['PRIVATE_DIR'] = str((Path(scratch.name) / 'private') if scratch is not None else Path(cfg['ROOT']) / 'private')
    os.environ['BACKUP_DIR'] = str((Path(scratch.name) / 'backups') if scratch is not None else Path(AUTH_ROOT) / 'data' / 'backups')
    os.environ['PUBLIC_DEMO_MODE'] = 'true' if cfg['AUTH_PROFILE'] == 'demo' else 'false'
    os.environ['PUBLIC_DEMO_DATA_CONFIRMED'] = 'true' if cfg['AUTH_PROFILE'] == 'demo' else 'false'
    os.environ['AUTH_MULTI_USER_MODE'] = 'true' if cfg['AUTH_PROFILE'] == 'multi_user' else 'false'
    os.environ['AUTH_USER_DATA_ROOT'] = str((Path(cfg['ROOT']) / cfg['AUTH_USER_DATA_ROOT']).resolve()
                                              if not Path(cfg['AUTH_USER_DATA_ROOT']).is_absolute()
                                              else Path(cfg['AUTH_USER_DATA_ROOT']).resolve())
    if cfg['AUTH_PROFILE'] == 'multi_user':
        os.environ['DISABLE_BACKGROUND_SCHEDULER'] = 'true'
    os.environ['TRUST_PROXY'] = 'false'
    os.environ['COOKIE_SECURE'] = 'false'
    os.environ['SMTP_ENABLED'] = 'false'
    os.environ['GEMINI_ENABLED'] = 'false'
    os.environ['GEMINI_SEARCH_ENABLED'] = 'false'
    os.environ['MAPS_ENABLED'] = 'false'
    sys.path.insert(0, str(cfg['ROOT']))
    from backend.web import create_app as create_backend
    from .app import create_app as create_gateway

    backend_server = None
    try:
        backend_app = create_backend()
        backend_server = make_server('127.0.0.1', cfg['AUTH_BACKEND_PORT'], backend_app,
                                     threaded=True, request_handler=QuietHandler)
        thread = threading.Thread(target=backend_server.serve_forever, daemon=True)
        thread.start()
        health_url = cfg['AUTH_BACKEND_URL'] + '/health'
        health_client = requests.Session()
        health_client.trust_env = False
        last_health = 'aucune réponse'
        for _ in range(50):
            try:
                health_response = health_client.get(health_url, timeout=1)
                last_health = f'HTTP {health_response.status_code}'
                if health_response.status_code == 200:
                    break
            except requests.RequestException:
                last_health = 'connexion refusée ou délai dépassé'
                time.sleep(.1)
        else:
            raise RuntimeError(f'Le backend local ne répond pas sur son port privé ({last_health}).')
        gateway_app = create_gateway()
        gateway_server = make_server('127.0.0.1', cfg['AUTH_GATEWAY_PORT'], gateway_app,
                                     threaded=True, request_handler=QuietHandler)
        if scratch is not None:
            print('La source synthétique a été copiée dans un dossier temporaire; elle sera supprimée à l’arrêt.', flush=True)
        print(f"Profil : {cfg['AUTH_PROFILE']}", flush=True)
        print(f"Canal local privé configuré automatiquement ({secret_path}).", flush=True)
        print(f"SQLite utilisée : {db_check['path']}", flush=True)
        counts = db_check['counts']
        print(f"Compteurs réels : entreprises={counts['entreprises']}, offres={counts['offres']}, candidatures={counts['candidatures']}.", flush=True)
        if db_check['email_count'] is not None:
            print(f"Entreprises avec une adresse email renseignée : {db_check['email_count']}.", flush=True)
        print(f"Passerelle Login : http://127.0.0.1:{cfg['AUTH_GATEWAY_PORT']} | backend privé : 127.0.0.1:{cfg['AUTH_BACKEND_PORT']}.", flush=True)
        print('Gemini, collecte externe, SMTP et Maps sont désactivés pour ce lancement.', flush=True)
        print('Ctrl+C arrête uniquement les deux serveurs lancés par cette fenêtre.', flush=True)
        gateway_server.serve_forever()
    except KeyboardInterrupt:
        print('\nArrêt demandé; arrêt des deux serveurs lancés ici.', flush=True)
    except Exception as exc:
        detail = str(exc).replace(cfg['AUTH_BACKEND_URL'], '[backend local]')
        print(f'ERREUR de démarrage : {type(exc).__name__}: {detail[:260]}. Aucun processus externe n’a été terminé.', flush=True)
        return 4
    finally:
        if backend_server is not None:
            backend_server.shutdown()
            backend_server.server_close()
        if scratch is not None:
            scratch.cleanup()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
