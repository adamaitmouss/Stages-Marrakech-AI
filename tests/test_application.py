import io
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from pypdf import PdfReader
from backend.db import migrate
from backend.cv_service import make_pdf, extract_pdf, validate_cv
from backend.matching import rank
from backend.gemini_service import interpret, payload, extract_profile

PROFILE={'skills':['Python','Pandas'],'education':'Data Science','experience':'Projet Python nettoyage de données',
         'domain':'analyse de données','location':'Marrakech','opportunity':'Stage'}


def test_migration_preserves_five_and_is_idempotent(legacy_database,tmp_path):
    with sqlite3.connect(legacy_database) as db:
        before=db.execute('SELECT * FROM candidatures ORDER BY id').fetchall()
    migrate(str(legacy_database),tmp_path/'backups')
    migrate(str(legacy_database),tmp_path/'backups')
    with sqlite3.connect(legacy_database) as db:
        assert db.execute('SELECT id,nom_entreprise,secteur,email,telephone,date_candidature,statut,commentaire FROM candidatures ORDER BY id').fetchall()==before
        assert db.execute('SELECT COUNT(*) FROM candidature_history').fetchone()[0]==5
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    backups=list((tmp_path/'backups').glob('*.db'));assert len(backups)==1
    with sqlite3.connect(backups[0]) as db:
        assert db.execute('SELECT * FROM candidatures ORDER BY id').fetchall()==before


def test_auth_and_csrf_required(app):
    client=app.test_client()
    for url in ['/api/candidatures','/api/cvs','/api/matching','/analytics/_dash-layout','/backend/generated_cv/test.pdf','/database/stages_marrakech.db']:
        assert client.get(url).status_code in (401,404)
    assert client.post('/api/auth/setup',json={'password':'aaaaaaaaaaaa'}).status_code==403


def test_internal_gateway_session_requires_random_secret_and_loopback(client,monkeypatch):
    import os
    monkeypatch.setenv('AUTH_INTERNAL_SECRET','internal-test-secret-'+'s'*64)
    assert client.post('/api/internal/gateway-session',json={}).status_code==403
    headers={'X-Internal-Gateway-Secret':os.environ['AUTH_INTERNAL_SECRET']}
    assert client.post('/api/internal/gateway-session',json={},headers=headers,
        environ_base={'REMOTE_ADDR':'192.0.2.15'}).status_code==403
    response=client.post('/api/internal/gateway-session',json={},headers=headers)
    assert response.status_code==200 and response.json['authenticated'] is True
    assert len(response.json['csrf'])>=32
    assert client.get('/api/auth/session').json['authenticated'] is True


def test_chat_rejects_stale_csrf_then_continues_after_authenticated_refresh(client):
    stale=client.post('/api/assistant/chat',json={'question':'Entreprises en informatique ?','mode':'local'},headers={'X-CSRF-Token':'jeton-expire'})
    assert stale.status_code==403 and stale.json['erreur']=='Session expirée. Rechargez la page.'
    session=client.get('/api/auth/session').json
    assert session['authenticated'] is True and session['csrf']
    headers={'X-CSRF-Token':session['csrf']}
    first=client.post('/api/assistant/chat',json={'question':'Entreprises en informatique ?','mode':'local'},headers=headers)
    second=client.post('/api/assistant/chat',json={'question':'Quelles offres Python ?','mode':'local'},headers=headers)
    assert first.status_code==second.status_code==200
    assert first.json['companies'] and 'entreprise' in first.json['answer'].lower()
    assert len(second.json['offers'])>=1
    assert len(client.get('/api/assistant/history').json['messages'])==4


def test_assistant_mode_reports_gemini_only_when_fully_configured(client,app):
    status=client.get('/api/assistant/status').json
    assert status['local_available'] is True and status['gemini_available'] is False
    assert any('clé' in reason.lower() for reason in status['reasons'])
    app.config.update(GEMINI_ENABLED=True,GEMINI_API_KEY='FAKE-TEST-KEY',GEMINI_FREE_TIER_CONFIRMED=True,
                      GEMINI_MODEL='gemini-3.5-flash-lite')
    enabled=client.get('/api/assistant/status').json
    assert enabled['gemini_available'] is True and enabled['model']=='gemini-3.5-flash-lite'
    assert 'FAKE-TEST-KEY' not in str(enabled)


