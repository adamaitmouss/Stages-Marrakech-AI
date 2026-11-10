# État des bases de données

Contrôle en lecture seule — 8 novembre 2026. Aucun historique n’a été restauré car la base active contient déjà les données demandées.

## Base utilisée en local

| Élément | Valeur vérifiée |
|---|---|
| Chemin résolu par `backend.config.settings()` | `database/stages_marrakech.db` |
| `PUBLIC_DEMO_MODE` | `false` |
| Version / intégrité | SQLite v6 / `ok` |
| Entreprises / offres / candidatures | 292 / 88 / 5 |
| CV en table SQLite | 0 |
| Coordonnées vérifiées | 0 |
| Quartier ou ville entreprise renseigné | 0 / 292 |
| Ville renseignée sur les offres | 0 / 88 |

Flask, APIs, assistant et Dash reçoivent le même `app.config['DATABASE']`. Smoke d’intégration sur copie : API et KPI Dash ont renvoyé 292/88/5. Le fichier `.env` existant reste intact.

## Base de démonstration publique séparée

| Élément | Valeur vérifiée |
|---|---|
| Chemin | `database/stages_marrakech_public_demo.db` |
| Profil Render | `PUBLIC_DEMO_MODE=true`, confirmation `true` |
| Version / intégrité | SQLite v6 / `ok` |
| Entreprises / offres / candidatures | 5 / 4 / 3 fictives |
| Marqueur | `deployment_metadata.dataset_type=synthetic_public_demo` |
| Différence de schéma | seule table additive `deployment_metadata` |

Les bases ne sont pas fusionnées. La démo est lecture seule, avec intégrations externes désactivées. L’archive publique exclut l’historique et les CV.

## Sauvegardes retrouvées

Les bases `.db` de `backups/` inspectées sont en v0–v5, intègres, et conservent chacune 292/88/5. La base v6 active n’avait donc pas besoin d’être restaurée. Un homonyme racine `stages_marrakech.db` de 0 octet, version 0 sans tables, n’est pas sélectionné par la configuration; conservé sans suppression automatique.

## Sauvegarde préalable aux corrections

`backups/avant_mission_dashboard_20261108_211441/` contient des sauvegardes SQLite cohérentes des deux bases et copies des fichiers touchés. Après correction, l’historique original reste v6/intégrité `ok`.

## Modèles d’environnement

- `.env.example` local : base historique, mode privé (`false`).
- `.env.public-demo.example` et `render.yaml` : base synthétique, mode public lecture seule.
- Copie GitHub : dataset synthétique seulement; pas de candidatures réelles, historique ou CV privé.

