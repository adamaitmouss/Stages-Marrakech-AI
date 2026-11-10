# Rapport final — Stages Marrakech AI

**Phase 2 — audit, améliorations et validation**  
**Date : 3 novembre 2026**  
**Périmètre :** copie modernisée dans cette livraison. L’archive RAR d’origine et les fichiers de sauvegarde n’ont pas été modifiés.

## 1. Résultat

Le projet Flask/SQLite a été repris dans sa version modernisée existante, auditée, puis complété. Les améliorations de cette phase portent sur l’optimisation locale du CV pour une offre, la suppression confirmée des versions de CV non utilisées, l’affichage d’un niveau de correspondance, la validation des périodes numériques inversées et la priorisation/signalisation des offres selon leur date d’expiration.

La base livrée conserve **292 entreprises, 88 offres et 5 candidatures historiques**. La migration existante reste additive et sauvegarde la base avant ses changements. Les anciennes colonnes et valeurs des tables métier ont été comparées ligne par ligne à l’extraction d’origine lors de la livraison précédente ; les tests de migration répétée confirment aussi la conservation des candidatures.

## 2. Matrice d’audit initial et validation

| Fonctionnalité | État vérifié | Problème relevé | Amélioration ou traitement | Validation |
|---|---|---|---|---|
| Navigation et pages | Flask sert les pages depuis une origine commune | Le rendu visuel seul ne prouve pas le fonctionnement des parcours | API commune, composants d’interface et pages reliés aux routes | Tests de routes; 16 contrôles navigateur de la version antérieure; relance navigateur de cette phase bloquée avant l’ouverture de Chrome |
| Entreprises et offres | Lecture réelle depuis SQLite | Relations entreprise/offre inconnues; expiration non signalée à l’écran | Champs restent inconnus si non vérifiés; offres actives d’abord, expirées signalées, date illisible reste inconnue | Tests API, comptages et test de priorité active/expirée/inconnue |
| Création de CV | PDF ReportLab, deux modèles, sauvegarde chiffrée | Pas de suppression visible ni d’aide par offre | Suppression après confirmation si le CV n’est lié à aucune candidature; suggestions locales par offre | Tests de PDF, chiffrement, suppression, optimisation, dates et conservation du CV |
| Matching local | Fonctionne sans service externe | Score à expliquer sans le confondre avec une chance d’embauche | Compétences communes/absentes, pondérations, contributions, incertitude et repère faible/partiel/fort | Tests de classement, somme des contributions, poids et validations |
| Gemini | SDK officiel intégré, désactivé par défaut | Quotas, réponses invalides et transmission de données sensibles | Prévisualisation, consentement avec empreinte, schéma JSON, validation locale, timeout et fallback explicitement marqué local | Tests mockés uniquement; aucun appel réel |
| Candidatures | Suivi SQLite et parcours de préparation | Risque de double envoi ou de statut envoyé prématurément | Confirmation explicite, historique, idempotence, statut incertain et aucun canal inventé | Tests de préparation, SMTP mocké, destinataire et panne; aucun email réel |
| Analyses Dash | Dash intégré à Flask, callbacks Python et lectures SQLite | Les filtres et visualisations doivent respecter les colonnes réellement présentes | Filtres/dates adaptés au jeu choisi, KPI, CSV protégé contre formules et export PNG | Tests callback/export; Dash affiché dans le test navigateur antérieur |
| Carte | Coordonnées filtrées par provenance et date de vérification | Les entreprises d’origine n’ont pas toutes des coordonnées | Mode local, recherche, filtres, points de démonstration séparés et Maps facultatif/consenti | Tests avec coordonnées fictives; aucune coordonnée réelle inventée ou géocodée |
| Collecte | Scripts présents, déclenchement manuel | Quotas, doublons, bases remplacées et effets à l’import étaient des risques | Garde `--allow-external`, timeouts, pagination, imports incrémentaux et non destructifs | Tests sans réseau, pagination mockée et absence d’effets d’import |
| Sécurité | Accès local authentifié et contrôles d’écriture | Données CV et historiques sensibles | CSRF, même origine, CSP, validation, chiffrement des nouveaux profils, protection des chemins privés | Tests d’auth, CSRF, XSS, fichiers privés et validations; aucun accès Internet publié |

