# Rapport Phase 5 — Collecte, alertes et assistant

Date : 6 novembre 2026

## Réalisations

- Connecteurs modulaires RSS Jawb, flux JSON Jawb par identifiants explicites et flux RSS carrière fourni par l’utilisateur; normalisation, contrôles URL, délais, journal par source, aperçu, simulation hors réseau, staging, import incrémental et rapprochements incertains à vérifier.
- Import CSV/XLSX d’entreprises avec aperçu, contrôles des coordonnées et détection de doublons sans remplacement destructif.
- Pages Centre de collecte et Mes alertes, compteur dans l’entête, historique et indicateurs de collecte Dash calculés depuis SQLite.
- Alertes locales, activables par l’utilisateur, avec critères et explication du score. Email facultatif avec destinataire chiffré, double activation, statut de livraison et regroupement instantané/quotidien/hebdomadaire. Alertes désactivées par défaut.
- Assistant structuré sur les données SQLite, mode local sans réseau, historique chiffré, consentement/aperçu séparés pour Gemini, contrôle des annonces référencées et repli local.
- Migration SQLite additive version 3 avec sauvegarde préalable.
- Script facultatif de tâche Windows, création uniquement après saisie explicite `OUI`; aperçu seulement, sans import automatique.

## Sources et limites d’autorisation

Le guide officiel Jawb documente son RSS et son JSON, mais le guide ne suffit pas à établir une licence générale d’agrégation. L’interface demande une confirmation explicite des droits avant import. Emploi.ma est écarté car ses conditions interdisent l’extraction automatisée de sa base; ReKrute est écarté sans autorisation écrite; aucune autorisation/API publique de Stagiaires.ma n’a été établie pour ce connecteur. Google Places et les sources payantes n’ont pas été appelés. Voir [Guide API Jawb](https://jawb.ma/api-recrutement), [CGU Jawb](https://jawb.ma/cgu), [CGU Emploi.ma](https://www.emploi.ma/conditions-generales-utilisation), [mentions légales ReKrute](https://www.rekrute.com/fr/mentions-legales.html).

## Validation

- Base historique avant et après migration : 292 entreprises, 88 offres, 5 candidatures.
- `PRAGMA integrity_check` : `ok`; `user_version` : 3 après migration.
- Sauvegardes avant migration : `backups/avant_phase5_20261106_123918.db` (état initial) et `backups/avant_phase5_migration_20261106_134224_561380.db` (avant migration version 3).
- Tests : 86 réussis, 0 échec, 0 ignoré (contre 72 avant Phase 5). Rapport XML dans `reports/tests_phase5.xml`. Un avertissement de dépréciation du plugin pytest Dash demeure externe au projet.
- Les collecteurs réseau et SMTP ont été testés avec mocks. Aucun import de source réelle, appel Google Places/Gemini payant ou email réel n’a été effectué. Les données historiques sont préservées.

## Limites connues

- Les emails d’alerte nécessitent un SMTP configuré et un accord explicite; le mode est désactivé par défaut. Les résumés quotidiens/hebdomadaires sont envoyés seulement pendant que Flask tourne. Une livraison incertaine n’est pas retentée automatiquement.
- Les connecteurs d’offres n’ajoutent pas automatiquement les fiches d’entreprise à la table `entreprises`; les noms transmis dans les annonces sont visibles sur les offres. Les fiches d’entreprise s’ajoutent par le parcours CSV/XLSX vérifié, car les champs fournis par les annonces ne suffisent pas à remplir de manière fiable la fiche complète.
- Le planificateur Windows lance des aperçus; il ne démarre pas le serveur et ne réalise pas d’import en arrière-plan. Le mode intégré nécessite que l’application reste ouverte.
- Il reste à vérifier les droits de chaque flux carrière/Jawb avec l’émetteur et à contrôler manuellement toute annonce importée avant candidature.
