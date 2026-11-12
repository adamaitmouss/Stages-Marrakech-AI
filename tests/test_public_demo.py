import sqlite3
from pathlib import Path

import pytest

from backend.db import connect
from scripts.create_public_demo_database import create_public_demo_database


def test_public_demo_is_synthetic_read_only_and_private_data_free(tmp_path):
    from backend.web import create_app
    database=Path(create_public_demo_database(tmp_path/'demo.db'))
    before=sqlite3.connect(database)
    original=(before.execute('SELECT count(*) FROM entreprises').fetchone()[0],
              before.execute('SELECT count(*) FROM offres').fetchone()[0],
              before.execute('SELECT count(*) FROM candidatures').fetchone()[0])
    before.close()
    app=create_app({'DATABASE':str(database),'PRIVATE_DIR':str(tmp_path/'private'),'BACKUP_DIR':str(tmp_path/'backups'),
        'PUBLIC_DEMO_MODE':True,'PUBLIC_DEMO_DATA_CONFIRMED':True,'DISABLE_BACKGROUND_SCHEDULER':True,'TESTING':True,
        'GEMINI_ENABLED':False,'GEMINI_SEARCH_ENABLED':False,'SMTP_ENABLED':False})
    client=app.test_client()
    auth=client.get('/api/auth/session')
    assert auth.status_code==200 and auth.json['authenticated'] is True and auth.json['public_demo'] is True
    csrf=auth.json['csrf'];headers={'X-CSRF-Token':csrf}
    assert client.get('/api/statistiques').json['total_entreprises']==5
    assert client.get('/api/cvs').json==[]
    assert client.get('/recherche-ia.html').status_code==200
    assert client.post('/api/candidatures',json={'nom_entreprise':'private'},headers=headers).status_code==403
    assert client.post('/api/alerts/read-all',json={},headers=headers).status_code==403
    assert client.post('/api/assistant/chat',json={'mode':'gemini','question':'private'},headers=headers).status_code==403
    chatbot=client.post('/api/assistant/chat',json={'mode':'local','question':'Stage Python à Marrakech'},headers=headers)
    assert chatbot.status_code==200,chatbot.json
    criteria={'prompt':'Stage PFE Python à Marrakech cette semaine','city':'Marrakech','domain':'Python',
              'opportunity_type':'Stage PFE','period':'7d','max_results':3}
    assert client.post('/api/ai-search/local',json=criteria,headers=headers).status_code==200
    assert client.get('/analytics/').status_code==200
    with connect(str(database)) as db:
        after=(db.execute('SELECT count(*) FROM entreprises').fetchone()[0],
               db.execute('SELECT count(*) FROM offres').fetchone()[0],
               db.execute('SELECT count(*) FROM candidatures').fetchone()[0])
        assert db.execute('SELECT count(*) FROM assistant_messages').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM gemini_search_history').fetchone()[0]==0
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert after==original


def test_public_mode_refuses_database_without_synthetic_marker(tmp_path,legacy_database):
    from backend.web import create_app
    with pytest.raises(RuntimeError,match='synthétique'):
        create_app({'DATABASE':str(legacy_database),'PRIVATE_DIR':str(tmp_path/'private'),
            'BACKUP_DIR':str(tmp_path/'backups'),'PUBLIC_DEMO_MODE':True,
            'PUBLIC_DEMO_DATA_CONFIRMED':True,'DISABLE_BACKGROUND_SCHEDULER':True})


def test_public_mode_requires_explicit_data_attestation(tmp_path):
    from backend.web import create_app
    with pytest.raises(RuntimeError,match='attestation'):
        create_app({'DATABASE':str(tmp_path/'missing.db'),'PRIVATE_DIR':str(tmp_path/'private'),
            'BACKUP_DIR':str(tmp_path/'backups'),'PUBLIC_DEMO_MODE':True,
            'PUBLIC_DEMO_DATA_CONFIRMED':False})


def test_public_mode_refuses_missing_database_without_creating_it(tmp_path):
    from backend.web import create_app
    database=tmp_path/'missing.db'
    with pytest.raises(RuntimeError,match='Base publique absente'):
        create_app({'DATABASE':str(database),'PRIVATE_DIR':str(tmp_path/'private'),
            'BACKUP_DIR':str(tmp_path/'backups'),'PUBLIC_DEMO_MODE':True,
            'PUBLIC_DEMO_DATA_CONFIRMED':True})
    assert not database.exists()
