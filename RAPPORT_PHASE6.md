# Rapport Phase 6 — validation du pipeline de collecte et synchronisation

## Résumé

Le pipeline local est prêt pour une activation contrôlée après vérification des droits de chaque source. La collecte réseau et l’automatisation restent désactivées par défaut. Aucun service tiers n’a été interrogé et aucune offre réelle n’a été importée pendant cette phase.

## Résultats

- Sources techniquement prêtes : connecteurs Jawb RSS/JSON et flux RSS/Atom HTTPS configurables. Leur fonctionnement a été vérifié uniquement avec des fixtures et mocks; aucune disponibilité actuelle de source externe n’est revendiquée.
- Sources dont le droit de réutilisation est confirmé pour ce projet : aucune autorisation écrite spécifique n’était disponible dans le dossier. Jawb et les flux personnalisés restent verrouillés jusqu’à documentation de l’accord. Emploi.ma et ReKrute sont exclus; Stagiaires.ma reste non connecté; Google Places n’est pas utilisé.
- Nouvelles offres réellement importées pendant la Phase 6 : **0**. Une offre synthétique a été importée uniquement dans une base de test temporaire; elle n’a pas rejoint la base livrée.
- Une offre fictive traverse l’extraction, la normalisation, le staging, l’approbation individuelle, l’import dans une base temporaire, le matching, l’alerte, l’assistant et les métriques Dash.
- Le registre distingue l’accès technique des autorisations de réutilisation. L’import Jawb et les flux personnalisés nécessitent une référence d’autorisation écrite; les annonces restent à approuver individuellement. Emploi.ma et ReKrute sont exclus selon leurs conditions. Stagiaires.ma n’est pas raccordé faute d’autorisation d’extraction documentée. Google Places reste séparé et non appelé.
- Les exécutions enregistrent durées, compteurs, statut et erreurs par source. Les éléments identiques sont comptés comme inchangés; une panne conserve l’état local.
- L’aperçu CSV/XLSX des entreprises valide les emails, normalise les secteurs connus, conserve les valeurs non reconnues et signale les champs manquants/risques de doublon.
- Les régressions Leaflet/OSM et de navigation Dash restent couvertes par les tests existants.

## Préservation de la base

Avant migration Phase 6, la base principale contenait 292 entreprises, 88 offres, 5 candidatures et 0 CV; `integrity_check` était `ok`, version de schéma 3. La sauvegarde préalable vérifiée est `backups/avant_phase5_migration_20261106_144721_600590.db` (SHA-256 `ef9bd730968e081e187ac31ab2dd30384b04dc9911a8443796b7d1b08f4a3df9`). La migration v4 est additive. Après migration : 292 entreprises, 88 offres, 5 candidatures, 0 CV, version 4, intégrité `ok`, zéro exécution de collecte et zéro identité de source importée. Les options de collecte restent non configurées et désactivées. Le détail est dans `reports/preservation_phase6.json`.

## Validation logicielle

Tests ciblés du pipeline : 19 réussis. Suite complète : 91 réussis, 1 avertissement de dépréciation du plugin de test Dash. `compileall` sur `backend` et `scripts` s’est terminé sans erreur. L’intégrité SQLite après migration est `ok`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q backend scripts
```

Les tests utilisent des bases temporaires et des réponses simulées. Le test 503 ne fait aucune connexion réseau. Les informations historiques restent préservées.

## Points restant soumis à l’utilisateur

La collecte réelle ne peut commencer qu’après vérification et documentation des droits de réutilisation pour la source choisie. Le champ de référence prouve uniquement qu’une référence a été fournie; l’application ne peut pas authentifier la validité juridique du document. Les entreprises se mettent à jour par import CSV/XLSX, sans source web automatique autorisée dans cette phase.

## Documents

- [Guide d’activation](GUIDE_ACTIVATION_COLLECTE.md)
- [Registre des sources](GUIDE_SOURCES_AUTORISEES.md)
- [Guide des tests](GUIDE_TEST_PHASE6.md)
