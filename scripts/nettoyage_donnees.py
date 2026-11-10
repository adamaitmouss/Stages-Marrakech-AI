import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.common import prepare
import pandas as pd
import os

def main():
    prepare(external=False)
    fichier_entreprises = 'data_raw/base_stages_marrakech_classee.xlsx'
    fichier_offres = 'data_raw/offres_stagiaires_marrakech.xlsx'
    sortie_entreprises = 'data_clean/entreprises_marrakech_clean.xlsx'
    sortie_offres = 'data_clean/offres_stagiaires_marrakech_clean.xlsx'
    os.makedirs('data_clean', exist_ok=True)
    print('\n======================================')
    print('NETTOYAGE DES ENTREPRISES')
    print('======================================')
    df_entreprises = pd.read_excel(fichier_entreprises)
    print('Avant nettoyage :', len(df_entreprises), 'lignes')
    colonnes_a_supprimer = ['Date candidature', 'Statut']
    df_entreprises.drop(columns=colonnes_a_supprimer, errors='ignore', inplace=True)
    for colonne in df_entreprises.select_dtypes(include='object').columns:
        df_entreprises[colonne] = df_entreprises[colonne].str.strip()
    df_entreprises.replace(['', 'nan', 'NaN', 'None'], pd.NA, inplace=True)
    if 'Emails' in df_entreprises.columns:
        df_entreprises['Emails'] = df_entreprises['Emails'].str.lower().str.strip()
    avant = len(df_entreprises)
    df_entreprises.drop_duplicates(inplace=True)
    apres = len(df_entreprises)
    print('Doublons supprimés :', avant - apres)
    df_entreprises.to_excel(sortie_entreprises, index=False)
    print('Après nettoyage :', len(df_entreprises), 'lignes')
    print('\nColonnes finales :')
    for colonne in df_entreprises.columns:
        print('-', colonne)
    print('\n✅ Fichier créé :')
    print(sortie_entreprises)
    print('\n======================================')
    print('NETTOYAGE DES OFFRES MARRAKECH')
    print('======================================')
    df_offres = pd.read_excel(fichier_offres)
    print('Avant nettoyage :', len(df_offres), 'lignes')
    df_offres.drop(columns=['Ville ID'], errors='ignore', inplace=True)
    for colonne in df_offres.select_dtypes(include='object').columns:
        df_offres[colonne] = df_offres[colonne].str.strip()
    df_offres.replace(['', 'nan', 'NaN', 'None'], pd.NA, inplace=True)
    df_offres['Date publication'] = pd.to_datetime(df_offres['Date publication'], errors='coerce', utc=True).dt.tz_localize(None)
    df_offres['Date expiration'] = pd.to_datetime(df_offres['Date expiration'], errors='coerce', utc=True).dt.tz_localize(None)
    avant = len(df_offres)
    df_offres.drop_duplicates(subset=['ID'], inplace=True)
    apres = len(df_offres)
    print('Doublons supprimés :', avant - apres)
    df_offres.sort_values(by='Date publication', ascending=False, inplace=True)
    df_offres.to_excel(sortie_offres, index=False)
    print('Après nettoyage :', len(df_offres), 'lignes')
    print('\nColonnes finales :')
    for colonne in df_offres.columns:
        print('-', colonne)
    print('\n✅ Fichier créé :')
    print(sortie_offres)
    print('\n')
    print('======================================')
    print('       NETTOYAGE TERMINÉ')
    print('======================================')

if __name__ == "__main__":
    main()
