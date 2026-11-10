# Rapport des tests du chatbot

Date : 9 novembre 2026

## Résultats automatisés

- Suite Pytest locale complète : **133 réussis, 0 échec**, 46,19 s.
- Une alerte non bloquante de compatibilité Dash/pytest (`PytestRemovedIn10Warning`).
- `node --check dashboard/js/ui.js` : réussi.
- `python -m compileall -q backend scripts tests` : réussi.
- Tests ciblés : mode Gemini sans fuite de clé, session CSRF expirée puis renouvelée, comptage depuis SQLite, matching sur offres existantes et chemins absolus indépendants du dossier courant.

## Résultat navigateur

`tests/browser_smoke.py` a lancé Chrome, chargé l'accueil et authentifié la session sur une base de test temporaire. Le parcours s'est interrompu ensuite sur un délai d'attente du libellé `MODE DÉMONSTRATION` dans l'écran Recherche IA. Le scénario complet (chatbot, Dash, mobile et captures) n'est donc pas validé visuellement; le délai ne démontre pas à lui seul une régression du chatbot.

## Sécurité des essais

Les essais utilisent une base de test temporaire ou des fixtures. La base historique demeure en lecture seule et conserve 292/88/5, SQLite v6 et `integrity_check=ok`. Aucun appel Gemini, SMTP, Places, collecte Internet ou service payant n'a été effectué.

Pour répéter les parcours manuels, suivre `GUIDE_TEST_MANUEL_CHATBOT.md` et lancer l'application avec `LANCER_SOUTENANCE_LOCALE.bat` après avoir libéré le port 5000.
