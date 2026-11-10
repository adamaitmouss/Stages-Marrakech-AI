import hashlib
import json
import threading
import time

import pytest

from backend import gemini_search
from backend.db import connect


CRITERIA = {'prompt': 'Stage PFE Python à Marrakech cette semaine', 'city': 'Marrakech',
            'domain': 'Développement', 'opportunity_type': 'Stage PFE', 'period': '7d', 'max_results': 3}
SOURCE = 'https://careers.example.org/jobs/stage-python'


class FakeModels:
    def __init__(self, response=None, error=None): self.response, self.error, self.calls = response, error, []
    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error: raise self.error
        return self.response


class FakeClient:
    def __init__(self, response=None, error=None): self.models = FakeModels(response, error); self.closed = False
    def close(self): self.closed = True


def config(**overrides):
    return {'GEMINI_API_KEY': 'test-key', 'GEMINI_SEARCH_ENABLED': True,
            'GEMINI_SEARCH_MODEL': gemini_search.SEARCH_MODEL,
            'GEMINI_SEARCH_BILLING_CONFIRMED': True, **overrides}


def response(payload=None, metadata=None):
    item = {'title': 'Stage Python PFE', 'company': 'Entreprise test', 'city': 'Marrakech',
            'opportunity_type': 'Stage PFE', 'summary': 'Stage de démonstration', 'skills': ['Python'],
            'published_at': '2026-11-05', 'published_evidence': 'Publication du 5 novembre',
            'source_url': SOURCE, 'source_name': 'Carrières', 'evidence': 'Texte étayant le titre'}
    grounding = metadata if metadata is not None else {
        'grounding_chunks': [{'web': {'uri': SOURCE, 'title': 'Carrières'}}],
        'grounding_supports': [{'segment': {'text': 'Stage Python PFE'}, 'grounding_chunk_indices': [0]}],
        'web_search_queries': ['stage Python Marrakech']}
    return {'text': json.dumps(payload or {'candidates': [item]}), 'candidates': [{'grounding_metadata': grounding}]}


def test_grounding_sources_citations_and_search_count():
    client = FakeClient(response())
    value = gemini_search.run_grounded_search(config(), CRITERIA, client)
    assert value['search_query_count'] == 1
    assert value['candidates'][0]['source_url'] == SOURCE
    assert value['citations'][0]['url'] == SOURCE
    assert client.models.calls[0]['model'] == gemini_search.SEARCH_MODEL


def test_no_grounding_means_no_importable_link_even_if_model_invents_one():
    value = gemini_search.run_grounded_search(config(), CRITERIA, FakeClient(response(metadata={})))
    assert value['candidates'][0]['source_url'] is None
    assert value['candidates'][0]['importable'] is False


@pytest.mark.parametrize('url', ['http://careers.example.org/a', 'https://127.0.0.1/a',
    'https://localhost/a', 'https://google.com/url?q=https://careers.example.org/a',
    'https://user:secret@careers.example.org/a'])
def test_untrusted_or_internal_grounding_urls_are_filtered(url):
    assert gemini_search._safe_public_https(url) is False


def test_invalid_structured_response_and_provider_error_are_rejected():
    with pytest.raises(ValueError, match='invalide'):
        gemini_search.run_grounded_search(config(), CRITERIA, FakeClient({'text': '{', 'candidates': []}))
    with pytest.raises(RuntimeError):
        gemini_search.run_grounded_search(config(), CRITERIA, FakeClient(error=RuntimeError('provider')))


def test_search_requires_enabled_key_and_billing_configuration():
    with pytest.raises(ValueError, match='indisponible'):
        gemini_search.run_grounded_search(config(GEMINI_SEARCH_ENABLED=False), CRITERIA, FakeClient(response()))
    with pytest.raises(ValueError, match='indisponible'):
        gemini_search.run_grounded_search(config(GEMINI_API_KEY=''), CRITERIA, FakeClient(response()))


def test_local_search_and_demo_workflow_leave_main_db_unchanged(client, legacy_database):
    local = client.post('/api/ai-search/local', json=CRITERIA)
    assert local.status_code == 200 and local.json['mode'] == 'local'
    demo = client.post('/api/ai-search/demo', json=CRITERIA)
    assert demo.status_code == 200, demo.json
    assert demo.json['is_demo'] is True
    assert demo.json['workflow']['main_database_touched'] is False
    assert demo.json['workflow']['integrity_check'] == 'ok'
    assert demo.json['workflow']['new_offers'] == 1
    assert demo.json['workflow']['matching_results'] > 0
    assert demo.json['workflow']['chatbot_results'] > 0
    assert demo.json['workflow']['alerts'] > 0
    assert demo.json['workflow']['dash_offer_rows'] == 1
    with connect(str(legacy_database)) as db:
        assert db.execute('SELECT count(*) FROM offres').fetchone()[0] == 3
        assert db.execute('SELECT count(*) FROM candidatures').fetchone()[0] == 5
        assert db.execute('SELECT count(*) FROM gemini_search_history WHERE mode="demo"').fetchone()[0] == 1


