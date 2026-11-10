# Rapport de modernisation — Stages Marrakech

Date : 3 novembre 2026. Projet Flask existant conservé et réellement modifié. Le présent document décrit la livraison, ses vérifications et les opérations externes restant manuelles.

## 1. Résultat de la livraison

L’application conserve Flask, SQLite et le front-end HTML/CSS/JavaScript. Elle sert désormais toutes les pages depuis le même serveur, avec accès personnel par mot de passe. La nouvelle interface comprend les huit rubriques demandées : Accueil, Entreprises, Offres de stages, Matching IA, Créateur de CV, Mes candidatures, Carte des entreprises et Analyses Dash.

Les pages utilisent les données SQLite et les routes métier : il ne s’agit pas d’une maquette. Le créateur produit des PDF textuels réels ; le matching fonctionne sans clé ; les candidatures sont enregistrées avec historique ; Dash est monté sur Flask avec des callbacks Python.

**Données originales intégralement conservées : 292 entreprises, 88 offres et 5 candidatures.** Un contrôle compare toutes les anciennes colonnes, ligne par ligne, dans les trois tables, à l’extraction originale. Aucune ancienne valeur n’a changé. Tous les Excel, PNG et le PDF historique sont identiques octet pour octet. L’archive RAR originale n’a pas été modifiée.

Une copie intégrale avant modification est conservée dans `work/sauvegarde_avant_modernisation/Projet_Stages_Marrakech` dans l’espace de travail de cette livraison. Elle n’est pas incluse dans l’archive livrée, car les anciennes sources contiennent la clé Google exposée. La sauvegarde de la base avant migration est incluse dans `backups/avant_migration_20261103_162226_655749.db`.

## 2. Fonctionnalités réalisées, par phase

### Phase 1 — Stabilisation et sécurité

- Suppression des clés Google littérales dans les trois scripts concernés, variables d’environnement, `.env.example` sans secret et `.gitignore`.
- Configuration centralisée, séparation routes/services/SQLite/PDF/matching/Gemini/Dash.
- Mot de passe personnel créé à la première visite locale ; hachage du mot de passe, limitation des échecs de connexion, session HttpOnly et SameSite Strict.
- Protection des routes API et des routes internes de Dash. Les CV, candidatures, sauvegardes et fichiers privés ne sont pas exposés par le serveur statique.
- API d’écriture protégées par jeton CSRF ; contrôle d’origine, CORS global supprimé au profit de la même origine Flask.
- Validation des objets JSON, dates, emails et statuts. Candidatures vides refusées. PUT/PATCH n’effacent plus les champs absents.
- Rendu DOM par nœuds texte, sans `innerHTML` pour les données. Les apostrophes ne sont plus insérées dans des attributs d’événements inline.
- Debug désactivé, serveur local seulement, erreurs fournisseur non exposées, limite HTTP 6 Mo.
- Migration additive et sauvegarde avant modification du schéma. Import Excel sans remplacement des tables et sans effacer les champs existants au profit de valeurs NULL.
- Scripts exécutés sous main, imports sans collecte ; chemins ancrés à la racine, écritures brutes dans `data_raw` et nettoyées dans `data_clean`.

**Action manuelle indispensable :** révoquer/renouveler la clé Google précédemment distribuée dans votre compte. Son retrait des fichiers ne révoque pas la clé chez Google. Aucune clé de remplacement n’a été créée ou utilisée ici.

### Phase 2 — UX/UI

Identité marine/bleu électrique/blanc/gris, sidebar commune avec icônes SVG locales, en-tête et recherche globale, cartes, boutons cohérents, notifications, squelettes, messages d’erreur et états vides. Thème clair/sombre mémorisé sans données personnelles. Adaptation ordinateur/tablette/mobile, focus clavier visible, lien d’évitement et formulaires libellés.

L’accueil affiche des statistiques réelles, quatre offres récentes, secteurs, taux de réponse et accès rapides. Les entreprises et offres restent recherchables et filtrables. Les anciennes URL statistiques et envoi de CV restent disponibles, intégrées à la nouvelle navigation. Le tableau analytique Dash conserve un thème clair à l’intérieur de son iframe.

### Phase 3 — Créateur de CV

Formulaire avec identité, titre, résumé, formation, expériences, projets, compétences techniques/personnelles, langues, certifications et liens. Sections répétables Ajouter/Supprimer. Deux modèles : Moderne avec bandeau marine et titres bleus ; Professionnel ATS à une colonne et typographie sobre.

