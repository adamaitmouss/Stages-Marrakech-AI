# Rapport de validation définitive

**Date : 9 novembre 2026**  
**Projet testé :** copie préparatoire `LIVRAISON_DEFINITIVE_SOUTENANCE/PROJET_FINAL`.

## État des données

Le lanceur privé pointe vers `database/stages_marrakech.db`. La base a été contrôlée en lecture seule : version 6, `integrity_check=ok`, zéro erreur de clé étrangère, 292 entreprises, 88 offres et 5 candidatures. 145 entreprises ont une valeur non vide dans le champ Emails; cela ne vérifie ni la délivrabilité ni les droits de republication. La base publique indépendante porte le marqueur synthétique et contient 5 entreprises, 4 offres et 3 candidatures fictives. Les droits de réaffichage historique ne sont pas démontrés : contenu historique publiable établi = **0 entreprise et 0 offre**. Voir `ETAT_DES_DONNEES.md`.

La base historique et les sauvegardes existantes n'ont pas été modifiées par cette mission. 217 empreintes historiques de fichiers suivies par le projet restent identiques. Le manifeste complet des copies locale/sauvegarde reste dans `SAUVEGARDE_ORIGINALE_PRIVEE`.

## Fonctionnalités couvertes par la suite automatisée

Les tests pytest du dépôt couvrent les routes Flask et CSRF, les chemins de configuration, le Dashboard Dash, les pages, Matching, génération/extraction PDF, import CSV/XLSX, connecteurs ATS/RSS simulés, validation des sources, staging et import, alertes, candidature/historique, carte, séparation démo/privé, recherche Gemini simulée et tests de la passerelle Login.

Les sources réseau et fournisseurs sont mockés. Aucun service payant, envoi réel d'email, candidature externe, collecte web réelle ou requête Gemini n'a été appelé. La suite ne constitue pas une validation de sécurité en production.

## Compte rendu des exécutions

À compléter après la dernière exécution de `pytest -q`, `compileall`, `node --check`, contrôles SQLite et `scripts/verify_soutenance.py`. Les résultats définitifs et durées seront inscrits dans ce tableau avant la remise.

| Contrôle | Résultat |
|---|---|
| `pytest -q` sur `PROJET_FINAL` | 166 réussis; 1 avertissement Dash/pytest; 57,86 s |
| Compilation Python (`compileall`) | Réussie |
| Vérification JavaScript (`node --check`) | 2 fichiers contrôlés, réussis |
| SQLite privé/publique | Les deux `integrity_check=ok`; 0 erreur FK; volumes conformes |
| Lanceur privé, lecture seule | Vérification réussie sur `PROJET_FINAL`: profil privé, chemin historique, intégrité OK, volumes 292/88/5, 145 entreprises avec email, port 5000 libre |
| Intégrité de l'archive publique | CRC valide, 154 fichiers, une base synthétique, aucune entrée sensible détectée |
| Présentation | 45 diapositives et 45 jeux de notes; paquet sans constat, 16:9, 5 diapositives à tables natives, Arial uniforme, 0 anomalie géométrique après correction. L'ouverture PowerPoint n'est pas attestée. |
| Publication du PPTX | Le finaliseur a validé le contenu mais Windows a refusé le lien fichier atomique. Le candidat contrôlé a été copié au nom final; SHA-256 comparé. Reçu finaliseur non produit. |
| PDF | Non généré : le moteur PDF intégré a échoué à charger une police du runtime; le PPTX reste le livrable de présentation. |

## Résultats fonctionnels et limites

- Le lanceur `LANCER_MON_PROJET.bat` fixe le profil privé et le chemin absolu de SQLite historique, vérifie les compteurs au démarrage et refuse les ports déjà occupés sans arrêter de processus. Le canal entre passerelle et Flask utilise désormais un secret aléatoire local généré automatiquement, limité à la boucle locale et ignoré par Git; aucun mot de passe technique n'est demandé. Les protections de compte, session, origine et CSRF restent actives.
- Les modules Flask et Dash pointent vers la même base via la configuration du backend; Chatbot et Matching interrogent les données locales de ce backend. La page historique de connexion et ses ressources ont été ouvertes dans le navigateur local. Le parcours complet derrière la passerelle Login n'a pas été validé avec une session authentifiée pendant cette vérification.
- L'authentification ne cloisonne pas CV/candidatures par utilisateur. L'inscription publique ne doit pas être activée pour des données personnelles.
- Aucune exécution de collecte réelle n'est inscrite. Les 88 offres historiques n'ont pas de date de dernière vérification; leur validité actuelle est inconnue.
- Les coordonnées et quartiers manquent pour l'ensemble des 292 entreprises; aucun marqueur réel n'est affichable à partir de l'instantané local.
- 85 `Entreprise ID` d'offre sur 88 ne correspondent pas à `entreprises.rowid`.
- Gemini, Google Places, SMTP, hébergement et envoi de candidature n'ont pas été activés réellement.

## Contrôles manuels non revendiqués

Le test de lancement réel a été exécuté avec `LANCER_MON_PROJET.bat`. Aucune saisie technique n'a été demandée. Le navigateur a affiché la page Login (HTTP 200); le canal interne local a répondu et les requêtes HTTP ont confirmé SQLite 292/88/5, 145 entreprises avec email, Dash 200, Chatbot local 200, Matching local 200 et 88 offres retournées. Des tests d'intégration avec un compte d'essai isolé vérifient aussi Login, accès privé et Logout; le mot de passe personnel de l'utilisateur n'a pas été saisi ni vérifié. Aucun déploiement Render, publication GitHub, collecte réelle ni audit d'intrusion n'a été effectué.

Le contrôle HTTP du Chatbot a inscrit deux messages de test dans la table locale `assistant_messages`. Cette écriture inattendue a été détectée en comparant les tables avec la sauvegarde pré-test; le serveur lancé par ce contrôle a été arrêté et le fichier SQLite a été restauré exactement depuis cette sauvegarde. L'empreinte actuelle correspond à celle de la sauvegarde, et le contrôle en lecture seule confirme de nouveau 292/88/5. Les vérifications Chatbot/Matching restantes sont couvertes par la suite automatisée.
