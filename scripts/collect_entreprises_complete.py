import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.common import prepare
import requests
import pandas as pd
import re
import time
from datetime import datetime, timezone
from scripts.places_client import search_places

def main():
    prepare(external=True)
    API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {'Content-Type': 'application/json', 'X-Goog-Api-Key': API_KEY, 'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri'}
    queries = ['entreprise informatique Marrakech', 'entreprise marketing Marrakech', 'entreprise comptabilité Marrakech', 'entreprise construction Marrakech', 'entreprise hôtellerie Marrakech', 'entreprise industrie Marrakech', 'entreprise tourisme Marrakech', 'entreprise RH Marrakech', 'entreprise commerce Marrakech', 'entreprise logistique Marrakech', "centre d'appel Marrakech", 'cabinet comptable Marrakech', 'agence web Marrakech', 'startup Marrakech', 'hôtel Marrakech', 'agence communication Marrakech', 'agence voyage Marrakech', 'bureau étude Marrakech']
    entreprises = []
    for q in queries:
        print(f'\nRecherche : {q}')
        try:
            data = {'places': search_places(q, API_KEY)}
            if 'places' in data:
                for p in data['places']:
                    entreprises.append({'Nom': p.get('displayName', {}).get('text', ''), 'Adresse': p.get('formattedAddress', ''), 'Téléphone': p.get('nationalPhoneNumber', ''), 'Site Web': p.get('websiteUri', ''), 'Google Maps': p.get('googleMapsUri', ''), 'place_id': p.get('id'), 'latitude': p.get('location', {}).get('latitude'), 'longitude': p.get('location', {}).get('longitude'), 'geo_source': 'Google Places New' if p.get('location') else None, 'geo_verified_at': datetime.now(timezone.utc).isoformat() if p.get('location') else None})
            time.sleep(1)
        except Exception as e:
            print('Erreur :', e)
    df = pd.DataFrame(entreprises)
    if df.empty:
        raise ValueError('Collecte vide : aucun fichier existant ne sera remplac?.')
    df.drop_duplicates(subset=['Nom'], inplace=True)
    print('\nEntreprises trouvées :', len(df))
    emails_trouves = []
    for index, row in df.iterrows():
        site = row['Site Web']
        if pd.isna(site) or site == '':
            emails_trouves.append('')
            continue
        try:
            print(f'Analyse : {site}')
            headers_site = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(site, headers=headers_site, timeout=10)
            html = response.text
            emails = re.findall('[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}', html)
            emails_valides = []
            for email in emails:
                email = email.lower()
                if '.png' in email:
                    continue
                if '.jpg' in email:
                    continue
                if '.jpeg' in email:
                    continue
                if '.webp' in email:
                    continue
                if 'example' in email:
                    continue
                if 'exemple' in email:
                    continue
                if 'votre@' in email:
                    continue
                emails_valides.append(email)
            emails_valides = list(set(emails_valides))
            emails_trouves.append(', '.join(emails_valides))
        except:
            emails_trouves.append('')
    df['Emails'] = emails_trouves
    df['Secteur'] = ''
    df['Date candidature'] = ''
    df['Statut'] = 'À contacter'
    df.to_excel('data_raw/base_stages_marrakech.xlsx', index=False)
    print('\n================================')
    print('Fichier créé :')
    print('data_raw/base_stages_marrakech.xlsx')
    print('================================')
    nb_emails = (df['Emails'] != '').sum()
    print('Entreprises :', len(df))
    print('Emails trouvés :', nb_emails)
if __name__ == '__main__':
    main()
