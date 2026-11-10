import re
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.common import prepare
import pandas as pd

def main():
    prepare(external=False)
    df = pd.read_excel('data_raw/base_stages_marrakech.xlsx')

    def classifier(row):
        texte = (str(row['Nom']) + ' ' + str(row['Site Web']) + ' ' + str(row['Adresse'])).lower()
        if any((re.search(r"(?<!\w)" + re.escape(mot) + r"(?!\w)", texte) for mot in ['informatique', 'it', 'tech', 'computer', 'software', 'digital', 'web'])):
            return 'Informatique'
        elif any((re.search(r"(?<!\w)" + re.escape(mot) + r"(?!\w)", texte) for mot in ['marketing', 'communication', 'publicite', 'publicité', 'agency', 'media'])):
            return 'Marketing'
        elif any((re.search(r"(?<!\w)" + re.escape(mot) + r"(?!\w)", texte) for mot in ['comptable', 'comptabilite', 'comptabilité', 'fiduciaire', 'audit', 'finance'])):
            return 'Comptabilité'
        elif any((re.search(r"(?<!\w)" + re.escape(mot) + r"(?!\w)", texte) for mot in ['hotel', 'hôtel', 'riad', 'resort', 'spa', 'palace'])):
            return 'Hôtellerie'
        elif any((re.search(r"(?<!\w)" + re.escape(mot) + r"(?!\w)", texte) for mot in ['construction', 'btp', 'travaux', 'batiment', 'bâtiment', 'villa'])):
            return 'Construction'
        elif any((re.search(r"(?<!\w)" + re.escape(mot) + r"(?!\w)", texte) for mot in ['tourisme', 'travel', 'voyage', 'tour', 'excursion'])):
            return 'Tourisme'
        elif any((re.search(r"(?<!\w)" + re.escape(mot) + r"(?!\w)", texte) for mot in ['rh', 'recrutement', 'ressources humaines', 'human resources'])):
            return 'RH'
        elif any((re.search(r"(?<!\w)" + re.escape(mot) + r"(?!\w)", texte) for mot in ['logistique', 'transport', 'livraison', 'supply'])):
            return 'Logistique'
        elif any((re.search(r"(?<!\w)" + re.escape(mot) + r"(?!\w)", texte) for mot in ['industrie', 'usine', 'factory', 'production'])):
            return 'Industrie'
        elif any((re.search(r"(?<!\w)" + re.escape(mot) + r"(?!\w)", texte) for mot in ['commerce', 'vente', 'distribution', 'market'])):
            return 'Commerce'
        else:
            return 'Autre'
    df['Secteur'] = df.apply(classifier, axis=1)
    df.to_excel('data_raw/base_stages_marrakech_classee.xlsx', index=False)
    print('\n===== RÉPARTITION =====')
    print(df['Secteur'].value_counts())
    print('\nFichier créé :')
    print('data_raw/base_stages_marrakech_classee.xlsx')

if __name__ == "__main__":
    main()
