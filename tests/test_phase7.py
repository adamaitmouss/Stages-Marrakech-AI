import io
import sqlite3
from datetime import date

from backend.collectors.catalog import source_catalog
from backend.collectors.provided_offers import parse_provided_offers
from backend.db import connect
from backend.assistant import retrieve


def _csv(title='Stage PFE Python SQL', source_id='employer-2026-1'):
    return (f'titre,id source,entreprise,ville,description,type de stage,compétences,date de publication,url\n'
            f'{title},{source_id},Entreprise légale,Marrakech,Stage de test Python et SQL,Stage PFE,"Python; SQL",{date.today().isoformat()},https://employer.example/jobs/{source_id}\n').encode()


def _file_form(data, filename='offres.csv', permissions=True):
    return {
        'file': (io.BytesIO(data), filename),
        'source_name': 'Entreprise source autorisée',
        'permission_ref': 'licence-test-2026-01',
        'consultation_allowed': str(permissions).lower(),
        'storage_allowed': str(permissions).lower(),
        'display_allowed': str(permissions).lower(),
    }


def test_provided_offer_file_requires_all_rights_and_valid_https_urls(app, client):
    rejected = client.post('/api/collect/offers/file/preview', data=_file_form(_csv(), permissions=False), content_type='multipart/form-data')
    assert rejected.status_code == 400
    items, errors = parse_provided_offers('offres.csv', _csv(), 'Entreprise source autorisée')
    assert len(items) == 1 and not errors
    assert items[0]['source'] == 'Entreprise source autorisée'
    invalid, errors = parse_provided_offers('offres.csv', _csv().replace(b'https://', b'http://'), 'Entreprise source autorisée')
    assert invalid == [] and errors[0]['row'] == 2
    with connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT COUNT(*) FROM collector_staging').fetchone()[0] == 0


def test_provided_file_import_is_previewed_reviewed_and_syncs_all_local_modules(app, client, tmp_path):
    path = app.config['DATABASE']
    with connect(path) as db:
        db.execute("UPDATE alert_preferences SET domain='Data Science',skills_json='[\"Python\",\"SQL\"]',city='Marrakech',minimum_score=40,enabled=1 WHERE id=1")
    valid_row=_csv().splitlines()[1]+b'\n'
    content = _csv() + valid_row + ' ,bad-id,Entreprise légale,Marrakech,broken,Stage PFE,Python,2026-11-06,https://employer.example/jobs/bad\n'.encode()
    preview = client.post('/api/collect/offers/file/preview', data=_file_form(content), content_type='multipart/form-data')
    assert preview.status_code == 201
    run_id = preview.json['id']
    assert preview.json['rejected_rows'] == 1 and preview.json['duplicate_rows'] == 1
    assert preview.json['fetched_count'] == 2 and preview.json['staged_count'] == 1
    preview_source=next(s for s in source_catalog(path) if s['name']=='Fichier fourni — Entreprise source autorisée')
    assert preview_source['detected_offers']==2 and preview_source['duplicates_last_run']==1
    assert preview_source['rejected_offers_last_run']==1 and preview_source['imported_offers_last_run']==0
    staged = preview.json['run']['staged']
    assert len(staged) == 1 and staged[0]['decision'] == 'pending'
    before = client.get('/api/offres').json
    assert not any(o['source'].startswith('Fichier fourni') for o in before)
    stage_id = staged[0]['id']
    assert client.post(f'/api/collect/runs/{run_id}/staged/{stage_id}/decision', json={'decision':'approved'}).status_code == 200
    denied = client.post(f'/api/collect/runs/{run_id}/import', json={'sources':[staged[0]['source']], 'rights_confirmed':False})
    assert denied.status_code == 400
    imported = client.post(f'/api/collect/runs/{run_id}/import', json={'sources':[staged[0]['source']], 'rights_confirmed':True})
    assert imported.status_code == 200 and imported.json['new_offers'] == 1 and imported.json['duplicates'] == 1
    offer = next(o for o in client.get('/api/offres').json if o['source'].startswith('Fichier fourni'))
    assert offer['Titre'] == 'Stage PFE Python SQL' and offer['Lien public'].endswith('/employer-2026-1')
    assistant = retrieve(path, 'Stage PFE Python SQL à Marrakech')
    assert any(item['id'] == offer['ID'] for item in assistant['offers'])
    profile = {'skills':['Python','SQL'], 'education':'Data Science', 'experience':'Projet', 'domain':'Data Science', 'location':'Marrakech', 'opportunity':'Stage PFE'}
    matched = client.post('/api/matching', json={'profile':profile,'weights':app.config['MATCH_WEIGHTS']})
    assert matched.status_code == 200 and any(item['offer']['ID'] == offer['ID'] for item in matched.json['results'])
    assert any(a['offer_id'] == offer['ID'] for a in client.get('/api/alerts').json)
    with connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM offer_source_identity WHERE source=?',(offer['source'],)).fetchone()[0]==1
        row = db.execute('SELECT imported_offers,rejected_offers,imported_at,source_metadata_json FROM collector_runs WHERE id=?',(run_id,)).fetchone()
        assert row['imported_offers'] == 1 and row['rejected_offers'] == 1 and row['imported_at']
        assert 'file_sha256' in row['source_metadata_json']
        assert db.execute('SELECT COUNT(*) FROM candidatures').fetchone()[0] == 5
        assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    source = next(s for s in source_catalog(path) if s['name'] == offer['source'])
    assert source['imported_offers_last_run'] == 1 and source['rejected_offers_last_run'] == 1


