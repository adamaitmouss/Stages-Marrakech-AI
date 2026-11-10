from __future__ import annotations

import re
import os
import socket
import shutil
import sqlite3

import pytest

from auth_gateway.app import COOKIE_NAME, create_app
from auth_gateway.proxy import BackendTunnel


class FakeTunnel:
    def __init__(self, public_demo=True):
        self.public_demo = public_demo
        self.ready = False
        self.last_headers = None

    def initialize(self):
        self.ready = True

    def request(self, path, method, query, body, headers, external_origin):
        self.last_headers = {**headers, 'X-CSRF-Token': 'backend-csrf'}
        return 200, [('Content-Type', 'application/json')], b'{"proxied":true}'


@pytest.fixture
def app_factory(tmp_path, monkeypatch):
    made = []

    def build(profile='multi_user', tunnel=None, max_attempts=5, secure=False):
        dbfile = tmp_path / f'auth-{len(made)}.db'
        monkeypatch.setenv('AUTH_SESSION_SECRET', 'local-test-secret-' + ('x' * 40))
        monkeypatch.setenv('AUTH_DATABASE_URL', 'sqlite:///' + dbfile.as_posix())
        monkeypatch.setenv('AUTH_PROFILE', profile)
        monkeypatch.setenv('AUTH_ALLOW_REGISTRATION', 'true' if profile == 'multi_user' else 'false')
        monkeypatch.setenv('AUTH_ENV', 'local')
        monkeypatch.setenv('AUTH_MAX_LOGIN_ATTEMPTS', str(max_attempts))
        monkeypatch.setenv('AUTH_LOGIN_WINDOW_SECONDS', '900')
        monkeypatch.setenv('AUTH_COOKIE_SECURE', 'true' if secure else 'false')
        if profile == 'private':
            monkeypatch.setenv('AUTH_ADMIN_EMAIL', 'admin@example.test')
            monkeypatch.setenv('AUTH_BOOTSTRAP_ADMIN_PASSWORD', 'Bootstrap-Admin-932!')
        else:
            monkeypatch.delenv('AUTH_ADMIN_EMAIL', raising=False)
            monkeypatch.delenv('AUTH_BOOTSTRAP_ADMIN_PASSWORD', raising=False)
        app = create_app({'ROOT': tmp_path, 'TESTING': True, 'AUTH_BACKEND_TUNNEL': tunnel or FakeTunnel(profile == 'demo')})
        made.append(app)
        return app

    return build


def csrf_from(response):
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match, response.data[:500]
    return match.group(1).decode()


def register(client, email='lea@example.test', password='Etudiant-Fort-2026!'):
    page = client.get('/register')
    token = csrf_from(page)
    return client.post('/register', data={'csrf_token': token, 'first_name': 'Léa', 'last_name': 'Benali',
                                         'email': email, 'password': password, 'confirm_password': password})


def login(client, email, password):
    page = client.get('/login')
    return client.post('/login', data={'csrf_token': csrf_from(page), 'email': email, 'password': password})


def test_register_valid_persists_hash_and_account_fields(app_factory):
    app = app_factory()
    client = app.test_client()
    login_page = client.get('/login')
    assert "Vous n'avez pas de compte ?" in login_page.get_data(as_text=True)
    assert 'href="/register"' in login_page.get_data(as_text=True)
    result = register(client)
    assert result.status_code == 302 and result.headers['Location'] == '/account'
    page = client.get('/account')
    assert 'Léa' in page.get_data(as_text=True) and 'lea@example.test' in page.get_data(as_text=True)
    user = app.extensions['auth_store'].get_user_by_email('lea@example.test')
    assert user['role'] == 'student' and user['status'] == 'active'
    assert user['password_hash'] != 'Etudiant-Fort-2026!'
    assert user['password_hash'].startswith('scrypt$')