## 3. Architecture finale

- **Interface :** pages HTML, CSS et JavaScript natifs dans `dashboard/`; création de nœuds DOM textuels, composants communs, navigation responsive, thème clair/sombre, états d’attente et messages accessibles.
- **Serveur :** Flask dans `backend/app.py`, fabrique d’application dans `backend/web.py`, routes métier dans `backend/api.py`.
- **Données :** SQLite dans `database/stages_marrakech.db`, accès dans `backend/db.py`, migration additive/idempotente, sauvegarde préalable sous `backups/`.
- **PDF :** ReportLab et polices embarquées; extraction texte par pypdf avec limites de taille et de pages.
- **Matching local :** vocabulaire maîtrisé, alias, TF-IDF/cosinus pour textes, couverture des compétences et contributions pondérées explicables.
- **IA facultative :** SDK officiel `google-genai`, réponses structurées et contrôles locaux dans `backend/gemini_service.py`.
- **Analytique :** Dash et Plotly Python montés sur `/analytics/`, callbacks relisant SQLite.
- **Sécurité locale :** hachage du mot de passe, session, CSRF, clé persistante, chiffrement Fernet des versions de CV.

### Schéma de données métier

Les tables historiques `entreprises`, `offres` et `candidatures` sont conservées. La migration ajoute des colonnes géographiques/provenance aux entreprises, des champs de source/liaison/vérification aux offres, et les champs de suivi aux candidatures. Elle ajoute `cvs` (versions chiffrées), `candidature_history` (transitions) et `send_attempts` (idempotence et état d’envoi), avec index utiles. Les dates d’historique créées pour les anciennes candidatures désignent l’état au moment de la migration ; elles ne reconstruisent pas les transitions anciennes inconnues.

## 4. Fonctionnalités utilisables sans service externe

- Démarrer l’application Windows et créer un mot de passe local.
- Parcourir les entreprises et offres réellement enregistrées.
- Voir d’abord les offres dont la date d’expiration connue est active, et distinguer les expirées des dates non renseignées/illisibles.
- Créer, prévisualiser, sauvegarder et exporter des CV PDF modernes ou ATS.
- Charger, modifier et enregistrer une nouvelle version d’un CV existant; supprimer une version non référencée après confirmation.
- Comparer un CV enregistré à une offre locale : compétences repérées, compétences manquantes, extraits existants à mettre en avant et suggestions d’organisation. L’analyse ne modifie pas le CV.
- Classer localement les offres et examiner les composantes. Les repères de niveau décrivent la compatibilité textuelle estimée et ne prédisent pas le recrutement.
- Préparer une candidature, ouvrir une annonce externe et confirmer soi-même une candidature envoyée, consulter le suivi et son historique.
- Utiliser les analyses Dash sur les données SQLite et la carte schématique/démonstration locale.
- Importer des données par les scripts conçus à cet effet, sans remplacer les tables par une collecte vide.

## 5. Fonctionnalités dépendantes de configuration ou d’action manuelle

| Fonction | Préparation requise | Réalisé pendant cette phase |
|---|---|---|
| Gemini | `GEMINI_API_KEY`, `GEMINI_MODEL`, activation explicite et consentement après aperçu | Tests mockés; pas d’appel à Google |
| SMTP | Paramètres du fournisseur, destinataire vérifié, activation et double confirmation | Tests mockés; aucun courriel envoyé |
| Google Maps JavaScript | Clé navigateur distincte, restriction de clé/API/origines, activation et consentement | Documentation officielle vérifiée; aucun chargement réel |
| Places/collecte en ligne | Clé, conditions de stockage/attribution vérifiées et commande explicite | Aucun géocodage ni collecte lancés |
| Offre externe | Site réel accessible et action manuelle de postulation | Aucun statut « envoyé » sans confirmation utilisateur |

