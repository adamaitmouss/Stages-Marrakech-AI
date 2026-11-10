# Rapport de validation finale

Date : 9 novembre 2026

## Résultats

- Pytest complet sur le projet local : **133 réussis, 0 échec**, 46,19 s.
- Pytest de la copie publique : **132 réussis, 1 ignoré, 0 échec**, 45,38 s; le lanceur local privé est volontairement absent de cette copie.
- Un avertissement non bloquant de compatibilité du plugin Dash/pytest (`PytestRemovedIn10Warning`).
- `node --check dashboard/js/ui.js` : réussi.
- `python -m compileall -q backend scripts tests` : réussi.
- Base historique SQLite v6 : `integrity_check=ok`, 292 entreprises, 88 offres, 5 candidatures, 0 CV; relation FK sans erreur. Contrôlée en lecture seule après modifications.
- Base publique synthétique distincte : 5 entreprises, 4 offres et 3 candidatures.
- Contrôle d'environnement : venv et dépendances présents, chemin local privé résolu; l'instance qui occupe actuellement le port 5000 répond avec `public_demo=true`.

## Chatbot et soutenance

Le chatbot est réorganisé en composants natifs JavaScript, garde son mode local par défaut, gère le renouvellement CSRF uniquement pour une session authentifiée et exige un aperçu et consentement explicite avant tout appel Gemini. Le lanceur de soutenance impose le chemin absolu historique, vérifie SQLite en lecture seule et refuse de démarrer si le port est occupé.

Le test navigateur a lancé Chrome et authentifié une base temporaire, puis a échoué sur l'attente du libellé de démonstration de la page Recherche IA. Le parcours navigateur complet et l'affichage mobile ne sont pas validés visuellement. Le serveur public déjà actif n'a pas été arrêté, car son PID n'a pas pu être attribué.

## Données préservées

Une copie de sauvegarde a été créée avant les modifications dans `backups/before_soutenance_mission_20261108_235804/`; volumes et intégrité vérifiés. Aucune base originale n'a été remplacée. Aucun appel Gemini, service payant, email, collecte Internet, publication ou déploiement n'a été effectué.

## À faire avant la soutenance

Fermer proprement l'instance de démonstration qui occupe le port 5000, démarrer avec `LANCER_SOUTENANCE_LOCALE.bat`, puis suivre `GUIDE_SOUTENANCE_LOCALE.md` et `GUIDE_TEST_MANUEL_CHATBOT.md`. Voir `DIAGNOSTIC_ENVIRONNEMENTS.md` pour le détail du diagnostic.