@pytest.mark.parametrize('email,password,confirmation', [
    ('pas-une-adresse', 'Etudiant-Fort-2026!', 'Etudiant-Fort-2026!'),
    ('lea@example.test', 'short', 'short'),
    ('lea@example.test', 'Etudiant-Fort-2026!', 'Autre-Mot-de-passe-2026!'),
])
def test_registration_validation(email, password, confirmation, app_factory):
    client = app_factory().test_client()
    page = client.get('/register')
    result = client.post('/register', data={'csrf_token': csrf_from(page), 'first_name': 'Léa', 'last_name': 'Benali',
                                            'email': email, 'password': password, 'confirm_password': confirmation})
    assert result.status_code == 400


def test_duplicate_email_is_normalized_and_reported(app_factory):
    client = app_factory().test_client()
    assert register(client).status_code == 302
    client.post('/auth/logout', data={'csrf_token': csrf_from(client.get('/account'))})
    page = client.get('/register')
    result = client.post('/register', data={'csrf_token': csrf_from(page), 'first_name': 'Lea', 'last_name': 'Test',
                                            'email': 'LEA@EXAMPLE.TEST', 'password': 'Nouveau-Mdp-2026!',
                                            'confirm_password': 'Nouveau-Mdp-2026!'})
    assert result.status_code == 409
    assert 'existe déjà' in result.get_data(as_text=True)


def test_bad_password_is_generic_then_valid_login_and_logout_revokes_session(app_factory):
    app = app_factory()
    client = app.test_client()
    register(client)
    client.post('/auth/logout', data={'csrf_token': csrf_from(client.get('/account'))})
    denied = login(client, 'lea@example.test', 'incorrect-credential')
    assert denied.status_code == 401
    assert 'Adresse email ou mot de passe incorrect' in denied.get_data(as_text=True)
    success = login(client, 'lea@example.test', 'Etudiant-Fort-2026!')
    assert success.status_code == 302
    account = client.get('/account')
    token = csrf_from(account)
    assert client.post('/auth/logout', data={'csrf_token': token}).status_code == 302
    assert client.get('/api/assistant/status').status_code == 401
    assert client.get('/index.html').status_code == 302
    assert client.get_cookie(COOKIE_NAME) is None


@pytest.mark.parametrize('path', ['/index.html', '/api/assistant/status', '/analytics/_dash-layout', '/api/cvs/1/pdf', '/api/auth/session'])
def test_private_routes_and_dash_are_protected_before_login(path, app_factory):
    response = app_factory().test_client().get(path)
    assert response.status_code in {302, 401}


def test_login_csrf_and_safe_next_reject_external_redirect(app_factory):
    client = app_factory().test_client()
    page = client.get('/login?next=https://evil.example/')
    token = csrf_from(page)
    bad = client.post('/login', data={'csrf_token': 'wrong', 'email': 'a@example.test', 'password': 'irrelevant'})
    assert bad.status_code == 403
    assert 'rel="noopener"' not in page.get_data(as_text=True)
    assert register(client).status_code == 302
    client.post('/auth/logout', data={'csrf_token': csrf_from(client.get('/account'))})
    result = login(client, 'lea@example.test', 'Etudiant-Fort-2026!')
    assert result.headers['Location'] == '/index.html'


def test_api_proxy_replaces_browser_csrf_with_private_backend_token(app_factory):
    tunnel = FakeTunnel(False)
    app = app_factory(tunnel=tunnel)
    client = app.test_client()
    register(client)
    status = client.get('/api/auth/session').get_json()
    assert status['authenticated'] and not status['public_demo'] and status['csrf']
    denied = client.post('/api/example', json={'sample': True})
    assert denied.status_code == 403
    allowed = client.post('/api/example', json={'sample': True}, headers={'X-CSRF-Token': status['csrf']})
    assert allowed.status_code == 200 and allowed.get_json()['proxied']
    assert tunnel.last_headers['X-CSRF-Token'] != status['csrf']
    assert tunnel.last_headers['X-CSRF-Token'] == 'backend-csrf'


