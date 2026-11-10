import json
import sqlite3
from datetime import date
from unittest.mock import Mock
import pytest
from backend.db import connect, migrate_phase5, now
from backend.collectors.jawb import parse_rss, fetch_company_feed
from backend.collectors.schema import normalize_offer
from backend.collectors.service import set_sources_config, import_run, execute_run, create_run, run_details, decide_staged_offer
from backend.collectors.companies import parse_company_file, company_plan, import_companies
from backend.alerts import maybe_create_alert, validate_preferences
from backend.assistant import retrieve, gemini_payload, gemini_answer


def _offer(title='Stage Data Python',source='Jawb RSS',source_id='j-1',url='https://jawb.ma/offres/1',city='Marrakech'):
    return normalize_offer({'id':source_id,'title':title,'description':'Stage PFE Python SQL Data Science et analyse de données pour un projet applicatif.','company':'Société Test','city':city,'sector':'Data Science','type_contrat':'Stage','type_stage':'Stage PFE','created_at':'2026-11-06T09:00:00Z','url':url},source)


def _stage(db_path,source,item):
    with connect(db_path) as db:
        cur=db.execute('INSERT INTO collector_runs(mode,status,started_at,finished_at,source_count,fetched_count) VALUES (?,?,?,?,?,?)',('preview','previewed',now(),now(),1,1));ident=cur.lastrowid
        db.execute('INSERT INTO collector_staging(run_id,source,identity_key,payload_json) VALUES (?,?,?,?)',(ident,source,item['source_id'] or item['canonical_url'],json.dumps(item,ensure_ascii=False)))
        stage_id=db.execute('SELECT id FROM collector_staging WHERE run_id=?',(ident,)).fetchone()[0]
    decide_staged_offer(db_path,ident,stage_id,'approved')
    return ident


def test_jawb_rss_parser_normalizes_and_keeps_source_link():
    rows=parse_rss('<rss><channel><item><title> Stage data </title><link>https://jawb.ma/offre/1</link><guid>j1</guid><description><![CDATA[<p>Python &amp; SQL</p>]]></description><pubDate>Fri, 06 Nov 2026 10:00:00 GMT</pubDate></item></channel></rss>')
    value=normalize_offer(rows[0],'Jawb RSS')
    assert value['title']=='Stage data' and value['description']=='Python & SQL'
    assert value['url']=='https://jawb.ma/offre/1' and value['source_id']=='j1'
    assert value['published_at'].startswith('2026-11-06')


def test_jawb_company_json_paginates_only_same_host():
    session=Mock();session.get.side_effect=[Mock(status_code=200,content=b'{"jobs":[{"id":"1","title":"Stage A","description":"D","url":"https://jawb.ma/a"}],"next":"/api/entreprises/x/offres.json?page=2"}',json=lambda:{'jobs':[{'id':'1','title':'Stage A','description':'D','url':'https://jawb.ma/a'}],'next':'/api/entreprises/x/offres.json?page=2'}),Mock(status_code=200,content=b'{"jobs":[{"id":"2","title":"Stage B","description":"D","url":"https://jawb.ma/b"}],"next":null}',json=lambda:{'jobs':[{'id':'2','title':'Stage B','description':'D','url':'https://jawb.ma/b'}],'next':None})]
    assert len(fetch_company_feed(session,['x']))==2
    assert session.get.call_count==2
    bad=Mock(status_code=200,content=b'{}',json=lambda:{'jobs':[],'next':'https://example.test/private'})
    with pytest.raises(ValueError):fetch_company_feed(Mock(get=Mock(return_value=bad)),['x'])


def test_empty_or_invalid_rss_and_bad_dates_are_not_fabricated():
    assert parse_rss('<rss><channel></channel></rss>')==[]
    value=normalize_offer({'title':'Stage','url':'https://jawb.ma/a','description':'Stage à Marrakech','published_at':'inconnu'},'Jawb RSS')
    assert value['published_at'] is None and value['company']=='' and value['city']==''


