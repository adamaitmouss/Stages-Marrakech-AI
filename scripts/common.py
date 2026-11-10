"""Chemins et autorisation explicite des commandes de collecte."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def prepare(external=False):
    load_dotenv(ROOT / '.env')
    if external:
        if '--allow-external' not in sys.argv:
            raise SystemExit('Collecte désactivée. Relisez les coûts et conditions, puis utilisez --allow-external pour autoriser cette commande.')
        if 'collect_entreprises' in sys.argv[0] or 'test_places' in sys.argv[0]:
            if not os.getenv('GOOGLE_PLACES_API_KEY'):
                raise SystemExit('Variable GOOGLE_PLACES_API_KEY absente.')
    os.chdir(ROOT)
    for directory in ('data_raw','data_clean','reports','reports/graphs','database'):
        (ROOT/directory).mkdir(parents=True, exist_ok=True)
