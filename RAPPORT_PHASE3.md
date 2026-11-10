# Rapport Phase 3 — Stages Marrakech AI

**Date : 3 novembre 2026**  
**Base de travail :** archive Phase 2 modernisée. Les sources initiales et les données métier n’ont pas été remplacées.

## 1. Résumé

La Phase 3 poursuit les améliorations vérifiables sans navigateur. Elle rend le panneau CV plus actionnable, affiche le PDF réellement généré dans l’aperçu, aligne les longueurs des champs HTML avec les validations Python, synchronise les KPI Dash avec le jeu filtré et ajoute des indicateurs de qualité des données. Les filtres de secteur sur les offres ne prennent en compte que les liens vers les entreprises marqués comme vérifiés.

La suite passe de **56 à 63 tests automatisés réussis** (0 échec, 2 avertissements de dépréciation issus des plugins tiers anyio/Dash). La syntaxe JavaScript est validée par Node. Aucune API externe, collecte, géolocalisation ou action SMTP n’a été appelée.

Cette phase n’est pas déclarée entièrement validée : les interactions et le nouveau rendu PDF n’ont pas fait l’objet d’un contrôle visuel navigateur. Le blocage Playwright/Windows est décrit en section 7 et des étapes manuelles détaillées sont fournies dans `GUIDE_TEST_MANUEL.md`.

## 2. Vérifications avant modification et conservation

Avant de modifier le code, une copie SQLite a été créée dans l’espace de travail. La base avant travaux était intègre et comportait :

| Données | Avant | Après | Résultat |
|---|---:|---:|---|
| Entreprises | 292 | 292 | Conservées |
| Offres | 88 | 88 | Conservées |
| Candidatures historiques | 5 | 5 | Conservées |
| Versions CV dans SQLite | 0 | 0 | Inchangées |
| Coordonnées géographiques vérifiées | 0 | 0 | Aucune coordonnée ajoutée |

Les six tables SQLite (`entreprises`, `offres`, `candidatures`, `cvs`, `candidature_history`, `send_attempts`) ont été comparées, ligne à ligne, à la sauvegarde initiale : elles sont identiques. `PRAGMA integrity_check` retourne `ok`. Le seul PDF historique trouvé dans l’application est octet pour octet identique à celui de l’archive Phase 2. Aucune migration n’a été exécutée pendant cette phase.

La base initiale contient 292 liens Google Maps existants, mais zéro latitude/longitude avec provenance et date de vérification. La page carte conserve les fiches/liens existants, indique le compte de positions réellement vérifiées et sépare les points de démonstration.

## 3. Problèmes examinés et corrections

### Créateur et optimisation de CV

- L’aperçu à droite montrait auparavant une maquette HTML, alors que le PDF pouvait avoir des différences de pagination ou de typographie. Il affiche maintenant un PDF temporaire réellement généré par l’API locale, avec une version HTML textuelle repliable pour l’accessibilité. Les URL blob précédentes sont révoquées; les erreurs de validation sont annoncées dans la page.
- Chaque proposition d’organisation/reformulation peut être **acceptée** ou **ignorée**. Accepter une expérience/un projet pertinent le remonte en tête de sa section dans le brouillon. Une suggestion de résumé, lorsqu’une phrase existante mentionne déjà une compétence commune, ne fait que réordonner ces phrases exactes. Les conseils généraux ont eux aussi un choix Accepter/Ignorer.
- L’acceptation ne sauvegarde jamais automatiquement : l’utilisateur voit la modification dans le brouillon et doit choisir explicitement d’enregistrer une nouvelle version.
- Le serveur vérifie que le brouillon correspond toujours à la version analysée avant d’appliquer une proposition d’organisation. Une section modifiée depuis l’analyse doit être rechargée puis réanalysée.
- Les attributs `maxlength` du formulaire correspondent maintenant aux limites backend pour l’identité, les liens et les entrées répétables.
- L’aperçu backend est testé en PDF pour les modèles Moderne et ATS; le texte français avec accents est extractible dans les réponses de test.

### Matching local et Gemini

- Ajout de trois profils synthétiques représentatifs (Python/Data, Java, marketing/SEO) afin de tester le premier résultat du classement, la plage de score et la somme des contributions.
- Les scores restent des estimations explicables calculées localement, et non des probabilités de recrutement.
- Le traitement Gemini conserve la prévisualisation/consentement, le résumé d’envoi, la validation de sortie et le repli local. Le SDK et ses branches sont testés avec mocks uniquement; aucun appel Google réel n’a été réalisé.