def test_consultation_and_start_without_keys(client):
    assert len(client.get('/api/entreprises').json)==2
    assert len(client.get('/api/offres').json)==3
    assert client.get('/api/statistiques').json['total_candidatures']==5
    assert client.get('/api/map').json['verified']==[]
    assert not client.get('/api/map').json['maps_enabled']


def test_offers_prioritize_active_and_label_expired_or_unknown(client,app):
    with sqlite3.connect(app.config['DATABASE']) as db:
        db.execute('UPDATE offres SET "Date expiration"=? WHERE ID=1',('2020-01-01',))
        db.execute('UPDATE offres SET "Date expiration"=? WHERE ID=3',('date illisible',))
    offers=client.get('/api/offres').json
    assert [(o['ID'],o['availability']) for o in offers]==[(2,'active'),(3,'unknown'),(1,'expired')]


@pytest.mark.parametrize('page',['index','entreprises','offres','candidatures','cv','matching','carte','analyses','envoyer_cv','statistiques'])
def test_pages_connected(client,page):
    response=client.get('/'+page+'.html')
    assert response.status_code==200 and b'/js/app.js' in response.data
    assert b'http://127.0.0.1:5000' not in response.data


@pytest.mark.parametrize('value',[{},None,[],{'nom_entreprise':'X'},{'nom_entreprise':'X','date_candidature':'incorrect','statut':'Envoyée'},
                                 {'nom_entreprise':'X','date_candidature':'2026-09-01','statut':'inconnu'}])
def test_invalid_application_rejected(client,value):
    assert client.post('/api/candidatures',data=json.dumps(value),content_type='application/json').status_code==400
    assert len(client.get('/api/candidatures').json)==5


def test_application_partial_update_and_history(client):
    r=client.post('/api/candidatures',json={'nom_entreprise':"L'entreprise fictive",'statut':'Non envoyée','date_candidature':'2026-09-03','commentaire':'Note à conserver'})
    assert r.status_code==201
    ident=r.json['id']
    assert client.patch('/api/candidatures/'+str(ident),json={'statut':'Entretien'}).status_code==200
    value=client.get('/api/candidatures').json[0]
    assert value['commentaire']=='Note à conserver' and value['nom_entreprise']=="L'entreprise fictive"
    history=client.get(f'/api/candidatures/{ident}/history').json
    assert len(history)==2 and history[-1]['new_status']=='Entretien'
    assert client.patch('/api/candidatures/999',json={'statut':'Entretien'}).status_code==404


@pytest.mark.parametrize('template',['modern','ats'])
def test_pdf_valid_and_extractable(cv_data,template):
    content=make_pdf(cv_data,template)
    reader=PdfReader(io.BytesIO(content))
    assert len(reader.pages)>=1
    value='\n'.join(p.extract_text() for p in reader.pages)
    assert 'Profil Démonstration' in value and 'Pandas' in value
    assert 'Python' in extract_pdf(content)


@pytest.mark.parametrize('template',['modern','ats'])
def test_cv_preview_endpoint_returns_readable_pdf(client,cv_data,template):
    response=client.post('/api/cvs/preview',json={'data':cv_data,'template':template})
    assert response.status_code==200 and response.mimetype=='application/pdf'
    text=''.join(page.extract_text() or '' for page in PdfReader(io.BytesIO(response.data)).pages)
    assert 'Profil Démonstration' in text and 'Français' in text


def test_long_pdf_does_not_overflow(cv_data):
    cv_data['projects']=[{'title':'Projet fictif '+str(i),'description':'Présentation du projet pédagogique. '*25} for i in range(20)]
    reader=PdfReader(io.BytesIO(make_pdf(cv_data)))
    assert len(reader.pages)>1
    assert 'Projet fictif 19' in ''.join(p.extract_text() for p in reader.pages)


def test_cv_rejects_reversed_structured_period(cv_data):
    cv_data['experience']=[{'title':'Stage fictif','period':'2026-09 – 2025-06'}]
    with pytest.raises(ValueError,match='ne peut pas se terminer'):
        validate_cv(cv_data)


@pytest.mark.parametrize('content',[b'not a PDF',b'%PDF-damaged',b'%PDF-'+b'x'*(5*1024*1024)])
def test_invalid_pdf_rejected(content):
    with pytest.raises(ValueError):extract_pdf(content)


