"""Create a new, synthetic SQLite dataset for a read-only public demo."""
import argparse
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.db import migrate, migrate_phase5, migrate_phase7, migrate_phase9, connect


def create_public_demo_database(output):
    path=Path(output).resolve()
    if path.exists():
        raise FileExistsError(f'Refusing to overwrite existing database: {path}')
    path.parent.mkdir(parents=True,exist_ok=True)
    with connect(path) as db:
        db.executescript('''
        CREATE TABLE entreprises (Nom TEXT, Adresse TEXT, "Téléphone" TEXT, "Site Web" TEXT,
            "Google Maps" TEXT, Emails TEXT, Secteur TEXT);
        CREATE TABLE offres (ID INTEGER, Titre TEXT, Description TEXT, "Type contrat" TEXT,
            "Type stage" TEXT, "Entreprise ID" INTEGER, "Date publication" TEXT,
            "Date expiration" TEXT, "Lien annonce" TEXT, "Lien public" TEXT);
        CREATE TABLE candidatures (id INTEGER PRIMARY KEY AUTOINCREMENT,nom_entreprise TEXT,secteur TEXT,email TEXT,
            telephone TEXT,date_candidature TEXT,statut TEXT,commentaire TEXT);
        ''')
    with tempfile.TemporaryDirectory(prefix='public_demo_migrations_') as backup_dir:
        migrate(str(path),backup_dir);migrate_phase5(str(path),backup_dir)
        migrate_phase7(str(path),backup_dir);migrate_phase9(str(path),backup_dir)
    companies=[
        ('Atlas Data Lab (démo)','Marrakech · données synthétiques','https://example.org/demo/atlas','Technologie'),
        ('Médina Numérique (démo)','Marrakech · données synthétiques','https://example.org/demo/medina','Services numériques'),
        ('Oasis Analytics (démo)','Marrakech · données synthétiques','https://example.org/demo/oasis','Data Science'),
        ('Pixel Sud (démo)','Marrakech · données synthétiques','https://example.org/demo/pixel','Développement'),
        ('Riad Conseil (démo)','Marrakech · données synthétiques','https://example.org/demo/riad','Conseil'),
    ]
    with connect(path) as db:
        for name,address,site,sector in companies:
            db.execute('INSERT INTO entreprises(Nom,Adresse,"Site Web",Secteur,ville) VALUES (?,?,?,?,?)',
                       (name,address,site,sector,'Marrakech'))
        offers=[
            (1,'Stage PFE Data Science (démo)','Offre entièrement synthétique pour démonstration. Python, pandas et SQL.','Stage','Stage PFE',1,'2026-10-20','2027-01-31','https://example.org/demo/offres/data-science','https://example.org/demo/offres/data-science'),
            (2,'Stage Développement Python (démo)','Annonce fictive. API Flask, tests automatisés et travail en équipe.','Stage','Stage PFE',2,'2026-10-18','2027-01-31','https://example.org/demo/offres/python','https://example.org/demo/offres/python'),
            (3,'Stage BI et visualisation (démo)','Annonce fictive. SQL, tableaux de bord et visualisation de données.','Stage','Stage fonctionnel',3,'2026-10-15','2027-01-31','https://example.org/demo/offres/bi','https://example.org/demo/offres/bi'),
            (4,'Développeur web junior (démo)','Annonce fictive de premier emploi pour valider les filtres.','Premier emploi','',4,'2026-10-10','2027-01-31','https://example.org/demo/offres/web','https://example.org/demo/offres/web'),
        ]
        for item in offers:
            ident,title,description,contract,stage,company_id,published,expiry,job_url,apply_url=item
            db.execute('''INSERT INTO offres("ID","Titre","Description","Type contrat","Type stage","Entreprise ID",
                "Date publication","Date expiration","Lien annonce","Lien public",source,entreprise_nom,ville,
                competences,relation_verified) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)''',
                (ident,title,description,contract,stage,company_id,published,expiry,job_url,apply_url,
                 'Données synthétiques de démonstration',companies[company_id-1][0],'Marrakech',
                 'Python, SQL' if ident<3 else 'SQL, visualisation'))
        applications=[
            ('Atlas Data Lab (démo)','Technologie',None,None,'2026-10-21','Entretien','Candidature fictive. Données de démonstration.'),
            ('Médina Numérique (démo)','Services numériques',None,None,'2026-10-22','Envoyée','Candidature fictive. Données de démonstration.'),
            ('Oasis Analytics (démo)','Data Science',None,None,'2026-10-23','Non envoyée','Candidature fictive. Données de démonstration.'),
        ]
        for app in applications:
            db.execute('''INSERT INTO candidatures(nom_entreprise,secteur,email,telephone,date_candidature,statut,commentaire)
                VALUES (?,?,?,?,?,?,?)''',app)
        db.execute('CREATE TABLE deployment_metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        db.execute("INSERT INTO deployment_metadata VALUES ('dataset_type','synthetic_public_demo')")
        db.execute("INSERT INTO deployment_metadata VALUES ('read_only','true')")
    return str(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='database/stages_marrakech_public_demo.db')
    args=parser.parse_args()
    print(create_public_demo_database(args.output))
