from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_leaflet_is_served_locally_and_osm_is_allowed_by_csp(client):
    javascript = client.get('/vendor/leaflet/leaflet.js')
    stylesheet = client.get('/vendor/leaflet/leaflet.css')
    image = client.get('/vendor/leaflet/images/marker-icon.png')
    page = client.get('/js/ui.js').data.decode('utf-8')
    policy = client.get('/carte.html').headers['Content-Security-Policy']

    assert javascript.status_code == stylesheet.status_code == image.status_code == 200
    assert b"L.version='1.9.4'" in javascript.data or b'1.9.4' in javascript.data
    assert b'images/marker-icon.png' in stylesheet.data
    assert "https://tile.openstreetmap.org/{z}/{x}/{y}.png" in page
    assert 'OpenStreetMap contributors' in page
    assert 'tileerror' in page and 'fond cartographique est indisponible' in page
    assert 'https://tile.openstreetmap.org' in policy
    assert '/vendor/leaflet/leaflet.js' in page


def test_map_keeps_historical_links_and_reports_only_verified_coordinates(client):
    response = client.get('/api/map')

    assert response.status_code == 200
    assert response.json['verified'] == []
    assert len(response.json['companies']) == 2
    assert any(company['Google Maps'] == 'https://www.google.com/maps/search/?api=1&query=Marrakech'
               for company in response.json['companies'])
    assert 'Aucun géocodage automatique' in response.json['notice']


def test_map_filter_controls_real_and_fictional_markers_without_guessing_data():
    source = (ROOT / 'dashboard/js/ui.js').read_text(encoding='utf-8')

    assert "c.Nom||''" in source
    assert "c.Secteur===sector.value" in source
    assert "data.verified.filter" in source
    assert "demo.checked?demoPoints" in source
    assert 'Point fictif : il ne représente aucune entreprise de la base.' in source
    assert 'Itinéraire ↗' in source and 'Ouvrir la fiche entreprise' in source
    assert 'innerHTML' not in source


def test_dash_prefixes_and_return_link_leave_the_iframe(client, app):
    dash = app.extensions['analytics']
    back = dash.layout.children[0].children[1]
    page = client.get('/analyses.html').data.decode('utf-8')
    navigation = (ROOT / 'dashboard/js/ui.js').read_text(encoding='utf-8')

    assert dash.config.routes_pathname_prefix == '/analytics/'
    assert dash.config.requests_pathname_prefix == '/analytics/'
    assert back.href == '/index.html'
    assert back.target == '_top'
    assert "src:'/analytics/'" in navigation
    assert client.get('/analytics/').status_code == 200
    assert client.get('/analytics/_dash-layout').status_code == 200
    assert 'iframe-dash' in (ROOT / 'dashboard/css/design.css').read_text(encoding='utf-8')
    assert 'data-page="analytics"' in page
    assert "['analytics','analyses.html','Analyses Dash'" in navigation


def test_verified_map_data_uses_only_imported_coordinate_provenance(client, app, tmp_path):
    from scripts.import_coordinates import import_coordinates

    csv = tmp_path / 'coordinates.csv'
    csv.write_text(
        'entreprise_id,place_id,latitude,longitude,source,verified_at,quartier,ville\n'
        '1,verified-fixture,31.63,-8.01,verified-test,2026-11-06T10:00:00+00:00,Quartier test,Marrakech\n',
        encoding='utf-8',
    )
    before = sqlite3.connect(app.config['DATABASE'])
    counts_before = tuple(before.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
                          for table in ('entreprises','offres','candidatures'))
    before.close()

    assert import_coordinates(app.config['DATABASE'], csv, tmp_path / 'backups') == 1
    data = client.get('/api/map').json
    assert len(data['verified']) == 1
    assert data['verified'][0]['geo_source'] == 'verified-test'
    assert data['verified'][0]['geo_verified_at'] == '2026-11-06T10:00:00+00:00'
    after = sqlite3.connect(app.config['DATABASE'])
    counts_after = tuple(after.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
                         for table in ('entreprises','offres','candidatures'))
    after.close()
    assert counts_after == counts_before == (2, 3, 5)
