# Rapport de validation Phase 8

## Résultat

- Suite complète : **107 tests réussis** (96 préexistants + 11 tests Phase 8).
- Python : compilation réussie.
- JavaScript : vérification syntaxique de `dashboard/js/ui.js` réussie.
- Avertissement restant : avis de dépréciation émis par le plugin pytest de Dash; aucun test en échec.
- Les nouveaux tests utilisent des fixtures et sessions simulées; aucun appel ATS réel n’a été lancé.

## Couverture Phase 8

- Greenhouse : endpoint et normalisation simulés, résultat vide.
- Lever : pagination de 101 annonces et normalisation simulées.
- Ashby : filtrage `isListed=false` et champs de publication.
- SmartRecruiters : destination publique, liste vide et parsing.
- Identifiants invalides, réponse HTTP en erreur, réponses mal formées.
- Mapping CSV des offres et dates/URLs invalides; fichier XLSX avec mapping d’entreprise.
- Activation d’un board refusée quand un droit ou sa référence manque.
- Chaîne simulée sur base temporaire : connecteur → normalisation → staging → approbation → import → matching → chatbot SQLite → alertes → KPI Dash.
- Intégrité SQLite `ok` et conservation des 5 candidatures de la base temporaire.

La validation de la base livrée est consignée dans `RAPPORT_PHASE8.md`.