Aperçu HTML immédiat, téléchargement de PDF générés par ReportLab, texte sélectionnable, accents français, gestion des sauts de page et numérotation. Le modèle ATS est conçu pour une lecture textuelle simple ; sa compatibilité avec tous les logiciels ATS n’est pas garantie.

Versions enregistrées et chiffrées avec Fernet dans SQLite. Chargement d’une version puis sauvegarde d’une nouvelle version, sans écrasement de la précédente. Les données non sauvegardées restent en mémoire du navigateur. Pour les exports, le PDF est préparé en mémoire côté serveur et délivré sur une URL authentifiée, temporaire et à usage unique ; aucun fichier public permanent n’est créé.

Les PDF importés pour extraction doivent être lisibles, non chiffrés, de moins de 5 Mo et d’au plus 15 pages. L’extraction se fait localement avec pypdf. Pas d’OCR ou de mise en page RTL arabe dans cette livraison.

### Phase 4 — Matching local et Gemini

Sélection d’un CV enregistré ou import PDF, extraction locale de compétences, relecture des informations et champs de formation/projets/domaine/ville/type modifiables. Le profil fictif permet une démonstration sans API.

Le classement local utilise les cinq critères demandés : compétences 40 %, formation/domaine 25 %, expérience/projets 15 %, localisation 10 %, type d’opportunité 10 %. Les poids sont modifiables et leur somme est contrôlée. Contributions et composantes sont retournées par le serveur et visibles dans les cartes. Formation/projets utilisent une comparaison TF-IDF/cosinus locale ; le vocabulaire des compétences est contrôlé. Une ville inconnue produit zéro sur ce critère et une mention d’incertitude. Le score n’est jamais présenté comme une probabilité d’embauche.

Intégration du SDK officiel `google-genai`, modèle configurable et liste de modèles autorisés pour ce mode gratuit. Gemini peut extraire compétences/domaine d’un texte relu et rapprocher les compétences sur les huit offres de la présélection locale. JSON structuré puis validation locale : identifiants d’offres connus, compétence du candidat fournie, preuve textuelle présente dans l’annonce. Le score final reste calculé en Python ; aucune expérience n’est ajoutée au CV automatiquement.

Prévisualisation exacte de la transmission, filtre des coordonnées et consentement explicite ; changement du profil invalide le consentement précédent. Les noms/détails identifiants dans le texte libre doivent encore être supprimés manuellement par l’utilisateur. Timeout de 20 secondes, message sur quota/429/indisponibilité et fallback local. Aucun retry ou passage à un modèle payant automatique. Aucun cache persistant de données sensibles n’a été ajouté.

Les résumés et recommandations Gemini restent des propositions à vérifier. La validation du schéma et des citations limite les inventions sans démontrer la justesse sémantique du modèle.

### Phase 5 — Postulation et suivi

Sur les offres et les résultats de matching, Postuler ouvre un parcours connecté : détails, canal réellement disponible, choix d’une version de CV, aperçu PDF, sujet/message, récapitulatif et confirmation.

- Lien externe : ouverture de l’annonce réelle, sans changement automatique de statut ; l’utilisateur confirme ensuite avoir effectivement postulé.
- Aucun canal : enregistrement confirmé à préparer, statut Non envoyée.
- Email d’offre : disponible seulement si une relation explicite vérifiée et un contact validé correspondent à la même entreprise. Aucune relation Places/Stagiaires.ma n’a été inventée.
- Candidature spontanée depuis une entreprise : adresse connue choisie dans la fiche, vérification du contact et autorisation d’envoi confirmées par l’utilisateur.

Le destinataire SMTP est le contact validé, jamais automatiquement SMTP_USER. SMTP est désactivé par défaut. Timeout, TLS, PDF issu d’une version enregistrée, clé d’idempotence persistante, verrou transactionnel et historique de tentatives préviennent les répétitions. Les PDF identiques sont générés de façon déterministe pour stabiliser l’empreinte d’idempotence. Un état incertain après problème réseau/SQLite oblige à vérifier la boîte d’envoi ; aucune répétition n’est lancée automatiquement.

Le suivi conserve les statuts Non envoyée, Envoyée, Relancée, Entretien, Acceptée et Refusée, avec recherche, filtre, notes, offre, CV, source, contact, mise à jour et historique. Six indicateurs : total, envoyées, entretiens, acceptées, refusées et taux de réponse. La suppression physique a été volontairement désactivée afin de préserver les données historiques.

