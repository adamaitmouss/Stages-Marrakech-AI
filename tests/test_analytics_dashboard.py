import sqlite3

from backend.analytics import dataset_notice, load_data


def _walk(node):
    if isinstance(node, (list, tuple)):
        for item in node:
            yield from _walk(item)
    elif hasattr(node, 'children'):
        yield node
        yield from _walk(node.children)
    else:
        yield node


def test_dashboard_removes_collection_panel_and_preserves_analysis_filters(app):
    dash = app.extensions['analytics']
    assert 'base locale privée' in dataset_notice(app.config['DATABASE'])
    components = list(_walk(dash.layout))
    ids = {getattr(component, 'id', None) for component in components}
    labels = [str(getattr(component, 'children', '')) for component in components]

    assert 'Activité de collecte' not in labels
    assert not {'collection-kpis', 'collection-sources', 'collection-daily', 'collection-quality'} & ids
    assert {'dataset', 'metric', 'sector', 'stage', 'contract', 'company', 'dates', 'kind', 'graph', 'quality'} <= ids
    assert 'collection-' not in '\n'.join(dash.callback_map)
    assert set(dash.audit_callbacks) == {'options', 'update', 'export'}

    return_link = next(component for component in components if getattr(component, 'href', None) == '/index.html')
    assert return_link.target == '_top'

    assert len(load_data(app.config['DATABASE'], 'companies')) == 2
    assert len(load_data(app.config['DATABASE'], 'offers')) == 3
    assert len(load_data(app.config['DATABASE'], 'applications')) == 5


def test_dashboard_labels_synthetic_database_from_its_marker(tmp_path):
    database = tmp_path / 'synthetic.db'
    with sqlite3.connect(database) as connection:
        connection.execute('CREATE TABLE deployment_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
        connection.execute("INSERT INTO deployment_metadata VALUES ('dataset_type', 'synthetic_public_demo')")

    notice = dataset_notice(str(database))
    assert 'synthétique de démonstration' in notice
    assert 'ne sont pas des offres réelles' in notice