### Dashboard Dash

- Le KPI correspondant au jeu actif suit désormais les filtres appliqués. Le taux de réponse suit les candidatures filtrées quand l’onglet Candidatures est choisi; ailleurs, il reste calculé sur toutes les candidatures et le libellé le précise.
- Une section qualité indique, suivant le jeu actif, emails/sites manquants, couverture géographique vérifiée, dates/type de stage manquants, offres expirées/date d’expiration inconnue, ou répartition des candidatures par statut.
- Le filtre secteur des offres est calculé uniquement par une jointure dont `relation_verified=1`; sinon le secteur reste vide et n’est pas inféré.
- Les callbacks, filtres, KPI, messages de graphique et export CSV sont testés directement en Python. La protection CSV contre les formules reste en place.

### Sécurité et candidatures

Les protections Phase 2 restent en place : authentification locale, CSRF, contrôle d’origine, validation, erreurs neutres, fichiers privés non servis, secrets dans l’environnement, consentement Gemini, confirmations pour email et absence de doubles envois. Les tests SMTP utilisent un mock. Aucun email n’a été envoyé.

## 4. Tableau final obligatoire

| Fonctionnalité | Implémentée | Testée | Réellement fonctionnelle | Configuration nécessaire | Limites |
|---|---|---|---|---|---|
| Pages locales et navigation serveur | Oui | Routes HTTP Flask testées | Pages servies; interactions visuelles non rejouées | Mot de passe local | Contrôle visuel manuel à faire après extraction |
| Recherche entreprises/offres | Oui | Endpoints et filtres de données testés | Recherche source SQLite; dates d’expiration signalées | Aucune | Les dates d’annonces peuvent être anciennes; vérifier la source avant candidature |
| CV PDF Moderne/ATS | Oui | PDF via API, texte/accents, sauvegarde chiffrée et suppression testés | Génération backend et réponse PDF fonctionnelles | Aucune | Nouveau cadre d’aperçu intégré non revu visuellement |
| Acceptation/refus de conseils CV | Oui | API de suggestions et invariance du CV enregistré testées; JS syntaxique vérifié | Actions front-end codées, pas exercées visuellement | Aucune | Contrôler manuellement l’ordre, l’aperçu et la sauvegarde d’une nouvelle version |
| Matching local | Oui | Trois profils synthétiques, scores et contributions testés | Fonctionne sans réseau | Aucune | Heuristique non évaluée sur un corpus annoté; données d’offre parfois pauvres |
| Gemini | Oui, facultatif | Mocks SDK/quota/erreurs/consentement testés | Branche simulée uniquement; service réel non vérifié | Clé, modèle, activation, quotas et consentement | Disponibilité/facturation liées au compte; contenu transmis au fournisseur |
| Préparer une candidature | Oui | API, confirmation, statut/historique testés | Fonctionne localement sans envoi | Aucune | Une candidature préparée n’est pas une candidature envoyée |
| SMTP | Oui, facultatif | Mocks destinataire/idempotence/erreur testés | Simulation réussie; SMTP réel non testé | Compte SMTP, adresse vérifiée, activation et confirmations | Pas de preuve de réception par le destinataire |
| Suivi des candidatures | Oui | CRUD partiel, statuts et historique testés | API et SQLite fonctionnent | Aucune | Suppression physique des candidatures désactivée pour conserver l’historique |
| Dash, graphiques, filtres et CSV | Oui | Layout HTTP, callbacks, filtres, KPI et export testés | Calculs Python/SQLite fonctionnels | Aucune | Pas de contrôle visuel de cette phase; filtre secteur offre limité aux relations vérifiées |
| Carte locale | Oui | API carte, coordonnées test et provenance testés | Mode local fonctionne; compteur actuel 0 coordonnée vérifiée | Aucune pour mode local | Les fonds Google nécessitent une clé; aucun géocodage réel effectué |
| Google Maps JavaScript/Places | Oui, facultatif | Configuration/branches documentées; pas d’appel réel | Intégration externe non vérifiée | Clés restreintes, quotas, consentement | Peut être facturable; aucune clé ajoutée |
| Scripts de collecte/import | Oui, déclenchement contrôlé | Import/dédoublonnage/pagination mockée et non-destruction testés | Import local disponible | Autorisation explicite `--allow-external` pour collecte | Aucune collecte réseau effectuée |
| Responsive/accessibilité | CSS et attributs présents | Syntaxe JS et routes vérifiées; test responsive navigateur de Phase 2 archivé | Non revalidé visuellement cette phase | Contrôle manuel navigateur | Le nouveau panneau d’optimisation et iframe PDF doivent être inspectés sur mobile/desktop |

