# Historique des tests — Phase 6

Le rapport de test à jour est [RAPPORT_TESTS_PHASE7.md](RAPPORT_TESTS_PHASE7.md). Cette page conserve les précisions historiques sur les fixtures de Phase 6.

Les tests utilisent des bases temporaires, des offres synthétiques et des réponses HTTP simulées. Aucun test n’appelle Jawb, un flux tiers, Google Places, Gemini ou SMTP. Les cinq candidatures historiques ne sont pas modifiées.

## Lancer la suite

À la racine du dossier du projet, avec les dépendances de développement installées :

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

La suite couvre le pipeline synthétique de bout en bout : extraction simulée, normalisation, aperçu, approbation manuelle, import SQLite temporaire, affichage d’offres, matching, alerte locale, réponse de l’assistant et métriques Dash. Elle vérifie aussi que l’absence de droits bloque la collecte, qu’un aperçu non approuvé ne s’importe pas, qu’une panne 503 conserve les données, et que l’aperçu XLSX normalise le secteur et l’email.

Les tests de carte et navigation Dash sont conservés dans `tests/test_map_dash.py` : ils contrôlent Leaflet/OSM, l’attribution et le retour vers l’application depuis Dash. Ils ne dépendent pas d’une navigation réelle ni d’un service cartographique.

## Résultat de la validation Phase 6

- Tests ciblés du pipeline : 19 réussis.
- Suite complète : 91 tests réussis, un avertissement de dépréciation du plugin de test Dash.
- Compilation des modules `backend` et `scripts` : réussie; intégrité SQLite après migration : `ok`.
- Les simulations et données de test restent dans des bases temporaires; aucune offre synthétique n’a été ajoutée à la base livrée.

Un avertissement de dépréciation de configuration du plugin pytest Dash peut apparaître; il n’affecte pas les résultats des tests.