def test_legacy_backend_login_routes_cannot_bypass_gateway(app_factory):
    client = app_factory().test_client()
    register(client)
    assert client.get('/api/auth/login').status_code == 404
    assert client.post('/api/auth/setup', json={'password': 'weak'}).status_code == 403


def test_existing_application_logout_endpoint_invalidates_gateway_session(app_factory):
    client = app_factory().test_client()
    register(client)
    csrf = client.get('/api/auth/session').get_json()['csrf']
    result = client.post('/api/auth/logout', json={}, headers={'X-CSRF-Token': csrf})
    assert result.status_code == 200
    assert result.get_json()['message'] == 'Déconnexion effectuée.'
    assert client.get('/api/assistant/status').status_code == 401


def test_rate_limit_applies_by_email_and_source_address(app_factory):
    client = app_factory(max_attempts=2).test_client()
    register(client)
    client.post('/auth/logout', data={'csrf_token': csrf_from(client.get('/account'))})
    for _ in range(2):
        assert login(client, 'lea@example.test', 'wrong-password').status_code == 401
    assert login(client, 'lea@example.test', 'Etudiant-Fort-2026!').status_code == 401


def test_expired_session_is_invalidated(app_factory):
    app = app_factory()
    client = app.test_client()
    register(client)
    cookie = client.get_cookie(COOKIE_NAME)
    store = app.extensions['auth_store']
    # An expired, correctly signed cookie must not restore authentication.
    from itsdangerous import URLSafeTimedSerializer
    serializer = URLSafeTimedSerializer(app.secret_key, salt='stages-auth-gateway-v1')
    session_id = serializer.loads(cookie.value)['sid']
    store.execute('UPDATE auth_sessions SET expires_at=? WHERE id=?', (0, session_id))
    client.set_cookie(COOKIE_NAME, serializer.dumps({'sid': session_id}))
    response = client.get('/account')
    assert response.status_code == 302 and response.headers['Location'].startswith('/login')


def test_account_cookie_flags_and_persistence_across_app_restart(app_factory):
    app = app_factory()
    client = app.test_client()
    result = register(client)
    cookie_header = result.headers.get('Set-Cookie', '')
    assert 'HttpOnly' in cookie_header and 'SameSite=Strict' in cookie_header
    value = client.get_cookie(COOKIE_NAME).value
    second_app = create_app({'ROOT': app.config['ROOT'], 'TESTING': True,
        'AUTH_DATABASE_URL': app.config['AUTH_DATABASE_URL'], 'AUTH_SESSION_SECRET': app.config['AUTH_SESSION_SECRET'],
        'AUTH_PROFILE': 'multi_user', 'AUTH_ALLOW_REGISTRATION': True, 'AUTH_BACKEND_TUNNEL': FakeTunnel(False)})
    second = second_app.test_client()
    second.set_cookie(COOKIE_NAME, value)
    assert second.get('/account').status_code == 200
    assert second_app.extensions['auth_store'].get_user_by_email('lea@example.test')['status'] == 'active'


def test_private_profile_bootstraps_only_named_admin_and_disables_signup(app_factory):
    app = app_factory(profile='private', tunnel=FakeTunnel(False))
    store = app.extensions['auth_store']
    assert store.get_user_by_email('admin@example.test')['role'] == 'admin'
    client = app.test_client()
    page = client.get('/register')
    assert page.status_code == 403
    denied = login(client, 'other@example.test', 'Etudiant-Fort-2026!')
    assert denied.status_code == 401
    accepted = login(client, 'admin@example.test', 'Bootstrap-Admin-932!')
    assert accepted.status_code == 302 and accepted.headers['Location'] == '/index.html'
    assert client.get('/account').status_code == 200
    logout_csrf = csrf_from(client.get('/account'))
    assert client.post('/auth/logout', data={'csrf_token':logout_csrf}).status_code == 302
    assert client.get('/account').status_code == 302


