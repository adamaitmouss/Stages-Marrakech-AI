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

    def audit_dataframe(df, nom):
        print('\n')
        print('=' * 70)
        print(f'AUDIT : {nom}')
        print('=' * 70)
        print('\n1. DIMENSIONS')
        print('-' * 40)
        print('Nombre de lignes   :', df.shape[0])
        print('Nombre de colonnes :', df.shape[1])
        print('\n2. COLONNES')
        print('-' * 40)
        for colonne in df.columns:
            print('-', colonne)
        print('\n3. TYPES DE DONNÉES')
        print('-' * 40)
        print(df.dtypes)
        print('\n4. VALEURS MANQUANTES')
        print('-' * 40)
        missing = df.isnull().sum()
        for colonne, nombre in missing.items():
            pourcentage = nombre / len(df) * 100
            print(f'{colonne} : {nombre} ({pourcentage:.2f} %)')
        print('\n5. DOUBLONS')
        print('-' * 40)
        doublons = df.duplicated().sum()
        print('Nombre de doublons complets :', doublons)
        print('\n6. NOMBRE DE VALEURS UNIQUES')
        print('-' * 40)
        for colonne in df.columns:
            nombre_unique = df[colonne].nunique(dropna=True)
            print(f'{colonne} : {nombre_unique} valeurs uniques')
        print('\n7. COLONNES AVEC UNE SEULE VALEUR')
        print('-' * 40)
        constantes = []
        for colonne in df.columns:
            if df[colonne].nunique(dropna=True) <= 1:
                constantes.append(colonne)
        if constantes:
            for colonne in constantes:
                print('⚠️', colonne)
        else:
            print('Aucune colonne constante.')
        print("\n8. VALEURS VIDES ('')")
        print('-' * 40)
        for colonne in df.columns:
            if df[colonne].dtype == 'object':
                vides = df[colonne].astype(str).str.strip().eq('').sum()
                if vides > 0:
                    print(f'{colonne} : {vides} valeurs vides')
        print('\n9. ESPACES AU DÉBUT / À LA FIN')
        print('-' * 40)
        espaces = {}
        for colonne in df.columns:
            if df[colonne].dtype == 'object':
                valeurs = df[colonne].dropna().astype(str)
                nombre = (valeurs.str.startswith(' ') | valeurs.str.endswith(' ')).sum()
                if nombre > 0:
                    espaces[colonne] = nombre
                    print(f'⚠️ {colonne} : {nombre} valeurs')
        if not espaces:
            print('Aucun espace suspect détecté.')
        if 'Emails' in df.columns:
            print('\n10. EMAILS')
            print('-' * 40)
            emails = df['Emails'].dropna().astype(str)
            email_invalides = []
            for email in emails:
                liste = email.split(',')
                for e in liste:
                    e = e.strip()
                    if '@' not in e or '.' not in e.split('@')[-1]:
                        email_invalides.append(e)
            print('Emails suspects :', len(email_invalides))
            if email_invalides:
                for email in email_invalides[:20]:
                    print('⚠️', email)
        print('\n11. URLS')
        print('-' * 40)
        colonnes_url = ['Site Web', 'Google Maps', 'Lien annonce', 'Lien public']
        for colonne in colonnes_url:
            if colonne in df.columns:
                valeurs = df[colonne].dropna().astype(str)
                invalides = valeurs[~valeurs.str.startswith(('http://', 'https://'))]
                print(f'{colonne} : {len(invalides)} URL(s) suspecte(s)')
        print('\n12. RÉSUMÉ')
        print('-' * 40)
        total_missing = df.isnull().sum().sum()
        print('Lignes :', len(df))
        print('Colonnes :', len(df.columns))
        print('Valeurs manquantes :', total_missing)
        print('Doublons complets :', doublons)
        return {'Dataset': nom, 'Lignes': len(df), 'Colonnes': len(df.columns), 'Valeurs_manquantes': total_missing, 'Doublons': doublons}
    print('\n')
    print('############################################')
    print('#       AUDIT DES DONNÉES - PROJET        #')
    print('############################################')
    if not os.path.exists(fichier_entreprises):
        print('\n❌ Fichier introuvable :')
        print(fichier_entreprises)
        exit()
    if not os.path.exists(fichier_offres):
        print('\n❌ Fichier introuvable :')
        print(fichier_offres)
        exit()
    entreprises = pd.read_excel(fichier_entreprises)
    offres = pd.read_excel(fichier_offres)
    resultat_entreprises = audit_dataframe(entreprises, 'ENTREPRISES')
    resultat_offres = audit_dataframe(offres, 'OFFRES MARRAKECH')
    resume = pd.DataFrame([resultat_entreprises, resultat_offres])
    print('\n')
    print('=' * 70)
    print('RÉSUMÉ FINAL')
    print('=' * 70)
    print(resume.to_string(index=False))
    os.makedirs('reports', exist_ok=True)
    resume.to_excel('reports/rapport_audit.xlsx', index=False)
    print('\n')
    print('✅ Audit terminé.')
    print('Rapport créé :')
    print('reports/rapport_audit.xlsx')

if __name__ == "__main__":
    main()
