import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.common import prepare
import pandas as pd
import requests
import re

def main():
    prepare(external=True)
    df = pd.read_excel('data_raw/entreprises_marrakech_complet.xlsx')
    emails_trouves = []
    for index, row in df.iterrows():
        site = row['Site Web']
        if pd.isna(site):
            emails_trouves.append('')
            continue
        try:
            print(f'Analyse : {site}')
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(site, headers=headers, timeout=10)
            html = response.text
            emails = re.findall('[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}', html)
            if emails:
                emails_trouves.append(', '.join(set(emails)))
            else:
                emails_trouves.append('')
        except:
            emails_trouves.append('')
    df['Emails'] = emails_trouves
    df.to_excel('data_raw/entreprises_marrakech_emails.xlsx', index=False)
    print('Terminé')

if __name__ == "__main__":
    main()
