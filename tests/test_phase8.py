import io
import json
from datetime import date

import pytest
from openpyxl import Workbook

from backend.collectors.classification import classify_offer, filter_offer
from backend.collectors.companies import parse_company_file
from backend.collectors.platforms import (
    fetch_ashby, fetch_greenhouse, fetch_lever, fetch_smartrecruiters,
    parse_ashby, parse_greenhouse, parse_lever, parse_smartrecruiters,
)
from backend.collectors.provided_offers import parse_provided_offers
from backend.collectors.service import create_run, execute_run, _connector_options
from backend.assistant import retrieve
from backend.db import connect


def offer(source_id='fixture-1', title='Stage PFE Data Science'):
    return {'id': source_id, 'title': title, 'company': 'Entreprise fictive',
            'location': 'Marrakech, Morocco', 'description': 'Stage PFE Python et données',
            'url': 'https://careers.example.test/jobs/fixture-1'}


class Response:
    def __init__(self, payload, status=200):
        self.payload, self.status_code = payload, status
        self.content = json.dumps(payload).encode()
        self.text = json.dumps(payload)

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f'HTTP {self.status_code}')


class Session:
    def __init__(self, responder):
        self.responder, self.calls = responder, []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responder(url, kwargs)


def test_greenhouse_mocked_fetch_and_empty_payload():
    session = Session(lambda url, kw: Response({'jobs': [dict(offer(), absolute_url=offer()['url'], updated_at='2026-11-01', content='Stage PFE Marrakech Python', location={'name':'Marrakech'})]}))
    items = fetch_greenhouse('test-board', 'Entreprise fictive', session)
    assert len(items) == 1 and items[0]['source_id'] == 'fixture-1'
    assert session.calls[0][0].endswith('/v1/boards/test-board/jobs')
    assert fetch_greenhouse('empty-board', 'Entreprise fictive', Session(lambda *_: Response({'jobs':[]}))) == []


def test_lever_mocked_pagination_and_normalization(monkeypatch):
    import backend.collectors.platforms as platforms
    monkeypatch.setattr(platforms.time, 'sleep', lambda *_: None)
    first = [{'id':str(i), 'text':'Stage PFE Python', 'categories':{'location':'Marrakech'},
              'descriptionPlain':'Stage Python', 'hostedUrl':f'https://jobs.example.test/{i}'} for i in range(100)]
    session = Session(lambda url, kw: Response(first if kw['params']['skip']==0 else [{'id':'last','text':'Stage','hostedUrl':'https://jobs.example.test/last'}]))
    items = fetch_lever('board', 'Entreprise fictive', session)
    assert len(items) == 101 and len(session.calls) == 2
    assert items[-1]['source_id'] == 'last' and items[0]['city'] == 'Marrakech'


def test_ashby_omits_unlisted_jobs_and_keeps_listed_job_fields():
    payload={'jobs':[{'id':'listed','title':'Data Intern','location':'Marrakech','isListed':True,
        'descriptionPlain':'Python internship','employmentType':'Intern','publishedAt':'2026-10-01',
        'jobUrl':'https://jobs.ashbyhq.com/org/job'}, {'id':'hidden','title':'Private role','isListed':False,
        'jobUrl':'https://jobs.ashbyhq.com/org/hidden'}]}
    items=parse_ashby(payload,'Entreprise fictive','Ashby · Entreprise fictive')
    assert len(items)==1 and items[0]['source_id']=='listed'
    session=Session(lambda *_:Response(payload))
    assert len(fetch_ashby('org','Entreprise fictive',session))==1


def test_smartrecruiters_public_filter_and_pagination(monkeypatch):
    import backend.collectors.platforms as platforms
    monkeypatch.setattr(platforms.time, 'sleep', lambda *_: None)
    payload={'content':[{'id':'public-1','name':'Stage Marrakech','ref':'https://jobs.example.test/public-1',
       'location':{'city':'Marrakech','country':'Morocco'}}], 'totalFound':1}
    session=Session(lambda *_:Response(payload))
    result=fetch_smartrecruiters('employer','Entreprise fictive',session)
    assert result[0]['source_id']=='public-1'
    assert session.calls[0][1]['params']['destination']=='PUBLIC'
    assert parse_smartrecruiters({'content':[]},'E','S')==[]


