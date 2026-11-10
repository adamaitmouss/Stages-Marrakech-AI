# Guide d’authentification — Stages Marrakech AI

## Fonctionnement

La passerelle indépendante écoute sur `127.0.0.1:5000`; le Flask existant écoute sur `127.0.0.1:5101`. Le backend n’écoute que sur l’interface locale. Le navigateur ne reçoit jamais son cookie de session : la passerelle conserve cette session en mémoire et transmet les requêtes autorisées après connexion.

Trois profils sont prévus :

- **Démo synthétique** : lecture seule, sans inscription de compte. La base reste un jeu d’exemples fictifs et les espaces personnels ne sont pas persistés.
- **Privé local** : la base historique est réservée à un seul administrateur de confiance. L’inscription est refusée et la passerelle vérifie que sa base de comptes ne contient aucun autre utilisateur. Les modules existants ne prennent pas en charge l’isolation CV/candidatures par compte; plusieurs étudiants ne doivent jamais partager ce profil.
- **Multi-utilisateur local** : inscription ouverte uniquement sur le poste local. Chaque compte étudiant possède son propre fichier SQLite durable, sous `private/user_data/`, créé à partir des entreprises et offres historiques. Les candidatures, CV, alertes, historiques Chatbot/Recherche IA, collectes et paramètres historiques sont retirés de la copie. Le compte historique administrateur conserve l’accès à la base privée originale. Les sauvegardes utilisateur restent dans le sous-dossier privé de chaque compte.

Le mode démo n’active ni Gemini, ni Maps, ni SMTP, ni collecte externe. En multi-utilisateur local, les services externes et l’ordonnanceur restent désactivés par le lanceur; le Centre de collecte reste disponible manuellement dans l’espace de l’utilisateur. Le profil Render reste sans inscription persistante tant qu’une base durable et les protections de production ne sont pas activées. L’ancien lanceur `LANCER_SOUTENANCE_LOCALE.bat` reste indépendant.

## Lancement local historique avec inscriptions isolées

1. Installez le projet avec `INSTALLER_WINDOWS.bat` si nécessaire.
2. Double-cliquez `LANCER_MON_PROJET.bat`. Le profil `multi_user` est sélectionné dans `auth_gateway/.env.auth`; le lanceur crée automatiquement le secret interne local et utilise la base historique comme modèle de départ.
3. Vérifiez les deux ports : `5000` pour Login et `5101` pour le backend privé. Si l’un est occupé, le lanceur s’arrête; il ne termine aucun processus et ne réutilise pas un ancien serveur.
4. Ouvrez `http://127.0.0.1:5000`, choisissez « Créer un compte », puis connectez-vous. Le nouvel espace est créé au premier accès à l’application.
5. « Mon compte » est disponible sur `http://127.0.0.1:5000/account`.
6. Arrêtez avec Ctrl+C dans la même fenêtre. Seuls les deux serveurs démarrés par cette fenêtre sont arrêtés.

Les comptes sont enregistrés dans `auth_gateway/data/auth_users_private.db`, séparée des données métier. Les bases personnelles par compte sont rangées sous `private/user_data/`; ce répertoire est ignoré par Git.

## Profil privé local — administrateur unique

Le profil privé ne se configure que sur ce poste et ne doit pas être publié. Fermez le serveur, éditez `auth_gateway/.env.auth` :

```ini
AUTH_PROFILE=private
AUTH_APP_DATABASE=database/stages_marrakech.db
AUTH_ALLOW_REGISTRATION=false
AUTH_DATABASE_URL=sqlite:///auth_gateway/data/auth_private_admin.db
AUTH_ADMIN_EMAIL=adresse-admin@example.org
AUTH_BOOTSTRAP_ADMIN_PASSWORD=mot-de-passe-initial-de-la-passerelle
```

Remplacez les exemples par des valeurs locales, uniques et robustes. Le mot de passe bootstrap est utilisé uniquement à la première création du compte administrateur; retirez cette variable du fichier après le premier démarrage réussi. Au lancement local normal, `LANCER_MON_PROJET.bat` génère automatiquement un secret aléatoire pour le canal de boucle locale et le conserve dans `private/auth_gateway_internal.secret` (répertoire ignoré par Git). Aucune saisie de mot de passe technique n'est nécessaire.

Le profil privé refuse le démarrage si l’inscription est ouverte, si la base est marquée synthétique, si l’adresse administrateur manque ou si le backend ne confirme pas sa session interne. Cette session interne est autorisée uniquement depuis `127.0.0.1`/`::1` avec le secret aléatoire local; elle ne remplace pas le mot de passe du compte Login. Le backend écoute uniquement sur l’interface de boucle locale. Le compte passerelle n’ajoute aucun rôle fin et n’isole pas des tables CV/candidatures : un seul administrateur doit être autorisé.

## Dépendances et stockage persistant

Le script utilise l’environnement `.venv` du projet et vérifie Flask, Werkzeug, ItsDangerous et Requests. Si un module manque, il affiche une commande d’installation; il ne télécharge rien sans action de l’utilisateur. Dépendances indépendantes : `auth_gateway/requirements.txt`.

En local, la base de comptes SQLite est persistante sur le disque du projet, mais doit rester privée. Pour un hébergement, utilisez PostgreSQL persistant avec TLS (`sslmode=require`, ou validation de certificat) via `auth_gateway/requirements-production.txt`, et configurez `AUTH_DATABASE_URL` avec le gestionnaire de secrets de l’hébergeur. Ne mettez ni URL avec mot de passe, ni secret de session dans Git.

## Limites avant toute publication

La passerelle n’est pas publiée ni configurée pour Render/GitHub. Le backend doit être un service réseau **privé**, inaccessible par une URL publique; le proxy n’offre aucune garantie si l’hébergeur laisse le backend public. Il faut également HTTPS, `AUTH_ENV=production`, `AUTH_COOKIE_SECURE=true`, une clé de session gérée par l’hébergeur, PostgreSQL persistant, `AUTH_TRUSTED_PROXY_HOPS` exact, `AUTH_ALLOWED_HOSTS` exacts, politique de sauvegarde, vérification de domaine/email si requise, et revue de sécurité de l’hébergeur. La configuration bloque les clés faibles, SQLite de production et les backends distants non explicitement approuvés.

Aucun mécanisme de mot de passe oublié ni de confirmation email n’est implémenté. Aucun message ne prétend qu’un email a été envoyé.
