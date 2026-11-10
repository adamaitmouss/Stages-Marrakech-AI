# Rapport de refonte du chatbot

Date : 9 novembre 2026

## Changements

- Remplacement du bloc monolithique par des composants JavaScript dédiés : en-tête, historique, bulles, suggestions, formulaire, sélecteur de mode, état de chargement et erreurs.
- Fil local sur SQLite par défaut, historique conservé entre fermeture et réouverture, bouton de nouvelle conversation avec confirmation, saisie limitée et prise en charge Entrée/Maj+Entrée.
- Affichage des informations utiles d'une offre et de sa source, avec liens externes protégés et présentation explicite des entreprises/localisations inconnues et des validités à vérifier.
- Les suggestions de matching distinguent très compatible, potentiellement compatible et à explorer; le résultat incertain reste signalé.
- Gemini n'apparaît que si la configuration locale est complète. Avant l'appel, une boîte de dialogue montre le contenu exact qui serait transmis et exige un consentement explicite. La clé n'est jamais renvoyée par l'API de statut.
- Reprise CSRF limitée à un seul renouvellement lorsque la session reste authentifiée. Une session expirée demande une reconnexion; aucune désactivation CSRF ni répétition générale des requêtes n'est utilisée.

## Données et intégration

Le chatbot interroge les données SQLite locales. Les demandes de comptage répondent par le nombre enregistré et précisent qu'il s'agit du contenu stocké, sans prétendre décrire l'activité du marché. Le matching CV réutilise les offres présentes en base et expose l'incertitude au lieu d'inventer des offres.

Le mode Gemini est désactivé par défaut et aucun appel réel n'a été effectué. Le chatbot ne crée pas d'offre ni de donnée historique.

## Validation

Les tests ciblés de statut Gemini, renouvellement CSRF, comptage SQLite et matching local passent. La suite complète du projet compte 133 tests réussis au 9 novembre 2026. Le test navigateur de bout en bout a démarré Chrome et s'est authentifié, puis a échoué sur l'attente du texte du parcours démo; aucun succès visuel complet n'est revendiqué. Voir `RAPPORT_TESTS_CHATBOT.md` et `GUIDE_TEST_MANUEL_CHATBOT.md`.