def test_platform_errors_and_http_failures_are_clear():
    with pytest.raises(ValueError,match='invalide'):
        fetch_greenhouse('../invalid','E',Session(lambda *_:Response({})))
    with pytest.raises(RuntimeError,match='HTTP 429'):
        fetch_ashby('board','E',Session(lambda *_:Response({},429)))
    with pytest.raises(ValueError,match='Réponse Lever invalide'):
        parse_lever({'jobs':[]},'E','Lever')
    with pytest.raises(ValueError,match='Réponse SmartRecruiters invalide'):
        parse_smartrecruiters({},'E','SmartRecruiters')


def test_csv_column_mapping_and_date_url_rejections():
    content=(b'Job Title,Company,Location,Apply URL,Published\n'
             b'Stage PFE,Entreprise fictive,Marrakech,https://example.test/pfe,'+date.today().isoformat().encode()+b'\n'
             b'Stage,Entreprise fictive,Marrakech,http://bad.example/pfe,invalid\n')
    values, errors, report=parse_provided_offers('jobs.csv',content,'Employeur autorisé',
        {'Job Title':'title','Company':'company','Location':'city','Apply URL':'url','Published':'published_at'},True)
    assert len(values)==1 and errors[0]['row']==3
    assert report['missing_columns']==[] and report['unmapped_columns']==[]


def test_xlsx_manual_import_mapping_and_company_mapping():
    workbook=Workbook();sheet=workbook.active
    sheet.append(['Company Name','Issuer','City','Website'])
    sheet.append(['Entreprise fictive','Autorité de test','Marrakech','https://example.test'])
    buf=io.BytesIO();workbook.save(buf)
    items,errors,report=parse_company_file('companies.xlsx',buf.getvalue(),
        {'Company Name':'name','Issuer':'source','City':'city','Website':'website'},True)
    assert not errors and items[0]['name']=='Entreprise fictive'
    assert report['missing_columns']==[]
    offer_book=Workbook();sheet=offer_book.active
    sheet.append(['Position','Apply Link','Employer']);sheet.append(['Stage technique','https://example.test/apply','Entreprise fictive'])
    buf=io.BytesIO();offer_book.save(buf)
    offers,offer_errors,offer_report=parse_provided_offers('offers.xlsx',buf.getvalue(),'Employeur autorisé',
        {'Position':'title','Apply Link':'url','Employer':'company'},True)
    assert not offer_errors and offers[0]['apply_url'].endswith('/apply') and offer_report['missing_columns']==[]


def test_classification_is_explainable_and_unknown_is_not_a_stage():
    unknown=classify_offer({'title':'Assistant administratif','contract_type':'','city':'Casablanca'})
    stage=classify_offer({'title':'Stage PFE développeur Python','contract_type':'Stage','city':'Marrakech'})
    assert unknown['opportunity_type']=='inconnu' and unknown['classification_confidence']=='incertaine'
    assert stage['opportunity_type']=='stage_pfe' and stage['location_group']=='Marrakech'
    assert filter_offer({'title':'Stage PFE développeur Python','contract_type':'Stage','city':'Marrakech'},location='Marrakech',kind='stage_pfe')
    assert classify_offer({'title':'Analyste','city':'Rabat'})['is_morocco'] is True


def test_board_registry_refuses_activation_without_all_rights(client, app):
    entry={'name':'Entreprise fictive','official_url':'https://example.test','career_url':'https://example.test/jobs',
       'platform':'greenhouse','board_id':'fixture-board','city':'Marrakech','sector':'Informatique',
       'permission_ref':'','consultation_allowed':False,'storage_allowed':True,'display_allowed':True,'enabled':True}
    response=client.post('/api/collect/settings',json={'career_boards':[entry]})
    assert response.status_code==400
    entry.update(permission_ref='fixture-permission',consultation_allowed=True,storage_allowed=True,display_allowed=True,enabled=False)
    response=client.post('/api/collect/settings',json={'career_boards':[entry]})
    assert response.status_code==200 and response.json['external_enabled'] is False
    assert response.json['career_boards'][0]['enabled'] is False