def test_provided_offer_file_upsert_is_idempotent(app, client):
    source_name = 'Entreprise source autorisée'
    source = 'Fichier fourni — ' + source_name
    for _ in range(2):
        preview = client.post('/api/collect/offers/file/preview', data=_file_form(_csv()), content_type='multipart/form-data')
        run_id = preview.json['id']
        stage = preview.json['run']['staged'][0]
        client.post(f'/api/collect/runs/{run_id}/staged/{stage["id"]}/decision', json={'decision':'approved'})
        result = client.post(f'/api/collect/runs/{run_id}/import', json={'sources':[source], 'rights_confirmed':True})
        assert result.status_code == 200
    assert result.json['new_offers'] == 0 and result.json['unchanged_offers'] == 1
    assert len([o for o in client.get('/api/offres').json if o['source'] == source]) == 1
    assert sqlite3.connect(app.config['DATABASE']).execute('PRAGMA integrity_check').fetchone()[0] == 'ok'


def test_source_register_separates_open_data_and_unlicensed_job_feeds(app):
    sources = {s['name']:s for s in source_catalog(app.config['DATABASE'])}
    jawb = sources['Jawb RSS']
    assert jawb['authorization_status'] == 'pending'
    assert 'Non attestée' in jawb['storage_permission']
    open_data = sources['Portail Open Data Maroc']
    assert open_data['authorization_status'] == 'licensed_non_offer_data'
    assert 'pas de flux général' in open_data['fields']
    cap = sources['Trouve Ton Emploi / CAPPRAfrica']
    assert cap['authorization_status'] == 'license_required'
    assert cap['last_status'] == 'not_run'


def test_network_source_settings_require_three_permission_scopes_and_https(client, app):
    missing = client.post('/api/collect/settings', json={
        'jawb_import_approved':True,'jawb_permission_ref':'permission-doc-1','rights_confirmed':True,
        'jawb_consult_allowed':True,'jawb_storage_allowed':True,
    })
    assert missing.status_code == 400
    bad_url = client.post('/api/collect/settings', json={
        'career_feeds':[{'name':'Feed','url':'http://127.0.0.1/private.xml','permission_ref':'doc',
                         'consultation_allowed':True,'storage_allowed':True,'display_allowed':True}],
    })
    assert bad_url.status_code == 400
    good = client.post('/api/collect/settings', json={
        'jawb_import_approved':True,'jawb_permission_ref':'permission-doc-1','rights_confirmed':True,
        'jawb_consult_allowed':True,'jawb_storage_allowed':True,'jawb_display_allowed':True,
    })
    assert good.status_code == 200
    assert good.json['external_enabled'] is False
    assert app.config['DATABASE']
