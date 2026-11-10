import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.common import prepare
import requests
import pandas as pd
import time
from datetime import datetime, timezone
from scripts.places_client import search_places

def main():
    prepare(external=True)
    API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {'Content-Type': 'application/json', 'X-Goog-Api-Key': API_KEY, 'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri'}
    entreprises = []
    queries = ['entreprise informatique Marrakech', 'entreprise marketing Marrakech', 'entreprise comptabilité Marrakech', 'entreprise construction Marrakech', 'entreprise hôtellerie Marrakech', 'entreprise industrie Marrakech', 'entreprise tourisme Marrakech', 'entreprise RH Marrakech', 'entreprise commerce Marrakech', 'entreprise logistique Marrakech']
    for q in queries:
        print(f'\nRecherche : {q}')
        data = {'places': search_places(q, API_KEY)}
        if 'places' in data:
            for p in data['places']:
                entreprises.append({'Nom': p.get('displayName', {}).get('text', ''), 'Adresse': p.get('formattedAddress', ''), 'Téléphone': p.get('nationalPhoneNumber', ''), 'Site Web': p.get('websiteUri', ''), 'Google Maps': p.get('googleMapsUri', ''), 'place_id': p.get('id'), 'latitude': p.get('location', {}).get('latitude'), 'longitude': p.get('location', {}).get('longitude'), 'geo_source': 'Google Places New' if p.get('location') else None, 'geo_verified_at': datetime.now(timezone.utc).isoformat() if p.get('location') else None})
        time.sleep(1)
    df = pd.DataFrame(entreprises)
    if df.empty:
        raise ValueError('Collecte vide : aucun fichier existant ne sera remplac?.')
    df.drop_duplicates(subset=['Nom'], inplace=True)
    print("\nNombre d'entreprises :", len(df))
    print(df.head())
    df.to_excel('data_raw/entreprises_marrakech_complet.xlsx', index=False)
    print('\nFichier créé : entreprises_marrakech_complet.xlsx')
if __name__ == '__main__':
    main()