def test_pdf_extraction_endpoint(client,cv_data):
    r=client.post('/api/profile/extract',data={'cv':(io.BytesIO(make_pdf(cv_data)),'cv.pdf')})
    assert r.status_code==200 and 'python' in r.json['profile']['skills']


def test_cv_encrypted_and_versions(client,cv_id,cv_data,app):
    assert client.get(f'/api/cvs/{cv_id}').json['data']['name']==cv_data['name']
    with sqlite3.connect(app.config['DATABASE']) as db:
        content=db.execute('SELECT payload FROM cvs WHERE id=?',(cv_id,)).fetchone()[0]
        assert b'Profil' not in content and b'Python' not in content
    assert client.get(f'/api/cvs/{cv_id}/pdf').data.startswith(b'%PDF-')
    second=client.post('/api/cvs',json={'name':'Deuxième version','template':'ats','data':cv_data})
    assert second.status_code==201 and len(client.get('/api/cvs').json)==2


def test_cv_offer_optimization_is_local_grounded_and_non_destructive(client,cv_id,cv_data):
    response=client.post('/api/cvs/optimize',json={'cv_id':cv_id,'offer_id':1})
    assert response.status_code==200
    result=response.json
    assert 'python' in result['matched'] and 'pandas' in result['matched']
    assert result['evidence'] and result['evidence'][0]['source'].find('Pandas')>=0
    assert 'Nettoyage de données avec Pandas.' in result['evidence'][0]['suggested_rewrite']
    assert any('uniquement' in item or 'réellement' in item for item in result['recommendations'])
    assert client.get(f'/api/cvs/{cv_id}').json['data']==validate_cv(cv_data)
    assert client.post('/api/cvs/optimize',json={'cv_id':999,'offer_id':1}).status_code==404
    assert client.post('/api/cvs/optimize',json={'cv_id':cv_id,'offer_id':999}).status_code==404


def test_cv_summary_suggestion_reorders_only_existing_sentences(client,cv_data):
    data={**cv_data,'summary':'Je recherche un stage. Mon projet utilisait Python et Pandas. Je suis étudiant.'}
    saved=client.post('/api/cvs',json={'name':'Résumé de démonstration','template':'modern','data':data})
    result=client.post('/api/cvs/optimize',json={'cv_id':saved.json['id'],'offer_id':1}).json
    suggestion=result['summary_suggestion']
    assert suggestion['proposed'].startswith('Mon projet utilisait Python et Pandas.')
    assert set(suggestion['proposed'].split('. ')) == set(data['summary'].split('. '))
    assert client.get(f"/api/cvs/{saved.json['id']}").json['data']['summary']==data['summary']


def test_cv_deletion_requires_existing_unreferenced_version(client,cv_id):
    assert client.delete('/api/cvs/999').status_code==404
    assert client.delete(f'/api/cvs/{cv_id}').status_code==200
    assert client.get(f'/api/cvs/{cv_id}').status_code==404


def test_local_matching_explainable(client):
    result=client.post('/api/matching',json={'profile':PROFILE,'mode':'local'})
    assert result.status_code==200
    values=result.json['results'];assert values[0]['offer']['ID']==1
    assert 0<=values[0]['score']<=100
    assert values[0]['score']==round(sum(values[0]['contributions'].values()),1)
    assert values[0]['offer']['entreprise_nom'] is None
    assert values[0]['uncertain'] and values[0]['components']['location']==0


@pytest.mark.parametrize('skills,expected_offer',[(['Python','Pandas'],1),(['Java'],3),(['marketing','SEO'],2)])
def test_matching_ranks_representative_profiles(client,skills,expected_offer):
    profile={**PROFILE,'skills':skills,'education':'','experience':'','domain':'','location':'','opportunity':''}
    response=client.post('/api/matching',json={'profile':profile,'mode':'local'})
    assert response.status_code==200
    ranked=response.json['results']
    assert ranked[0]['offer']['ID']==expected_offer
    assert all(0<=item['score']<=100 for item in ranked)
    assert all(abs(item['score']-sum(item['contributions'].values()))<0.11 for item in ranked)


def test_matching_invalid_weights(client):
    assert client.post('/api/matching',json={'profile':PROFILE,'weights':{'skills':100}}).status_code==400


def test_gemini_consent_and_missing_api(client):
    assert client.post('/api/matching',json={'profile':PROFILE,'mode':'gemini'}).status_code==400
    preview=client.post('/api/matching/preview',json={'profile':PROFILE}).json
    response=client.post('/api/matching',json={'profile':PROFILE,'mode':'gemini','consent':True,'digest':preview['digest']})
    assert response.status_code==200 and response.json['mode']=='local'
    assert 'indisponible' in response.json['notice']