## 5. Tests exécutés

- **56 tests Phase 2** relancés avant toute modification : 56 réussis.
- **Suite finale : 63 réussis, 0 échec**, sur bases de test temporaires, avec réseau bloqué et Gemini/SMTP mockés.
- **JavaScript :** `node --check dashboard/js/ui.js` réussi.
- **SQLite :** sauvegarde avant travaux, 292/88/5 conservés, versions CV à 0, six tables inchangées, intégrité `ok`.
- **PDF :** tests des deux modèles, endpoint d’aperçu, accents, export, versions et documents multipages.
- **Dash :** callback options, callbacks de graphes/KPI, synchronisation de filtres, relation de secteur vérifiée, message graphique incohérent et export CSV.
- **Réseau externe :** 0 appel Gemini/Maps/Places/Stagiaires.ma/SMTP.
- **Échecs :** aucun dans la suite finale. Deux avertissements pytest concernent les plugins de test tiers anyio et Dash (compatibilité avec pytest 10).

Rapport JUnit : `reports/tests_phase3.xml`. Résumé de préservation : `reports/preservation_phase3.json`.

## 6. Fichiers modifiés/créés

- `backend/api.py` : suggestions de résumé basées sur le réordonnancement de phrases existantes et index des éléments source.
- `backend/analytics.py` : jointure de secteur limitée aux relations vérifiées, KPI synchronisés, indicateurs de qualité.
- `dashboard/js/ui.js` : aperçu PDF Blob réel, acceptation/refus des suggestions, contrôle des longueurs de champs.
- `dashboard/css/cv-preview.css` : styles d’aperçu PDF et cartes de proposition, adaptations CSS mobile.
- `dashboard/css/design.css` : chargement du nouveau fichier CSS.
- `tests/test_application.py` : 7 tests supplémentaires couvrant aperçu PDF, profils, résumé, filtres Dash et relations vérifiées.
- `README.md`, `RAPPORT_PHASE3.md`, `GUIDE_TEST_MANUEL.md` : installation, fonctionnement et validation.
- `reports/tests_phase3.xml`, `reports/preservation_phase3.json`, `reports/validation_phase3.json` : preuves de test et préservation.

Aucune dépendance Python supplémentaire n’a été requise; `requirements.txt` et `.env.example` restent sans changement et sans secret.

## 7. Tests visuels non réalisés

Le test Playwright n’a pas été relancé dans cette reprise conformément à la demande de ne pas faire dépendre le développement du navigateur. Les sessions antérieures ont montré un blocage de `sync_playwright().start()` avant le lancement du navigateur. L’essai Edge précédent a expiré et le contrôle Chrome avait été interrompu par le garde-fou Windows lorsqu’il n’a pas pu déterminer l’URL active. Aucun contournement des protections Windows n’a été entrepris.

La Phase 2 avait archivé 16 contrôles navigateur réussis, 0 erreur JavaScript de page et 0 requête externe, mais ce résultat ne couvre pas les changements Phase 3. Les anciennes captures restent sous `docs/captures/`; elles ne montrent pas le nouvel aperçu PDF ni les boutons Accepter/Ignorer. Le contrôle visuel Phase 3 est donc à réaliser avec le guide ci-joint.

## 8. Fonctions dépendantes d’API ou de compte

- **Gemini :** renseigner `GEMINI_API_KEY`, modèle autorisé et activation; lire l’aperçu et donner le consentement avant transmission. Les tests utilisent des mocks.
- **SMTP :** paramètres d’un compte valide et adresses destinataires vérifiées; activation et double confirmation nécessaires. Les tests utilisent un serveur simulé.
- **Maps/Places :** clés séparées, restrictions par API et origine, vérification des coûts/quotas et accord explicite. Les clés ne figurent pas dans le projet. Aucun géocodage n’est lancé.
- **Collecte :** commande manuelle, options de garde et examen des conditions des sources; aucun scraping/collecte effectué.

Les anciennes clés Google exposées dans les sources originelles doivent encore être révoquées manuellement dans le compte propriétaire; les retirer du code ne les révoque pas.

## 9. Lancement

Depuis la racine extraite sous Windows PowerShell :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe backend\app.py
```

Ouvrir `http://127.0.0.1:5000` et créer votre mot de passe. Pour les tests :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

