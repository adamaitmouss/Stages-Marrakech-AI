"""Import MANUEL de coordonnées vérifiées, sans aucun appel réseau.

CSV UTF-8 : entreprise_id,place_id,latitude,longitude,source,verified_at,quartier,ville
Le rapprochement entreprise_id (rowid existant) doit être vérifié humainement.
"""
import argparse
import csv
import math
import sqlite3
from datetime import datetime
from pathlib import Path


def import_coordinates(database, csv_path, backup_dir):
    with Path(csv_path).open(encoding='utf-8-sig', newline='') as stream:
        entries = list(csv.DictReader(stream))
    validated = []
    seen=set()
    for row in entries:
        ident=int(row['entreprise_id']);lat=float(row['latitude']);lng=float(row['longitude'])
        if ident in seen:
            raise ValueError('Entreprise répétée dans le fichier de coordonnées.')
        seen.add(ident)
        if not math.isfinite(lat) or not math.isfinite(lng) or not -90 <= lat <= 90 or not -180 <= lng <= 180:
            raise ValueError('Coordonnées hors limites.')
        if not row.get('source') or not row.get('verified_at'):
            raise ValueError('Provenance et date de vérification obligatoires.')
        datetime.fromisoformat(row['verified_at'])
        validated.append((ident, lat, lng, row))
    Path(backup_dir).mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(database) as db:
        with sqlite3.connect(Path(backup_dir)/('avant_coordonnees_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.db')) as backup:
            db.backup(backup)
        for ident, lat, lng, row in validated:
            if not db.execute('SELECT 1 FROM entreprises WHERE rowid=?',(ident,)).fetchone():
                raise ValueError('Entreprise inconnue : '+str(ident))
            db.execute('''UPDATE entreprises SET place_id=?,latitude=?,longitude=?,geo_source=?,geo_verified_at=?,quartier=?,ville=? WHERE rowid=?''',
                       (row.get('place_id') or None,lat,lng,row['source'],row['verified_at'],row.get('quartier') or None,row.get('ville') or None,ident))
        db.commit()
    return len(validated)


if __name__ == '__main__':
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv');parser.add_argument('--confirm-verified',action='store_true')
    args=parser.parse_args()
    if not args.confirm_verified:
        parser.error('Vérifiez les identités et coordonnées, puis ajoutez --confirm-verified.')
    print(import_coordinates(root/'database/stages_marrakech.db',args.csv,root/'backups'),'coordonnées importées.')