def test_gemini_quota_falls_back(client):
    preview=client.post('/api/matching/preview',json={'profile':PROFILE}).json
    with patch('backend.api.interpret',side_effect=RuntimeError('429 RESOURCE_EXHAUSTED')):
        r=client.post('/api/matching',json={'profile':PROFILE,'mode':'gemini','consent':True,'digest':preview['digest']})
    assert r.status_code==200 and r.json['mode']=='local' and '429' in r.json['notice']


def test_gemini_actual_sdk_contract_mocked(app):
    sent={'profile':PROFILE,'offers':[{'id':1,'title':'Stage Python','description':'Python SQL requis'}]}
    value={'offers':[{'id':1,'pairs':[{'candidate_skill':'Python','offer_skill':'Python','evidence':'Python SQL requis'}],
                       'explanation':'Python est présent.','recommendation':'Documentez vos projets.'}]}
    call=Mock(return_value=SimpleNamespace(text=json.dumps(value)))
    client=SimpleNamespace(models=SimpleNamespace(generate_content=call),close=Mock())
    cfg={**app.config,'GEMINI_ENABLED':True,'GEMINI_API_KEY':'FAKE-TEST-KEY','GEMINI_FREE_TIER_CONFIRMED':True}
    result=interpret(cfg,sent,client=client)
    assert result['1']['pairs'][0]['candidate_skill']=='Python'
    assert call.call_args.kwargs['config']['response_mime_type']=='application/json'
    value['offers'][0]['pairs'][0]['candidate_skill']='Compétence inventée'
    call.return_value=SimpleNamespace(text=json.dumps(value))
    with pytest.raises(ValueError):interpret(cfg,sent,client=client)


def test_gemini_extraction_mocked(app):
    value={'skills':[{'name':'Python','evidence':'Projet Python'}],'domain':'Data Science','domain_evidence':'Data Science'}
    client=SimpleNamespace(models=SimpleNamespace(generate_content=Mock(return_value=SimpleNamespace(text=json.dumps(value)))),close=Mock())
    cfg={**app.config,'GEMINI_ENABLED':True,'GEMINI_API_KEY':'FAKE','GEMINI_FREE_TIER_CONFIRMED':True}
    assert extract_profile(cfg,'Data Science. Projet Python',client)['skills']==['Python']


def test_anonymized_payload_and_stale_consent(client):
    profile={**PROFILE,'experience':'Projet Python. secret@example.test https://example.test +212 600000000'}
    preview=client.post('/api/matching/preview',json={'profile':profile}).json
    assert 'secret@example.test' not in str(preview['payload'])
    changed={**profile,'domain':'marketing'}
    assert client.post('/api/matching',json={'profile':changed,'mode':'gemini','consent':True,'digest':preview['digest']}).status_code==400


def test_external_apply_confirmation_and_prepare(client,cv_id):
    assert client.get('/api/offres/1/application').json['channel']['type']=='external'
    assert client.post('/api/offres/1/apply',json={'cv_id':cv_id,'action':'external_confirmed'}).status_code==400
    prepared=client.post('/api/offres/1/apply',json={'cv_id':cv_id,'action':'prepare','confirmed':True})
    assert prepared.status_code==201
    assert client.get('/api/candidatures').json[0]['statut']=='Non envoyée'
    sent=client.post('/api/offres/1/apply',json={'cv_id':cv_id,'action':'external_confirmed','confirmed':True})
    assert sent.status_code==200 and sent.json['duplicate']
    assert len(client.get('/api/candidatures').json)==6
    assert client.get('/api/candidatures').json[0]['statut']=='Envoyée'


def test_no_channel_prepare(client,cv_id,app):
    with sqlite3.connect(app.config['DATABASE']) as db:
        db.execute('UPDATE offres SET "Lien annonce"=NULL,"Lien public"=NULL WHERE ID=3')
    assert client.get('/api/offres/3/application').json['channel']['type']=='unavailable'
    assert client.post('/api/offres/3/apply',json={'cv_id':cv_id,'action':'external_confirmed','confirmed':True}).status_code==400