def test_authorized_rss_registry_is_gated_by_global_external_switch(client, app):
    entry={'name':'Flux de démonstration','official_url':'https://example.test','career_url':'https://example.test/jobs.xml',
       'platform':'rss','board_id':'','city':'Marrakech','sector':'Informatique','permission_ref':'permission-rss',
       'consultation_allowed':True,'storage_allowed':True,'display_allowed':True,'enabled':True,'last_verified_at':'2026-11-08'}
    saved=client.post('/api/collect/settings',json={'career_boards':[entry],'external_enabled':False})
    assert saved.status_code==200
    cfg,choices=_connector_options(app.config['DATABASE'])
    assert cfg['external_enabled'] is False and [x[0] for x in choices]==['Rss · Flux de démonstration']
    run_id=create_run(app.config['DATABASE'],'preview')
    result=execute_run(app.config['DATABASE'],run_id,'preview')
    assert result['status']=='failed' and 'Collecte externe désactivée' in result['errors'][0]


def test_mock_connector_runs_through_staging_validation_and_local_modules(app,client,monkeypatch):
    from backend.collectors import platforms
    from backend.collectors.schema import normalize_offer
    raw={'id':'e2e-8','title':'Stage PFE Data Python','company':'L’Agence d\'essai',
         'city':'Marrakech','description':'Stage PFE Python et SQL', 'contract_type':'Stage',
         'internship_type':'Stage PFE','job_url':'https://employer.example.test/jobs/e2e-8',
         'apply_url':'https://employer.example.test/apply/e2e-8'}
    monkeypatch.setitem(platforms.FETCHERS,'greenhouse',lambda board,company:[normalize_offer(raw,f'Greenhouse · {company}')])
    entry={'name':'Entreprise fictive','official_url':'https://employer.example.test','career_url':'https://employer.example.test/jobs',
       'platform':'greenhouse','board_id':'fixture-board','city':'Marrakech','sector':'Data Science',
       'permission_ref':'fixture-permission-2026','consultation_allowed':True,'storage_allowed':True,
       'display_allowed':True,'enabled':True}
    saved=client.post('/api/collect/settings',json={'external_enabled':True,'career_boards':[entry]})
    assert saved.status_code==200
    path=app.config['DATABASE']
    with connect(path) as db:
        db.execute("UPDATE alert_preferences SET domain='Data Science',skills_json='[\"Python\",\"SQL\"]',city='Marrakech',minimum_score=40,enabled=1 WHERE id=1")
    run_id=create_run(path,'preview');result=execute_run(path,run_id,'preview')
    assert result['status']=='previewed' and result['fetched_count']==1
    with connect(path) as db:
        staged=db.execute('SELECT id,decision FROM collector_staging WHERE run_id=?',(run_id,)).fetchone()
    assert staged['decision']=='pending'
    detail=client.get(f'/api/collect/runs/{run_id}').json
    assert detail['staged'][0]['company_match']['status']=='exact_existing_match'
    assert client.post(f'/api/collect/runs/{run_id}/staged/{staged["id"]}/decision',json={'decision':'approved'}).status_code==200
    imported=client.post(f'/api/collect/runs/{run_id}/import',json={'sources':['Greenhouse · Entreprise fictive'],'rights_confirmed':True})
    assert imported.status_code==200 and imported.json['new_offers']==1
    imported_offer=next(x for x in client.get('/api/offres').json if x['Titre']=='Stage PFE Data Python')
    assert imported_offer['Entreprise ID'] is not None
    assert imported_offer['Lien annonce'].endswith('/jobs/e2e-8')
    assert imported_offer['Lien public'].endswith('/apply/e2e-8')
    offer_row=next(x for x in client.get('/api/offres').json if x['Titre']=='Stage PFE Data Python')
    assert any(x['id']==offer_row['ID'] for x in retrieve(path,'Stage PFE Data Python à Marrakech')['offers'])
    profile={'skills':['Python','SQL'],'education':'Data Science','experience':'Projet','domain':'Data Science','location':'Marrakech','opportunity':'Stage PFE'}
    assert client.post('/api/matching',json={'profile':profile,'weights':app.config['MATCH_WEIGHTS']}).status_code==200
    assert any(a['offer_id']==offer_row['ID'] for a in client.get('/api/alerts').json)
    with connect(path) as db:
        assert db.execute('SELECT COUNT(*) FROM offer_source_identity WHERE source=?',('Greenhouse · Entreprise fictive',)).fetchone()[0]==1
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert db.execute('SELECT COUNT(*) FROM candidatures').fetchone()[0]==5
