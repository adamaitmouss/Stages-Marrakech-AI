# Rapport Phase 4 — Stages Marrakech AI

**Date : 5 novembre 2026**  
**Base :** archive et code Phase 3 existants, complétés sans recréer le projet.

## Résumé

La version Phase 4 ajoute un parcours d’installation Windows guidé, un vérificateur en lecture seule, des tests dédiés à ces outils, un guide d’installation et les captures du test navigateur. Le serveur reste local à `127.0.0.1:5000`; Gemini, SMTP et Maps restent désactivés par défaut.

## Dossier Phase 3 et erreur de chemin

Le projet réellement traité dans cet espace de travail est `outputs\Projet_Stages_Marrakech`. Il contient `requirements.txt`, `.env.example`, `backend\app.py`, sa base SQLite et le manifeste de fichiers Phase 3.

L’archive `Projet_Stages_Marrakech_phase3.zip` était disponible et a été vérifiée : 98 entrées, intégrité ZIP correcte, 97 empreintes du manifeste concordantes, avec les fichiers requis à la racine `Projet_Stages_Marrakech\`.

Le dossier du Bureau `C:\Users\HP\Desktop\Projet_Stages_Marrakech` existe, mais il ne contient ni `requirements.txt`, ni `.env.example`, ni le manifeste Phase 3. C’est une copie ancienne ou incomplète; elle n’a pas été modifiée. Les messages « requirements.txt introuvable », « .env.example introuvable » et l’absence de Flask s’expliquent par le lancement dans cette copie ou sans installation de ses dépendances.

## Corrections et améliorations

- `INSTALLER_WINDOWS.bat` vérifie les fichiers, reconnaît Python 3.12 par `py -3.12` ou par la commande `python`, crée `.venv`, crée `.env` uniquement s’il n’existe pas, puis demande l’accord avant tout téléchargement. Les paquets vont dans l’environnement du projet; aucun droit administrateur n’est utilisé.
- `LANCER_APPLICATION.bat` contrôle l’installation, puis lance `backend\app.py`. `VERIFIER_INSTALLATION.bat` contrôle les fichiers, les modules et SQLite en lecture seule, sans afficher le contenu de `.env`.
- `LANCER_WINDOWS.bat` reste disponible comme ancien point d’entrée et transmet au nouveau lanceur.
- `scripts\verify_installation.py` vérifie Python du `.venv`, Flask, Werkzeug, Dash, Plotly, Pandas, ReportLab, OpenPyXL, Requests, Beautiful Soup, Matplotlib, pypdf, Cryptography, python-dotenv et Google GenAI SDK. Il contrôle aussi la présence des fichiers de configuration et l’intégrité/comptage SQLite.
- `tests\test_installation.py` ajoute des contrôles sur la lecture seule SQLite, les fichiers manquants et les protections des scripts d’installation.
- Dans `tests\browser_smoke.py`, une attente incorrecte comparait le titre d’une offre à son identifiant numérique. Elle vérifie maintenant la présence de la section réelle des conseils CV.
- `README.md` et `GUIDE_TEST_MANUEL.md` décrivent le lancement et les limites constatées. `GUIDE_INSTALLATION_WINDOWS.md` détaille l’installation, les erreurs courantes et les commandes de test.
- Le parcours navigateur a produit 12 captures, conservées dans `reports\screenshots_phase4\` avec le résultat JSON. Le parcours a contrôlé navigation, Dash, matching local, CV, candidature, carte et mobile.

## Dépendances et installation

L’environnement virtuel du projet a été créé avec **Python 3.12.2** et les versions épinglées de `requirements.txt` et `requirements-dev.txt`. Flask, Dash, Plotly, ReportLab et les autres bibliothèques sont installés dans `.venv`. `pip check` ne signale aucune dépendance cassée. Aucun paquet n’a été installé dans Python global.

Le chemin `INSTALLER_WINDOWS.bat` a été exercé sur cette machine avec le choix `N` : la détection de Python de secours a fonctionné, le fichier `.env` existant a été conservé et l’installation réseau a bien été annulée. Le chemin de vérification `.bat` s’est exécuté avec succès. L’installation des dépendances a été testée séparément dans `.venv` à partir des fichiers `requirements`.

## Tests et résultats

- Suite Phase 3 avant changement : **63 réussis**.
- Suite Phase 4 : **67 réussis, 0 échec**, en 20,47 secondes. Un avertissement de dépréciation provient du plugin de test Dash sous Pytest 9; il n’affecte pas les résultats.
- `pip check` : aucune dépendance manquante ou incompatible.
- Vérificateur d’installation : tous les fichiers, modules et la base sont déclarés `OK`.
- Tests Flask/Dash et génération PDF : passent dans la suite sur des données temporaires; le serveur du test navigateur est lié à `127.0.0.1`.
- Parcours Chrome : **17 contrôles terminés**, aucune erreur JavaScript et aucune requête externe. Cela comprend les pages principales, Dash et changement d’onglet, suggestions CV, matching local, préparation d’une candidature, suivi, carte et menu mobile à 390 px.
- L’aperçu PDF a répondu HTTP 200. Le lecteur PDF interne Chromium n’a pas fourni de rendu headless visuellement concluant. Le téléchargement natif Chrome a été bloqué par Windows (« Insufficient permissions »); le flux HTTP a été vérifié séparément et le PDF produit commence par `%PDF-`.

Les vérifications visuelles avec navigateur normal à 768 px et 1366 px, en thème sombre, et l’affichage réel de l’aperçu PDF restent à faire avec le guide manuel. Aucune de ces vérifications n’est présentée comme réussie.

## Préservation des données

Une copie du projet et une sauvegarde SQLite ont été créées avant les changements. Toutes les tables comparées à la sauvegarde sont identiques; l’intégrité SQLite est `ok` avant et après. Les comptes restent **292 entreprises, 88 offres et 5 candidatures**. Le PDF historique généré pour CV est byte-identique à la copie préalable. Le test navigateur utilise une base temporaire anonymisée et les tests applicatifs des bases jetables.

La base active reste `database\stages_marrakech.db`; le fichier vide historique à la racine n’est pas utilisé par l’application. Le vérificateur ouvre SQLite en lecture seule. `.env`, `.venv` et le dossier `private` sont exclus de l’archive finale.

## Services externes et sécurité

Aucun appel réel Gemini, SMTP, Google Maps/Places ou collecteur n’a été effectué. Le navigateur a bloqué toute requête hors du serveur local. Les tests d’envoi utilisent des mocks. La carte conserve zéro coordonnée géographique vérifiée; aucun emplacement n’a été inventé ni ajouté.

Les paramètres par défaut de `.env.example` désactivent les services externes. Le propriétaire du projet doit révoquer dans Google Cloud toute ancienne clé Google précédemment exposée et créer une nouvelle clé restreinte si un service Maps ou Places est un jour activé. N’intégrez pas cette ancienne clé à `.env`, au code ou à l’archive.

## Fichiers ajoutés ou actualisés

- Ajoutés : `INSTALLER_WINDOWS.bat`, `LANCER_APPLICATION.bat`, `VERIFIER_INSTALLATION.bat`, `GUIDE_INSTALLATION_WINDOWS.md`, `RAPPORT_PHASE4.md`, `scripts\verify_installation.py`, `tests\test_installation.py`, `reports\tests_phase4.xml`, `reports\preservation_phase4.json`, `reports\screenshots_phase4\`.
- Actualisés : `README.md`, `GUIDE_TEST_MANUEL.md`, `LANCER_WINDOWS.bat`, `tests\browser_smoke.py`, `MANIFEST_SHA256.json`.
- Architecture existante, données, base, règles de matching, flux CV et intégrations conservés.

## Lancement exact

Après extraction de l’archive Phase 4 dans un dossier privé :

1. Double-cliquez `INSTALLER_WINDOWS.bat` et répondez `O` à la confirmation de téléchargement.
2. Double-cliquez `VERIFIER_INSTALLATION.bat`.
3. Double-cliquez `LANCER_APPLICATION.bat`.
4. Ouvrez `http://127.0.0.1:5000`; à la première visite, créez votre mot de passe personnel.

Depuis PowerShell à la racine du projet :

```powershell
.\INSTALLER_WINDOWS.bat
.\VERIFIER_INSTALLATION.bat
.\LANCER_APPLICATION.bat
```

Pour les tests :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tests\browser_smoke.py
```

## Limites restantes

- L’installation des paquets nécessite une connexion Internet et une confirmation explicite.
- Le test natif de téléchargement Chrome est limité par les permissions Windows de ce navigateur automatisé.
- L’aperçu PDF et l’aspect du thème sombre restent à examiner dans un navigateur ouvert normalement.
- Les services externes restent désactivés et non testés en conditions réelles; l’activation requiert la configuration et le consentement du propriétaire.
- Le matching reste un indicateur explicable à examiner par un humain; il n’est pas validé sur un jeu de résultats annotés.
- Les CV sont prévus pour le français/latin; OCR et mise en page arabe RTL ne sont pas intégrés.
