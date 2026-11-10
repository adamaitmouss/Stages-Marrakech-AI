import sqlite3
import sys
import socket
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def no_external_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError('Tout appel réseau est interdit dans ces tests.')
    monkeypatch.setattr(socket.socket, 'connect', blocked)
    monkeypatch.setattr(socket, 'create_connection', blocked)


@pytest.fixture
def legacy_database(tmp_path):
    path=tmp_path/'data.db'
    with sqlite3.connect(path) as db:
        db.executescript('''
        CREATE TABLE entreprises (Nom TEXT, Adresse TEXT, "Téléphone" TEXT, "Site Web" TEXT, "Google Maps" TEXT, Emails TEXT, Secteur TEXT);
        CREATE TABLE offres (ID INTEGER, Titre TEXT, Description TEXT, "Type contrat" TEXT, "Type stage" TEXT,
            "Entreprise ID" INTEGER, "Date publication" TEXT, "Date expiration" TEXT, "Lien annonce" TEXT, "Lien public" TEXT);
        CREATE TABLE candidatures (id INTEGER PRIMARY KEY AUTOINCREMENT,nom_entreprise TEXT,secteur TEXT,email TEXT,
            telephone TEXT,date_candidature TEXT,statut TEXT,commentaire TEXT);
        ''')
        db.execute('INSERT INTO entreprises VALUES (?,?,?,?,?,?,?)',("L’Agence d'essai",'Adresse fictive',None,'https://example.test','https://www.google.com/maps/search/?api=1&query=Marrakech','jobs@example.test','Informatique'))
        db.execute('INSERT INTO entreprises VALUES (?,?,?,?,?,?,?)',('Exemple sans contact','Adresse de test',None,None,None,None,'Marketing'))
        description='Stage Python SQL Pandas et analyse de données. '+'Collecter nettoyer analyser présenter les données avec une équipe et documenter les projets pédagogiques. '*4
        for ident,title,contract,desc in [(1,'Stage Python','Stage',description),(2,'Stage marketing','Stage','Marketing communication SEO réseaux sociaux.'),(3,'Développeur Java','CDI','Java SQL développement logiciel.')]:
            db.execute('INSERT INTO offres VALUES (?,?,?,?,?,?,?,?,?,?)',(ident,title,desc,contract,'Stage fonctionnel',100+ident,'2026-09-01','2026-12-01','https://example.test/offer/'+str(ident),'https://example.test/apply/'+str(ident)))
        for i in range(5):
            db.execute('INSERT INTO candidatures(nom_entreprise,date_candidature,statut,commentaire) VALUES (?,?,?,?)',('Entreprise fictive '+str(i),'2026-09-01','Envoyée','Historique anonymisé '+str(i)))
    return path


@pytest.fixture
def app(legacy_database,tmp_path):
    from backend.web import create_app
    return create_app({'DATABASE':str(legacy_database),'PRIVATE_DIR':str(tmp_path/'private'),
                       'BACKUP_DIR':str(tmp_path/'backups'),'TESTING':True,'SMTP_ENABLED':False,
                       'PUBLIC_DEMO_MODE':False,'PUBLIC_DEMO_DATA_CONFIRMED':False,
                       'GEMINI_ENABLED':False,'GEMINI_API_KEY':'','MAPS_ENABLED':False,'MAPS_BROWSER_KEY':''})


@pytest.fixture
def client(app):
    client=app.test_client()
    info=client.get('/api/auth/session').json
    result=client.post('/api/auth/setup',json={'password':'Mot-de-passe-test-123!'},headers={'X-CSRF-Token':info['csrf']})
    assert result.status_code==200
    client.environ_base['HTTP_X_CSRF_TOKEN']=result.json['csrf']
    return client


@pytest.fixture
def cv_data():
    return {'name':'Profil Démonstration','title':'Étudiant Data Science','email':'demo@example.test','city':'Marrakech',
            'summary':'Profil fictif pour les tests.','technical':'Python, SQL, Pandas','languages':'Français, anglais',
            'education':[{'title':'Formation de démonstration','organization':'École fictive','period':'2026','description':'Python et statistiques.'}],
            'projects':[{'title':'Analyse pédagogique','description':'Nettoyage de données avec Pandas.'}]}


@pytest.fixture
def cv_id(client,cv_data):
    r=client.post('/api/cvs',json={'name':'Version fictive','template':'modern','data':cv_data})
    assert r.status_code==201, r.json
    return r.json['id']
