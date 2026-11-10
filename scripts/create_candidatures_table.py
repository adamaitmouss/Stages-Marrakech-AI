import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.common import prepare
import sqlite3

def main():
    prepare(external=False)
    conn = sqlite3.connect('database/stages_marrakech.db')
    cursor = conn.cursor()
    cursor.execute('\nCREATE TABLE IF NOT EXISTS candidatures (\n\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n    nom_entreprise TEXT,\n\n    secteur TEXT,\n\n    email TEXT,\n\n    telephone TEXT,\n\n    date_candidature TEXT,\n\n    statut TEXT,\n\n    commentaire TEXT\n)\n')
    conn.commit()
    print('Table candidatures créée.')
    conn.close()

if __name__ == "__main__":
    main()
