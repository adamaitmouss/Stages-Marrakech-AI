# Installer Stages Marrakech AI sous Windows

## Prérequis

- Windows 10 ou 11 et Python 3.12 installé pour votre compte Windows avec le Python Launcher (`py`). L'installation ne demande pas de droits administrateur.
- Une connexion Internet au moment du téléchargement des dépendances. L'application elle-même s'exécute localement.
- Un dossier privé avec suffisamment d'espace libre pour l'environnement Python et les bibliothèques.

## Installation en quelques étapes

1. Décompressez `Projet_Stages_Marrakech_phase5.zip` dans un dossier privé, par exemple `Documents\StagesMarrakech`.
2. Ouvrez ce dossier et double-cliquez `INSTALLER_WINDOWS.bat`.
3. Le script vérifie la présence de `requirements.txt`, `.env.example` et `backend\app.py`, crée `.venv` avec Python 3.12 puis crée `.env` depuis `.env.example` uniquement si aucun `.env` n'existe déjà.
4. À la question d'installation depuis Internet, saisissez `O` pour télécharger les dépendances ou `N` pour annuler. Les paquets sont installés dans `.venv`; Python global n'est pas modifié.
5. Double-cliquez `VERIFIER_INSTALLATION.bat`. Chaque fichier requis, bibliothèque, configuration et l'intégrité SQLite sont contrôlés. Le contenu de `.env` n'est jamais affiché.
6. Double-cliquez `LANCER_APPLICATION.bat` et ouvrez `http://127.0.0.1:5000`.

Au premier accès, créez votre propre mot de passe de 12 caractères minimum. Il n'y a pas de compte ni mot de passe prédéfini. Gardez ce mot de passe et le dossier `private` confidentiels.

Pour arrêter le serveur, cliquez dans sa fenêtre puis appuyez sur Ctrl+C. Le serveur écoute seulement sur `127.0.0.1`.

## Utilisation depuis PowerShell

Dans PowerShell ouvert dans le dossier extrait :

```powershell
.\INSTALLER_WINDOWS.bat
.\VERIFIER_INSTALLATION.bat
.\LANCER_APPLICATION.bat
```

Le port par défaut est 5000. Les pages et Analyses Dash sont servies par le même serveur Flask.

## Configuration et confidentialité

Les fonctions Gemini, SMTP et Google Maps sont désactivées par défaut. Aucune clé n'est nécessaire pour tester le mode local. N'activez pas ces services pendant une démonstration sans avoir d'abord vérifié les tarifs, quotas, destinataires et consentements concernés. Aucun appel externe réel n'est effectué par l'installateur ou le vérificateur.

Ne partagez pas l'archive publiquement : elle contient les données historiques du projet. Conservez ensemble la base `database\stages_marrakech.db` et le dossier privé `private`; celui-ci protège l'authentification et les profils CV chiffrés. Faites une copie privée du dossier avant vos essais avec un CV ou une nouvelle candidature.

Le fichier `.env` est ignoré par l'archive et par Git. L'installateur ne remplace jamais un `.env` déjà présent. Ne collez pas vos clés dans un rapport ou une capture d'écran.

## Dépannage

### « Python 3.12 est requis » ou `py` introuvable

Installez Python 3.12 pour votre compte Windows en incluant le Python Launcher. Fermez puis rouvrez PowerShell et relancez `INSTALLER_WINDOWS.bat`. Aucune installation globale de paquets n'est faite par le projet.

### Une dépendance manque

Vérifiez la connexion Internet, puis relancez `INSTALLER_WINDOWS.bat` et confirmez le téléchargement. Pour vérifier manuellement, depuis la racine du projet :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\VERIFIER_INSTALLATION.bat
```

### `.env` est absent

Relancez `INSTALLER_WINDOWS.bat`; il copiera `.env.example` seulement si `.env` est toujours absent. Si vous le créez manuellement, copiez `.env.example` vers `.env` sans écraser une configuration existante.

### Le port 5000 est déjà utilisé

Fermez une ancienne fenêtre de l'application et réessayez. Le programme ne change pas automatiquement de port.

### Le navigateur ne s'ouvre pas automatiquement

Saisissez vous-même `http://127.0.0.1:5000` dans le navigateur après le message de démarrage. Laissez la fenêtre du serveur ouverte.

### Vous avez extrait une ancienne version du Bureau

Vérifiez que le dossier extrait contient `INSTALLER_WINDOWS.bat`, `VERIFIER_INSTALLATION.bat`, `LANCER_APPLICATION.bat`, `requirements.txt`, `.env.example` et `backend\app.py`. Utilisez l'archive Phase 5 complète si ces fichiers manquent; ne mélangez pas des fichiers de plusieurs versions.

## Installer les outils de tests

L'installation standard fournit les bibliothèques nécessaires à l'application. Pour lancer Pytest depuis une copie de développement, installez aussi les outils de test :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Cette commande télécharge Pytest et Playwright depuis Internet. La suite applicative n'envoie pas de CV, ne contacte aucun service Gemini/SMTP/Maps et utilise des bases de test temporaires.
