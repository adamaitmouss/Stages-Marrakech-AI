"""Véritable application Dash montée sur Flask, données relues à chaque callback."""
import io
import sqlite3
from collections import Counter
from datetime import date
from dash import Dash, html, dcc, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .db import rows, request_database

PALETTE = ['#2864F5', '#19B6A4', '#F6AB49', '#8D7CF5', '#527291']


def load_data(path, tab, sector=None, stage=None, contract=None, start=None, end=None, company=None):
    table = {'companies': 'entreprises', 'offers': 'offres', 'applications': 'candidatures'}[tab]
    if tab=='offers':
        data=rows(path, '''SELECT offres.*,
            CASE WHEN COALESCE(offres.relation_verified,0)=1 THEN entreprises."Secteur" ELSE NULL END AS secteur
            FROM offres LEFT JOIN entreprises ON offres.entreprise_ref=entreprises.rowid AND COALESCE(offres.relation_verified,0)=1''')
    else:
        data=rows(path, f'SELECT * FROM {table}')
    df = pd.DataFrame(data)
    if df.empty:
        return df
    for column, value in [('Secteur' if tab == 'companies' else 'secteur', sector), ('Type stage', stage), ('Type contrat', contract),
                          ('Nom' if tab == 'companies' else 'nom_entreprise' if tab == 'applications' else 'entreprise_nom', company)]:
        if column in df.columns and value:
            df = df[df[column] == value]
    date_col = 'Date publication' if tab == 'offers' else 'date_candidature' if tab == 'applications' else None
    if date_col:
        dates = pd.to_datetime(df[date_col], errors='coerce', utc=True)
        if start:
            df = df[dates >= pd.Timestamp(start, tz='UTC')]
            dates = dates.loc[df.index]
        if end:
            df = df[dates < pd.Timestamp(end, tz='UTC')+pd.Timedelta(days=1)]
    return df


def figure_for(df, metric, kind):
    fig = go.Figure()
    if df.empty or metric not in df.columns:
        fig.add_annotation(text='Données insuffisantes pour cette sélection.', showarrow=False)
    else:
        is_date = metric in ('Date publication', 'date_candidature')
        values = pd.to_datetime(df[metric], errors='coerce').dt.strftime('%Y-%m-%d') if is_date else df[metric].fillna('Non renseigné')
        counts = values.value_counts().sort_index() if is_date else values.value_counts().head(20)
        summary = pd.DataFrame({'Valeur': counts.index.astype(str), 'Nombre': counts.values})
        if kind == 'histogram' and not is_date:
            fig.add_annotation(text='L’histogramme est réservé aux dates. Choisissez Barres pour ces catégories.', showarrow=False)
        elif kind == 'line' and not is_date:
            fig.add_annotation(text='La courbe exige une date : choisissez un indicateur temporel.', showarrow=False)
        elif kind == 'scatter':
            fig = px.scatter(summary, x='Valeur', y='Nombre', size='Nombre', color_discrete_sequence=PALETTE)
        elif kind == 'pie':
            fig = px.pie(summary, names='Valeur', values='Nombre', color_discrete_sequence=PALETTE)
        elif kind == 'line':
            fig = px.line(summary, x='Valeur', y='Nombre', markers=True, color_discrete_sequence=PALETTE)
        elif kind == 'histogram':
            fig = px.histogram(pd.DataFrame({'Date': values.dropna()}), x='Date', color_discrete_sequence=PALETTE)
        else:
            fig = px.bar(summary, x='Valeur', y='Nombre', color_discrete_sequence=PALETTE)
    fig.update_layout(template='plotly_white', font={'family': 'Segoe UI, sans-serif'}, margin=dict(l=30,r=20,t=30,b=80),
                      paper_bgcolor='#ffffff', plot_bgcolor='#ffffff', height=430)
    return fig


def missing_values(series):
    return series.isna() | series.astype(str).str.strip().eq('')


def dataset_notice(path, public_demo=False):
    """Describe the selected dataset without implying that demo rows are real."""
    try:
        marker = rows(path, "SELECT value FROM deployment_metadata WHERE key='dataset_type'")
    except sqlite3.Error:
        marker = []
    if public_demo or any(item.get('value') == 'synthetic_public_demo' for item in marker):
        return 'Jeu synthétique de démonstration dans SQLite; ces exemples ne sont pas des offres réelles.'
    return 'Données de la base locale privée. Les offres couvrent une période limitée, pas une tendance annuelle.'