def test_collection_offers_incrementally_upserts_and_preserves_history(app,tmp_path):
    path=app.config['DATABASE'];set_sources_config(path,{'external_enabled':True,'jawb_rss_enabled':True,'jawb_import_approved':True,'jawb_consult_allowed':True,'jawb_storage_allowed':True,'jawb_display_allowed':True,'jawb_permission_ref':'mock written permission'})
    first=_stage(path,'Jawb RSS',_offer());one=import_run(path,first,['Jawb RSS'],tmp_path/'backups')
    assert one['new_offers']==1 and one['updated_offers']==0
    second=_stage(path,'Jawb RSS',_offer());two=import_run(path,second,['Jawb RSS'],tmp_path/'backups')
    assert two['new_offers']==0 and two['updated_offers']==0 and two['unchanged_offers']==1
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM offres').fetchone()[0]==4
        assert db.execute('SELECT COUNT(*) FROM candidatures').fetchone()[0]==5
        assert db.execute('SELECT COUNT(*) FROM offer_source_identity').fetchone()[0]==1
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'


def test_cross_source_similar_offer_is_flagged_not_merged(app,tmp_path):
    path=app.config['DATABASE'];set_sources_config(path,{'external_enabled':True,'jawb_import_approved':True,'jawb_consult_allowed':True,'jawb_storage_allowed':True,'jawb_display_allowed':True,'jawb_permission_ref':'mock written permission'})
    first=_stage(path,'Jawb RSS',_offer());import_run(path,first,['Jawb RSS'],tmp_path/'backups')
    second=_stage(path,'Jawb JSON',_offer(source='Jawb JSON',source_id='json-1',url='https://jawb.ma/offres/mirror'))
    result=import_run(path,second,['Jawb JSON'],tmp_path/'backups')
    assert result['new_offers']==1 and result['duplicates']==1
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM offres').fetchone()[0]==5
        assert db.execute("SELECT status FROM collector_duplicate_candidates").fetchone()[0]=='review'


def test_external_import_requires_rights_and_empty_run_never_deletes(app):
    path=app.config['DATABASE'];before=sqlite3.connect(path).execute('SELECT COUNT(*) FROM offres').fetchone()[0]
    set_sources_config(path,{'external_enabled':True,'jawb_import_approved':False})
    with pytest.raises(ValueError):import_run(path,999,['Jawb RSS'])
    with connect(path) as db:
        cur=db.execute('INSERT INTO collector_runs(mode,status,started_at,finished_at) VALUES (?,?,?,?)',('preview','previewed',now(),now()));ident=cur.lastrowid
    set_sources_config(path,{'jawb_import_approved':True,'jawb_consult_allowed':True,'jawb_storage_allowed':True,'jawb_display_allowed':True,'jawb_permission_ref':'mock written permission'})
    result=import_run(path,ident,['Jawb RSS'])
    assert result['imported']==0
    assert sqlite3.connect(path).execute('SELECT COUNT(*) FROM offres').fetchone()[0]==before


def test_alert_filters_city_skills_expiry_and_deduplicates(app):
    from backend.alerts import preferences,score_offer
    path=app.config['DATABASE']
    with connect(path) as db:
        db.execute("UPDATE alert_preferences SET domain=?,skills_json=?,city=?,minimum_score=?,enabled=1 WHERE id=1",('Data Science','["Python","SQL"]','Marrakech',60))
        ident=db.execute('SELECT COALESCE(MAX("ID"),0)+1 FROM offres').fetchone()[0]
        db.execute('INSERT INTO offres("ID","Titre","Description","Type contrat","Type stage","Date publication","Date expiration","Lien public",source,entreprise_nom,ville,competences) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (ident,'Stage Data','Python SQL analyse data','Stage','Stage PFE','2026-11-06',None,'https://example.test/stage','fixture','Fictive','Marrakech','Python, SQL'))
        assert maybe_create_alert(db,ident)['score']>=60
        maybe_create_alert(db,ident)
        assert db.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]==1
        db.execute('UPDATE offres SET "Date expiration"=? WHERE "ID"=?',('2020-01-01',ident))
        other=db.execute('SELECT COALESCE(MAX("ID"),0)+1 FROM offres').fetchone()[0]
        db.execute('INSERT INTO offres("ID","Titre","Description","Date expiration",ville) VALUES (?,?,?,?,?)',(other,'Stage expired','Python SQL','2020-01-01','Marrakech'))
        assert maybe_create_alert(db,other) is None


