# Diagnostic des environnements

Contrôle effectué le 9 novembre 2026. Les valeurs de clés et mots de passe n’ont pas été lues dans ce rapport.

## Résultat local

| Élément | Constat |
|---|---|
| Racine du projet | `outputs/Projet_Stages_Marrakech` |
| Entrée Flask | `backend.web:create_app`, lancée par les scripts Windows du projet |
| Chemin SQLite résolu | `database/stages_marrakech.db` |
| Profil effectif dans cette vérification | Privé, `PUBLIC_DEMO_MODE=false` |
| Données privées | 292 entreprises, 88 offres, 5 candidatures; SQLite v6, intégrité `ok` |
| Base de démonstration | `database/stages_marrakech_public_demo.db`, 5 entreprises, 4 offres, 3 candidatures synthétiques |
| Point de service Dash | Flask, préfixe `/analytics/`; même `app.config['DATABASE']` que les routes API |
| Clé de session | Stable et conservée dans `private/session.key` |
| CV en base | 0 entrée CV dans SQLite; aucun CV historique à migrer |
| SDK Gemini | `google-genai` installé dans l’environnement virtuel |
| Gemini | Clé absente et activation désactivée; aucun appel réel |

`backend.config.settings()` charge le `.env` local sans écraser les variables déjà définies par l’environnement. Le `.env.example` fourni sélectionne le profil privé. `render.yaml` sélectionne la base synthétique, active le mode public en lecture seule et n’active pas Gemini. L’archive publique ne contient pas la base privée ni le fichier `.env`.

Les sauvegardes antérieures dans `backups/` sont des versions v0 à v5 mais conservent les volumes 292/88/5; l’actuelle v6 est valide et ne nécessitait aucune restauration. L’homonyme racine `stages_marrakech.db` est un fichier vide non sélectionné par la configuration. Il a été conservé.

## Pourquoi l’écran peut montrer 5/4/3

Les chiffres 5 entreprises, 4 offres et 3 candidatures correspondent à la base **synthétique publique**, pas à une suppression de l’historique. L’instance Flask utilise le chemin configuré au démarrage; le Dashboard Dash lit cette même configuration. Une copie de démonstration ou un ancien processus lancé depuis un autre dossier peut donc afficher la démo. Cette session ne permet pas d’inspecter les processus Windows: la requête CIM a été refusée par le système. L’onglet Chrome observé portait le titre « Prompt Codex pour audit »; il ne démontrait pas l’accès au serveur local ni à un déploiement donné. L’URL d’un navigateur ou l’identité d’un ancien processus ne peuvent donc pas être attribuées avec preuve.

Pour ouvrir les données historiques, lancer `LANCER_SOUTENANCE_LOCALE.bat` depuis ce dossier local privé, puis vérifier le mode et le chemin dans ce rapport. Ne copiez pas la base historique dans `PROJET_PUBLIC` et ne changez pas le profil public.

## Session et chatbot

Flask utilise le secret persistant de `private/session.key`, un cookie HttpOnly/SameSite Strict et un jeton CSRF exigé sur chaque écriture. L’ancienne interface capturait le jeton au chargement et renvoyait un 403 « Session expirée » si le jeton de la page n’était plus celui du cookie. La cause compatible avec ce message est un jeton périmé ou un contexte de page ancien; l’inventaire de processus et la reproduction sur l’instance qui avait affiché le message n’ont pas été possibles.

La correction actualise le jeton via l’endpoint de session, seulement si la session est toujours authentifiée, puis répète une fois la requête protégée. Si l’authentification n’est plus valide, l’interface indique de recharger et se reconnecter. La vérification CSRF reste active; le jeton n’est jamais contourné.

## Limites de ce diagnostic

- Aucun navigateur n’a fourni l’URL de l’instance qui affichait la démo; aucun ancien processus n’a pu être attribué.
- Aucun déploiement public n’a été ouvert ou validé depuis une URL de production.
- Le compte Google, ses quotas, son niveau de facturation et les modèles disponibles pour ce compte ne sont pas accessibles depuis le projet.
- Aucun accès externe, appel Gemini, email ou collecte réelle n’a été effectué.

## Vérification du port, 9 novembre 2026

Le contrôle local en lecture seule a constaté que `127.0.0.1:5000` répond avec HTTP 200 sur `/health` (Werkzeug 3.1.8) et `/api/auth/session`. La session retourne `public_demo=true`, ce qui confirme que l'instance déjà lancée utilise le profil de démonstration synthétique. Un bind indépendant retourne Windows `WSAEADDRINUSE` (10048). `netstat -ano`, `Get-NetTCPConnection` et l'inventaire des processus n'ont pas fourni de PID attribuable; aucun processus n'a été interrompu et le serveur n'a pas été réutilisé.

Le nouveau lanceur local contrôle le port avant démarrage et s'arrête si le port est occupé. Pour la soutenance, fermez proprement l'instance de démonstration depuis sa fenêtre de lancement, puis exécutez `LANCER_SOUTENANCE_LOCALE.bat`. L'identité du PID reste inconnue faute d'information exposée par Windows dans cette session.

## Chemins absolus

`backend.config.settings()` résout maintenant `DATABASE`, `PRIVATE_DIR` et `BACKUP_DIR` contre la racine du projet lorsqu'ils sont relatifs. Le lanceur de soutenance définit explicitement les chemins locaux absolus et impose le profil privé. Les contrôles SQLite du lanceur utilisent `mode=ro`; ils vérifient l'intégrité et les comptes sans écrire dans la base.