def quality_summary(tab, df):
    if tab == 'companies':
        total = len(df)
        no_email = int(missing_values(df['Emails']).sum()) if 'Emails' in df else total
        no_site = int(missing_values(df['Site Web']).sum()) if 'Site Web' in df else total
        if {'latitude','longitude','geo_verified_at','geo_source'}.issubset(df.columns):
            lat, lon = pd.to_numeric(df['latitude'],errors='coerce'), pd.to_numeric(df['longitude'],errors='coerce')
            verified = lat.between(-90,90) & lon.between(-180,180) & ~missing_values(df['geo_verified_at']) & ~missing_values(df['geo_source'])
            located = int(verified.sum())
        else:
            located = 0
        pct = f'{located/total*100:.1f} %' if total else 'Non calculable'
        return [f'Entreprises sans email : {no_email}/{total}.', f'Entreprises sans site web : {no_site}/{total}.',
                f'Coordonnées vérifiées : {located}/{total} ({pct}).']
    if tab == 'offers':
        total = len(df)
        no_stage = int(missing_values(df['Type stage']).sum()) if 'Type stage' in df else total
        if 'Date expiration' in df:
            expiry = pd.to_datetime(df['Date expiration'],errors='coerce').dt.date
            expired = int((expiry.notna() & (expiry < date.today())).sum())
            unknown_expiry = int(expiry.isna().sum())
        else:
            expired,unknown_expiry=0,total
        locations = int((~missing_values(df['ville'])).sum()) if 'ville' in df else 0
        return [f'Offres sans type de stage : {no_stage}/{total}.', f'Offres expirées selon la date source : {expired}/{total}.',
                f'Date d’expiration inconnue : {unknown_expiry}/{total}.', f'Offres avec ville renseignée : {locations}/{total}.']
    statuses = Counter(str(v) if pd.notna(v) and str(v).strip() else 'Non renseigné' for v in df.get('statut',pd.Series(dtype=str)))
    return ['Candidatures par statut : '+(', '.join(f'{key} ({value})' for key,value in sorted(statuses.items())) if statuses else 'aucune ligne filtrée.')]


