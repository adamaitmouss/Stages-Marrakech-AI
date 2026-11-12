"""Migrations additives, sauvegardées, sans remplacement de table métier."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


def request_database(default):
    """Return the authenticated account's database during a gateway request."""
    try:
        from flask import g, has_request_context
        if has_request_context():
            return getattr(g, 'user_database_path', default)
    except ImportError:
        pass
    return default


def request_backup_dir(default):
    try:
        from flask import g, has_request_context
        if has_request_context():
            return getattr(g, 'user_backup_dir', default)
    except ImportError:
        pass
    return default


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def backup_database(path, backup_dir, label='avant_import'):
    target_dir=Path(backup_dir);target_dir.mkdir(parents=True,exist_ok=True)
    target=target_dir/f'{label}_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.db'
    source=sqlite3.connect(path,timeout=15);destination=sqlite3.connect(target)
    try:source.backup(destination)
    finally:destination.close();source.close()
    return target


@contextmanager
def connect(path):
    readonly = False
    try:
        from flask import current_app, has_app_context
        if has_app_context() and current_app.config.get('PUBLIC_DEMO_MODE'):
            readonly = Path(path).resolve() == Path(current_app.config['DATABASE']).resolve()
    except (ImportError, RuntimeError, KeyError):
        pass
    if readonly:
        con = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=15)
    else:
        con = sqlite3.connect(path, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def migrate(path, backup_dir):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if version >= 1:
            return
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        target = Path(backup_dir) / ('avant_migration_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.db')
        backup = sqlite3.connect(target)
        db.backup(backup)
        backup.close()
        db.execute('BEGIN IMMEDIATE')
        if db.execute('PRAGMA user_version').fetchone()[0] >= 1:
            return
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='entreprises'").fetchone():
            raise RuntimeError('Base initiale entreprises/offres absente. Restaurer la base livrée avant de démarrer.')
        db.execute('''CREATE TABLE IF NOT EXISTS candidatures (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nom_entreprise TEXT, secteur TEXT,
            email TEXT, telephone TEXT, date_candidature TEXT, statut TEXT, commentaire TEXT)''')
        additions = {
            'entreprises': {'place_id': 'TEXT', 'latitude': 'REAL', 'longitude': 'REAL', 'geo_verified_at': 'TEXT',
                            'geo_source': 'TEXT', 'quartier': 'TEXT', 'ville': 'TEXT'},
            'offres': {'source': "TEXT DEFAULT 'Stagiaires.ma'", 'entreprise_nom': 'TEXT', 'entreprise_ref': 'INTEGER',
                       'relation_verified': 'INTEGER DEFAULT 0', 'ville': 'TEXT', 'recruitment_email': 'TEXT',
                       'email_verified': 'INTEGER DEFAULT 0'},
            'candidatures': {'offre_id': 'INTEGER', 'offre_titre': 'TEXT', 'cv_id': 'INTEGER', 'source': 'TEXT',
                             'canal': 'TEXT', 'updated_at': 'TEXT', 'created_at': 'TEXT', 'email_validated': 'INTEGER DEFAULT 0'},
        }
        for table, columns in additions.items():
            existing = {r['name'] for r in db.execute(f'PRAGMA table_info({table})')}
            for name, typ in columns.items():
                if name not in existing:
                    db.execute(f'ALTER TABLE {table} ADD COLUMN {name} {typ}')
        schema = '''
        CREATE TABLE IF NOT EXISTS cvs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, template TEXT NOT NULL,
            payload BLOB NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS candidature_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, candidature_id INTEGER NOT NULL,
            old_status TEXT, new_status TEXT NOT NULL, changed_at TEXT NOT NULL,
            FOREIGN KEY(candidature_id) REFERENCES candidatures(id));
        CREATE TABLE IF NOT EXISTS send_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, idempotency_key TEXT UNIQUE NOT NULL,
            payload_hash TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
            candidature_id INTEGER, error_code TEXT);
        CREATE INDEX IF NOT EXISTS idx_candidatures_offre ON candidatures(offre_id);
        CREATE INDEX IF NOT EXISTS idx_history_candidature ON candidature_history(candidature_id);
        '''
        for statement in schema.split(';'):
            if statement.strip():
                db.execute(statement)
        timestamp = now()
        db.execute('UPDATE candidatures SET updated_at=COALESCE(updated_at,?),created_at=COALESCE(created_at,?)', (timestamp, timestamp))
        db.execute('''INSERT INTO candidature_history(candidature_id,old_status,new_status,changed_at)
                      SELECT id,NULL,COALESCE(statut,'Non envoyée'),? FROM candidatures''', (timestamp,))
        db.execute('PRAGMA user_version=1')


def migrate_phase5(path, backup_dir):
    """Tables additives pour collecte, alertes et assistant; aucune table métier n'est remplacée."""
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        if db.execute('PRAGMA user_version').fetchone()[0] >= 4:
            return
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup = sqlite3.connect(Path(backup_dir) / f'avant_phase5_migration_{stamp}.db')
        db.backup(backup)
        backup.close()
        db.execute('BEGIN IMMEDIATE')
        # L'import historique utilise un ID métier explicite, non rowid; assurer son unicité sans remplacer la table.
        db.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_offres_public_id ON offres("ID")')
        existing = {r['name'] for r in db.execute('PRAGMA table_info(offres)')}
        for name, typ in {'competences': 'TEXT', 'collected_at': 'TEXT', 'last_verified_at': 'TEXT',
                          'statut_offre': "TEXT NOT NULL DEFAULT 'unknown'"}.items():
            if name not in existing:
                db.execute(f'ALTER TABLE offres ADD COLUMN "{name}" {typ}')
        db.execute('''UPDATE offres SET statut_offre=CASE
            WHEN "Date expiration" IS NULL OR trim(CAST("Date expiration" AS TEXT))='' THEN 'unknown'
            WHEN date("Date expiration") IS NULL THEN 'unknown'
            WHEN date("Date expiration")<date('now') THEN 'expired' ELSE 'active' END''')
        schema = '''
        CREATE TABLE IF NOT EXISTS collection_settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS collector_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, mode TEXT NOT NULL, status TEXT NOT NULL,
            started_at TEXT NOT NULL, finished_at TEXT, source_count INTEGER NOT NULL DEFAULT 0,
            fetched_count INTEGER NOT NULL DEFAULT 0, new_offers INTEGER NOT NULL DEFAULT 0,
            updated_offers INTEGER NOT NULL DEFAULT 0, new_companies INTEGER NOT NULL DEFAULT 0,
            duplicates INTEGER NOT NULL DEFAULT 0, expired_offers INTEGER NOT NULL DEFAULT 0,
            error_summary TEXT);
        CREATE TABLE IF NOT EXISTS collector_source_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER NOT NULL, source TEXT NOT NULL,
            status TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
            fetched_count INTEGER NOT NULL DEFAULT 0, new_offers INTEGER NOT NULL DEFAULT 0,
            updated_offers INTEGER NOT NULL DEFAULT 0, duplicates INTEGER NOT NULL DEFAULT 0,
            error_summary TEXT, FOREIGN KEY(run_id) REFERENCES collector_runs(id));
        CREATE TABLE IF NOT EXISTS offer_source_identity (
            id INTEGER PRIMARY KEY AUTOINCREMENT, offer_id INTEGER NOT NULL, source TEXT NOT NULL,
            external_id TEXT, canonical_url TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
            UNIQUE(source,external_id), UNIQUE(source,canonical_url));
        CREATE INDEX IF NOT EXISTS idx_offer_source_identity_offer ON offer_source_identity(offer_id);
        CREATE TABLE IF NOT EXISTS collector_staging (
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER NOT NULL, source TEXT NOT NULL,
            identity_key TEXT NOT NULL, payload_json TEXT NOT NULL, decision TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY(run_id) REFERENCES collector_runs(id), UNIQUE(run_id,source,identity_key));
        CREATE TABLE IF NOT EXISTS collector_duplicate_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER NOT NULL, offer_id INTEGER NOT NULL,
            candidate_offer_id INTEGER NOT NULL, score REAL NOT NULL, status TEXT NOT NULL DEFAULT 'review',
            created_at TEXT NOT NULL, UNIQUE(run_id,offer_id,candidate_offer_id));
        CREATE TABLE IF NOT EXISTS company_source_identity (
            id INTEGER PRIMARY KEY AUTOINCREMENT, company_rowid INTEGER NOT NULL, source TEXT NOT NULL,
            external_id TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
            UNIQUE(source,external_id));
        CREATE TABLE IF NOT EXISTS company_duplicate_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER, company_rowid INTEGER NOT NULL,
            candidate_rowid INTEGER NOT NULL, score REAL NOT NULL, status TEXT NOT NULL DEFAULT 'review',
            created_at TEXT NOT NULL, UNIQUE(company_rowid,candidate_rowid));
        CREATE TABLE IF NOT EXISTS alert_preferences (
            id INTEGER PRIMARY KEY CHECK(id=1), domain TEXT NOT NULL DEFAULT '', skills_json TEXT NOT NULL DEFAULT '[]',
            city TEXT NOT NULL DEFAULT 'Marrakech', internship_type TEXT NOT NULL DEFAULT '',
            contract_type TEXT NOT NULL DEFAULT '', minimum_score INTEGER NOT NULL DEFAULT 50,
            frequency TEXT NOT NULL DEFAULT 'instant', enabled INTEGER NOT NULL DEFAULT 0,
            email_enabled INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, offer_id INTEGER NOT NULL UNIQUE,
            created_at TEXT NOT NULL, score REAL NOT NULL, explanation TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(offer_id) REFERENCES offres("ID"));
        CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(is_read,created_at DESC);
        CREATE TABLE IF NOT EXISTS assistant_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL CHECK(role IN ('user','assistant')),
            message TEXT NOT NULL, created_at TEXT NOT NULL);
        '''
        for statement in schema.split(';'):
            if statement.strip():
                db.execute(statement)
        for table, columns in {
            'collector_runs': {'unchanged_offers':'INTEGER NOT NULL DEFAULT 0','review_offers':'INTEGER NOT NULL DEFAULT 0','duration_ms':'INTEGER','updated_companies':'INTEGER NOT NULL DEFAULT 0','error_count':'INTEGER NOT NULL DEFAULT 0'},
            'collector_source_runs': {'duration_ms':'INTEGER'},
            'offer_source_identity': {'content_hash':'TEXT'},
        }.items():
            present={r['name'] for r in db.execute(f'PRAGMA table_info("{table}")')}
            for name, typ in columns.items():
                if name not in present:db.execute(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {typ}')
        pref_columns = {r['name'] for r in db.execute('PRAGMA table_info(alert_preferences)')}
        if 'email_payload' not in pref_columns:
            db.execute('ALTER TABLE alert_preferences ADD COLUMN email_payload TEXT')
        if 'email_next_at' not in pref_columns:
            db.execute('ALTER TABLE alert_preferences ADD COLUMN email_next_at TEXT')
        db.execute('''CREATE TABLE IF NOT EXISTS alert_email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, alert_id INTEGER NOT NULL UNIQUE,
            status TEXT NOT NULL, attempted_at TEXT NOT NULL, error_summary TEXT,
            FOREIGN KEY(alert_id) REFERENCES alerts(id) ON DELETE CASCADE)''')
        db.execute('INSERT OR IGNORE INTO alert_preferences(id,updated_at) VALUES (1,?)', (now(),))
        db.execute('PRAGMA user_version=4')


def migrate_phase7(path, backup_dir):
    """Champs de traçabilité pour les imports autorisés et fichiers fournis."""
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        if db.execute('PRAGMA user_version').fetchone()[0] >= 5:
            return
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup = sqlite3.connect(Path(backup_dir) / f'avant_phase7_migration_{stamp}.db')
        db.backup(backup)
        backup.close()
        db.execute('BEGIN IMMEDIATE')
        columns = {
            'collector_runs': {
                'source_metadata_json': 'TEXT',
                'imported_at': 'TEXT',
                'imported_offers': 'INTEGER NOT NULL DEFAULT 0',
                'rejected_offers': 'INTEGER NOT NULL DEFAULT 0',
            },
            'collector_source_runs': {
                'imported_at': 'TEXT',
                'imported_offers': 'INTEGER NOT NULL DEFAULT 0',
                'rejected_offers': 'INTEGER NOT NULL DEFAULT 0',
            },
        }
        for table, additions in columns.items():
            present = {row['name'] for row in db.execute(f'PRAGMA table_info("{table}")')}
            for name, kind in additions.items():
                if name not in present:
                    db.execute(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {kind}')
        db.execute('PRAGMA user_version=5')


def migrate_phase9(path, backup_dir):
    """Historique minimal des recherches IA; aucun contenu de CV ni résultat web n'est conservé."""
    Path(backup_dir).mkdir(parents=True,exist_ok=True)
    with connect(path) as db:
        if db.execute('PRAGMA user_version').fetchone()[0] >= 6:
            return
        stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        backup=sqlite3.connect(Path(backup_dir)/f'avant_phase9_migration_{stamp}.db')
        db.backup(backup);backup.close()
        db.execute('BEGIN IMMEDIATE')
        db.execute('''CREATE TABLE IF NOT EXISTS gemini_search_history (
            id TEXT PRIMARY KEY, session_digest TEXT NOT NULL, mode TEXT NOT NULL CHECK(mode IN ('local','demo','gemini')),
            prompt TEXT NOT NULL DEFAULT '', criteria_json TEXT NOT NULL DEFAULT '{}', model TEXT,
            status TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
            result_count INTEGER NOT NULL DEFAULT 0, verified_count INTEGER NOT NULL DEFAULT 0,
            imported_count INTEGER NOT NULL DEFAULT 0, search_queries INTEGER NOT NULL DEFAULT 0,
            error_summary TEXT)''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_gemini_search_history_session_time ON gemini_search_history(session_digest,started_at DESC)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_gemini_search_history_day_mode ON gemini_search_history(mode,started_at,status)')
        db.execute('PRAGMA user_version=6')


def rows(path, sql, args=()):
    with connect(path) as db:
        return [dict(row) for row in db.execute(sql, args)]
