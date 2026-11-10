# Évaluation finale — Stages Marrakech AI

Périmètre : version Phase 9 après retrait du bloc Dash « Activité de collecte ». Contrôle le 8 novembre 2026 sur bases en lecture seule et copies temporaires.

## A. Évaluation fonctionnelle

| Fonctionnalité | État initial | Test effectué | Correction | État final |
|---|---|---|---|---|
| Accueil/navigation | Présents | Routes/pages, API statistiques; rendu responsive non observé en navigateur | Aucune | Fonctionnelle avec limitation visuelle |
| Entreprises | Présentes | API et lecture de 292 lignes sur copie; tests recherche/filtres | Aucune | Fonctionnelle et testée |
| Offres | Présentes | 88 lignes sur copie; filtres, dates expirées/inconnues | Aucune | Fonctionnelle et testée; données âgées, liens à vérifier |
| Matching local | Présent | Scores, pondérations, explications et API sur copie | Aucune | Fonctionnelle avec limitation : indicatif |
| CV/PDF | Présent | Deux modèles, validation, extraction, versions et PDF | Aucune | Fonctionnelle et testée localement |
| Candidatures | Présentes | Création, transition de statut, historique sur DB temporaire | Aucune | Fonctionnelle et testée localement; aucun envoi réel |
| Carte | Présente | Coordonnées et provenance vérifiées par API/tests | Aucune | Fonctionnelle avec limite de données; OSM non vérifié visuellement |
| Dashboard Dash | Présent | Routes, callbacks, filtres, KPI, export, layout et retour | Retrait du bloc/callback; mention de provenance corrigée | Fonctionnelle et testée; aucun quartier disponible |
| Centre de collecte | Présent | CSV/XLSX, mapping, validation, doublons, staging/import/historique via fixtures | Conservé; ses tests ne dépendent plus du callback Dash | Fonctionnel avec limite : pas de collecte réelle validée |
| Alertes | Présentes | Préférences, correspondance, création, compteur, lecture, doublons | Aucune | Fonctionnelles en local; SMTP réel non appelé |
| Chatbot local | Présent | Retrieval SQLite et réponse locale sur copie historique | Aucune | Fonctionnel localement |
| Gemini Search | Optionnel | Désactivé sans clé; contrats externes simulés | Aucune | Limité : aucun appel réel |

## B. Évaluation technique

- Architecture Flask/API, services métier, SQLite et Dash monté sur `/analytics/`; la page Flask embarque Dash, le lien `target=_top` revient à Flask sans iframe imbriqué.
- Modules séparés et migrations additives; compilation Python réussie.
- Base active locale : SQLite v6, 292 entreprises, 88 offres, 5 candidatures. Base publique distincte : v6, 5/4/3, marqueur synthétique.
- ETL avec staging, provenance, autorisations, mapping, dédoublonnage et import contrôlé; tests avec fixtures, pas d’extraction réelle.
- Pas de test de charge. Le code Dash relit SQLite sur callbacks; l’échelle actuelle convient au prototype.
- `.env`, historiques et CV exclus de l’archive. Mode public synthétique lecture seule. Les tests couvrent notamment CSRF, validation, XSS/CSV et accès public. Ce n’est pas un audit d’intrusion.
- Blueprint Render prêt, mais aucun site déployé. Le disque gratuit est éphémère et inadapté à la persistance des candidatures/CV.

## C. Évaluation Data Science

La base historique contient 88 offres avec descriptions, mais les champs intégrés du nom d’entreprise sont vides. Les 292 villes/quartiers d’entreprises et les 88 villes d’offres sont vides; aucune analyse géographique ne peut être validée. Les dates observées sont anciennes. Des relations entreprise/offre sont incohérentes. Les offres historiques n’ont pas de permission de réaffichage établie.

Les graphiques descriptifs sont vérifiables; le matching n’est pas évalué sur un corpus annoté humain. Le dataset public est synthétique et ne démontre pas le marché réel.

## D. Objectifs du professeur

