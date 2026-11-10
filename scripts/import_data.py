"""Import Excel idempotent et non destructif. Sauvegarde avant chaque import."""
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def import_excel(database=None, source_dir=None, backup_dir=None):
    path = Path(database) if database else ROOT/'database/stages_marrakech.db'
    backups = Path(backup_dir) if backup_dir else (path.parent/'backups' if database else ROOT/'backups')
    backups.mkdir(exist_ok=True)
    with sqlite3.connect(path) as db:
        with sqlite3.connect(backups/('avant_import_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.db')) as target:
            db.backup(target)
        for table, filename, identity in [('entreprises','entreprises_marrakech_clean.xlsx','Nom'),('offres','offres_stagiaires_marrakech_clean.xlsx','ID')]:
            data = pd.read_excel((Path(source_dir) if source_dir else ROOT/'data_clean')/filename)
            if data.empty or identity not in data or data[identity].isna().any() or data[identity].duplicated().any():
                raise ValueError('Import refusé : identifiants vides, dupliqués ou fichier vide pour '+table)
            columns = {row[1] for row in db.execute(f'PRAGMA table_info({table})')}
            if not columns:
                raise ValueError('Table absente : restaurez la base initiale livrée.')
            data = data[[col for col in data if col in columns]]
            for row in data.to_dict('records'):
                cleaned = {k: (None if pd.isna(v) else v.isoformat() if isinstance(v,pd.Timestamp) else v) for k,v in row.items()}
                existing = db.execute(f'SELECT rowid FROM "{table}" WHERE "{identity}"=?', (cleaned[identity],)).fetchone()
                names=list(cleaned)
                if existing:
                    db.execute(f'UPDATE "{table}" SET '+','.join('"'+n+'"=COALESCE(?,"'+n+'")' for n in names)+' WHERE rowid=?', (*cleaned.values(),existing[0]))
                else:
                    db.execute(f'INSERT INTO "{table}" ('+','.join('"'+n+'"' for n in names)+') VALUES ('+','.join('?' for _ in names)+')',tuple(cleaned.values()))
        db.commit()
    print('Import terminé. Aucun enregistrement historique supprimé.')


if __name__ == '__main__':
    import_excel()
