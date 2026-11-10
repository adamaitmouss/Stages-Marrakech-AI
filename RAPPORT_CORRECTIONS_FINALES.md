# Rapport des corrections finales

Date : 8 novembre 2026.

## Modifications

1. Retrait dans `backend/analytics.py` du titre/descriptif, 5 KPI, 2 graphiques et bloc qualité « Activité de collecte ».
2. Suppression du callback correspondant. L’intervalle reste utilisé par le graphique analytique principal. Centre de collecte, tables SQLite, API, historique, validations et connecteurs inchangés.
3. Remplacement de « Données SQLite réelles » par un message distinguant base locale privée et dataset de démonstration, grâce au marqueur SQLite.
4. Ajout d’un breakpoint mobile sous 520 px : filtres et KPI en une colonne, actions réorganisées.
5. Profils d’environnement explicités dans `.env.example`, `.env.public-demo.example`, README et rapports. `.env` existant inchangé.
6. Tests qui dépendaient du callback supprimé adaptés pour vérifier la provenance dans SQLite/source_catalog. Deux tests de non-régression ajoutés.

## Bases et sauvegarde

La configuration résolue du lancement local sélectionne `database/stages_marrakech.db`, v6, 292/88/5, intégrité `ok`. Aucun effacement/restauration ni écriture sur cette base pendant la tâche. Les sauvegardes antérieures inspectées v0 à v5 conservent 292/88/5 et ont `integrity_check=ok`.

Render pointe vers `database/stages_marrakech_public_demo.db`, v6, 5/4/3 fictives, `dataset_type=synthetic_public_demo`, intégrité `ok`. Les bases ne sont pas mélangées; les CV et données historiques ne sont pas dans l’archive.

Avant modification, les deux bases (copie cohérente SQLite) et les fichiers code/tests/CSS/README/config touchés ont été sauvegardés dans `backups/avant_mission_dashboard_20261108_211441/`.

## Problèmes et résultat

| Priorité | Problème/constat | Correction ou état | Validation |
|---|---|---|---|
| Mineure UX | Activité ETL répétée dans Dash | Section et callback retirés; ETL conservé ailleurs | Test layout sans IDs et callback |
| Mineure confiance | Libellé impliquait que tout dataset était réel | Provenance affichée selon marqueur et mode | Test dataset synthétique |
| Mineure UX | Filtres en deux colonnes sur très petit écran | Une colonne sous 520 px | CSS vérifié; navigateur manuel restant |
| Limite de données | 0/292 quartiers/villes d’entreprise; 0/88 villes d’offre | Aucun chiffre inventé; limitation documentée | Requête SQLite en lecture seule |
| Limite QA | Chromium automatisé indisponible | Checklist manuelle fournie | Aucun rendu déclaré visuellement validé |

Aucun problème critique ou majeur n’a été mis en évidence par les essais exécutés. Ce n’est pas un audit de pénétration.

## Présentation PowerPoint

Le PPTX existant a été inspecté après la correction : il ne mentionne pas la section « Activité de collecte », conserve ses 26 diapositives et ses 26 notes orales. Aucune modification PowerPoint n’était nécessaire.

## Fichiers modifiés

`backend/analytics.py`, `dashboard/css/analytics.css`, `tests/test_phase5.py`, `tests/test_phase7.py`, `tests/test_phase8.py`, nouveau `tests/test_analytics_dashboard.py`, `.env.example`, nouveau `.env.public-demo.example`, `README.md`. Rapports : `EVALUATION_FINALE_PROJET.md`, `RAPPORT_CORRECTIONS_FINALES.md`, `RAPPORT_TESTS_FINAUX.md`, `GUIDE_VERIFICATION_MANUELLE.md`, `ETAT_DES_BASES_DE_DONNEES.md`.

## Résultats avant/après

Dernier compte avant correction : 123 tests. Après suppression, adaptation des assertions de collecte et ajout de tests : **125 réussis, 0 échec**, un avertissement non bloquant Dash/pytest. Smoke isolé réussi sur copies temporaires privées/publiques.

## Addendum — mission finale ultime, 8 novembre 2026

- Le diagnostic a confirmé en lecture seule que l’application privée charge `database/stages_marrakech.db` (292/88/5, v6, intégrité `ok`). Le profil public reste sur la base synthétique 5/4/3. Aucune restauration ni fusion n’a été nécessaire; `.env` et données historiques inchangés.
- La cause exacte de l’écran 5/4/3 est la sélection du profil de démonstration ou d’une autre instance. La session courante n’a pas accès aux processus Windows; l’instance navigateur à l’origine du signalement n’a pas pu être reliée à un PID/URL. Voir `DIAGNOSTIC_ENVIRONNEMENTS.md`.
- Le client API renouvelle une fois le jeton CSRF depuis la session authentifiée après le 403 de jeton périmé et répète la requête. Si l’authentification a expiré, il demande une reconnexion. Aucune protection n’a été désactivée. Test ajouté pour rejet du jeton périmé et deux échanges chatbot après renouvellement.
- Chatbot : messages plus lisibles, historique dans une zone défilante, boutons flexibles, état « Recherche… », envoi avec Entrée, saut de ligne avec Maj+Entrée, fenêtre mobile plein écran. Le lancement du navigateur de test n’a pas répondu; aucune validation visuelle n’est revendiquée.
- Matching : affichage des trois sections de recommandations avec seuils explicites 70 et 40; offres incertaines classées en « Potentiellement compatibles ». Les seuils sont des outils de tri, pas une évaluation de recrutement. Le flux Postuler existant permet de préparer le suivi, sans envoyer de candidature.
- Ajout des guides Gemini et Matching et du diagnostic des environnements. Gemini reste désactivé, clé absente, appel réel non effectué; niveau gratuit et modèle du compte non vérifiés.

La base privée n’a été ni restaurée ni modifiée. Le projet public n’est pas déployé. L’archive a été reconstruite depuis la copie synthétique synchronisée : 130 fichiers, un seul SQLite (`stages_marrakech_public_demo.db`), aucun `.env`, dossier privé, sauvegarde ou motif de clé contrôlé; ZIP intact.

Suite finale : 126/126 tests dans les environnements privés et public de démonstration; vérification JavaScript/Python réussie. Le navigateur visuel reste non vérifié.