Définition du taux : **(Entretien + Acceptée + Refusée) / (Envoyée + Relancée + Entretien + Acceptée + Refusée)**, selon le statut actuel, et non un taux de lecture des courriels.

### Phase 6 — Analyses Dash réelles

Dash Python est intégré au serveur Flask via `Dash(server=server, url_base_pathname='/analytics/')`. Utilisation réelle de dcc.Dropdown, dcc.RadioItems, dcc.DatePickerRange, dcc.Graph, dcc.Tabs, Input, Output, State et callbacks.

Onglets par jeu de données, listes adaptées aux colonnes disponibles, secteur/stage/contrat/entreprise connue/période, barres/courbe/camembert/scatter/histogramme temporel. Les combinaisons inappropriées affichent une explication. Les compétences et quartiers inconnus ne sont pas inventés comme axes analytiques. Les changements d’onglet réinitialisent les filtres incompatibles.

KPI et qualité des données relus dans SQLite ; actualisation manuelle et toutes les minutes. CSV filtré avec protection contre les formules de tableur, export PNG via Plotly. L’ancienne représentation mélangeant emails/sites a été retirée ; les comptes de présence sont séparés et les secteurs utilisent leur propre population. La période limitée des offres est explicitée, sans présentation comme tendance annuelle.

### Phase 7 — Carte et stratégie de géolocalisation

Carte locale schématique, recherche, filtre secteur et quartier si connu, marqueurs exclusivement pour des coordonnées avec provenance/date. Fiches, site, adresse, téléphone, lien Maps et itinéraire. Mode de démonstration explicite avec trois points fictifs séparés des données réelles.

Aucune coordonnée n’a été ajoutée artificiellement aux entreprises d’origine. Aucun géocodage des 292 entreprises n’a été lancé. Les collecteurs futurs demandent Place ID, location et pagination Places ; provenance et date sont conservées dans l’export. Un import CSV manuel validé sauvegarde SQLite avant mise à jour. Le rapprochement des identités doit être vérifié humainement.

Google Maps JavaScript est intégré mais chargé uniquement après configuration ET accord sur la page. Clé navigateur distincte de Places ; aucune clé serveur exposée. Sans clé, les liens Maps et le mode local fonctionnent. Aucun bouton d’offres liées n’est affiché en l’absence de relation vérifiée.

## 3. Modifications SQLite

Migration numéro 1, additive, transactionnelle et idempotente (`PRAGMA user_version=1`). Sauvegarde SQLite avant les changements. Aucune utilisation de `to_sql(..., if_exists='replace')` dans l’import livré.

| Table | Ajouts |
|---|---|
| entreprises | place_id, latitude, longitude, geo_verified_at, geo_source, quartier, ville |
| offres | source, entreprise_nom, entreprise_ref, relation_verified, ville, recruitment_email, email_verified |
| candidatures | offre_id, offre_titre, cv_id, source, canal, updated_at, created_at, email_validated |
| cvs (nouvelle) | Métadonnées de version, modèle, contenu chiffré, dates |
| candidature_history (nouvelle) | Candidature, ancien/nouveau statut, date ; état initial documenté à la migration |
| send_attempts (nouvelle) | Clé unique d’idempotence, empreinte, statut, date, candidature liée et code d’erreur neutre |

Index sur offre de candidature et historique. Les anciennes colonnes et toutes leurs valeurs sont préservées. Les champs inconnus restent NULL/non vérifiés. Les dates d’historique initiales correspondent à la migration : elles ne prétendent pas reconstituer les transitions antérieures.

La base, les anciens Excel et les sauvegardes ne sont pas intégralement chiffrés. L’accès au dossier Windows et la sauvegarde privée restent nécessaires. Pour récupérer les nouveaux CV chiffrés : conserver ensemble SQLite et `private/cv.key`. Ne jamais supprimer cette clé pour réinitialiser le mot de passe.

## 4. Fichiers créés et modifiés

### Backend créé

`backend/__init__.py`, `config.py`, `db.py`, `security.py`, `validation.py`, `web.py`, `api.py`, `cv_service.py`, `matching.py`, `gemini_service.py`, `application_service.py`, `analytics.py`.

`backend/app.py` reste le point d’entrée, simplifié pour utiliser la fabrique d’application. Le fonctionnement métier ancien (consultation, statistiques et suivi) est conservé et étendu.

### Interface

Créés : `dashboard/cv.html`, `matching.html`, `carte.html`, `analyses.html`, `dashboard/js/ui.js`, `dashboard/css/design.css`, `analytics.css`.