def smtp_body(cv_id):
    return {'entreprise_id':1,'cv_id':cv_id,'email':'jobs@example.test','subject':'Candidature fictive',
            'message':'Message de test anonymisé.','confirmed':True,'email_confirmed':True}


def test_smtp_disabled_and_no_confirmation(client,cv_id):
    data=smtp_body(cv_id)
    assert client.post('/api/envoyer-cv',json=data).status_code==400
    data['confirmed']=False
    assert client.post('/api/envoyer-cv',json=data).status_code==400


def test_smtp_mocked_correct_recipient_and_idempotency(client,cv_id,app):
    app.config.update(SMTP_ENABLED=True,SMTP_USER='sender@example.test',SMTP_PASSWORD='fake-test-password')
    with patch('backend.application_service.smtplib.SMTP') as smtp:
        server=smtp.return_value.__enter__.return_value
        server.send_message.return_value={}
        first=client.post('/api/envoyer-cv',json=smtp_body(cv_id),headers={'Idempotency-Key':'test-idempotence-12345678'})
        second=client.post('/api/envoyer-cv',json=smtp_body(cv_id),headers={'Idempotency-Key':'test-idempotence-12345678'})
        assert first.status_code==200 and first.json['status']=='sent',first.json
        assert second.json['duplicate'] and server.send_message.call_count==1
        assert server.send_message.call_args.args[0]['To']=='jobs@example.test'
        assert smtp.call_args.kwargs['timeout']==20
    assert len(client.get('/api/candidatures').json)==6


def test_smtp_untrusted_email_and_uncertain_failure(client,cv_id,app):
    app.config.update(SMTP_ENABLED=True,SMTP_USER='sender@example.test',SMTP_PASSWORD='fake')
    data=smtp_body(cv_id);data['email']='invented@example.test'
    assert client.post('/api/envoyer-cv',json=data).status_code==400
    with patch('backend.application_service.smtplib.SMTP',side_effect=TimeoutError()):
        result=client.post('/api/envoyer-cv',json=smtp_body(cv_id),headers={'Idempotency-Key':'test-failed-1234567890'})
    assert result.json['status']=='uncertain'
    assert client.get('/api/attempts').json[0]['status']=='uncertain'
    assert len(client.get('/api/candidatures').json)==5


def test_dash_real_routes_and_callbacks(client,app):
    assert client.get('/analytics/').status_code==200
    layout=client.get('/analytics/_dash-layout')
    assert layout.status_code==200 and 'Dropdown' in str(layout.json)
    callbacks=app.extensions['analytics'].audit_callbacks
    values=callbacks['options']('offers',0)
    assert {'value':'Type contrat','label':'Type contrat'} in values[0]
    fig,kpis,quality=callbacks['update']('offers','Type contrat','bar',None,None,'Stage',None,None,None,0,0)
    assert sum(fig.data[0].y)==2 and len(kpis)==4
    assert kpis[1].children[1].children=='2'
    assert any('Offres expirées selon la date source' in str(item.children) for item in quality)
    csv=callbacks['export'](1,'offers',None,None,'Stage',None,None,None)
    assert 'Stage Python' in csv['content'] and 'Développeur Java' not in csv['content']


def test_dash_sector_filter_uses_only_explicit_verified_relations(app):
    with sqlite3.connect(app.config['DATABASE']) as db:
        db.execute('UPDATE offres SET entreprise_ref=1,relation_verified=1 WHERE ID=1')
    callbacks=app.extensions['analytics'].audit_callbacks
    options=callbacks['options']('offers',0)
    assert {'label':'Informatique','value':'Informatique'} in options[2]
    filtered=callbacks['update']('offers','Titre','bar','Informatique',None,None,None,None,None,0,0)
    assert sum(filtered[0].data[0].y)==1
    assert filtered[1][1].children[1].children=='1'


def test_dash_incoherent_graph_explained(app):
    callbacks=app.extensions['analytics'].audit_callbacks
    fig,_,_=callbacks['update']('companies','Secteur','line',None,None,None,None,None,None,0,0)
    assert 'courbe exige une date' in fig.layout.annotations[0].text


def test_coordinates_verified_and_import(client,app,tmp_path):
    from scripts.import_coordinates import import_coordinates
    f=tmp_path/'coordinates.csv'
    f.write_text('entreprise_id,place_id,latitude,longitude,source,verified_at,quartier,ville\n1,TEST-ID,31.63,-8.01,synthetic-test,2026-11-03,Quartier fictif,Marrakech\n',encoding='utf-8')
    assert import_coordinates(app.config['DATABASE'],f,tmp_path/'geo-backups')==1
    data=client.get('/api/map').json
    assert len(data['verified'])==1 and data['verified'][0]['latitude']==31.63
    assert len(data['companies'])==2


