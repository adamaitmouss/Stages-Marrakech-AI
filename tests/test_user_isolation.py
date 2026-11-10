import sqlite3
import uuid


def test_multi_user_backend_isolates_personal_data_and_preserves_historical_source(
        legacy_database, tmp_path, monkeypatch, cv_data):
    from backend.web import create_app

    data_root = tmp_path / 'private' / 'user_data'
    monkeypatch.setenv('AUTH_MULTI_USER_MODE', 'true')
    monkeypatch.setenv('AUTH_USER_DATA_ROOT', str(data_root))
    secret = 'test-internal-secret-' + ('x' * 50)
    monkeypatch.setenv('AUTH_INTERNAL_SECRET', secret)
    app = create_app({'DATABASE': str(legacy_database), 'PRIVATE_DIR': str(tmp_path / 'private'),
                      'BACKUP_DIR': str(tmp_path / 'backups'), 'AUTH_USER_DATA_ROOT': str(data_root),
                      'TESTING': True, 'SMTP_ENABLED': False})
    client = app.test_client()

    denied = client.get('/api/candidatures', headers={'X-Internal-User-ID': str(uuid.uuid4())})
    assert denied.status_code == 401
    handshake = client.post('/api/internal/gateway-session', json={}, headers={
        'X-Internal-Gateway-Secret': secret})
    assert handshake.status_code == 200
    csrf = handshake.json['csrf']
    user_a, user_b = str(uuid.uuid4()), str(uuid.uuid4())
    from backend.user_data import provision_user_database
    first_db, _ = provision_user_database(legacy_database, data_root, user_a)
    assert first_db.is_file()

    def request_as(user, method, path, **kwargs):
        headers = kwargs.pop('headers', {})
        headers['X-Internal-User-ID'] = user
        if method != 'get':
            headers['X-CSRF-Token'] = csrf
        return getattr(client, method)(path, headers=headers, **kwargs)

    assert request_as(user_a, 'get', '/api/candidatures').json == []
    assert request_as(user_b, 'get', '/api/candidatures').json == []
    app_a = request_as(user_a, 'post', '/api/candidatures', json={
        'nom_entreprise': 'Étudiant A', 'date_candidature': '2026-11-10', 'statut': 'Non envoyée'})
    assert app_a.status_code == 201
    cv_a = request_as(user_a, 'post', '/api/cvs', json={
        'name': 'CV privé A', 'template': 'modern', 'data': cv_data})
    assert cv_a.status_code == 201

    assert len(request_as(user_a, 'get', '/api/candidatures').json) == 1
    assert len(request_as(user_a, 'get', '/api/cvs').json) == 1
    assert request_as(user_b, 'get', '/api/candidatures').json == []
    assert request_as(user_b, 'get', '/api/cvs').json == []
    assert request_as(user_b, 'get', '/api/assistant/history').json['messages'] == []
    assert request_as(user_a, 'get', '/api/statistiques').json['total_candidatures'] == 1
    assert request_as(user_b, 'get', '/api/statistiques').json['total_candidatures'] == 0

    user_dbs = list(data_root.glob('*.db'))
    assert len(user_dbs) == 2 and user_dbs[0] != user_dbs[1]
    for path in user_dbs:
        with sqlite3.connect(path) as db:
            assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            assert db.execute('SELECT COUNT(*) FROM entreprises').fetchone()[0] == 2
            assert db.execute('SELECT COUNT(*) FROM offres').fetchone()[0] == 3
    with sqlite3.connect(legacy_database) as db:
        assert db.execute('SELECT COUNT(*) FROM candidatures').fetchone()[0] == 5
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'


def test_per_user_dash_reads_the_matching_isolated_database(app, tmp_path):
    from flask import g
    from backend.user_data import provision_user_database

    source = app.config['DATABASE']
    first, _ = provision_user_database(source, tmp_path / 'users', str(uuid.uuid4()))
    second, _ = provision_user_database(source, tmp_path / 'users', str(uuid.uuid4()))
    with sqlite3.connect(first) as db:
        db.execute("INSERT INTO candidatures(nom_entreprise,date_candidature,statut) VALUES ('Espace A','2026-11-10','Envoyée')")
    dash = app.extensions['analytics']

    def count_for(path):
        with app.test_request_context('/analytics/update'):
            g.user_database_path = str(path)
            _, kpis, _ = dash.audit_callbacks['update'](
                'applications', 'statut', 'bar', None, None, None, None, None, None, 0, 0)
            return [item.children[1].children for item in kpis]

    assert count_for(first)[2] == '1'
    assert count_for(second)[2] == '0'
