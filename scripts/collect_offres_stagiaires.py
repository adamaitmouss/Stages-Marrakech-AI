import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.common import prepare
import requests

def main():
    prepare(external=True)
    url = 'https://api.stagiaires.ma/api/v1/public/annonces'
    params = {'page': 1, 'limit': 20, 'ville': 48360}
    response = requests.get(url, params=params, timeout=15)
    print('Code :', response.status_code)
    data = response.json()
    print('Pagination :', data.get('pagination'))
    print('Nombre :', len(data.get('data', [])))
    for offre in data.get('data', []):
        print(offre.get('id'), '|', offre.get('titre'), '| ville_id =', offre.get('ville_id'))

if __name__ == "__main__":
    main()
