import secrets
import hmac
import os
import time
import sqlite3
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask, jsonify, request, session, send_from_directory, redirect
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import settings
from .db import migrate, migrate_phase5, migrate_phase7, migrate_phase9, connect, now, request_database
from .security import Vault
from .api import api


def create_app(overrides=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(settings(overrides))
    app.config['MULTI_USER_MODE'] = os.environ.get('AUTH_MULTI_USER_MODE', 'false').lower() == 'true'
    app.config['AUTH_USER_DATA_ROOT'] = os.environ.get(
        'AUTH_USER_DATA_ROOT', app.config.get('AUTH_USER_DATA_ROOT') or
        str(Path(app.config['ROOT']) / 'private' / 'user_data'))
    if app.config.get('TRUST_PROXY'):
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
    if app.config.get('PUBLIC_DEMO_MODE'):
        if not app.config.get('PUBLIC_DEMO_DATA_CONFIRMED'):
            raise RuntimeError('Le mode public exige l’attestation d’un jeu synthétique.')
        database = Path(app.config['DATABASE']).resolve()
        if not database.is_file():
            raise RuntimeError(f'Base publique absente au chemin attendu : {database}')
        db_uri = database.as_uri() + '?mode=ro'
        try:
            check=sqlite3.connect(db_uri,uri=True)
            integrity=check.execute('PRAGMA integrity_check').fetchone()[0]
            tables={row[0] for row in check.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'entreprises','offres','deployment_metadata'}.issubset(tables):
                raise RuntimeError('Base refusée en mode public : jeu synthétique incomplet.')
            marker=check.execute("SELECT value FROM deployment_metadata WHERE key='dataset_type'").fetchone()
            company_count=check.execute('SELECT COUNT(*) FROM entreprises').fetchone()[0]
            offer_count=check.execute('SELECT COUNT(*) FROM offres').fetchone()[0]
            version=check.execute('PRAGMA user_version').fetchone()[0]
            check.close()
        except sqlite3.Error as exc:
            raise RuntimeError(f'Base publique SQLite illisible ou incomplète : {database}') from exc
        if integrity != 'ok' or version < 6:
            raise RuntimeError(f'Base publique invalide (intégrité/version) : {database}')
        if not marker or marker[0]!='synthetic_public_demo':
            raise RuntimeError('Base refusée en mode public : les données doivent être synthétiques.')
        app.logger.info('Profil public démonstration | SQLite=%s | intégrité=%s | entreprises=%s | offres=%s',
                        database, integrity, company_count, offer_count)
    vault = Vault(app.config['PRIVATE_DIR'])
    app.secret_key = vault.session_key
    app.extensions['vault'] = vault
    if not app.config.get('PUBLIC_DEMO_MODE'):
        migrate(app.config['DATABASE'], app.config['BACKUP_DIR'])
        migrate_phase5(app.config['DATABASE'], app.config['BACKUP_DIR'])
        migrate_phase7(app.config['DATABASE'], app.config['BACKUP_DIR'])
        migrate_phase9(app.config['DATABASE'], app.config['BACKUP_DIR'])
    app.extensions['gemini_search_jobs']={}
    with connect(app.config['DATABASE']) as db:
        if not app.config.get('PUBLIC_DEMO_MODE') and not app.config.get('MULTI_USER_MODE'):
            db.execute("UPDATE collector_runs SET status='failed',finished_at=?,error_summary='Collecte interrompue à l’arrêt précédent.' WHERE status='running'",(now(),))
    attempts = {}

    @app.before_request
    def access():
        origin = request.headers.get('Origin')
        if origin and origin.rstrip('/') != request.host_url.rstrip('/'):
            return jsonify(erreur='Origine non autorisée.'), 403
        if app.config.get('PUBLIC_DEMO_MODE'):
            if request.path.startswith('/api/auth/') and request.path!='/api/auth/session':
                return jsonify(erreur='Authentification indisponible en mode public de démonstration.'),403
            if request.path.startswith('/api/') and request.method not in ('GET','HEAD','OPTIONS'):
                safe_posts={'/api/matching/preview','/api/matching','/api/assistant/chat','/api/ai-search/local','/api/ai-search/demo',
                            '/api/internal/gateway-session'}
                if request.method!='POST' or request.path not in safe_posts:
                    return jsonify(erreur='Cette démonstration publique est en lecture seule.'),403
                data=request.get_json(silent=True) or {}
                if request.path in ('/api/matching/preview','/api/matching') and data.get('mode','local')!='local':
                    return jsonify(erreur='Les services IA externes sont désactivés en démonstration.'),403
                if request.path=='/api/assistant/chat' and data.get('mode','local')!='local':
                    return jsonify(erreur='Les services IA externes sont désactivés en démonstration.'),403
            if request.path.startswith(('/api/','/analytics/')) or request.path=='/test-db':
                session['authenticated']=True
                session.setdefault('csrf',secrets.token_urlsafe(32))
        if request.path == '/api/internal/gateway-session':
            if request.remote_addr not in ('127.0.0.1', '::1'):
                return jsonify(erreur='Accès interne refusé.'),403
            return
        if app.config.get('MULTI_USER_MODE') and request.path != '/health':
            if (request.remote_addr not in ('127.0.0.1', '::1') or not session.get('gateway_internal')):
                return jsonify(erreur='Session passerelle interne requise.'), 401
            account = request.headers.get('X-Internal-User-ID', '')
            from flask import g
            g.authenticated_user_id = account
            if account == '__admin__':
                g.user_database_path = app.config['DATABASE']
                g.user_backup_dir = app.config['BACKUP_DIR']
            elif account:
                try:
                    from .user_data import provision_user_database
                    database_path, backup_dir = provision_user_database(
                        app.config['DATABASE'], app.config['AUTH_USER_DATA_ROOT'], account)
                    g.user_database_path = str(database_path)
                    g.user_backup_dir = str(backup_dir)
                except (ValueError, OSError, RuntimeError, sqlite3.Error) as exc:
                    app.logger.error('Impossible de préparer l’espace personnel (%s; compte masqué).', type(exc).__name__)
                    return jsonify(erreur='Votre espace personnel n’a pas pu être initialisé.'), 503
            else:
                return jsonify(erreur='Compte utilisateur interne manquant.'), 401
        if request.path.startswith('/api/auth/'):
            if request.method == 'POST':
                token = request.headers.get('X-CSRF-Token', '')
                if not session.get('csrf') or not secrets.compare_digest(token, session['csrf']):
                    return jsonify(erreur='Session expirée. Rechargez la page.'), 403
            return
        personal = request.path.startswith(('/api/', '/analytics/')) or request.path == '/test-db'
        if personal and not session.get('authenticated'):
            if request.path.startswith('/analytics/') and request.method == 'GET' and request.path == '/analytics/':
                return redirect('/index.html?login=1')
            return jsonify(erreur='Connectez-vous pour accéder à vos données.'), 401
        if request.path.startswith('/api/') and request.method not in ('GET', 'HEAD', 'OPTIONS'):
            token = request.headers.get('X-CSRF-Token', '')
            if not session.get('csrf') or not secrets.compare_digest(token, session['csrf']):
                return jsonify(erreur='Session expirée. Rechargez la page.'), 403

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Dash inclut son propre initialiseur inline ; seul son espace bénéficie de cette exception.
        scripts = "'self' 'unsafe-inline'" if request.path.startswith('/analytics/') else "'self' https://maps.googleapis.com https://maps.gstatic.com"
        response.headers['Content-Security-Policy'] = f"default-src 'self'; script-src {scripts}; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://tile.openstreetmap.org https://*.googleapis.com https://*.gstatic.com https://*.google.com; connect-src 'self' https://*.googleapis.com https://*.gstatic.com; font-src 'self' data:; frame-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'"
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/api/auth/session')
    def auth_session():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        if app.config.get('PUBLIC_DEMO_MODE'):
            session['authenticated']=True
        return jsonify(configured=True if app.config.get('PUBLIC_DEMO_MODE') else vault.configured,
                       authenticated=bool(session.get('authenticated')), csrf=session['csrf'],
                       public_demo=bool(app.config.get('PUBLIC_DEMO_MODE')))

    @app.post('/api/auth/setup')
    def setup():
        if vault.configured:
            return jsonify(erreur='Un mot de passe est déjà configuré.'), 409
        if request.remote_addr not in ('127.0.0.1', '::1'):
            return jsonify(erreur='La première configuration doit être faite sur cet ordinateur.'), 403
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError('Objet JSON attendu.')
        try:
            vault.setup(data.get('password'))
        except FileExistsError:
            return jsonify(erreur='Configuration déjà effectuée.'), 409
        session.clear()
        session.update(authenticated=True, csrf=secrets.token_urlsafe(32))
        return jsonify(csrf=session['csrf'])

    @app.post('/api/auth/login')
    def login():
        remote = request.remote_addr
        recent = [t for t in attempts.get(remote, []) if time.monotonic()-t < 60]
        if len(recent) >= 5:
            return jsonify(erreur='Trop de tentatives. Réessayez dans une minute.'), 429
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not vault.login(data.get('password')):
            attempts[remote] = recent + [time.monotonic()]
            return jsonify(erreur='Mot de passe incorrect.'), 401
        attempts.pop(remote, None)
        session.clear()
        session.update(authenticated=True, csrf=secrets.token_urlsafe(32))
        return jsonify(csrf=session['csrf'])

    @app.post('/api/auth/logout')
    def logout():
        session.clear()
        return jsonify(message='Déconnexion effectuée.')

    @app.post('/api/internal/gateway-session')
    def internal_gateway_session():
        expected = os.environ.get('AUTH_INTERNAL_SECRET', '')
        supplied = request.headers.get('X-Internal-Gateway-Secret', '')
        if (request.remote_addr not in ('127.0.0.1', '::1') or len(expected) < 48
                or not hmac.compare_digest(expected, supplied)):
            return jsonify(erreur='Accès interne refusé.'), 403
        session.clear()
        session.update(authenticated=True, csrf=secrets.token_urlsafe(32), gateway_internal=True)
        return jsonify(authenticated=True, configured=True, csrf=session['csrf'],
                       public_demo=bool(app.config.get('PUBLIC_DEMO_MODE')))

    @app.get('/health')
    def health():
        return jsonify(status='ok')

    @app.get('/test-db')
    def test_db():
        from .db import rows
        return jsonify(entreprises=rows(request_database(app.config['DATABASE']), 'SELECT COUNT(*) AS n FROM entreprises')[0]['n'])

    @app.get('/')
    def home():
        return redirect('/index.html')

    @app.get('/<path:filename>')
    def frontend(filename):
        root = Path(app.config['ROOT']) / 'dashboard'
        allowed_pages = {'index.html', 'entreprises.html', 'offres.html', 'candidatures.html', 'statistiques.html',
                         'envoyer_cv.html', 'cv.html', 'matching.html', 'carte.html', 'analyses.html','collecte.html','alertes.html','recherche-ia.html'}
        if filename not in allowed_pages and not filename.startswith(('css/', 'js/', 'vendor/leaflet/')):
            return jsonify(erreur='Page introuvable.'), 404
        return send_from_directory(root, filename)

    @app.errorhandler(ValueError)
    def invalid(exc):
        return jsonify(erreur=str(exc)), 400

    @app.errorhandler(LookupError)
    def missing(exc):
        return jsonify(erreur=str(exc)), 404

    @app.errorhandler(Exception)
    def unexpected(exc):
        if isinstance(exc, HTTPException):
            messages = {413: 'Fichier ou requête trop volumineux (maximum 6 Mo).', 404: 'Ressource introuvable.'}
            return jsonify(erreur=messages.get(exc.code, exc.name)), exc.code
        # Aucun corps de requête, secret ou message d’exception fournisseur n’est journalisé.
        app.logger.error('Erreur interne (%s)', type(exc).__name__)
        return jsonify(erreur='Une erreur interne est survenue. Vos données existantes sont conservées.'), 500

    app.register_blueprint(api)
    from .analytics import mount_dash
    app.extensions['analytics'] = mount_dash(app)
    from .collectors.service import sources_config
    from .db import rows
    email_alerts=rows(app.config['DATABASE'],'SELECT email_enabled FROM alert_preferences WHERE id=1')
    if not app.config.get('PUBLIC_DEMO_MODE') and not app.config.get('MULTI_USER_MODE') and not app.config.get('DISABLE_BACKGROUND_SCHEDULER') and (sources_config(app.config['DATABASE'])['auto_enabled'] or (email_alerts and email_alerts[0]['email_enabled'])):
        from .collection_manager import ensure_scheduler
        ensure_scheduler(app)
    return app
