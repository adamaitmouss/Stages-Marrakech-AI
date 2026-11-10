"""Vérifications en lecture seule du lancement local privé de soutenance."""
from __future__ import annotations

import importlib.util
import errno
import os
import socket
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_MODULES = ('flask', 'dash', 'plotly', 'pandas', 'reportlab', 'openpyxl', 'requests', 'bs4', 'pypdf', 'cryptography', 'dotenv')


def port_is_available(port: int = 5000, host: str = '127.0.0.1') -> tuple[bool, str]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((host, port))
        return True, f'{host}:{port} libre'
    except OSError as exc:
        code = getattr(exc, 'winerror', None) or exc.errno
        if code in (errno.EADDRINUSE, 10048):
            return False, f'{host}:{port} est déjà occupé'
        if code in (errno.EACCES, 10013):
            return False, f'Windows refuse la vérification de {host}:{port}; impossible de confirmer sa disponibilité'
        return False, f'{host}:{port} indisponible (erreur socket {code})'


def inspect_environment(root: Path = ROOT, check_port: bool = True, port: int = 5000) -> dict:
    sys.path.insert(0, str(Path(root).resolve()))
    from backend.config import settings

    root = Path(root).resolve()
    config = settings()
    expected = (root / 'database' / 'stages_marrakech.db').resolve()
    actual = Path(config['DATABASE']).resolve()
    problems: list[str] = []
    checks: list[tuple[str, bool, str]] = []

    in_venv = Path(sys.executable).resolve().is_relative_to((root / '.venv').resolve())
    checks.append(('Python du projet', in_venv, sys.executable if in_venv else 'Utilisez .venv\\Scripts\\python.exe'))
    modules = [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is not None]
    checks.append(('Dépendances', len(modules) == len(REQUIRED_MODULES), f'{len(modules)}/{len(REQUIRED_MODULES)} modules requis'))
    is_expected = actual == expected
    checks.append(('Base locale', is_expected, str(actual)))
    is_private = not bool(config.get('PUBLIC_DEMO_MODE'))
    checks.append(('Mode privé', is_private, 'PUBLIC_DEMO_MODE désactivé' if is_private else 'La démo publique est activée'))

    if not is_expected:
        problems.append(f'Chemin SQLite inattendu : {actual}')
    if not is_private:
        problems.append('Le profil public de démonstration est actif.')
    if not expected.is_file():
        checks.append(('Fichier SQLite', False, 'Base historique absente; aucun remplacement effectué'))
        problems.append('La base historique attendue est absente.')
    else:
        try:
            uri = expected.as_uri() + '?mode=ro'
            with sqlite3.connect(uri, uri=True, timeout=5) as db:
                integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
                tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                required_tables = {'entreprises', 'offres', 'candidatures'}
                missing = required_tables - tables
                counts = ({table: db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                           for table in sorted(required_tables)} if not missing else {})
                fk_issues = len(db.execute('PRAGMA foreign_key_check').fetchall())
                synthetic = False
                if 'deployment_metadata' in tables:
                    marker = db.execute("SELECT value FROM deployment_metadata WHERE key='dataset_type'").fetchone()
                    synthetic = bool(marker and marker[0] == 'synthetic_public_demo')
            populated = bool(counts) and counts.get('entreprises', 0) > 0 and counts.get('offres', 0) > 0
            good = integrity == 'ok' and not missing and not fk_issues and not synthetic and populated
            checks.append(('SQLite en lecture seule', good, f'intégrité={integrity}; volumes={counts}; relations FK en erreur={fk_issues}; marqueur démo={synthetic}'))
            if not good:
                problems.append('La base historique est invalide, incomplète ou porte le marqueur synthétique.')
        except sqlite3.Error as exc:
            checks.append(('SQLite en lecture seule', False, f'lecture impossible ({type(exc).__name__})'))
            problems.append('La vérification SQLite a échoué.')

    if check_port:
        port_ok, detail = port_is_available(port)
        checks.append(('Port local', port_ok, detail))
        if not port_ok:
            problems.append('Le lanceur ne démarre pas si le port 5000 est occupé ou si Windows ne permet pas de le vérifier; il ne réutilise jamais silencieusement un serveur existant.')

    return {'ok': not problems and all(item[1] for item in checks), 'checks': checks, 'problems': problems}


def main() -> int:
    result = inspect_environment()
    print('Vérification du lancement local privé de soutenance')
    for label, passed, detail in result['checks']:
        print(f"[{'OK' if passed else 'ERREUR'}] {label} : {detail}")
    for problem in result['problems']:
        print('Action requise : ' + problem)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
