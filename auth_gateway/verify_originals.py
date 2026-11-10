"""Compare les empreintes des fichiers préexistants sans parcourir les dossiers privés."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).resolve().parent / 'ORIGINAL_SHA256_BEFORE.json'


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    changes = []
    for item in manifest['files']:
        path = ROOT / item['path']
        if not path.is_file():
            changes.append(f"absent: {item['path']}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item['sha256']:
            changes.append(f"modifié: {item['path']}")
    db_path = ROOT / 'database' / 'stages_marrakech.db'
    if db_path.is_file():
        with sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True) as db:
            integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
            counts = tuple(db.execute('SELECT COUNT(*) FROM "' + table + '"').fetchone()[0]
                           for table in ('entreprises', 'offres', 'candidatures'))
            fk_errors = len(db.execute('PRAGMA foreign_key_check').fetchall())
        print(f'Base locale : intégrité={integrity}; entreprises/offres/candidatures={counts}; erreurs FK={fk_errors}')
        if integrity != 'ok' or counts != (292, 88, 5) or fk_errors:
            changes.append('état/intégrité de la base historique inattendu')
    if changes:
        print('Écarts détectés :')
        for change in changes:
            print('- ' + change)
        return 1
    print(f"Empreintes inchangées : {len(manifest['files'])} fichiers préexistants suivis; aucun écart.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
