import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.common import prepare
import requests
import pandas as pd
import time

def main():
    prepare(external=True)
    url = 'https://api.stagiaires.ma/api/v1/public/annonces'
    offres = []
    page = 1
    limit = 20
    ville_id = 48360
    while True:
        print(f'\n===== PAGE {page} =====')
        params = {'page': page, 'limit': limit, 'ville': ville_id}
        response = requests.get(url, params=params, timeout=15)
        print('Code :', response.status_code)
        if response.status_code != 200:
            print('Erreur API')
            break
        data = response.json()
        if not data.get('success'):
            print('Erreur dans la réponse API')
            break
        liste_offres = data.get('data', [])
        pagination = data.get('pagination', {})
        print('Offres trouvées :', len(liste_offres))
        print('Total API :', pagination.get('total'))
        print('Total pages :', pagination.get('totalPages'))
        if not liste_offres:
            print('Fin de la collecte.')
            break
        for offre in liste_offres:
            offres.append({'ID': offre.get('id'), 'Titre': offre.get('titre'), 'Description': offre.get('description'), 'Type contrat': offre.get('type_contrat'), 'Type stage': offre.get('type_stage'), 'Ville ID': offre.get('ville_id'), 'Entreprise ID': offre.get('entreprise_id'), 'Date publication': offre.get('date_publication'), 'Date expiration': offre.get('date_expiration'), 'Lien annonce': offre.get('lien_annonce'), 'Lien public': offre.get('lien_publique')})
        total_pages = pagination.get('totalPages', page)
        if page >= total_pages:
            print('Toutes les pages ont été récupérées.')
            break
        page += 1
        time.sleep(1)
    df = pd.DataFrame(offres)
    if df.empty:
        raise ValueError("Collecte vide : aucun fichier existant ne sera remplac?.")
    df.drop_duplicates(subset=['ID'], inplace=True)
    print('\n================================')
    print('TOTAL OFFRES MARRAKECH :', len(df))
    print('================================')
    fichier = 'data_raw/offres_stagiaires_marrakech.xlsx'
    df.to_excel(fichier, index=False)
    print('\nFichier créé :')
    print(fichier)

if __name__ == "__main__":
    main()