def test_alert_preferences_are_bounded_and_explainable():
    with pytest.raises(ValueError):validate_preferences({'skills':['x']*51})
    with pytest.raises(ValueError):validate_preferences({'minimum_score':101})
    assert validate_preferences({'skills':['Python'],'enabled':True})['enabled'] is True


def test_alert_email_requires_explicit_consent_and_uses_mock_smtp(app,client,monkeypatch):
    app.config.update(SMTP_ENABLED=True,SMTP_USER='sender@example.test',SMTP_PASSWORD='not-a-real-password',SMTP_HOST='smtp.example.test',SMTP_PORT=587)
    base={'domain':'','skills':[],'city':'','minimum_score':0,'enabled':True,'email_enabled':True,'email_recipient':'student@example.test'}
    rejected=client.put('/api/alerts/preferences',json={**base,'email_consent':False})
    assert rejected.status_code==400
    accepted=client.put('/api/alerts/preferences',json={**base,'email_consent':True})
    assert accepted.status_code==200 and accepted.json['email_recipient_saved'] is True
    path=app.config['DATABASE']
    with connect(path) as db:
        prefs=db.execute('SELECT email_payload FROM alert_preferences WHERE id=1').fetchone()
        assert b'student@example.test' not in prefs['email_payload']
        ident=db.execute('SELECT "ID" FROM offres LIMIT 1').fetchone()[0]
        alert=maybe_create_alert(db,ident)
        alert_id=db.execute('SELECT id FROM alerts WHERE offer_id=?',(ident,)).fetchone()[0]
    class FakeSMTP:
        def __init__(self,*args,**kwargs):self.sent=None
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def starttls(self,**kwargs):pass
        def login(self,*args):pass
        def send_message(self,message):self.sent=message;assert message['To']=='student@example.test';return {}
    smtp=FakeSMTP()
    monkeypatch.setattr('backend.alert_mail.smtplib.SMTP',lambda *args,**kwargs:smtp)
    with app.app_context():
        from backend.alert_mail import deliver_new_alerts
        deliver_new_alerts(path,[alert_id])
    assert smtp.sent is not None
    assert sqlite3.connect(path).execute('SELECT status FROM alert_email_log WHERE alert_id=?',(alert_id,)).fetchone()[0]=='sent'


def test_assistant_retrieves_only_database_rows_and_sanitizes_gemini(app):
    path=app.config['DATABASE'];result=retrieve(path,'Stages Python et SQL à Marrakech')
    ids={r[0] for r in sqlite3.connect(path).execute('SELECT ID FROM offres')}
    assert all(item['id'] in ids for item in result['offers'])
    assert result['last_updated'] is None
    sent=gemini_payload('Cherche python, email perso moi@example.test',result)
    assert all('CV' not in json.dumps(sent) for _ in [0])
    assert 'moi@example.test' not in json.dumps(sent)


def test_assistant_counts_companies_and_uses_local_cv_matching_explanations(app):
    path=app.config['DATABASE']
    count=retrieve(path,'Combien d’entreprises existent dans mon projet ?')
    assert count['company_count']==2 and '2 entreprise(s)' in count['answer']
    missing=retrieve(path,'Offre Xylophone introuvable')
    assert missing['offers']==[] and 'Aucune offre' in missing['answer']
    profile={'skills':['Python','Pandas'],'education':'Data Science','experience':'Projet Python et Pandas',
             'domain':'analyse de données','location':'','opportunity':'Stage'}
    matches=retrieve(path,'Quelles offres correspondent à mon CV ? ',profile)
    assert matches['offers'] and all('match_score' in item and 'uncertain' in item for item in matches['offers'])
    with connect(path) as db: offer_ids={row[0] for row in db.execute('SELECT ID FROM offres')}
    assert all(item['id'] in offer_ids for item in matches['offers'])