def test_xss_data_never_rendered_as_html(client):
    value='<img src=x onerror=alert(1)>'
    client.post('/api/candidatures',json={'nom_entreprise':value,'date_candidature':'2026-09-01','statut':'Non envoyée'})
    assert client.get('/api/candidatures').json[0]['nom_entreprise']==value
    source=client.get('/js/ui.js').data.decode('utf-8')
    assert 'innerHTML' not in source and 'createTextNode' in source
    assert 'unsafe-inline' not in client.get('/index.html').headers['Content-Security-Policy'].split('style-src')[0]


def test_cross_origin_and_sensitive_files_denied(client):
    assert client.get('/api/candidatures',headers={'Origin':'https://evil.example.test'}).status_code==403
    for path in ['/private/cv.key','/database/stages_marrakech.db','/backups/x.db','/backend/generated_cv/x.pdf']:
        assert client.get(path).status_code==404


def test_scripts_import_without_side_effects():
    import importlib
    for module in ['collect_entreprises','collect_entreprises_complete','collect_offres_marrakech','test_places_api','nettoyage_donnees','classifier_entreprises','create_database']:
        importlib.import_module('scripts.'+module)


def test_excel_import_preserves_history_and_nonnull_contacts(app,tmp_path):
    import pandas as pd
    from scripts.import_data import import_excel
    directory=tmp_path/'excel';directory.mkdir()
    pd.DataFrame([{'Nom':"L’Agence d'essai",'Emails':None,'Secteur':'Informatique'}]).to_excel(directory/'entreprises_marrakech_clean.xlsx',index=False)
    pd.DataFrame([{'ID':1,'Titre':'Titre actualisé fictif'}]).to_excel(directory/'offres_stagiaires_marrakech_clean.xlsx',index=False)
    import_excel(app.config['DATABASE'],directory,tmp_path/'import-backups')
    import_excel(app.config['DATABASE'],directory,tmp_path/'import-backups')
    with sqlite3.connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT COUNT(*) FROM candidatures').fetchone()[0]==5
        assert db.execute('SELECT COUNT(*) FROM offres').fetchone()[0]==3
        assert db.execute('SELECT Emails FROM entreprises WHERE rowid=1').fetchone()[0]=='jobs@example.test'


def test_pdf_deterministic_for_idempotency(cv_data):
    assert make_pdf(cv_data)==make_pdf(cv_data)


def test_pdf_export_authenticated_single_use(client,cv_data):
    r=client.post('/api/cvs/export',json={'data':cv_data,'template':'ats'})
    assert r.status_code==200
    url='/api/cvs/export/'+r.json['token']
    download=client.get(url)
    assert download.status_code==200 and download.data.startswith(b'%PDF-')
    assert 'attachment' in download.headers['Content-Disposition']
    assert client.get(url).status_code==404


def test_places_pagination_mocked():
    from scripts.places_client import search_places
    first=Mock();first.json.return_value={'places':[{'id':'fake1','location':{'latitude':31.63,'longitude':-8.01}}],'nextPageToken':'token-fictif'}
    second=Mock();second.json.return_value={'places':[{'id':'fake2'}]}
    with patch('scripts.places_client.requests.post',side_effect=[first,second]) as call,patch('scripts.places_client.time.sleep'):
        result=search_places('Entreprise fictive','FAKE-KEY')
    assert len(result)==2 and call.call_count==2
    assert call.call_args.kwargs['json']['pageToken']=='token-fictif'
    assert 'places.location' in call.call_args.kwargs['headers']['X-Goog-FieldMask']


def test_external_scripts_require_authorization(monkeypatch):
    from scripts.common import prepare
    monkeypatch.setattr('sys.argv',['collect_offres_marrakech.py'])
    with pytest.raises(SystemExit):prepare(external=True)


def test_official_sdk_accepts_structured_schema():
    from google.genai import types
    from backend.gemini_service import SCHEMA
    assert types.GenerateContentConfig(response_mime_type='application/json',response_json_schema=SCHEMA).response_json_schema==SCHEMA
    assert types.HttpOptions(timeout=20000).timeout==20000