Modifiés : `dashboard/index.html`, `entreprises.html`, `offres.html`, `candidatures.html`, `statistiques.html`, `envoyer_cv.html`, `dashboard/js/app.js`, `dashboard/css/style.css`. Les HTML chargent le composant commun ; les données et interactions sont gérées dans ui.js, avec API relative au même serveur.

### Scripts et données

Créés : `scripts/common.py`, `places_client.py`, `import_data.py`, `import_coordinates.py`.

Les 13 scripts historiques sont adaptés : main sans effets à l’import, chemins cohérents, secrets par environnement, garde explicite pour les collectes. `create_database.py` devient un point d’entrée vers l’import non destructif. Les variantes Places partagent le client paginé ; le filtre de ville du diagnostic est harmonisé. Les règles sectorielles utilisent des frontières de mots pour limiter les faux positifs de sous-chaînes, sans reclasser les données livrées.

Modifié : `database/stages_marrakech.db`, uniquement par migration additive. Conservés sans modification : classeurs, images, ancien PDF, base vide racine et documents historiques.

### Installation, tests et documentation

Créés : `requirements.txt`, `requirements-dev.txt`, `.env.example`, `.gitignore`, `README.md`, `LANCER_WINDOWS.bat`, `pytest.ini`, `tests/conftest.py`, `tests/test_application.py`, `tests/browser_smoke.py`, le présent rapport, sauvegarde de migration et rapports de validation sous `reports/`.

Le rapport d’audit initial est fourni dans `docs/RAPPORT_ANALYSE_PROJET.md` comme référence historique. Ses numéros de ligne décrivent l’ancienne version.

## 5. Tests et vérifications

### Tests automatisés : 52 réussites, aucun échec final

Exécutés sous Python 3.12, sur bases temporaires avec données fictives et connexions réseau bloquées. Gemini et SMTP sont simulés. Le fichier `reports/tests_automatises.xml` contient le résultat exploitable par un outil de tests.

Couverture : consultation ; validation JSON et champs ; protection auth/CSRF/origine ; conservation des cinq candidatures fictives après migration et répétition de migration ; mise à jour partielle/historique ; deux PDF extractibles et PDF long multipage ; fichiers invalides ; versions chiffrées ; export authentifié à usage unique ; matching local et poids ; SDK Gemini/JSON/preuves simulés ; extraction Gemini simulée ; absence de clés ; consentement et modification de profil ; quota 429 ; parcours externe/à préparer ; SMTP désactivé et simulé, destinataire, timeout, double envoi et panne incertaine ; routes/callbacks/exports Dash ; coordonnées de test et import ; XSS rendue comme texte ; scripts sans effets à l’import ; import Excel non destructif ; pagination Places simulée.

Deux avertissements de dépréciation proviennent des plugins de test tiers anyio/Dash de l’environnement : migration des API pytest avant pytest 10. Ils ne constituent pas des échecs fonctionnels.

Les premiers essais ont mis au jour deux problèmes désormais corrigés : une réponse de mock n’était pas actualisée dans un test de refus Gemini, et les métadonnées variables des PDF changeaient l’empreinte d’un même envoi. Les tests finaux vérifient le refus des compétences inventées et la génération déterministe.

### Parcours navigateur : 16 contrôles, aucune erreur JavaScript, aucun appel externe

Chrome/Playwright sur copie anonymisée : accueil et huit rubriques, rendu Dash et changement d’onglet, CV fictif/sauvegarde/export, matching local des 88 offres, choix de CV et confirmation à préparer, suivi actualisé, points cartographiques fictifs, charge XSS affichée comme texte, largeur mobile 390 px, menu et navigation clavier.

**Limite explicite :** Chrome automatisé ne peut pas écrire les téléchargements dans cet environnement Windows (« Failed - Insufficient permissions »). La même erreur a été reproduite sur une page indépendante ne contenant que le lien vers un PDF. L’événement de téléchargement est déclenché et l’endpoint livre un PDF correct ; l’ouverture/extraction et une sauvegarde de contrôle via le client HTTP sont vérifiées. L’enregistrement natif par Chrome n’est donc pas déclaré réussi ici. Cette limite est consignée dans `reports/validation_navigateur.json` et dans le test lui-même ; aucun réglage de sécurité système n’a été contourné.

### Vérifications sur les données livrées

