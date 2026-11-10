# Base SQLite

## Fichiers et versions contrôlés

- Base locale privée : `database/stages_marrakech.db`, 643 072 octets, `PRAGMA user_version=6`, 19 tables, vérifiée en lecture seule le 9 novembre 2026.
- Base de démonstration publique : `database/stages_marrakech_public_demo.db`, 180 224 octets, version 6, avec marqueur de jeu synthétique.
- Les deux bases ont renvoyé `integrity_check=ok` et 0 ligne de `foreign_key_check`.
- Les tables principales privées contiennent 292 entreprises, 88 offres et 5 candidatures. La démo publique contient 5 entreprises, 4 offres et 3 candidatures.

## Tables principales

| Table | Rôle |
|---|---|
| `entreprises` | Répertoire des entreprises, contacts, secteur et champs de localisation |
| `offres` | Offres historiques, dates, liens, statut stocké et classification |
| `candidatures` | Suivi privé des candidatures et référence possible à une offre/un CV |
| `candidature_history` | Historique des changements de statut |
| `cvs` | Versions de CV chiffrées au repos par `Vault` |
| `alerts`, `alert_preferences`, `alert_email_log` | Préférences et notifications |
| `collector_runs`, `collector_source_runs`, `collector_staging` | Exécutions, résultats par source et offres en attente d'approbation |
| `offer_source_identity`, `company_source_identity` | Identités et provenance externes, vides dans la base historique auditée |
| `collection_settings` | Permissions, activation et fréquence des sources |
| `assistant_messages`, `gemini_search_history` | Messages locaux et historique de recherche associé à une session |
| `send_attempts` | Idempotence et suivi des tentatives d'envoi |

Le schéma historique ne déclare pas de clé étrangère entre `offres` et `entreprises`, ni sur `candidatures.offre_id` et `candidatures.cv_id`. `candidature_history.candidature_id` référence `candidatures.id`. Index observés: `idx_offres_public_id` et `idx_candidatures_offre`; aucun index n'est déclaré sur `entreprises`.

## Relations interprétées avec prudence

Le modèle applicatif prévoit `offres."Entreprise ID"` comme référence vers l'entreprise, mais 85 valeurs sur 88 ne correspondent pas à `entreprises.rowid`. La relation reste donc faible dans cette base. Les candidatures peuvent contenir `offre_id` et `cv_id`; l'absence de contraintes de base impose de valider les références côté application. Le contrôle de clés étrangères SQLite ne détecte que les contraintes déclarées.

## Transactions et migrations

`backend/db.py` centralise la connexion SQLite, la sauvegarde cohérente avec `Connection.backup`, les migrations de schéma et les fonctions de lecture. `backend/web.py` applique les migrations au démarrage. La version lue avec `PRAGMA user_version` vaut 6. Aucun test ni outil de cette mission n'a écrit dans la base historique.

## Séparation local/public

Le lanceur de soutenance fixe le chemin absolu de la base privée. Le mode public exige `PUBLIC_DEMO_MODE=true`, une attestation et le marqueur `deployment_metadata.dataset_type=synthetic_public_demo`, puis sert la base en lecture seule. La copie publique ne doit inclure ni `.env`, ni CV, candidatures réelles, base de comptes privée, sauvegardes privées ou secrets.
