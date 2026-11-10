# Profil local principal — version historique

## Dossier et bases

- Copie locale principale : `LIVRAISON_DEFINITIVE_SOUTENANCE/PROJET_FINAL/`.
- Base des entreprises, offres et candidatures : `database/stages_marrakech.db`.
- Base distincte des comptes Login : `auth_gateway/data/auth_users.db`.
- Démonstration synthétique conservée à part : `database/stages_marrakech_public_demo.db`.

Contrôle SQLite en lecture seule : 292 entreprises, 88 offres, 5 candidatures; intégrité `ok`, 0 erreur FK. Le champ `Emails` n'est pas vide pour 145 entreprises. Cela ne vérifie ni la validité des adresses ni le droit de les utiliser.

## Lanceurs

| Fichier | Profil et effet |
|---|---|
| `LANCER_MON_PROJET.bat` | Lanceur quotidien : Login local, `AUTH_PROFILE=private`, chemin absolu de la base historique, inscription désactivée, contrôle des ports 5000 et 5101. |
| `LANCER_APPLICATION_AVEC_LOGIN.bat` | Alias vers `LANCER_MON_PROJET.bat`; ne choisit plus la Demo. |
| `LANCER_SOUTENANCE_LOCALE.bat` | Démarre Flask directement sur la base historique, sans passerelle Login. |
| `LANCER_APPLICATION.bat` | Vérifie l'installation puis démarre Flask; `backend/config.py` pointe par défaut vers la base historique. |
| `LANCER_WINDOWS.bat` | Alias historique vers `LANCER_APPLICATION.bat`. |
| `scripts/serve_public_demo.py` | Sert la copie publique synthétique séparément; ce n'est pas le lanceur local principal. |

`auth_gateway/.env.auth` est une configuration locale privée. Elle cible la base historique et l'unique compte actif déjà présent dans la base des comptes. Au lancement, le canal interne passerelle/backend génère et réutilise `private/auth_gateway_internal.secret`, sans saisie de mot de passe technique. Le backend accepte cette session seulement sur une connexion de boucle locale avec un secret d'au moins 48 caractères. Le secret n'est jamais renvoyé au navigateur et son fichier est ignoré par Git. Ne partagez pas `.env.auth`, `private/` ou `auth_gateway/data/`.

## Pourquoi les modules restent sur la même base

Le lanceur Login passe le chemin de `AUTH_APP_DATABASE` au backend comme variable `DATABASE` dans `auth_gateway/launcher.py`. `backend/config.py` le charge dans la configuration Flask. Les routes d'entreprises et offres, le Matching et la Recherche IA locale utilisent ensuite cette configuration. Dash reçoit la même application Flask et lit `server.config['DATABASE']`. La Demo n'est copiée dans un dossier temporaire que pour le profil `demo`; le profil `private` utilise le fichier historique directement et refuse une base marquée synthétique.

Repères vérifiés dans le code :

- `LANCER_MON_PROJET.bat` — profil et chemin de base explicités.
- `auth_gateway/config.py:47-107` — validation du profil et choix de `AUTH_APP_DATABASE`.
- `auth_gateway/launcher.py:33-63, 83-108, 132-139` — vérification SQLite, profil Demo/privé, transmission du chemin au backend et affichage des compteurs.
- `backend/config.py:7-16` — variable `DATABASE` et valeur par défaut historique.
- `backend/web.py:15-41, 115-119` — application Flask et intégration des routes/Dash.
- `backend/analytics.py:114-121` — Dash monte sur Flask et récupère le chemin SQLite de l'application.
- `backend/api.py:94-110, 370-401, 593-605, 824-856` — lecture entreprises/offres, Matching, Recherche IA locale et Chatbot.

## Authentification et limites

Login et Logout restent disponibles. Le profil privé n'accepte qu'un compte administrateur existant; Register est conservé à l'écran mais la création de comptes est désactivée. Les CV et candidatures ne sont pas cloisonnés entre utilisateurs, donc l'inscription ouverte n'est pas sûre.

Si le port 5000 ou 5101 est occupé, le lanceur refuse le démarrage et ne termine aucun processus. Fermez uniquement une fenêtre de serveur dont vous connaissez l'origine, puis relancez `LANCER_MON_PROJET.bat`.

## Paquet public

Les droits de redistribution historique ne sont documentés pour aucune des 292 entreprises ni aucune des 88 offres : le nombre actuellement démontré comme publiable est donc **0 entreprise et 0 offre historiques**. Le dossier `GITHUB_RENDER_PUBLIC/PROJET_PUBLIC/` est extrait de l'archive publique déjà vérifiée; sa base est indépendante et synthétique (5 entreprises, 4 offres, 3 candidatures synthétiques). Elle ne doit pas être présentée comme un extrait réel ni comme une version actuelle du marché.
