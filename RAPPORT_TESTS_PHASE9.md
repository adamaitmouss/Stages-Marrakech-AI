# Rapport des tests — Phase 9

## Résultat

- Phase 8 avant modifications : **107 tests réussis**.
- Suite finale après Phase 9 : **120 tests réussis, 0 échec**.
- Python `compileall` : réussi.
- `node --check dashboard/js/ui.js` : réussi.
- Un avertissement existant du plugin pytest Dash signale une ancienne configuration de hook; aucun échec n’y est associé.

## Couverture Phase 9

- Parsing structuré Gemini, grounding, sources citées, citations et nombre de recherches.
- Absence de sources, réponse invalide, erreurs fournisseur et modèle/configuration désactivés.
- Rejet des URL HTTP, localhost, IP privée, redirection Google et identifiants intégrés.
- Plafond de requêtes et annulation; résultat d’un appel annulé non présenté.
- Recherche locale explicitement SQLite.
- Démonstration de bout en bout dans une base jetable : import, Matching, Chatbot, alertes, Dash, intégrité et absence de modification de la base principale.
- Refus du staging sans vérification et droits; approbation individuelle puis import via le pipeline existant.
- Préservation des 5 candidatures de fixture lors d’un import autorisé simulé.

Tous les tests bloquent l’accès réseau et utilisent des fixtures. Aucun test ne contacte Gemini, Google Search ou une autre API.

## Vérification navigateur

Le contrôle Playwright/Chrome a été tenté sur une copie anonymisée de la base. Chromium ne s’est pas initialisé dans l’environnement d’exécution, donc aucune capture ni résultat navigateur n’est revendiqué. La nouvelle page, ses routes API et son flux de démonstration sont couverts par les tests serveur.