def test_synthetic_demo_profile_does_not_allow_shared_account_registration(app_factory):
    app = app_factory(profile='demo', tunnel=FakeTunnel(True))
    client = app.test_client()
    login_page = client.get('/login')
    assert 'Créer un compte' not in login_page.get_data(as_text=True)
    assert client.get('/register').status_code == 403


def test_gateway_refuses_nonisolated_private_mode_with_open_signup(monkeypatch):
    monkeypatch.setenv('AUTH_SESSION_SECRET', 'test-private-secret-' + ('k' * 40))
    monkeypatch.setenv('AUTH_PROFILE', 'private')
    monkeypatch.setenv('AUTH_ALLOW_REGISTRATION', 'true')
    monkeypatch.setenv('AUTH_ADMIN_EMAIL', 'admin@example.test')
    with pytest.raises(RuntimeError, match='profil multi_user'):
        from auth_gateway.config import load_config
        load_config()


def test_origin_and_csrf_block_cross_site_writes(app_factory):
    client = app_factory().test_client()
    register(client)
    csrf = client.get('/api/auth/session').get_json()['csrf']
    response = client.post('/api/example', json={'sample': True}, headers={
        'X-CSRF-Token': csrf, 'Origin': 'https://evil.example'})
    assert response.status_code == 403


def test_secure_cookie_flag_can_be_enabled(app_factory):
    client = app_factory(secure=True).test_client()
    response = register(client)
    assert 'Secure' in response.headers.get('Set-Cookie', '')


@pytest.mark.parametrize('environment,backend,db,expected', [
    ('local', 'https://public.example', 'sqlite:///auth_gateway/data/users.db', 'backend distant'),
    ('production', 'http://internal-backend:5101', 'sqlite:///auth_gateway/data/users.db', 'PostgreSQL'),
    ('production', 'https://backend.example.com', 'postgresql://private/db', 'adresse privée/interne'),
    ('production', 'http://internal-backend:5101', 'postgresql://private/db', 'sslmode'),
])
def test_configuration_fails_closed_for_public_backend_or_ephemeral_production_db(
        monkeypatch, environment, backend, db, expected):
    monkeypatch.setenv('AUTH_PROFILE', 'demo')
    monkeypatch.setenv('AUTH_ALLOW_REGISTRATION', 'false')
    monkeypatch.setenv('AUTH_SESSION_SECRET', 'test-config-secret-' + ('z' * 40))
    monkeypatch.setenv('AUTH_ENV', environment)
    monkeypatch.setenv('AUTH_BACKEND_URL', backend)
    monkeypatch.setenv('AUTH_DATABASE_URL', db)
    monkeypatch.delenv('AUTH_TRUSTED_PRIVATE_BACKEND', raising=False)
    if environment == 'production':
        monkeypatch.setenv('AUTH_TRUSTED_PRIVATE_BACKEND', 'true')
        monkeypatch.setenv('AUTH_COOKIE_SECURE', 'true')
        monkeypatch.setenv('AUTH_TRUSTED_PROXY_HOPS', '1')
        monkeypatch.setenv('AUTH_ALLOWED_HOSTS', 'example.test')
    from auth_gateway.config import load_config
    with pytest.raises(RuntimeError, match=expected):
        load_config()


class MockResponse:
    def __init__(self, status, payload=None, content=b'', headers=None):
        self.status_code = status
        self.payload = payload or {}
        self.content = content
        self.headers = headers or {}

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError('unexpected HTTP status')


class MockBackendHTTP:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(('POST', url, kwargs))
        return MockResponse(200, {'configured': True, 'authenticated': True, 'csrf': 'backend-csrf', 'public_demo': False})

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return MockResponse(200, content=b'private-response', headers={'Content-Type': 'text/plain'})


