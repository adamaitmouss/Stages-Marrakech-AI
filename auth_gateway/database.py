from __future__ import annotations

import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import unquote

from .security import hash_password


class AuthStore:
    def __init__(self, database_url: str, root: Path):
        self.database_url = database_url
        self.root = Path(root)
        if database_url.startswith('sqlite:///'):
            raw = unquote(database_url[len('sqlite:///'):])
            path = Path(raw)
            self.sqlite_path = path if path.is_absolute() else (self.root / path).resolve()
            self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
            self.driver = 'sqlite'
        elif database_url.startswith(('postgresql://', 'postgres://')):
            self.sqlite_path = None
            self.driver = 'postgres'
            if database_url.startswith('postgres://'):
                self.database_url = 'postgresql://' + database_url[len('postgres://'):]
        else:
            raise RuntimeError('AUTH_DATABASE_URL doit être sqlite:///… ou postgresql://…')
        self.initialize()

    @contextmanager
    def connection(self):
        if self.driver == 'sqlite':
            db = sqlite3.connect(self.sqlite_path, timeout=10, isolation_level=None)
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA busy_timeout=10000')
        else:
            try:
                import psycopg
                from psycopg.rows import dict_row
            except ImportError as exc:
                raise RuntimeError('Installez auth_gateway/requirements-postgres.txt pour PostgreSQL persistant.') from exc
            db = psycopg.connect(self.database_url, row_factory=dict_row)
        try:
            yield db
        finally:
            db.close()

    def sql(self, statement: str) -> str:
        return statement if self.driver == 'sqlite' else statement.replace('?', '%s')

    def initialize(self):
        with self.connection() as db:
            if self.driver == 'sqlite':
                db.executescript('''
                    CREATE TABLE IF NOT EXISTS auth_users (
                        id TEXT PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL, status TEXT NOT NULL, role TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS auth_sessions (
                        id TEXT PRIMARY KEY, user_id TEXT, csrf TEXT NOT NULL,
                        created_at REAL NOT NULL, expires_at REAL NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES auth_users(id) ON DELETE CASCADE
                    );
                    CREATE TABLE IF NOT EXISTS auth_attempts (
                        key TEXT PRIMARY KEY, window_started REAL NOT NULL, count INTEGER NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_auth_sessions_expiry ON auth_sessions(expires_at);
                ''')
            else:
                db.execute('''CREATE TABLE IF NOT EXISTS auth_users (
                    id TEXT PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL, status TEXT NOT NULL, role TEXT NOT NULL)''')
                db.execute('''CREATE TABLE IF NOT EXISTS auth_sessions (
                    id TEXT PRIMARY KEY, user_id TEXT REFERENCES auth_users(id) ON DELETE CASCADE,
                    csrf TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL, expires_at DOUBLE PRECISION NOT NULL)''')
                db.execute('''CREATE TABLE IF NOT EXISTS auth_attempts (
                    key TEXT PRIMARY KEY, window_started DOUBLE PRECISION NOT NULL, count INTEGER NOT NULL)''')
                db.execute('CREATE INDEX IF NOT EXISTS idx_auth_sessions_expiry ON auth_sessions(expires_at)')
                db.commit()

    def fetch_one(self, statement: str, params=()):
        with self.connection() as db:
            cur = db.execute(self.sql(statement), params)
            row = cur.fetchone()
            return dict(row) if row else None

    def execute(self, statement: str, params=()):
        with self.connection() as db:
            cur = db.execute(self.sql(statement), params)
            if self.driver == 'postgres':
                db.commit()
            return cur.rowcount

    def get_user_by_email(self, email: str):
        return self.fetch_one('SELECT * FROM auth_users WHERE email=?', (email,))

    def get_user_by_id(self, ident: str):
        return self.fetch_one('SELECT id,first_name,last_name,email,created_at,status,role FROM auth_users WHERE id=?', (ident,))

    def create_user(self, first: str, last: str, email: str, password_hash: str, role='demo') -> bool:
        ident = str(uuid.uuid4())
        created = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        try:
            self.execute('INSERT INTO auth_users(id,first_name,last_name,email,password_hash,created_at,status,role) VALUES(?,?,?,?,?,?,?,?)',
                         (ident, first, last, email, password_hash, created, 'active', role))
            return True
        except Exception as exc:
            if 'unique' in str(exc).lower() or 'duplicate key' in str(exc).lower():
                return False
            raise

    def bootstrap_admin(self, email: str, password_hash: str):
        if not email:
            return
        if self.get_user_by_email(email):
            return
        first, _, last = email.partition('@')
        self.create_user(first[:80] or 'Administrateur', last[:80] or 'Local', email, password_hash, role='admin')

    def new_session(self, user_id: str | None, csrf: str, ttl: int):
        ident = str(uuid.uuid4()); now = time.time()
        self.execute('INSERT INTO auth_sessions(id,user_id,csrf,created_at,expires_at) VALUES(?,?,?,?,?)',
                     (ident, user_id, csrf, now, now + ttl))
        return ident

    def get_session(self, ident: str):
        data = self.fetch_one('SELECT id,user_id,csrf,created_at,expires_at FROM auth_sessions WHERE id=?', (ident,))
        if not data:
            return None
        if float(data['expires_at']) <= time.time():
            self.delete_session(ident)
            return None
        if data['user_id']:
            data['user'] = self.get_user_by_id(data['user_id'])
            if not data['user'] or data['user']['status'] != 'active':
                self.delete_session(ident)
                return None
        return data

    def delete_session(self, ident: str):
        self.execute('DELETE FROM auth_sessions WHERE id=?', (ident,))

    def rotate_session(self, old_id: str | None, user_id: str | None, csrf: str, ttl: int):
        if old_id:
            self.delete_session(old_id)
        return self.new_session(user_id, csrf, ttl)

    def consume_attempt(self, key: str, max_attempts: int, window: int) -> bool:
        now = time.time()
        with self.connection() as db:
            if self.driver == 'sqlite':
                db.execute('BEGIN IMMEDIATE')
            cur = db.execute(self.sql('SELECT window_started,count FROM auth_attempts WHERE key=?'), (key,))
            row = cur.fetchone()
            if row and float(row['window_started']) > now - window and int(row['count']) >= max_attempts:
                return False
            if row and float(row['window_started']) > now - window:
                started, count = float(row['window_started']), int(row['count']) + 1
            else:
                started, count = now, 1
            db.execute(self.sql('''INSERT INTO auth_attempts(key,window_started,count) VALUES(?,?,?)
                ON CONFLICT(key) DO UPDATE SET window_started=excluded.window_started,count=excluded.count'''),
                       (key, started, count))
            db.commit()
            return count <= max_attempts

    def clear_attempt(self, key: str):
        self.execute('DELETE FROM auth_attempts WHERE key=?', (key,))

    def prune(self):
        self.execute('DELETE FROM auth_sessions WHERE expires_at<=?', (time.time(),))