| Critère | État et preuve |
|---|---|
| Rechercher des opportunités | Vérifié sur copie locale via API et filtres, 88 offres |
| Collecter les données | Pipeline et fichiers autorisés testés avec fixtures; extraction réelle non validée |
| Analyser | Dash et services locaux vérifiés; conclusions limitées par les données |
| Visualiser | Graphiques et callbacks testés; navigateur/mobile non testé visuellement |
| Postuler | Suivi local fonctionnel; aucun email ni envoi externe réel |
| Suivre les candidatures | Statuts/historique testés en DB temporaire |
| Interface | Routes Flask/Dash vérifiées; preuve visuelle manuelle restante |
| Architecture | Flask, API, services, SQLite et Dash documentés |
| Backend/API | Routes et tests présents |
| Sources/méthode | Provenance et staging présents; droits de publication non confirmés |
| Data Exploration/nettoyage | Répartition et contrôles de qualité examinés; logique testée avec fixtures |
| Intégration IA | Chatbot/matching locaux vérifiés; Gemini réel désactivé et non appelé |

## E. Autoévaluation indicative sur 20

Cette note est une autoévaluation technique, pas une prédiction de note OFPPT.

| Domaine | Pondération | Score | Motif |
|---|---:|---:|---|
| Architecture et code | 3 | 2,5 | Couches séparées, routes et compilation contrôlées |
| Parcours fonctionnels | 5 | 3,8 | Tests API et parcours isolés; parcours navigateur incomplet |
| Données, provenance, ETL | 4 | 1,7 | Pipeline testable, mais collecte réelle/droits non prouvés; lieux vides |
| Data Science et IA | 3 | 2,0 | Matching/chat locaux; pas d’évaluation humaine/Gemini réel |
| Interface et Dash | 2,5 | 1,7 | Dash testé et bloc supprimé; contrôle visuel restant |
| Sécurité, tests, déploiement | 2,5 | 1,8 | 126 tests; pas de site HTTPS ni audit d’intrusion |
| **Total indicatif** | **20** | **13,5** | Présenter clairement les limites |

**Points forts :** intégration des modules, tests, base historique conservée, import contrôlé. **Points faibles :** provenance/réaffichage non autorisés, données géographiques vides, informations d’entreprise manquantes, offres anciennes. **Risques :** profil DB mal choisi; stockage volatil en hébergement gratuit. **Reste à faire :** test visuel Chrome/Edge/mobile, personnaliser le nom/groupe, ne coller que des URLs réellement publiées.

**Préparation de soutenance :** présentable si les limites sont annoncées et si la démo publique utilise exclusivement les données synthétiques.

## Addendum — contrôle final du 8 novembre 2026

- L’application locale privée a été résolue sur la base historique 292/88/5; `integrity_check=ok`. La démo 5/4/3 reste séparée. L’affichage 5/4/3 résulte du profil synthétique/instance utilisée, mais le PID ou l’URL de l’ancienne instance n’a pas pu être prouvé : l’accès Windows aux processus a été refusé.
- Le client web corrige maintenant le jeton CSRF périmé en relisant la session authentifiée et en réessayant une seule fois; une session réellement déconnectée doit être renouvelée par reconnexion. Les écritures restent protégées.
- Le chatbot a des commandes clavier, une progression d’envoi et un panneau mobile plein écran. Un test API confirme que le jeton périmé est rejeté, puis que deux messages fonctionnent avec le jeton renouvelé. Résultat du navigateur : consulter la ligne « Contrôle navigateur » du rapport de tests final.
- Le Matching IA regroupe les offres avec des seuils locaux documentés (≥70, 40–69, <40); les offres incertaines restent dans le groupe intermédiaire. Ce classement reste indicatif et non évalué contre un jeu de vérité terrain.
- Gemini SDK présent, clé absente, mode désactivé. Aucun test Google réel, compte, quota, modèle ou niveau gratuit n’a été vérifié. L’intégration ne peut être qualifiée d’opérationnelle en réel.
- Aucun import réel, email réel, déploiement Render/GitHub, ni candidature externe n’a été déclenché. La recherche d’offres garde ses contrôles de droits et reste non validée sur une source réelle autorisée.
- Résultat de test final : 126/126 tests passent en local et sur la copie publique, plus contrôle final JavaScript/Python réussi; Chrome visuel reste à faire.