def test_backend_tunnel_uses_random_internal_channel_without_exposing_its_cookie(monkeypatch):
    import auth_gateway.proxy as proxy_module
    session = MockBackendHTTP()
    monkeypatch.setattr(proxy_module.requests, 'Session', lambda: session)
    tunnel = BackendTunnel('http://127.0.0.1:5101', 'private', 'x' * 64)
    tunnel.initialize()
    assert session.calls[0][0] == 'POST'
    assert session.calls[0][1].endswith('/api/internal/gateway-session')
    assert session.calls[0][2]['headers']['X-Internal-Gateway-Secret'] == 'x' * 64
    status, headers, content = tunnel.request('api/private', 'POST', '', b'{}', {'Content-Type': 'application/json'}, 'http://127.0.0.1:5000')
    assert status == 200 and content == b'private-response'
    assert session.calls[-1][2]['headers']['X-CSRF-Token'] == 'backend-csrf'
    assert all(k.lower() != 'set-cookie' for k, _ in headers)


def test_backend_tunnel_rejects_demo_registration_on_private_backend(monkeypatch):
    import auth_gateway.proxy as proxy_module
    session = MockBackendHTTP()
    session.post = lambda *args, **kwargs: MockResponse(200, {'configured': True, 'authenticated': True, 'csrf': 'token', 'public_demo': False})
    monkeypatch.setattr(proxy_module.requests, 'Session', lambda: session)
    tunnel = BackendTunnel('http://127.0.0.1:5101', 'demo', 'x' * 64)
    with pytest.raises(RuntimeError, match='base synthétique'):
        tunnel.initialize()


def test_gateway_local_port_check_does_not_take_over_existing_listener():
    from auth_gateway.launcher import port_free
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0)); sock.listen()
    try:
        assert not port_free(sock.getsockname()[1])
    finally:
        sock.close()


def test_internal_secret_is_generated_and_reused_without_password_input(tmp_path,monkeypatch):
    from auth_gateway.launcher import ensure_internal_secret
    target=tmp_path/'private'/'gateway.secret'
    monkeypatch.setenv('AUTH_INTERNAL_SECRET_FILE',str(target))
    monkeypatch.delenv('AUTH_INTERNAL_SECRET',raising=False)
    ensure_internal_secret()
    first=os.environ['AUTH_INTERNAL_SECRET']
    assert len(first)>=48 and target.read_text(encoding='ascii').strip()==first
    monkeypatch.delenv('AUTH_INTERNAL_SECRET',raising=False)
    ensure_internal_secret()
    assert os.environ['AUTH_INTERNAL_SECRET']==first


def test_demo_database_preflight_reads_synthetic_copy_only(tmp_path):
    from auth_gateway.launcher import check_database
    source = __import__('pathlib').Path(__file__).resolve().parents[2] / 'database' / 'stages_marrakech_public_demo.db'
    copied = tmp_path / 'synthetic-copy.db'
    shutil.copy2(source, copied)
    before = copied.read_bytes()
    with sqlite3.connect(copied) as db:
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    config = {'ROOT': tmp_path, 'AUTH_APP_DATABASE': str(copied), 'AUTH_PROFILE': 'demo'}
    result = check_database(config)
    assert result['counts'] == {'candidatures': 3, 'entreprises': 5, 'offres': 4}
    assert result['marker'] == 'synthetic_public_demo'
    assert copied.read_bytes() == before