- Comparaison de toutes les anciennes colonnes des tables entreprises/offres/candidatures : égalité intégrale avec l’original.
- Effectifs inchangés : 292 / 88 / 5 ; contrôle d’intégrité SQLite ok.
- Excel, PNG et PDF historiques identiques octet pour octet.
- Sources Python analysées et syntaxe JavaScript vérifiée.
- Absence de clé Google littérale dans les fichiers texte livrés.
- Deux modèles PDF anonymisés rendus avec Poppler et inspectés visuellement : accents, hiérarchie, marges et absence de chevauchement vérifiés.

## 6. Fonctions dépendant d’une configuration externe

| Service | Configuration | État de cette livraison |
|---|---|---|
| Gemini | GEMINI_API_KEY, GEMINI_MODEL, GEMINI_ENABLED, GEMINI_FREE_TIER_CONFIRMED | SDK/consentement/JSON/fallback implémentés ; tests simulés seulement |
| SMTP | SMTP_HOST/PORT/USER/PASSWORD, SMTP_ENABLED | Désactivé ; tests simulés, aucun vrai CV/courriel envoyé |
| Maps JavaScript | MAPS_BROWSER_KEY, MAPS_ENABLED | Intégration sur chargement consenti ; pas d’appel réel ; fallback local opérationnel |
| Collecte Places | GOOGLE_PLACES_API_KEY et commande --allow-external | Client partagé/pagination/provenance prêts ; aucune collecte effectuée |
| Stagiaires.ma | Commande de collecte explicitement autorisée | Collecteur conservé/amélioré ; contrat actuel non vérifié en ligne par un appel métier |

Les étapes détaillées figurent dans README. Aucun service payant n’a été activé, aucune facturation Cloud modifiée, aucun géocodage massif exécuté.

Documentation officielle consultée le 3 novembre 2026 : [tarification Gemini](https://ai.google.dev/gemini-api/docs/pricing), [SDK Google GenAI](https://googleapis.github.io/python-genai/), [intégration Dash](https://dash.plotly.com/reference), [Places Text Search New](https://developers.google.com/maps/documentation/places/web-service/text-search), [restrictions Maps](https://developers.google.com/maps/api-security-best-practices).

Le modèle Flash-Lite 3.5 est configuré pour le niveau gratuit documenté ; le logiciel ne peut pas vérifier la facturation attachée à une clé. Vérifier le compte et les tarifs avant toute activation. Les quotas gratuits peuvent évoluer et le contenu transmis au niveau gratuit peut être utilisé par Google pour améliorer ses produits. Maps/Places peuvent être facturables selon services/champs ; budgets d’alerte, quotas et restrictions doivent être configurés manuellement. Aucun tarif numérique n’est promis.

## 7. Fonctions non réalisées ou limites restantes

- Réécriture IA du résumé professionnel : option facultative non ajoutée. L’IA propose des pistes liées au matching sans modifier le CV automatiquement.
- Aucun entraînement de modèle supervisé, évaluation de pertinence sur corpus annoté, prévision annuelle ou garantie de recrutement.
- Pas de nouvelle source LinkedIn/ReKrute/Emploi.ma, pas de collecte réelle ou de contrôle de délivrabilité des emails.
- Pas de rapprochement automatique entre entreprises Google Places et IDs Stagiaires.ma. Les noms/contacts inconnus restent inconnus.
- Pas de géocodage automatique des entreprises existantes, de quartiers déduits ou de marqueurs inventés.
- OCR, arabe RTL, multiutilisateur, déploiement Internet et sauvegarde cloud non intégrés.
- Carte locale schématique sans fond de rues ; une vraie carte Google exige clé, activation et accord.
- La qualité des anciennes classifications et la disponibilité actuelle des offres n’ont pas été réévaluées par appels externes.
- Les sauvegardes historiques sur disque restent privées mais non intégralement chiffrées. Les nouveaux profils CV sont chiffrés ; le dossier des clés doit être sauvegardé et protégé.
- Le callback Dash relit SQLite sans nouvelle collecte ; un changement d’Excel seul ne met pas l’application à jour.

## 8. Commandes Windows de lancement

Depuis la racine du projet décompressé :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe backend\app.py
```

Puis ouvrir `http://127.0.0.1:5000` et créer votre mot de passe personnel. Ne pas écraser un fichier .env déjà configuré. Le projet démarre sans clés Gemini/Maps ni SMTP. Après installation, `LANCER_WINDOWS.bat` lance le même serveur.

Tests :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tests\browser_smoke.py
```

L’archive livrée contient le code modifié, la base préservée et les documents d’installation ; elle contient aussi vos données historiques. Elle est destinée à votre usage privé. L’environnement Python de développement et les identifiants fictifs des tests ne sont pas inclus comme configuration utilisateur.