def test_assistant_gemini_can_only_reference_retrieved_ids():
    with pytest.raises(ValueError):
        from backend.assistant import gemini_answer as validate
        cfg={'GEMINI_ENABLED':True,'GEMINI_API_KEY':'mock','GEMINI_FREE_TIER_CONFIRMED':True,'GEMINI_MODEL':'gemini-3.5-flash-lite'}
        client=Mock();client.models.generate_content.return_value=Mock(text='{"answer":"OK","offer_ids":[2]}')
        validate(cfg, {'question':'q','offers':[]}, {1}, client=client)


def test_company_csv_preview_and_import_are_non_destructive(app,tmp_path):
    content=b'name,source,source_id,address,sector,city,website\nEntreprise nouvelle,Source autorisee,abc,Adresse,Informatique,Marrakech,https://example.test\n'
    items,errors=parse_company_file('entreprises.csv',content)
    assert not errors and len(items)==1
    plan=company_plan(app.config['DATABASE'],items);assert plan['new']==1
    result=import_companies(app.config['DATABASE'],tmp_path/'backups',items)
    assert result['new_companies']==1
    with sqlite3.connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT COUNT(*) FROM entreprises').fetchone()[0]==3
        assert db.execute('SELECT COUNT(*) FROM candidatures').fetchone()[0]==5


def test_company_csv_rejects_unverified_coordinates_and_bad_urls():
    content=b'name,source,latitude,longitude\nExample,Source,999,2\n'
    with pytest.raises(ValueError):parse_company_file('x.csv',content)


def test_dash_hides_collection_activity_but_keeps_collection_pages(app):
    dash=app.extensions['analytics']
    assert not any('collection-' in key for key in dash.callback_map)
    assert set(dash.audit_callbacks)=={'options','update','export'}
    assert app.test_client().get('/collecte.html').status_code==200
    assert app.test_client().get('/alertes.html').status_code==200


def test_pipeline_end_to_end_synthetic_source_syncs_offers_matching_alerts_chatbot_and_dash(app,client,tmp_path):
    path=app.config['DATABASE']
    with connect(path) as db:
        db.execute("UPDATE alert_preferences SET domain='Data Science',skills_json='[\"Python\",\"SQL\"]',city='Marrakech',minimum_score=50,enabled=1 WHERE id=1")
    run_id=create_run(path,'simulation')
    extracted=execute_run(path,run_id,'simulation')
    assert extracted['status']=='simulated'
    staged=run_details(path,run_id)['staged'][0]
    assert staged['offer']['title']=='Stage de démonstration Python et SQL'
    assert '<p>' not in staged['offer']['description']
    assert staged['offer']['status']=='unknown' and 'Date de publication' in staged['missing_fields']
    decide_staged_offer(path,run_id,staged['id'],'approved')
    set_sources_config(path,{'external_enabled':True})
    imported=import_run(path,run_id,['Simulation locale'],tmp_path/'backups',allow_simulation=True)
    assert imported['new_offers']==1 and imported['status']=='imported'
    offer_id=sqlite3.connect(path).execute('SELECT offer_id FROM offer_source_identity WHERE external_id=?',('demo-python-sql',)).fetchone()[0]
    listed=client.get('/api/offres').json
    assert any(o['ID']==offer_id and o['source']=='Simulation locale' and o['statut_offre']=='unknown' for o in listed)
    profile={'skills':['Python','SQL'],'education':'Data Science','experience':'Projet Python SQL','domain':'Data Science','location':'Marrakech','opportunity':'Stage'}
    matching=client.post('/api/matching',json={'profile':profile,'weights':app.config['MATCH_WEIGHTS']})
    assert matching.status_code==200 and any(r['offer']['ID']==offer_id for r in matching.json['results'])
    alerts=client.get('/api/alerts').json
    assert any(a['offer_id']==offer_id and a['score']>=50 for a in alerts)
    answer=retrieve(path,'Quelles nouvelles offres de cette semaine ?')
    assert any(o['id']==offer_id for o in answer['offers']) and 'Aucune nouvelle offre' not in answer['answer']
    _,dash_kpis,_=app.extensions['analytics'].audit_callbacks['update'](
        'offers','Titre','bar',None,None,None,None,None,None,0,0)
    assert dash_kpis[1].children[1].children=='4'
    with connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM offer_source_identity WHERE source=?',('Simulation locale',)).fetchone()[0]==1
        assert db.execute('SELECT COUNT(*) FROM offer_source_identity WHERE substr(first_seen,1,10)=?',(date.today().isoformat(),)).fetchone()[0]==1
        assert db.execute('SELECT COUNT(*) FROM candidatures').fetchone()[0]==5
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'