def test_gateway_end_to_end_with_unchanged_flask_app_dash_chat_and_matching(tmp_path, monkeypatch):
    import hashlib
    import json
    from pathlib import Path
    from requests import Response
    from werkzeug.test import Client as WsgiClient

    from auth_gateway.proxy import BackendTunnel
    from backend.web import create_app as create_existing_backend

    root = Path(__file__).resolve().parents[2]
    original = root / 'database' / 'stages_marrakech_public_demo.db'
    copy = tmp_path / 'backend-copy.db'
    shutil.copy2(original, copy)
    initial_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    monkeypatch.setenv('AUTH_INTERNAL_SECRET', 'e2e-internal-secret-' + ('z' * 64))
    backend = create_existing_backend({'DATABASE': str(copy), 'PRIVATE_DIR': str(tmp_path / 'private'),
        'BACKUP_DIR': str(tmp_path / 'backups'), 'PUBLIC_DEMO_MODE': True,
        'PUBLIC_DEMO_DATA_CONFIRMED': True, 'TESTING': True, 'SMTP_ENABLED': False,
        'GEMINI_ENABLED': False, 'GEMINI_SEARCH_ENABLED': False, 'MAPS_ENABLED': False})
    backend_client = WsgiClient(backend, use_cookies=False)

    class BridgeSession:
        def __init__(self):
            self.cookie = ''

        def dispatch(self, method, url, **kwargs):
            from urllib.parse import urlsplit
            parsed = urlsplit(url)
            headers = dict(kwargs.get('headers') or {})
            headers['Host'] = parsed.netloc
            if self.cookie:
                headers['Cookie'] = self.cookie
            result = backend_client.open(parsed.path + (('?' + parsed.query) if parsed.query else ''),
                method=method, data=kwargs.get('data'), headers=headers, follow_redirects=False,
                environ_overrides={'REMOTE_ADDR':'127.0.0.1'})
            for cookie in result.headers.getlist('Set-Cookie'):
                if cookie.startswith('session='):
                    self.cookie = cookie.split(';', 1)[0]
            response = Response()
            response.status_code = result.status_code
            response.headers.update(result.headers)
            response._content = result.get_data()
            response._content_consumed = True
            response.url = url
            response.reason = 'OK'
            return response

        def get(self, url, **kwargs):
            return self.dispatch('GET', url, **kwargs)

        def post(self, url, **kwargs):
            return self.dispatch('POST', url, **kwargs)

        def request(self, method, url, **kwargs):
            return self.dispatch(method, url, **kwargs)

    bridge = BridgeSession()
    monkeypatch.setattr('auth_gateway.proxy.requests.Session', lambda: bridge)
    monkeypatch.setenv('AUTH_SESSION_SECRET', 'integrated-test-secret-' + ('p' * 32))
    monkeypatch.setenv('AUTH_DATABASE_URL', 'sqlite:///' + (tmp_path / 'gateway-users.db').as_posix())
    monkeypatch.setenv('AUTH_PROFILE', 'demo')
    monkeypatch.setenv('AUTH_ALLOW_REGISTRATION', 'false')
    gateway = create_app({'ROOT': root, 'TESTING': True,
        'AUTH_BACKEND_TUNNEL': BackendTunnel('http://127.0.0.1:5101', 'demo', os.environ['AUTH_INTERNAL_SECRET'])})
    client = gateway.test_client()
    from auth_gateway.security import hash_password
    gateway.extensions['auth_store'].create_user('Test', 'Demo', 'integrated@example.test',
                                                  hash_password('Etudiant-Fort-2026!'), role='demo')
    assert login(client, 'integrated@example.test', 'Etudiant-Fort-2026!').status_code == 302
    page = client.get('/index.html')
    assert page.status_code == 200 and b'Stages Marrakech' in page.data
    assert client.get('/analytics/').status_code == 200
    assistant_status = client.get('/api/assistant/status')
    assert assistant_status.status_code == 200 and assistant_status.get_json()['local_available']
    csrf = client.get('/api/auth/session').get_json()['csrf']
    answer = client.post('/api/assistant/chat', json={'question': 'combien d’offres?', 'mode': 'local'},
                         headers={'X-CSRF-Token': csrf})
    assert answer.status_code == 200 and answer.get_json()['mode'] == 'local'
    match = client.post('/api/matching', json={'profile': {'skills': ['Python'], 'education': '', 'experience': '',
        'domain': 'Data', 'location': 'Marrakech', 'opportunity': 'Stage'}, 'mode': 'local'},
        headers={'X-CSRF-Token': csrf})
    assert match.status_code == 200 and 'results' in match.get_json()
    assert all(k.lower() != 'set-cookie' for k, _ in gateway.extensions['auth_tunnel'].request(
        'index.html', 'GET', '', b'', {}, 'http://127.0.0.1:5000')[1])
    assert hashlib.sha256(original.read_bytes()).hexdigest() == initial_hash