def mount_dash(server):
    app = Dash(__name__, server=server, routes_pathname_prefix='/analytics/',
               requests_pathname_prefix='/analytics/', title='Analyses • Stages Marrakech',
               external_stylesheets=['/css/analytics.css'], serve_locally=True)
    path = server.config['DATABASE']
    origin_notice = dataset_notice(path, server.config.get('PUBLIC_DEMO_MODE', False))
    app.layout = html.Main([
        html.Div([html.Div([html.Small('EXPLORATEUR DE DONNÉES'), html.H1('Comprendre vos opportunités'),
                           html.P(origin_notice, className='data-origin')]),
                  html.A('← Retour à l’application', href='/index.html', target='_top', className='back')], className='dash-head'),
        html.Div(id='kpis', className='dash-kpis'),
        dcc.Tabs(id='dataset', value='offers', children=[dcc.Tab(label='Offres', value='offers'), dcc.Tab(label='Entreprises', value='companies'), dcc.Tab(label='Candidatures', value='applications')]),
        html.Div([
            html.Label(['Indicateur', dcc.Dropdown(id='metric', clearable=False)]),
            html.Label(['Secteur', dcc.Dropdown(id='sector', placeholder='Tous les secteurs')]),
            html.Label(['Type de stage', dcc.Dropdown(id='stage', placeholder='Tous les stages')]),
            html.Label(['Contrat', dcc.Dropdown(id='contract', placeholder='Tous les contrats')]),
            html.Label(['Entreprise connue', dcc.Dropdown(id='company', placeholder='Toutes les entreprises')]),
            html.Label(['Période', dcc.DatePickerRange(id='dates', display_format='DD/MM/YYYY', start_date_placeholder_text='Début', end_date_placeholder_text='Fin')]),
        ], className='dash-filters'),
        dcc.RadioItems(id='kind', value='bar', inline=True, options=[{'label': l, 'value': v} for l,v in [('Barres','bar'),('Courbe','line'),('Camembert','pie'),('Scatter','scatter'),('Histogramme','histogram')]], className='kinds'),
        dcc.Loading(dcc.Graph(id='graph', config={'displaylogo': False, 'toImageButtonOptions': {'format': 'png', 'filename': 'analyse_stages'}})),
        html.Div(id='quality', className='quality'),
        html.Div([html.Button('Exporter les données filtrées (CSV)', id='export', n_clicks=0),
                  html.Button('Actualiser', id='refresh', n_clicks=0)], className='dash-actions'),
        dcc.Download(id='download'), dcc.Interval(id='tick', interval=60000, n_intervals=0),
    ], className='dash-main')

    @app.callback(Output('metric','options'), Output('metric','value'), Output('sector','options'), Output('sector','disabled'),
                  Output('stage','options'), Output('stage','disabled'), Output('contract','options'), Output('contract','disabled'),
                  Output('company','options'), Output('company','disabled'), Output('dates','disabled'),
                  Input('dataset','value'), Input('refresh','n_clicks'))
    def options(tab, refresh):
        df = load_data(request_database(path), tab)
        fields = {'companies': ['Secteur'], 'offers': ['Type stage','Type contrat','Date publication'], 'applications': ['statut','date_candidature','nom_entreprise']}[tab]
        metrics = [{'label': c, 'value': c} for c in fields if c in df.columns]
        result = [metrics, metrics[0]['value'] if metrics else None]
        for column in [('Secteur' if tab=='companies' else 'secteur'), 'Type stage', 'Type contrat',
                       ('Nom' if tab=='companies' else 'nom_entreprise' if tab=='applications' else 'entreprise_nom')]:
            values = sorted(df[column].dropna().astype(str).unique()) if column in df else []
            result += [[{'label': v,'value':v} for v in values if v], not bool(values)]
        result += [tab == 'companies']
        return result

    @app.callback(Output('graph','figure'), Output('kpis','children'), Output('quality','children'),
                  Input('dataset','value'), Input('metric','value'), Input('kind','value'), Input('sector','value'),
                  Input('stage','value'), Input('contract','value'), Input('dates','start_date'), Input('dates','end_date'),
                  Input('company','value'), Input('refresh','n_clicks'), Input('tick','n_intervals'))
    def update(tab, metric, kind, sector, stage, contract, start, end, company, refresh, tick):
        active_path = request_database(path)
        df = load_data(active_path, tab, sector, stage, contract, start, end, company)
        counts = {t: len(rows(active_path, f'SELECT rowid FROM {t}')) for t in ['entreprises','offres','candidatures']}
        counts[{'companies':'entreprises','offers':'offres','applications':'candidatures'}[tab]]=len(df)
        applications = ([{'statut':value} for value in df['statut'].tolist()] if tab=='applications' and 'statut' in df
                        else rows(active_path, 'SELECT statut FROM candidatures'))
        contacted = sum(a['statut'] in ('Envoyée','Relancée','Entretien','Acceptée','Refusée') for a in applications)
        response = sum(a['statut'] in ('Entretien','Acceptée','Refusée') for a in applications)
        kpis = [html.Div([html.Small(label),html.Strong(str(value))], className='dash-kpi') for label,value in [
            ('Entreprises',counts['entreprises']),('Offres',counts['offres']),('Candidatures',counts['candidatures']),
            ('Taux de réponse', f'{response/contacted*100:.1f} %' if contacted else 'Non calculable')]]
        quality = [html.P(f'{len(df)} ligne(s) dans le jeu actif après filtres. Les autres compteurs restent des totaux SQLite.')]
        quality.extend(html.P(item) for item in quality_summary(tab,df))
        quality.append(html.P('Taux de réponse : statuts Entretien, Acceptée ou Refusée / candidatures ayant quitté Non envoyée ; calcul selon le statut actuel.'
                              + (' Le taux utilise les candidatures du filtre actif.' if tab=='applications' else ' Le taux est calculé sur toutes les candidatures.')))
        if not df.empty:
            missing = df.isna().sum()
            quality.append(html.P('Valeurs manquantes : '+', '.join(f'{k} ({v})' for k,v in missing.items() if v)[:1800]))
        return figure_for(df,metric,kind), kpis, quality

    @app.callback(Output('download','data'), Input('export','n_clicks'), State('dataset','value'), State('sector','value'),
                  State('stage','value'), State('contract','value'), State('dates','start_date'), State('dates','end_date'),
                  State('company','value'), prevent_initial_call=True)
    def export(n, tab, sector, stage, contract, start, end, company):
        df = load_data(request_database(path),tab,sector,stage,contract,start,end,company)
        # Protection des tableurs contre les formules injectées dans un CSV.
        for column in df.select_dtypes(include=['object','str']):
            df[column] = df[column].map(lambda v: "'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v)
        return dcc.send_data_frame(df.to_csv, f'stages_{tab}.csv', index=False, encoding='utf-8-sig')
    app.audit_callbacks = {'options': options, 'update': update, 'export': export}
    @app.callback(Output('sector','value'),Output('stage','value'),Output('contract','value'),
                  Output('company','value'),Output('dates','start_date'),Output('dates','end_date'),
                  Input('dataset','value'),prevent_initial_call=True)
    def clear_filters(tab):
        return [None]*6
    return app