Au 3 novembre 2026, la documentation Google répertorie `gemini-3.5-flash-lite` comme modèle stable avec entrée/sortie standard au niveau gratuit. Les quotas et l’éligibilité dépendent du compte; le niveau gratuit peut utiliser le contenu pour améliorer les produits Google. L’application n’essaie pas de vérifier la facturation du compte.

La grille globale Maps publiée à la même date indique 10 000 événements gratuits par mois pour le SKU Dynamic Maps, puis des tarifs par paliers; le premier palier indiqué est de 7 USD par 1 000 événements. Places, itinéraires et autres SKU ont leurs propres unités et limites. Une alerte de budget n’est pas un plafond. Vérifier les pages Google et paramètres du compte avant toute activation.

Références officielles consultées : [modèle Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [tarifs Gemini](https://ai.google.dev/gemini-api/docs/pricing), [SDK Google Gen AI](https://googleapis.github.io/python-genai/), [tarifs Maps Platform](https://developers.google.com/maps/billing-and-pricing/pricing), [gestion des coûts et quotas Maps](https://developers.google.com/maps/billing-and-pricing/manage-costs), [restrictions des clés Maps](https://developers.google.com/maps/api-security-best-practices).

## 6. Matching et optimisation du CV

Le matching local donne à chaque offre un score indicatif de 0 à 100, somme des cinq contributions pondérées : compétences (40 % par défaut), formation/domaine (25 %), expérience/projets (15 %), ville (10 %) et type d’opportunité (10 %). La somme des poids doit être 100. Les compétences proviennent du texte disponible et d’un vocabulaire contrôlé; la similarité cosinus TF-IDF compare les textes de formation/domaine et d’expérience/projets. Les données manquantes ne sont pas complétées artificiellement. Une localisation inconnue ne crée aucun point. Le niveau de correspondance affiché est un repère éditorial du score, pas un résultat validé statistiquement.

Gemini peut annoter les huit offres qui précèdent déjà dans le classement local; le score reste calculé côté serveur. Le mode et son message indiquent si Gemini a effectivement répondu ou si les résultats sont restés locaux. Les suggestions de CV de cette phase sont séparées de Gemini et fonctionnent localement : elles réutilisent uniquement des compétences et passages trouvés dans le CV, montrent les lacunes comme compétences à vérifier et ne modifient aucune donnée.

## 7. Tests et éléments de preuve

### Tests automatisés

**56 tests réussis, 0 échec**, sur bases temporaires avec données fictives et appels réseau bloqués. Deux avertissements de dépréciation proviennent des plugins de test tiers anyio/Dash concernant pytest 10; ils ne correspondent pas à des échecs.

La couverture comprend migration répétée et sauvegarde, conservation des anciennes candidatures, authentification/CSRF, routes/pages, validation CRUD, priorisation/étiquetage de dates d’offres, CV chiffrés et PDF (deux modèles et document long), extraction et PDF invalide, suppression de CV, optimisation CV/offre sans modification du CV, dates inversées, matching, consentement Gemini/mock/quota/fallback, candidatures préparées, email SMTP mocké/idempotence/état incertain, callbacks Dash, filtres/exports, carte et coordonnées fictives, XSS, imports et collecte mockée.

Le rapport JUnit est fourni sous `reports/tests_automatises_phase2.xml`.

### Navigateur et rendu

La livraison précédente a réussi **16 contrôles Playwright** sur une copie anonymisée : navigation, pages principales, Dash, création/export PDF, matching, préparation de candidature, suivi, carte de démonstration, charge XSS et largeur mobile. Le rapport précédent note 0 erreur JavaScript et 0 appel réseau externe. Il précise aussi que Chrome ne pouvait pas enregistrer nativement un téléchargement dans cet environnement Windows; le flux HTTP PDF restait valide.

Pour cette phase, j’ai tenté de relancer Playwright afin de vérifier le nouveau panneau d’optimisation dans le navigateur. Le pilote Playwright est resté bloqué à `sync_playwright().start()`, avant même la tentative de lancement de Chromium et avant la première capture. Je ne déclare donc pas ce parcours visuel nouvellement retesté. L’API d’optimisation, la conservation du CV, le rendu JavaScript syntaxique et l’ensemble des 55 tests automatisés ont été vérifiés. Les captures conservées illustrent les pages de la livraison précédente, pas le nouveau panneau.

### Données et services

Aucun appel Gemini, Maps, Places, Stagiaires.ma ou SMTP réel n’a été fait. Les mock tests vérifient les branches de code, pas la disponibilité ou la facturation d’un compte externe. Aucun email n’a été envoyé. Aucune nouvelle donnée géographique n’a été introduite.

## 8. Sécurité et confidentialité

- Serveur local `127.0.0.1`, mode debug désactivé, compte personnel local unique.
- Cookies de session HttpOnly/SameSite, CSRF sur mutations, contrôle d’origine, CSP et absence de rendu des données par `innerHTML`.
- Les CV sauvegardés sont chiffrés en base. Conserver ensemble le fichier SQLite et `private/cv.key`; sans cette clé, les CV chiffrés ne sont pas récupérables.
- Les candidatures historiques, Excel et sauvegardes existantes ne sont pas chiffrés intégralement. Protéger le dossier Windows et les archives.
- Les anciennes clés Google trouvées dans les sources initiales ont été retirées du code distribué. Il reste indispensable de les révoquer/renouveler manuellement dans le compte Google; supprimer une clé des fichiers ne la révoque pas.
- L’application n’est pas une plateforme multiutilisateur ou une publication Internet; pas de déploiement HTTPS réalisé.

## 9. Fichiers livrés et modifiés dans cette phase

Améliorations ajoutées :

- `backend/api.py` : endpoint local d’optimisation CV/offre, erreurs 404 explicites pour la suppression d’un CV inexistant, statut/tri calculé selon la date d’expiration des offres.
- `backend/cv_service.py` : rejet des périodes numériques explicitement inversées.
- `dashboard/js/ui.js` : panneau d’optimisation CV/offre, action de suppression confirmée, repère de niveau de correspondance et étiquette Active/Expirée/Validité inconnue dans les cartes d’offres.
- `tests/test_application.py` : tests d’optimisation, non-modification du CV, suppression et périodes.
- `tests/browser_smoke.py` : contrôle de navigateur supplémentaire préparé, mais non validé dans cette session car Chrome n’a pas démarré.
- `README.md` : parcours ajoutés, conditions et prix Maps vérifiés, références officielles.
- `RAPPORT_FINAL_PROJET.md` : audit de phase, matrice et état de validation.

Le projet garde les documents d’installation, `.env.example` sans secrets, `requirements.txt`, tests et base originale migrée. L’archive de livraison exclut les clés privées, `.env`, environnements Python et caches.

## 10. Lancement et tests Windows

Depuis le dossier racine décompressé dans PowerShell :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe backend\app.py
```

Ouvrir `http://127.0.0.1:5000`, puis créer un mot de passe de 12 caractères minimum. Pour les tests :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tests\browser_smoke.py
```

## 11. Limites et suite possible

- Relancer une validation visuelle navigateur après rétablissement du lancement Chrome automatisé, en incluant le nouveau panneau CV.
- Ajouter OCR, arabe RTL, tests sur plusieurs navigateurs et procédures d’accessibilité approfondies.
- Évaluer le matching avec un jeu de pertinence annoté par des personnes; les scores restent heuristiques.
- Vérifier manuellement la réputation et la délivrabilité des emails et l’actualité des offres avant chaque candidature.
- Revoir les quotas, tarifs, règles d’attribution et politiques de confidentialité avant activation externe.
- Ajouter toute nouvelle source d’offres uniquement après vérification des conditions d’utilisation, sans contournement de protections.
