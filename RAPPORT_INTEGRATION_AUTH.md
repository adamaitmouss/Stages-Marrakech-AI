# Rapport d’intégration — passerelle d’authentification

Date : 9 novembre 2026

## Résumé

Ajout d’une passerelle indépendante dans `auth_gateway/` et de `LANCER_APPLICATION_AVEC_LOGIN.bat`. Aucun fichier métier préexistant n’a été modifié. Le compte utilisateur est stocké séparément de SQLite historique. Les changements s’ajoutent à côté du projet et peuvent être retirés en supprimant les nouveaux fichiers et l’état local `auth_gateway/data/`.

## Architecture retenue

La passerelle Flask protège les requêtes avant leur transfert vers l’application Flask existante. Elle accepte les requêtes à `127.0.0.1:5000`; le backend est lié à `127.0.0.1:5101`. Les deux ports sont contrôlés par bind; si l’un est occupé, le lanceur s’arrête sans identifier ni arrêter le processus existant. Les routes API, pages, Dash, téléchargements et autres chemins du backend passent par cette barrière. `/health`, Login et Inscription sont les seules routes publiques de la passerelle.

Le navigateur reçoit un cookie opaque, HttpOnly, SameSite=Strict et Secure en production. La session du Flask historique reste dans le serveur passerelle; son cookie et son jeton CSRF ne sont pas renvoyés au navigateur. Chaque écriture API exige le jeton CSRF de la passerelle, que celle-ci remplace par le jeton de la session interne. Les connexions utilisateur se connectent au backend global existant, sans changer ses routes.

## Profils et autorisations

- **Démo** : inscription permise uniquement si le backend confirme le mode public synthétique. Le backend utilise une copie de la base synthétique dans un dossier temporaire supprimé à l’arrêt. Les comptes partagent les mêmes données fictives.
- **Privé local** : une adresse administrateur explicitement configurée, aucune inscription, et une base utilisateurs contenant uniquement cet administrateur. Le backend utilise la session globale existante via un secret local fourni par l’utilisateur.
- Les rôles ne constituent pas une autorisation métier. L’isolation des CV, candidatures et données d’étudiant par utilisateur n’existe pas. Le profil privé reste administrateur unique; les comptes démo ne voient qu’un jeu synthétique partagé.

## Stockage

Par défaut les comptes sont dans `auth_gateway/data/auth_users.db`; aucune table n’est ajoutée à SQLite historique. Email normalisé unique, identifiant UUID, nom/prénom, hash scrypt, date, état et rôle de démonstration sont enregistrés. Les sessions et compteurs de tentatives sont indépendants. PostgreSQL est pris en charge par `psycopg` dans la configuration de production, qui refuse SQLite éphémère.

## Fichiers nouveaux

- `auth_gateway/` : configuration, base de comptes, hash scrypt, passerelle/proxy, lanceur contrôlé, templates, CSS, JS, WSGI et tests.
- `.env.auth.example`, `LANCER_APPLICATION_AVEC_LOGIN.bat`.
- `GUIDE_AUTHENTIFICATION.md`, `RAPPORT_INTEGRATION_AUTH.md`, `RAPPORT_TESTS_AUTH.md`.
- `auth_gateway/ORIGINAL_SHA256_BEFORE.json` : empreintes avant changements des fichiers préexistants non secrets.

Les fichiers créés au premier lancement (`auth_gateway/.env.auth`, `auth_gateway/data/`) sont exclus par le `.gitignore` ajouté à ce module.

## Préservation et non-régression

Au départ, les fichiers de code, documentation et données non secrets listés dans l’empreinte comprenaient 217 fichiers. Le hash SHA-256 de `database/stages_marrakech.db` était `11036604a8584b45331dca9419c74233dde35c8e5d4f83a85b1f64c9bb3f3e51`; intégrité `ok`, 292 entreprises, 88 offres, 5 candidatures et 0 erreur FK. La base synthétique a aussi été copiée dans un fichier temporaire pendant le test de proxy Flask réel.

Les vérifications finales d’empreintes sont inscrites dans `RAPPORT_TESTS_AUTH.md`. `LANCER_SOUTENANCE_LOCALE.bat`, les pages, CSS, JavaScript et modules métier restent inchangés. Les **133 tests préexistants** passent, en plus des **31 tests dédiés** du module (164 au total). Le script `.bat` d’authentification a aussi été lancé et arrêté pendant le contrôle local.

## Publication et limites

Aucun dépôt, site ou service externe n’a été publié. Il manque une cible d’hébergement avec réseau privé pour Flask, PostgreSQL persistant, HTTPS et secrets de production. Sans ces conditions, ne pas activer l’inscription publique. Aucun accès Internet au backend ne doit être possible.