def test_external_preview_is_blocked_without_documented_source_rights(app,monkeypatch):
    from backend.collectors.service import sources_config,_connector_options
    path=app.config['DATABASE']
    set_sources_config(path,{'external_enabled':True,'jawb_rss_enabled':True,'jawb_import_approved':False})
    assert _connector_options(path)[1]==[]
    run_id=create_run(path,'preview');result=execute_run(path,run_id,'preview')
    assert result['status']=='failed' and result['fetched_count']==0
    assert sources_config(path)['auto_enabled'] is False


def test_unreviewed_staging_cannot_be_imported(app,tmp_path):
    path=app.config['DATABASE'];set_sources_config(path,{'external_enabled':True,'jawb_import_approved':True,'jawb_consult_allowed':True,'jawb_storage_allowed':True,'jawb_display_allowed':True,'jawb_permission_ref':'mock written permission'})
    with connect(path) as db:
        cur=db.execute('INSERT INTO collector_runs(mode,status,started_at) VALUES (?,?,?)',('preview','previewed',now()));run_id=cur.lastrowid
        item=_offer();db.execute('INSERT INTO collector_staging(run_id,source,identity_key,payload_json) VALUES (?,?,?,?)',(run_id,'Jawb RSS',item['source_id'],json.dumps(item)))
    outcome=import_run(path,run_id,['Jawb RSS'],tmp_path/'backups')
    assert outcome['imported']==0 and outcome['status']=='previewed'
    assert sqlite3.connect(path).execute('SELECT decision FROM collector_staging WHERE run_id=?',(run_id,)).fetchone()[0]=='pending'


def test_http_failure_is_logged_and_keeps_previously_imported_offers(app,monkeypatch,tmp_path):
    from requests import HTTPError
    import backend.collectors.service as service
    path=app.config['DATABASE'];set_sources_config(path,{'external_enabled':True,'jawb_rss_enabled':True,'jawb_import_approved':True,'jawb_consult_allowed':True,'jawb_storage_allowed':True,'jawb_display_allowed':True,'jawb_permission_ref':'mock written permission'})
    first=_stage(path,'Jawb RSS',_offer());import_run(path,first,['Jawb RSS'],tmp_path/'backups')
    before=sqlite3.connect(path).execute('SELECT COUNT(*) FROM offres').fetchone()[0]
    monkeypatch.setattr(service,'fetch_rss',lambda **kwargs:(_ for _ in ()).throw(HTTPError('503 Service Unavailable')))
    failed=create_run(path,'preview');result=execute_run(path,failed,'preview')
    assert result['status']=='failed' and '503' in result['errors'][0]
    assert sqlite3.connect(path).execute('SELECT COUNT(*) FROM offres').fetchone()[0]==before
    with connect(path) as db:
        assert db.execute('SELECT status FROM collector_source_runs WHERE run_id=?',(failed,)).fetchone()[0]=='failed'


def test_company_xlsx_preview_normalizes_sector_and_email(app,tmp_path):
    from openpyxl import Workbook
    import io
    wb=Workbook();ws=wb.active;ws.append(['Nom','Source','Adresse','Secteur','Ville','Email professionnel'])
    ws.append(['Société légale','Liste autorisée','Adresse Marrakech','IT','Marrakech','contact@example.test'])
    stream=io.BytesIO();wb.save(stream);wb.close()
    items,errors=parse_company_file('entreprises.xlsx',stream.getvalue())
    assert not errors and items[0]['sector']=='Informatique' and items[0]['emails']=='contact@example.test'
    assert company_plan(app.config['DATABASE'],items)['new']==1
    imported=import_companies(app.config['DATABASE'],tmp_path/'backups',items)
    assert imported['new_companies']==1
    company=sqlite3.connect(app.config['DATABASE']).execute('SELECT Emails,"Secteur" FROM entreprises WHERE "Nom"=?',('Société légale',)).fetchone()
    assert company==('contact@example.test','Informatique')

