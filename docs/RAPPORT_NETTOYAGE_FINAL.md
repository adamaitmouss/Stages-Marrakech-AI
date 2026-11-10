# Rapport de nettoyage final

**Date : 9 novembre 2026**  
**Copie préparée :** `outputs/LIVRAISON_DEFINITIVE_SOUTENANCE/PROJET_FINAL`  
**Sauvegarde d'origine :** `outputs/LIVRAISON_DEFINITIVE_SOUTENANCE/SAUVEGARDE_ORIGINALE_PRIVEE/Projet_Stages_Marrakech`

## Sauvegarde et périmètre

Une copie initiale du projet a été faite avant tout nettoyage. Elle garde le code, les données historiques, `.env`, le dossier `private/`, les bases, les journaux et les sauvegardes préexistantes. Un manifeste SHA-256 local permet de contrôler chaque fichier copié. Une seconde copie sert de préparation de livraison. Les originaux n'ont été ni déplacés ni supprimés.

Les environnements Python `.venv`, caches pytest/Python et fichiers `.pyc/.pyo` ne sont pas copiés dans les deux copies de travail car ils sont régénérables par `INSTALLER_WINDOWS.bat`. Le dossier de sauvegarde demeure indépendant. Les tests sont ensuite exécutés contre `PROJET_FINAL` avec l'environnement de l'original.

## Éléments conservés

- Backend Flask, routes, sécurité, services, migrations et WSGI.
- Frontend HTML, CSS, JavaScript, Leaflet et ressources locales.
- Dashboard Dash/Plotly, modules Matching, Chatbot, CV PDF et alertes.
- Connecteurs, import CSV/XLSX, registre des sources, fichiers de permissions et scripts opérationnels.
- Tests maintenus et scripts de lancement Windows.
- Base historique, base publique synthétique, configurations et données privées dans la copie locale.
- Guides et rapports de phases précédentes. Ils restent présents pour l'audit, la provenance et les liens historiques; aucun n'a été supprimé sur la base de son seul nom.
- Sauvegardes historiques existantes, non modifiées.

## Fichiers exclus ou retirés de la copie de préparation

| Élément | Opération dans `PROJET_FINAL` | Justification | Sauvegarde intacte |
|---|---|---|---|
| `.venv/`, `.pytest_cache/`, `__pycache__/`, `.pyc`, `.pyo` | Non copiés | Environnement/cache régénérables; les dépendances sont décrites dans les requirements | Les originaux restent intacts; la sauvegarde privée contient code, données et fichiers de projet, sans l'environnement `.venv` |
| `stages_marrakech.db` à la racine du projet | Retiré de la copie | Fichier vide de 0 octet; aucun code ou lanceur ne pointe vers lui. Le fichier actif est `database/stages_marrakech.db` | Présent dans la sauvegarde privée initiale |
| `auth_gateway/data/auth_visual_test.db` | Retiré de la copie | Base de test visuel générée, vide de comptes et distincte de la base de comptes locale | Présente dans la sauvegarde privée initiale |

## Fichiers ambigus

Les journaux, captures, anciens rapports, anciens guides, scripts de collecte, fichiers historiques et répertoire de sauvegardes ont été conservés. Les scripts liés à Google Places sont conservés mais aucun appel n'a été fait. Les dossiers potentiellement personnels restent dans la copie locale et la sauvegarde privée; ils ne rejoignent pas l'archive publique.

## Doublons, liens et structure

Aucune réorganisation des modules de code n'a été faite. Les chemins Python, imports, scripts de lancement et liens internes historiques restent valides. Les nouveaux documents de référence sont regroupés sous `docs/`. Le fichier racine vide a été traité après vérification de la configuration et des références. Aucun dossier vide ambigu n'a été supprimé.

## Publication

La copie locale ne doit pas être publiée. L'archive publique synthétique est livrée séparément sous `PROJET_PUBLIC_AUTH.zip`; son propre manifeste est distinct. Elle exclut les secrets, bases privées, fichiers utilisateur et états de connexion.

## Éléments temporaires encore présents

Les dossiers `.build_private` et certaines sorties `.pytest_cache` provenant des préparations antérieures restent dans la copie locale. Une suppression récursive a été refusée par le contrôle de sécurité Windows; aucune tentative n'a été faite sur l'original. Ils ne sont pas inclus dans `MANIFEST_FINAL_SHA256.json` ni dans l'archive publique et ne doivent pas être partagés. Le projet reste utilisable; ces fichiers ne sont pas nécessaires au lancement.
