# Rapport des tests — Phase 7

## Commandes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q backend scripts
```

## Résultats

- Tests Phase 6 conservés : 91.
- Nouveaux tests Phase 7 : 5.
- Suite complète : 96 réussis, un avertissement de dépréciation du plugin de test Dash.
- Réseau bloqué dans les fixtures de test. Aucun site de recrutement, Google Places, Gemini ou SMTP n’est contacté.
- Compilation `backend`, `scripts` et `tests` : réussie.
- Validation de syntaxe JavaScript de `dashboard/js/ui.js` avec `node --check` : réussie.

## Couverture Phase 7

| Contrôle | Vérification |
|---|---|
| Droits du fichier | Le staging refuse si l’un des droits consultation, stockage ou affichage n’est pas confirmé. |
| URL | Une URL source HTTPS est exigée; les URL HTTP sont rejetées sans appel réseau. |
| Import incrémental | Identifiant source + URL canonique réutilisés; un second import ne crée pas une seconde offre. |
| Préservation | Import de données uniquement en base temporaire; nombre de candidatures et `integrity_check` contrôlés. |
| Synchronisation | Offre importée retrouvée par Offres, Matching, alertes, assistant local et métriques Dash. |
| Registre | Droit ODbL du portail Open Data séparé des flux de jobs qui nécessitent encore une licence. |

Le test de parcours utilise un CSV synthétique et un document d’autorisation fictif uniquement comme fixture. Il démontre le mécanisme logiciel; il ne constitue ni une autorisation réelle ni une validation d’une source web.