def test_gemini_route_never_runs_when_not_configured(client):
    page = client.get('/recherche-ia.html')
    assert page.status_code == 200 and b'data-page="ai-search"' in page.data
    status = client.get('/api/ai-search/status')
    assert status.status_code == 200 and status.json['enabled'] is False
    result = client.post('/api/ai-search/gemini', json={**CRITERIA, 'confirm_cost': True})
    assert result.status_code == 400


def test_gemini_quota_and_cancel_suppress_returned_results(client, app, monkeypatch):
    import backend.api as api_module
    app.config.update(GEMINI_SEARCH_ENABLED=True, GEMINI_API_KEY='mocked',
        GEMINI_SEARCH_MODEL=gemini_search.SEARCH_MODEL, GEMINI_SEARCH_BILLING_CONFIRMED=True,
        GEMINI_SEARCH_MAX_SESSION=1, GEMINI_SEARCH_MAX_DAILY=5, GEMINI_SEARCH_COOLDOWN_SECONDS=0)
    called, release = threading.Event(), threading.Event()
    def fake_search(*args, **kwargs):
        called.set(); release.wait(3)
        return {'candidates': [], 'sources': [], 'citations': [], 'search_suggestions': [],
                'search_queries': [], 'search_query_count': 0, 'criteria': CRITERIA, 'mode': 'gemini'}
    monkeypatch.setattr(api_module, 'run_grounded_search', fake_search)
    started = client.post('/api/ai-search/gemini', json={**CRITERIA, 'confirm_cost': True})
    assert started.status_code == 202
    assert called.wait(2)
    cancelled = client.post(f"/api/ai-search/jobs/{started.json['id']}/cancel", json={})
    assert cancelled.status_code == 200
    release.set()
    for _ in range(50):
        result = client.get(f"/api/ai-search/jobs/{started.json['id']}")
        if result.json['status'] != 'running': break
        time.sleep(.02)
    assert result.json['status'] == 'cancelled'
    assert result.json['result'] is None
    limited = client.post('/api/ai-search/gemini', json={**CRITERIA, 'confirm_cost': True})
    assert limited.status_code == 400


def test_staging_requires_manual_verification_rights_and_source(client, app, legacy_database):
    with client.session_transaction() as sess:
        sess['ai_search_session'] = 'fixture-session'
        digest = hashlib.sha256(sess['ai_search_session'].encode()).hexdigest()
    ident = 'fixture-job'
    app.extensions['gemini_search_jobs'][ident] = {'status': 'completed', 'cancel': threading.Event(),
        'session_digest': digest, 'result': {'candidates': [{'candidate_id': 'candidate-1', 'title': 'Stage PFE Python',
            'company': 'Entreprise source', 'city': 'Marrakech', 'opportunity_type': 'Stage PFE', 'summary': 'Stage Python',
            'skills': ['Python'], 'source_name': 'Carrières', 'source_url': SOURCE}]}}
    denied = client.post(f'/api/ai-search/jobs/{ident}/stage', json={'candidate_id': 'candidate-1'})
    assert denied.status_code == 400
    from backend.api import ai_search_stage
    with app.test_request_context(f'/api/ai-search/jobs/{ident}/stage', method='POST', json={'candidate_id': 'candidate-1', 'manual_verified': True,
        'consultation_allowed': True, 'storage_allowed': True, 'display_allowed': True, 'permission_ref': 'accord test 2026'}):
        from flask import session
        session.update(authenticated=True, csrf='test', ai_search_session='fixture-session')
        staged = ai_search_stage(ident)
    staged_data=staged[0].get_json()
    assert staged[1] == 201, staged_data
    run_id, source = staged_data['id'], staged_data['source']
    approved=client.post(f"/api/collect/runs/{run_id}/staged/{staged_data['stage_id']}/decision",json={'decision':'approved'})
    assert approved.status_code == 200
    imported = client.post(f'/api/collect/runs/{run_id}/import', json={'sources': [source], 'rights_confirmed': True})
    assert imported.status_code == 200, imported.json
    assert imported.json['imported'] == 1
    with connect(str(legacy_database)) as db:
        assert db.execute('SELECT count(*) FROM offres').fetchone()[0] == 4
        assert db.execute('SELECT count(*) FROM candidatures').fetchone()[0] == 5

