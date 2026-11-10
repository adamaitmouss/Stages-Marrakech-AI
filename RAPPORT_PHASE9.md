# Rapport Phase 9 — recherche IA sourcée et import contrôlé

## Résultat opérationnel

La page **Recherche IA sur Internet** propose trois parcours explicitement séparés : recherche locale SQLite, démonstration sur base temporaire et recherche Gemini avec Google Search Grounding. La recherche externe reste désactivée par défaut et n’a pas été appelée pendant les travaux. Aucun résultat réel n’a été candidat, vérifié ou importé en Phase 9.

La configuration locale ne contient pas de clé Gemini. Le modèle par défaut est `gemini-3.8-flash`; l’option Grounding est indisponible tant que la fonction, la clé serveur et la confirmation de facturation ne sont pas configurées. L’utilisateur doit aussi confirmer le coût avant chaque requête. Une requête peut déclencher plusieurs recherches facturables; les plafonds logiciels sont des garde-fous locaux, pas une garantie de facture maximale.

## Fonctionnalités livrées

- Formulaire en français avec prompt, ville, domaine, type d’opportunité, période et limite de résultats; exemples prêts à l’emploi.
- Mode local alimenté uniquement par SQLite et mode de démonstration clairement signalé.
- Démonstration bout en bout sur une base temporaire supprimée à la fin, avec import, Matching, Chatbot, alertes, données de dashboard et contrôle d’intégrité; la base métier n’est pas modifiée par ce parcours.
- Connecteur utilisant le SDK officiel `google-genai`, Search Grounding, métadonnées de sources, citations et suggestions Google. Les URL de résultats ne sont jamais suivies par le serveur. Une URL candidate n’est utilisable que si elle correspond exactement à une URL citée dans les métadonnées de grounding.
- Les candidats ne sont jamais considérés comme actifs ou vérifiés sur la seule parole de Gemini. Le staging exige un lien cité, une vérification humaine et une référence documentée des droits de consultation, stockage et réaffichage. L’import reste une action distincte et confirmée, via le pipeline Phase 8 existant.
- Détection de doublons SQLite, signalement prudent des dates anciennes, historique local minimal, clés de session, limite de 2 appels/session/jour, 5 appels/jour tous utilisateurs, délai de 60 secondes et arrêt qui empêche d’afficher les résultats d’un appel déjà envoyé.
- Clé Gemini conservée côté serveur. Les prompts d’historique masquent les adresses email, numéros et URL; les résultats web complets ne sont pas persistés dans l’historique.

## Mesures de données

| Mesure | État après validation |
|---|---:|
| Entreprises historiques | 292 |
| Offres historiques avant import réel | 88 |
| Candidatures historiques | 5 |
| CV | 0 en base (aucun CV utilisateur supprimé ou remplacé) |
| Intégrité SQLite | `ok` |
| Version SQLite | 6 après migration additive de l’historique |
| Recherches Google réellement réalisées | 0 |
| Résultats candidats réels | 0 |
| Offres réelles vérifiées/importées | 0 / 0 |
| Recherche Gemini | désactivée |
| Planification | non créée; aucun job Windows |

La migration Phase 9 ajoute une table d’historique sans remplacer les tables métier. Sauvegarde antérieure : `backups/avant_phase9_20261108_190635_394545.db`, SHA-256 `c493de1e46f39684449af0210f4c1232e79c8e4fe272096414f16481d0a5d868`.

## Validation

Les 107 tests précédents ont été relancés avant les nouveaux changements et ont réussi. L’ensemble final compte **120 tests réussis**. Les tests Phase 9 utilisent uniquement des faux clients/fixtures; ils couvrent le grounding et ses absences, les réponses invalides, les URL internes/usurpées, l’API désactivée, quotas et annulation, la recherche locale, la démo isolée, les garde-fous de droits, staging et import, ainsi que la conservation des candidatures. Voir `RAPPORT_TESTS_PHASE9.md`.

Le connecteur réel n’a pas été validé contre Google car aucun appel n’a été autorisé ou effectué. Le contrôle Chrome a été tenté sur une copie locale anonymisée, mais Chromium n’a pas démarré dans l’environnement d’exécution; aucune capture Phase 9 n’est donc livrée. Les routes, contrôles API et parcours de démonstration sont vérifiés dans les tests. Les sources citées par Google ne prouvent pas à elles seules la licence d’agrégation; il faudra obtenir et inscrire les droits pertinents pour chaque source avant tout stockage/réaffichage.

## Facturation et limites

La documentation tarifaire Google consultée indique que Grounding avec Google Search n’est pas compris dans le niveau gratuit de l’API Gemini 3; le palier Standard présenté comprend 5 000 requêtes de recherche par mois puis 14 USD par 1 000 requêtes. Une seule invite peut utiliser plusieurs recherches et donc consommer plusieurs unités. Tarifs et disponibilité peuvent changer : vérifiez la [page tarifaire officielle](https://ai.google.dev/gemini-api/docs/pricing.md) avant activation. Aucun compte, quota, moyen de paiement ou paramètre Cloud n’a été modifié.

Les conditions de réutilisation des pages trouvées ne sont pas établies par le seul fait qu’elles soient accessibles. Pas de scraping d’Indeed, LinkedIn, Emploi.ma ou ReKrute, pas de contournement anti-bot, pas d’extraction HTTP automatique et pas d’appel payant.

## Fichiers et guides

- `GUIDE_GEMINI_SEARCH.md` : modes, droits et parcours de vérification.
- `GUIDE_CONFIGURATION_API.md` : configuration locale facultative, clé et coûts.
- `GUIDE_TEST_PHASE9.md` : tests automatisés et contrôle manuel.

