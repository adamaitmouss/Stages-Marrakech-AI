"""Durable, per-account SQLite workspaces seeded without historical personal data."""
from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
import uuid
from pathlib import Path


_locks_guard = threading.Lock()
_locks: dict[str, threading.Lock] = {}
_PERSONAL_TABLES = (
    'candidature_history', 'send_attempts', 'candidatures', 'cvs', 'alert_email_log',
    'alerts', 'alert_preferences', 'assistant_messages', 'gemini_search_history',
    'collector_duplicate_candidates', 'collector_staging', 'collector_source_runs',
    'collector_runs', 'collection_settings', 'offer_source_identity',
    'company_duplicate_candidates', 'company_source_identity',
)


def _account_key(user_id: str) -> str:
    try:
        canonical = str(uuid.UUID(str(user_id)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError('Identifiant de compte invalide.') from exc
    return hashlib.sha256(canonical.encode('ascii')).hexdigest()


def _user_lock(key: str) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(key, threading.Lock())


def _validate_existing_workspace(target: Path, key: str) -> None:
    try:
        existing = sqlite3.connect(f'file:{target.as_posix()}?mode=ro', uri=True, timeout=5)
        marker = existing.execute('SELECT account_key FROM user_workspace_metadata LIMIT 1').fetchone()
        integrity = existing.execute('PRAGMA integrity_check').fetchone()[0]
        existing.close()
    except sqlite3.Error as exc:
        raise RuntimeError('Le fichier de votre espace existe mais son intégrité ne peut pas être confirmée.') from exc
    if integrity != 'ok' or not marker or marker[0] != key:
        raise RuntimeError('Le fichier SQLite trouvé ne correspond pas à cet espace utilisateur.')


def provision_user_database(source: str | Path, data_root: str | Path, user_id: str) -> tuple[Path, Path]:
    """Create one durable database per account; never edit the historical source."""
    key = _account_key(user_id)
    source_path = Path(source).resolve()
    user_dir = Path(data_root).resolve()
    target = user_dir / (key + '.db')
    backups = user_dir / 'backups' / key
    with _user_lock(key):
        if target.is_file():
            _validate_existing_workspace(target, key)
            return target, backups
        user_dir.mkdir(parents=True, exist_ok=True)
        backups.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.close(descriptor)
        except FileExistsError:
            _validate_existing_workspace(target, key)
            return target, backups
        try:
            src = sqlite3.connect(source_path, timeout=15)
            dst = sqlite3.connect(target, timeout=15)
            try:
                src.backup(dst)
                dst.execute('PRAGMA foreign_keys=ON')
                tables = {row[0] for row in dst.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                for table in _PERSONAL_TABLES:
                    if table in tables and table != 'alert_preferences':
                        dst.execute(f'DELETE FROM "{table}"')
                if 'alert_preferences' in tables:
                    columns = {row[1] for row in dst.execute('PRAGMA table_info(alert_preferences)')}
                    reset = {'domain': '', 'skills_json': '[]', 'city': 'Marrakech', 'internship_type': '',
                             'contract_type': '', 'minimum_score': 50, 'frequency': 'instant', 'enabled': 0,
                             'email_enabled': 0, 'email_payload': None, 'email_next_at': None,
                             'updated_at': '1970-01-01T00:00:00+00:00'}
                    fields = [name for name in reset if name in columns]
                    dst.execute('DELETE FROM alert_preferences')
                    dst.execute('INSERT INTO alert_preferences(' + ','.join('"'+name+'"' for name in fields) +
                                ') VALUES (' + ','.join('?' for _ in fields) + ')', tuple(reset[name] for name in fields))
                integrity = dst.execute('PRAGMA integrity_check').fetchone()[0]
                fk_errors = dst.execute('PRAGMA foreign_key_check').fetchall()
                if integrity != 'ok' or fk_errors:
                    raise RuntimeError('La base isolée n’a pas passé les contrôles SQLite.')
                source_counts = {
                    name: src.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                    for name in ('entreprises', 'offres')
                }
                copied_counts = {
                    name: dst.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                    for name in ('entreprises', 'offres')
                }
                remaining_personal = {
                    name: dst.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                    for name in _PERSONAL_TABLES if name in tables and name != 'alert_preferences'
                }
                if copied_counts != source_counts or any(remaining_personal.values()):
                    raise RuntimeError('La base isolée ne préserve pas les données métier ou contient des données personnelles héritées.')
                dst.execute('CREATE TABLE user_workspace_metadata (account_key TEXT PRIMARY KEY, created_at TEXT NOT NULL)')
                dst.execute("INSERT INTO user_workspace_metadata(account_key,created_at) VALUES (?,datetime('now'))", (key,))
                dst.commit()
            finally:
                dst.close()
                src.close()
        except Exception:
            try:
                target.unlink()
            except OSError:
                pass
            raise
    return target, backups
