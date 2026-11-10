from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from urllib.parse import urlsplit

from flask import Flask, abort, g, jsonify, make_response, redirect, render_template, request, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import AUTH_ROOT, load_config
from .database import AuthStore
from .proxy import BackendTunnel
from .security import hash_password, valid_password, verify_password

COOKIE_NAME = 'stages_auth_gateway'
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
DUMMY_PASSWORD_HASH = hash_password('invalid-password-placeholder-5482')


def normalize_email(value: str) -> str:
    return value.strip().casefold()


def valid_name(value: str) -> bool:
    value = value.strip()
    return bool(value) and len(value) <= 80 and all(ch.isalpha() or ch in " '-’" for ch in value)


def safe_next(value: str | None) -> str:
    if not value:
        return '/index.html'
    value = value.strip()
    parsed = urlsplit(value)
    if (not value.startswith('/') or value.startswith('//') or parsed.scheme or parsed.netloc
            or '\\' in value or any(ord(c) < 32 for c in value)
            or parsed.path in {'/login', '/register', '/account', '/auth/logout'}):
        return '/index.html'
    return value


def _attempt_key(kind: str, value: str) -> str:
    return kind + ':' + hashlib.sha256(value.encode('utf-8')).hexdigest()


def create_app(overrides: dict | None = None) -> Flask:
    cfg = load_config()
    if overrides:
        cfg.update(overrides)
    app = Flask(__name__, static_folder=str(AUTH_ROOT / 'static'), static_url_path='/_auth',
                template_folder=str(AUTH_ROOT / 'templates'))
    app.config.update(cfg)
    app.secret_key = cfg['AUTH_SESSION_SECRET']
    if cfg['AUTH_ENV'] == 'production':
        hops = cfg['AUTH_TRUSTED_PROXY_HOPS']
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=1, x_host=1)
    app.extensions['auth_store'] = AuthStore(cfg['AUTH_DATABASE_URL'], cfg['ROOT'])
    tunnel = cfg.get('AUTH_BACKEND_TUNNEL') or BackendTunnel(
        cfg['AUTH_BACKEND_URL'], cfg['AUTH_PROFILE'], cfg.get('AUTH_INTERNAL_SECRET', ''))
    app.extensions['auth_tunnel'] = tunnel
    tunnel.initialize()
    serializer = URLSafeTimedSerializer(cfg['AUTH_SESSION_SECRET'], salt='stages-auth-gateway-v1')

    if cfg['AUTH_PROFILE'] == 'private':
        admin_password = cfg.get('AUTH_BOOTSTRAP_ADMIN_PASSWORD', '')
        existing = app.extensions['auth_store'].get_user_by_email(cfg['AUTH_ADMIN_EMAIL'])
        if not existing and not valid_password(admin_password):
            raise RuntimeError('Configurez AUTH_BOOTSTRAP_ADMIN_PASSWORD (12 caractères minimum, lettres et chiffres) pour le premier administrateur.')
        if not existing:
            app.extensions['auth_store'].bootstrap_admin(cfg['AUTH_ADMIN_EMAIL'], hash_password(admin_password))
        existing = app.extensions['auth_store'].get_user_by_email(cfg['AUTH_ADMIN_EMAIL'])
        if not existing or existing['status'] != 'active' or existing['role'] != 'admin':
            raise RuntimeError('Le compte configuré doit être un administrateur actif.')
        extra = app.extensions['auth_store'].fetch_one('SELECT COUNT(*) AS n FROM auth_users WHERE email<>?', (cfg['AUTH_ADMIN_EMAIL'],))
        if int(extra['n']) > 0:
            raise RuntimeError('Le profil privé exige une base d’authentification réservée à l’administrateur autorisé.')

    store: AuthStore = app.extensions['auth_store']

    def get_cookie_sid() -> str | None:
        token = request.cookies.get(COOKIE_NAME, '')
        if not token:
            return None
        try:
            payload = serializer.loads(token, max_age=cfg['AUTH_SESSION_TTL_SECONDS'])
            return payload.get('sid') if isinstance(payload, dict) else None
        except (BadSignature, SignatureExpired, AttributeError):
            return None

    def set_cookie(response, sid: str, clear=False):
        if clear:
            response.delete_cookie(COOKIE_NAME, path='/', secure=cfg['AUTH_COOKIE_SECURE'], httponly=True, samesite='Strict')
        else:
            token = serializer.dumps({'sid': sid})
            response.set_cookie(COOKIE_NAME, token, max_age=cfg['AUTH_SESSION_TTL_SECONDS'], path='/',
                                secure=cfg['AUTH_COOKIE_SECURE'], httponly=True, samesite='Strict')
        return response

    def csrf_ok(session_data) -> bool:
        if not session_data:
            return False
        supplied = request.form.get('csrf_token', '') if request.form else request.headers.get('X-CSRF-Token', '')
        return bool(supplied) and hmac.compare_digest(str(supplied), str(session_data['csrf']))

    def make_anonymous():
        csrf = secrets.token_urlsafe(32)
        sid = store.new_session(None, csrf, cfg['AUTH_SESSION_TTL_SECONDS'])
        g.new_auth_sid = sid
        return store.get_session(sid)

    @app.before_request
    def load_auth_session():
        if cfg['AUTH_ENV'] == 'production' and request.host.lower() not in cfg['AUTH_ALLOWED_HOSTS']:
            return jsonify(erreur='Nom d’hôte non autorisé.'), 400
        sid = get_cookie_sid()
        data = store.get_session(sid) if sid else None
        g.auth_session = data
        g.auth_sid = sid if data else None
        g.clear_auth_cookie = False
        if sid and not data:
            store.delete_session(sid)
            g.clear_auth_cookie = True
        public_endpoints = {'gateway_login', 'gateway_register', 'gateway_health', 'static'}
        endpoint = request.endpoint or ''
        if endpoint in public_endpoints:
            if endpoint in {'gateway_login', 'gateway_register'} and data and data.get('user_id'):
                return redirect('/account' if endpoint == 'gateway_login' else '/index.html')
            if endpoint in {'gateway_login', 'gateway_register'} and not data:
                g.auth_session = make_anonymous()
            return None
        if endpoint == 'gateway_auth_session':
            if not data or not data.get('user_id'):
                return jsonify(authenticated=False, erreur='Authentification requise.'), 401
            return None
        if endpoint == 'gateway_logout':
            if not data or not data.get('user_id'):
                return redirect('/login')
            if not csrf_ok(data):
                return jsonify(erreur='Jeton de sécurité expiré. Rechargez la page.'), 403
            return None
        if endpoint == 'gateway_account':
            if not data or not data.get('user_id'):
                return redirect('/login?next=%2Faccount')
            return None
        if not data or not data.get('user_id'):
            if request.path.startswith(('/api/', '/analytics/')) or request.path == '/test-db':
                return jsonify(erreur='Authentification requise.'), 401
            if request.method not in {'GET', 'HEAD'}:
                return jsonify(erreur='Authentification requise.'), 401
            return redirect(url_for('gateway_login', next=request.full_path.rstrip('?')))
        if cfg['AUTH_PROFILE'] == 'private' and data['user'].get('email') != cfg['AUTH_ADMIN_EMAIL']:
            store.delete_session(data['id'])
            g.clear_auth_cookie = True
            return redirect('/login')
        if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            origin = request.headers.get('Origin')
            if origin and origin.rstrip('/') != request.host_url.rstrip('/'):
                return jsonify(erreur='Origine non autorisée.'), 403
            if request.path.startswith('/api/') and not csrf_ok(data):
                return jsonify(erreur='Jeton de sécurité expiré. Rechargez la page.'), 403
            if request.path.startswith('/analytics/') and request.headers.get('Sec-Fetch-Site') == 'cross-site':
                return jsonify(erreur='Origine non autorisée.'), 403

    @app.after_request
    def auth_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Cache-Control', 'no-store')
        if request.endpoint in {'gateway_login', 'gateway_register', 'gateway_account', 'gateway_health', 'static'}:
            response.headers.setdefault('Content-Security-Policy',
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
                "connect-src 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'")
            response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        if getattr(g, 'new_auth_sid', None):
            set_cookie(response, g.new_auth_sid)
        elif getattr(g, 'clear_auth_cookie', False):
            set_cookie(response, '', clear=True)
        return response

    def rotate_for(user_id: str | None):
        old_id = getattr(g, 'auth_sid', None)
        csrf = secrets.token_urlsafe(32)
        new_id = store.rotate_session(old_id, user_id, csrf, cfg['AUTH_SESSION_TTL_SECONDS'])
        g.auth_sid = new_id
        g.auth_session = store.get_session(new_id)
        g.new_auth_sid = new_id
        return g.auth_session

    def auth_page(title: str, error: str | None = None, **values):
        return render_template(title + '.html', error=error, **values)

    @app.get('/health')
    def gateway_health():
        return jsonify(status='ok', component='auth-gateway')

    @app.route('/login', methods=['GET', 'POST'])
    def gateway_login():
        current = g.auth_session
        target = safe_next(request.values.get('next'))
        if request.method == 'GET':
            return auth_page('login', next_url=target, csrf=current['csrf'])
        if not csrf_ok(current):
            return auth_page('login', 'Votre formulaire a expiré. Rechargez la page.', next_url=target, csrf=current['csrf']), 403
        email = normalize_email(request.form.get('email', ''))
        password = request.form.get('password', '')
        if len(email) > 254 or not EMAIL_RE.fullmatch(email):
            return auth_page('login', 'Adresse email ou mot de passe incorrect.', next_url=target, csrf=current['csrf']), 400
        ip = request.remote_addr or 'unknown'
        keys = [_attempt_key('login-email-ip', email + '|' + ip), _attempt_key('login-email', email), _attempt_key('login-ip', ip)]
        permitted = all(store.consume_attempt(key, cfg['AUTH_MAX_LOGIN_ATTEMPTS'], cfg['AUTH_LOGIN_WINDOW_SECONDS']) for key in keys)
        user = store.get_user_by_email(email) if permitted else None
        ok = bool(user and user['status'] == 'active' and
                  (cfg['AUTH_PROFILE'] != 'private' or user['email'] == cfg['AUTH_ADMIN_EMAIL']) and
                  verify_password(password, user['password_hash']))
        if not user or not permitted:
            verify_password(password or ' ', DUMMY_PASSWORD_HASH)
        if not ok:
            return auth_page('login', 'Adresse email ou mot de passe incorrect.', next_url=target, csrf=current['csrf']), 401
        for key in keys:
            store.clear_attempt(key)
        rotate_for(user['id'])
        return redirect(target)

    @app.route('/register', methods=['GET', 'POST'])
    def gateway_register():
        current = g.auth_session
        if not cfg['AUTH_ALLOW_REGISTRATION']:
            return auth_page('register', 'La création de compte est désactivée pour cette base privée.', csrf=current['csrf']), 403
        tunnel.initialize()
        if cfg['AUTH_PROFILE'] == 'multi_user' and (cfg['AUTH_ENV'] != 'local' or tunnel.public_demo):
            return auth_page('register', 'L’inscription est disponible uniquement en local avec le stockage isolé.', csrf=current['csrf']), 403
        if cfg['AUTH_PROFILE'] == 'demo' and not tunnel.public_demo:
            return auth_page('register', 'L’inscription du mode démo exige un jeu synthétique.', csrf=current['csrf']), 403
        if request.method == 'GET':
            return auth_page('register', csrf=current['csrf'])
        if not csrf_ok(current):
            return auth_page('register', 'Votre formulaire a expiré. Rechargez la page.', csrf=current['csrf']), 403
        first = request.form.get('first_name', '').strip()
        last = request.form.get('last_name', '').strip()
        email = normalize_email(request.form.get('email', ''))
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        errors = []
        if not valid_name(first) or not valid_name(last):
            errors.append('Saisissez un prénom et un nom valides.')
        if len(email) > 254 or not EMAIL_RE.fullmatch(email):
            errors.append('Saisissez une adresse email valide.')
        if not valid_password(password):
            errors.append('Le mot de passe doit contenir au moins 12 caractères, une lettre et un chiffre.')
        if password != confirm:
            errors.append('La confirmation du mot de passe ne correspond pas.')
        if errors:
            return auth_page('register', ' '.join(errors), csrf=current['csrf'], first_name=first, last_name=last, email=email), 400
        ip_key = _attempt_key('register-ip', request.remote_addr or 'unknown')
        if not store.consume_attempt(ip_key, 10, 3600):
            return auth_page('register', 'Trop de créations depuis cette adresse. Réessayez plus tard.', csrf=current['csrf']), 429
        if not store.create_user(first, last, email, hash_password(password), role='student' if cfg['AUTH_PROFILE'] == 'multi_user' else 'demo'):
            return auth_page('register', 'Un compte existe déjà avec cette adresse email.', csrf=current['csrf'], first_name=first, last_name=last, email=email), 409
        created = store.get_user_by_email(email)
        rotate_for(created['id'])
        return redirect('/account')

    @app.get('/account')
    def gateway_account():
        user = g.auth_session['user']
        return auth_page('account', user=user, csrf=g.auth_session['csrf'], profile=cfg['AUTH_PROFILE'])

    @app.post('/auth/logout')
    def gateway_logout():
        current = g.auth_session
        store.delete_session(current['id'])
        g.auth_session = None
        g.clear_auth_cookie = True
        response = redirect('/login')
        response.delete_cookie(COOKIE_NAME, path='/', secure=cfg['AUTH_COOKIE_SECURE'], httponly=True, samesite='Strict')
        return response

    @app.route('/api/auth/session', methods=['GET'])
    def gateway_auth_session():
        tunnel.initialize()
        current = g.auth_session
        return jsonify(configured=True, authenticated=True, csrf=current['csrf'],
                       public_demo=tunnel.public_demo, gateway_profile=cfg['AUTH_PROFILE'])

    @app.route('/api/auth/logout', methods=['POST'])
    def gateway_api_logout():
        # The embedded application's legacy logout becomes a real gateway logout.
        current = g.auth_session
        if not current or not csrf_ok(current):
            return jsonify(erreur='Jeton de sécurité expiré.'), 403
        store.delete_session(current['id'])
        g.clear_auth_cookie = True
        response = jsonify(message='Déconnexion effectuée.')
        response.delete_cookie(COOKIE_NAME, path='/', secure=cfg['AUTH_COOKIE_SECURE'], httponly=True, samesite='Strict')
        return response

    @app.route('/api/auth/login', methods=['GET', 'POST'])
    @app.route('/api/auth/setup', methods=['GET', 'POST'])
    def block_legacy_auth():
        return jsonify(erreur='Utilisez la passerelle d’authentification.'), 404

    @app.route('/', defaults={'path': ''}, methods=['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
    @app.route('/<path:path>', methods=['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
    def proxy_to_application(path: str):
        if path.startswith('_auth/'):
            abort(404)
        if path == 'api/auth/session':
            return gateway_auth_session()
        if path == 'api/auth/logout':
            return gateway_api_logout()
        if path in {'api/auth/login', 'api/auth/setup'}:
            return block_legacy_auth()
        current = g.auth_session
        if not current or not current.get('user_id'):
            return jsonify(erreur='Authentification requise.'), 401
        tunnel.initialize()
        incoming = {key: value for key, value in request.headers.items()
                    if key.lower() not in {'cookie', 'host', 'content-length', 'connection', 'x-forwarded-for', 'x-csrf-token', 'x-internal-user-id'}}
        if cfg['AUTH_PROFILE'] == 'multi_user':
            incoming['X-Internal-User-ID'] = '__admin__' if current['user'].get('role') == 'admin' else str(current['user_id'])
        status, headers_out, content = tunnel.request(path, request.method, request.query_string.decode('latin1'),
                                                       request.get_data(cache=False), incoming, request.headers.get('Origin'))
        response = make_response(content, status)
        for key, value in headers_out:
            if key.lower() not in {'set-cookie', 'content-length', 'content-encoding', 'connection'}:
                response.headers[key] = value
        response.headers.pop('Set-Cookie', None)
        return response

    return app


if __name__ == '__main__':
    from .launcher import run_gateway_only
    run_gateway_only()
