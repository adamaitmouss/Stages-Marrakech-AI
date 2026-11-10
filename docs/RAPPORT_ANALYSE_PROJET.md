# RAPPORT D’ANALYSE DU PROJET — Stages Marrakech

Date : 3 novembre 2026. Source : `C:\Users\HP\Desktop\Projet_Stages_Marrakech.rar`.

## 1. Présentation générale et périmètre

Le projet vise la recherche d’entreprises et d’opportunités professionnelles à Marrakech, leur analyse et le suivi des candidatures. Le code livré constitue un prototype de consultation et de gestion : collecte Google Places et Stagiaires.ma, fichiers Excel, base SQLite, API Flask et interface HTML/CSS/JavaScript.

L’intelligence actuellement implémentée est une classification par règles de mots-clés. Aucun modèle d’apprentissage automatique, moteur de recommandation ou modèle sémantique entraîné n’a été trouvé.

**Respect de la mission :** l’archive originale est restée intacte. Une copie a été extraite sous `work/Projet_Stages_Marrakech` pour lecture. Aucun fichier de cette copie n’a été modifié ou supprimé. Les essais d’écriture ont utilisé une base séparée, `work/audit_test.db`. Le présent rapport est le seul livrable ajouté. Aucun scraping réel, appel Google, appel Stagiaires.ma ou envoi SMTP n’a été effectué. Les secrets et les données personnelles des candidatures/CV ne sont pas reproduits.

Les documents internes ont été considérés comme des éléments descriptifs, sans exécuter leurs éventuelles instructions. Les sources prévues dans le cahier des charges ne sont pas nécessairement réalisées. Les références `fichier:ligne` ci-dessous sont relatives à la racine du projet extrait et correspondent aux sources de l’archive.

## 2. Arborescence des fichiers

```text
Projet_Stages_Marrakech/
├── backend/
│   ├── app.py
│   ├── generated_cv/
│   │   └── [un CV PDF nominatif existant]
│   └── uploads/                       [vide]
├── dashboard/
│   ├── index.html
│   ├── entreprises.html
│   ├── offres.html
│   ├── candidatures.html
│   ├── statistiques.html
│   ├── envoyer_cv.html
│   ├── css/style.css
│   └── js/app.js
├── database/stages_marrakech.db       [base utilisée par Flask]
├── stages_marrakech.db                [autre base, sans tables]
├── data_raw/
│   ├── base_stages_marrakech_classee.xlsx
│   ├── entreprises_marrakech_complet.xlsx
│   ├── offres_stages_brutes.xlsx
│   ├── offres_stagiaires_marrakech.xlsx
│   └── offres_stagiaires_toutes.xlsx
├── data_clean/
│   ├── entreprises_marrakech_clean.xlsx
│   ├── offres_stagiaires_marrakech_clean.xlsx
│   └── suivi_candidatures.xlsx
├── scripts/
│   ├── collect_entreprises.py
│   ├── collect_entreprises_complete.py
│   ├── extract_emails.py
│   ├── classifier_entreprises.py
│   ├── collect_offres_stagiaires.py
│   ├── collect_offres_marrakech.py
│   ├── audit_donnees.py
│   ├── nettoyage_donnees.py
│   ├── analyse_exploratoire.py
│   ├── generer_graphiques.py
│   ├── create_database.py
│   ├── create_candidatures_table.py
│   └── test_places_api.py
├── docs/
│   ├── cahier_des_charges.rtf
│   ├── config.json
│   └── configuration_api.md           [vide]
├── reports/
│   ├── rapport_audit.xlsx
│   └── graphs/
│       ├── emails.png
│       ├── offres_dates.png
│       ├── secteurs_barplot.png
│       ├── secteurs_pie.png
│       ├── sites_web.png
│       ├── types_contrat.png
│       ├── types_contrat_pie.png
│       ├── types_stage.png
│       └── types_stage_pie.png
├── logs/                             [vide]
└── presentation/                     [vide]
```

Aucun `requirements.txt`, `pyproject.toml`, fichier de verrouillage, README de démarrage, dossier de tests automatisés, migration ou fichier Power BI n’a été trouvé. Le nom du PDF est volontairement masqué dans cette arborescence.

## 3. Architecture et technologies

### 3.1 Communication entre les composants

```text
Google Places → collecte entreprises → Excel
Sites des entreprises → extraction regex des emails → Excel enrichi
Excel enrichi → classification par règles → Excel classé
Stagiaires.ma (API JSON) → collecte paginée → Excel offres
Excel bruts → nettoyage → Excel nettoyés
Excel nettoyés → import SQLite → API Flask → pages web / Chart.js
Excel nettoyés → analyse console et graphiques PNG
Formulaires web → API candidatures → SQLite
Formulaire CV → Flask → SMTP Gmail → insertion candidature
```

Ce schéma décrit les composants présents. **La chaîne complète n’est pas raccordée automatiquement** : certaines sorties sont écrites dans `data_clean`, tandis que les étapes suivantes lisent les équivalents dans `data_raw`. Aucun orchestrateur ne réalise ces transferts.

Les scripts ne s’importent pas mutuellement ; ils communiquent par fichiers. L’API lit SQLite, pas les Excel à chaque requête. Modifier un Excel ne rafraîchit donc pas automatiquement l’interface. Les candidatures web restent dans SQLite et ne sont pas synchronisées vers `suivi_candidatures.xlsx`.

### 3.2 Bibliothèques

| Usage | Dépendances observées |
|---|---|
| API | Flask, flask-cors, Werkzeug |
| Collecte | requests |
| Tableaux et Excel | pandas ; openpyxl nécessaire pour les `.xlsx` |
| Figures | matplotlib |
| Extraction | `re` ; BeautifulSoup importé dans `extract_emails.py`, mais inutilisé |
| Base et courriel | sqlite3, smtplib, email.message — bibliothèque standard |
| Autres imports standard | os, time, json, datetime |
| Navigateur | HTML, CSS, JavaScript natif, fetch, sessionStorage, Chart.js via CDN |

Aucune utilisation de Streamlit, Dash, Tkinter, scikit-learn ou d’un framework de front-end n’a été trouvée. Les versions requises ne sont pas documentées.

### 3.3 Configuration et points d’entrée

- Serveur : `backend/app.py:525–526`, lancement Flask en mode debug.
- Interface : `dashboard/index.html`, servie séparément de Flask. La route Flask `/` renvoie un texte, pas le tableau de bord.
- Adresse API codée en dur : `http://127.0.0.1:5000`, répétée dans les pages et `dashboard/js/app.js:1`.
- Base Flask : chemin construit depuis `__file__`, vers `database/stages_marrakech.db` (`backend/app.py:21–28`).
- SMTP : variables d’environnement `SMTP_USER` et `SMTP_PASSWORD`, Gmail, port 587 (`backend/app.py:10–14`). Pas de chargement de fichier `.env` dans le code.
- `docs/config.json` contient Marrakech, Maroc, un rayon de 15 000 et LinkedIn, ReKrute, Emploi.ma, Stagiaires.ma. **Aucun code ne lit ce fichier.** Le rayon et la liste des sources ne pilotent pas les collecteurs.
- `docs/configuration_api.md` est vide. Le cahier des charges évoque Power BI et Google Maps API ; aucune intégration Power BI ni API Maps distincte de Places n’a été trouvée. Les liens Maps viennent de Places.

### 3.4 Rôle de chaque script Python

| Script | Fonction réelle |
|---|---|
| `collect_entreprises.py` | Dix recherches Places, dédoublonnage sur le nom, export de cinq attributs dans `data_clean/entreprises_marrakech_complet.xlsx`. |
| `collect_entreprises_complete.py` | Dix-huit recherches Places, visite des sites et extraction d’emails, colonnes de suivi initiales, export `data_clean/base_stages_marrakech.xlsx`. |
| `extract_emails.py` | Autre extraction d’emails depuis le premier export ; produit `data_clean/entreprises_marrakech_emails.xlsx`. |
| `classifier_entreprises.py` | Lit `data_clean/base_stages_marrakech.xlsx`, classe par règles, exporte `data_clean/base_stages_marrakech_classee.xlsx`. |
| `collect_offres_stagiaires.py` | Diagnostic d’une page d’API ; affiche pagination, titres et identifiants de ville ; aucun export. |
| `collect_offres_marrakech.py` | Collecte paginée, filtre `ville=48360`, export `data_clean/offres_stagiaires_marrakech.xlsx`. |
| `audit_donnees.py` | Dimensions, types, manquants, doublons, URL/emails suspects des fichiers bruts sélectionnés ; écrit un résumé Excel. |
| `nettoyage_donnees.py` | Normalise textes et dates, retire des colonnes, dédoublonne, écrit les deux fichiers nettoyés. |
| `analyse_exploratoire.py` | Statistiques en console sur les fichiers nettoyés, sans sauvegarde. |
| `generer_graphiques.py` | Produit neuf PNG depuis les fichiers nettoyés. |
| `create_database.py` | Importe les deux Excel nettoyés dans SQLite en remplaçant entreprises et offres. |
| `create_candidatures_table.py` | Crée si nécessaire la table candidatures. |
| `test_places_api.py` | Réalise un véritable appel Google Places ; ce n’est pas un test unitaire hors réseau. |
| `backend/app.py` | Routes de lecture, statistiques, CRUD candidatures et transmission de CV par SMTP. |

Les scripts sont majoritairement exécutés au niveau global. Leur simple import peut déclencher une collecte ou écraser une sortie. Ils contiennent peu de fonctions réutilisables ; l’organisation repose surtout sur des blocs procéduraux. Le backend concentre toutes ses routes dans un seul fichier. Aucune classe métier n’est définie.

## 4. Fonctionnalités existantes et état

« Testée » désigne un essai local isolé, sans validation des services externes ou du rendu navigateur.

| Fonctionnalité | État | Preuve / limite |
|---|---|---|
| Consultation entreprises/offres | Opérationnelle côté API, testée | HTTP 200 ; 292 entreprises et 88 offres. |
| Filtres entreprises/offres | Implémentés, vérifiés par lecture | JavaScript en mémoire ; navigation non testée. |
| Collecte Google Places | Partiellement implémentée ; service actuel non vérifié | Code et exports présents ; pas de requête externe. |
| Extraction d’emails | Partiellement implémentée | Regex sur pages d’accueil ; erreurs masquées et adresses non validées. |
| Classification sectorielle | Implémentée par règles | Aucun modèle IA ; faux positifs possibles. |
| Collecte Stagiaires.ma | Partiellement implémentée ; service actuel non vérifié | API paginée ; paramètres de ville divergents. |
| Nettoyage/stockage | Implémentés ; chaîne complète incomplète | Fichiers lisibles ; ruptures de chemins entre étapes. |
| Analyse exploratoire | Opérationnelle sur les fichiers livrés, testée | Exécutée en mémoire avec chemins adaptés. |
| Graphiques PNG | Implémentés ; génération non relancée | Neuf fichiers présents et code lu. |
| Statistiques API | Opérationnelles, testées | Agrégations cohérentes avec les effectifs de base. |
| Suivi manuel des candidatures | Opérationnel sur données valides, testé | Ajout/modification/suppression sur copie ; validation insuffisante. |
| Envoi de CV | Non conforme à l’objectif | Destinataire fixé à `SMTP_USER`, adresse d’entreprise ignorée. SMTP non testé. |
| Génération automatique de CV | Absente du code livré | Présence d’un PDF uniquement. |
| LinkedIn/ReKrute/Emploi.ma | Collectes absentes | Noms dans configuration et cahier des charges uniquement. |

## 5. Fonctionnement de la recherche d’entreprises

Les collecteurs utilisent `POST https://places.googleapis.com/v1/places:searchText` et `textQuery`. Le FieldMask demande nom, adresse formatée, téléphone national, site web et lien Google Maps (`collect_entreprises.py:7–12`, version complète `:8–13`).

Le premier script utilise dix formulations sectorielles à Marrakech. Le second ajoute centres d’appel, cabinets comptables, agences web, startups, hôtels, agences de communication/voyage et bureaux d’étude. Il s’agit de recherches prédéfinies : aucun formulaire ne pilote Places, aucun rayon ou filtre géographique strict n’est appliqué.

Les réponses alimentent un DataFrame, puis un dédoublonnage exact sur `Nom`. Aucun identifiant Places stable n’est conservé. Les homonymes peuvent être fusionnés et les variantes orthographiques conservées. Aucune pagination Places, reprise, gestion des coûts/quotas ou actualisation incrémentale n’est codée. Les appels Google n’ont pas de timeout, retry ou `raise_for_status` ; le statut est affiché puis le JSON lu.

Dans la version complète, chaque site est visité avec un timeout de dix secondes. Une regex extrait les emails ; ils sont mis en minuscules, dédoublonnés et filtrés sur certains motifs d’images/exemples (`:107–144`). Le code ne parcourt pas systématiquement les pages Contact et ne vérifie ni délivrabilité ni pertinence RH. L’extracteur séparé filtre moins. Les exceptions des visites deviennent silencieusement des emails vides.

Les fichiers nettoyés contiennent 292 entreprises, dont 145 avec email (49,7 %) et 236 avec site (80,8 %). Une adresse présente n’est pas nécessairement un contact de recrutement validé. Ces observations ne prouvent pas une collecte actuelle réussie.

## 6. Fonctionnement de la recherche d’offres

La source réellement codée est l’API JSON publique de Stagiaires.ma. Aucun scraping HTML d’offres LinkedIn, ReKrute ou Emploi.ma n’est présent.

`collect_offres_marrakech.py:15–80` parcourt les pages avec limite de 20 et filtre `ville=48360`, s’arrête sur liste vide ou dernière page, et attend une seconde entre pages. Il contrôle les statuts non 200 et `success`, mais ne capture pas les exceptions réseau/JSON. Si `totalPages` manque, il utilise la page courante et s’arrête, au risque de tronquer les résultats.

Champs collectés (`:57–68`) : ID, titre, description, type de contrat/stage, identifiants de ville et entreprise, publication/expiration, lien annonce et lien public. **Le nom de l’entreprise et celui de la ville ne sont pas résolus.** Les 88 offres brutes ciblées ont toutes `Ville ID=48360` ; l’association actuelle de cet identifiant à Marrakech n’a pas été vérifiée auprès du service.

Le diagnostic utilise `ville_id=3460` (`collect_offres_stagiaires.py:5–8`) : nom du paramètre et identifiant diffèrent du collecteur principal. Le fichier toutes villes contient 1 679 offres, dont 245 avec la valeur 48360, contre 88 dans le fichier ciblé. Les paramètres et l’historique exact de production ne sont pas tracés ; la cause de cet écart ne peut pas être affirmée.

Le dédoublonnage se fait sur ID. Il n’existe pas de mise à jour incrémentale, historique, détection des annonces retirées ou filtre d’expiration. Les conditions actuelles des sites et quotas n’ont pas été vérifiés en ligne. Le code ne montre pas de contrôle robots.txt pour les sites visités, ni gestion de 429/Retry-After. Aucun contournement de protection n’est implémenté.

## 7. Pipeline de collecte, nettoyage et stockage

### 7.1 Données réellement inspectées

| Fichier | Lignes × colonnes | Observations |
|---|---:|---|
| `data_raw/entreprises_marrakech_complet.xlsx` | 176 × 5 | 6 téléphones et 29 sites manquants. |
| `data_raw/base_stages_marrakech_classee.xlsx` | 292 × 9 | Date candidature vide sur les 292 lignes. |
| `data_raw/offres_stages_brutes.xlsx` | 0 × 0 | Classeur vide. |
| `data_raw/offres_stagiaires_marrakech.xlsx` | 88 × 11 | 22 types de stage manquants ; une valeur de ville. |
| `data_raw/offres_stagiaires_toutes.xlsx` | 1 679 × 10 | 593 types de stage, 69 villes, 26 liens annonce, 3 expirations et 1 contrat manquants ; pas de description. |
| `data_clean/entreprises_marrakech_clean.xlsx` | 292 × 7 | 10 téléphones, 56 sites et 147 emails manquants. |
| `data_clean/offres_stagiaires_marrakech_clean.xlsx` | 88 × 10 | 22 types de stage manquants ; ID uniques. |
| `data_clean/suivi_candidatures.xlsx` | 1 × 10 | Ligne largement vide, seul le statut renseigné ; pas l’historique web. |
| `reports/rapport_audit.xlsx` | 2 × 5 | Résumé d’audit de données existant. |

Les classeurs inspectés n’ont pas de doublons complets. Les noms normalisés des entreprises nettoyées sont uniques dans ce jeu, ce qui ne garantit pas l’unicité métier entre variantes de noms.

### 7.2 Nettoyage codé

`nettoyage_donnees.py` retire Date candidature et Statut des entreprises (`:40–49`), applique `str.strip`, remplace certains marqueurs textuels par des valeurs manquantes, met les emails en minuscules et retire les doublons complets. Pour les offres : retrait de Ville ID, normalisation des chaînes, conversion des dates avec `errors='coerce', utc=True`, suppression du fuseau après conversion UTC, dédoublonnage sur ID et tri décroissant par publication (`:142–224`).

Limites : dates invalides transformées en NaT sans bilan de rejets, absence de validation des identifiants et champs obligatoires, contrôle métier des emails/téléphones insuffisant, aucune normalisation des noms/URL. Les opérations `.str` supposent des colonnes textuelles homogènes. Retirer Ville ID supprime un moyen de recontrôler le périmètre.

### 7.3 Ruptures de chemins

- La classification écrit `data_clean/base_stages_marrakech_classee.xlsx` (`classifier_entreprises.py:124–126`) ; audit et nettoyage lisent l’équivalent de `data_raw` (`audit_donnees.py:9`, `nettoyage_donnees.py:12`).
- Le collecteur d’offres écrit `data_clean/offres_stagiaires_marrakech.xlsx` (`:97`) ; audit et nettoyage lisent celui de `data_raw` (`audit_donnees.py:10`, `nettoyage_donnees.py:13`).
- Les intermédiaires `data_clean/base_stages_marrakech.xlsx`, `base_stages_marrakech_classee.xlsx`, `entreprises_marrakech_complet.xlsx` et `entreprises_marrakech_emails.xlsx` ne sont pas livrés à ces emplacements. Certains sont normalement produits par les collecteurs nécessitant des accès externes.
- Les chemins relatifs supposent un lancement depuis la racine. Les dossiers ne sont pas systématiquement créés avant les exports. Aucune automatisation ne raccorde les étapes.

### 7.4 SQLite et cohérence des entités

`database/stages_marrakech.db` contient 292 entreprises, 88 offres et 5 candidatures. Les deux bases passent `PRAGMA integrity_check`. La base homonyme racine ne contient aucune table et n’est pas utilisée par Flask.

Les colonnes entreprises/offres correspondent aux Excel nettoyés. `to_sql(..., if_exists='replace')` remplace ces deux tables (`create_database.py:32–43`), sans upsert ou historique. La table candidatures n’est pas visée par ces remplacements.

Entreprises et offres n’ont pas de clé primaire déclarée. `Entreprise ID` provient de Stagiaires.ma ; les entreprises Places n’ont aucun identifiant correspondant. **Aucune jointure fiable n’existe entre ces sources.** Le front-end affiche donc l’identifiant brut.

La table candidatures possède un ID autoincrémenté et des champs texte : entreprise, secteur, email, téléphone, date, statut, commentaire. Aucune clé étrangère, obligation SQL de remplir ces champs, unicité métier ou liste de statuts imposée.

## 8. Analyses et visualisations disponibles

L’analyse exploratoire calcule les secteurs, types de stage/contrat, dix identifiants d’entreprise les plus présents, volumes par date et présence d’emails/sites. Elle a été exécutée sans erreur sur les Excel livrés, avec chemins adaptés en mémoire seulement.

Les neuf PNG représentent secteurs (barres/camembert), stages (barres/camembert), contrats (barres/camembert), emails, sites et évolution des publications. Leur présence et le code sont vérifiés ; leur rendu et leur concordance visuelle avec les données actuelles n’ont pas été examinés. La génération n’a pas été relancée.

L’API statistiques retourne :

- 292 entreprises, 88 offres, 11 secteurs, 145 entreprises avec email et 236 avec site.
- Secteurs : Informatique 98, Autre 83, Hôtellerie 22, Tourisme 19, Construction 18, Comptabilité 15, Industrie 14, Logistique 11, Marketing 8, RH 2, Commerce 2.
- Contrats : Stage 75, CDI 10, Premier Emploi 2, CDD 1.
- Stages : fonctionnel 33, pré-embauche 26, non renseigné 22, fin d’études 7.

Les publications vont du 27 août au 25 septembre 2026. Les expirations enregistrées vont du 27 novembre au 25 décembre 2026 : aucune des 88 offres n’est expirée selon la base au 3 novembre 2026. Cela ne prouve pas que les annonces restent accessibles ou ouvertes.

Chart.js affiche secteurs en barres, stages en camembert, contrats en barres et présence des contacts en anneau. **Cet anneau mélange deux répartitions**, email et site : ses quatre valeurs totalisent 584, deux fois 292 (`statistiques.html:399–434`). Les parts ne représentent donc pas chacune une part du parc d’entreprises. Deux graphiques ou un autre encodage seraient préférables.

Aucune analyse de compétences, salaires, similarité CV/offre, causalité ou prévision n’a été trouvée. Aucun filtre analytique dédié n’est présent dans la page statistiques.

## 9. Interface utilisateur existante

Six pages statiques, JavaScript natif et une feuille CSS de 704 lignes avec plusieurs règles d’adaptation à la largeur d’écran.

| Page | Interactions |
|---|---|
| `index.html` | Accueil, navigation et quatre indicateurs chargés par `js/app.js`. |
| `entreprises.html` | Recherche par nom, filtre secteur, compteur, coordonnées, liens site/Maps/mailto et bouton CV si email présent. |
| `offres.html` | Recherche dans le titre, filtres stage/contrat, compteur et cartes avec description/date/lien. |
| `candidatures.html` | Ajout, historique, changement de statut via prompt et suppression après confirmation. |
| `statistiques.html` | Indicateurs et quatre graphiques Chart.js. |
| `envoyer_cv.html` | Entreprise sélectionnée, sujet, message, PDF, bouton désactivé pendant la requête et résultat. |

L’entreprise est transférée à la page CV par `sessionStorage` (`entreprises.html:306–313`), sans session serveur ou compte utilisateur. Le formulaire transmet l’email (`envoyer_cv.html:258–260`), ensuite ignoré par Flask.

Les filtres agissent dans le navigateur sur les listes complètes ; l’API n’a ni pagination ni filtrage. Les descriptions intégrales alourdissent les transferts et le rendu lorsque le jeu grandit.

Le HTML est construit via `innerHTML` avec des données externes ou saisies non échappées : risque d’injection HTML/XSS. Le bouton CV place `JSON.stringify(entreprise)` dans un attribut JavaScript délimité par apostrophes (`entreprises.html:245–247`). JSON.stringify ne protège pas les apostrophes pour ce contexte HTML. Au moins 19 fiches avec email comportent une apostrophe dans le nom ou l’adresse : défaut concret dans les données, pouvant casser le bouton. Le clic n’a pas été testé dans un navigateur.

Les contrôles HTML required/type existent sur certains champs, sans remplacer la validation serveur. Le rendu, l’accessibilité, les interactions et le comportement mobile n’ont pas été testés visuellement.

## 10. Suivi des candidatures et envoi de CV

### 10.1 Suivi manuel

GET/POST `/api/candidatures`, PUT/DELETE `/api/candidatures/<id>`. Les écritures SQL utilisent des paramètres : aucune concaténation directe des saisies dans ces requêtes n’a été observée.

Statuts proposés : Non envoyée, Envoyée, Relancée, Entretien, Acceptée, Refusée (`candidatures.html:142–163`). L’API accepte n’importe quelle valeur. Le statut initial À contacter du collecteur entreprises n’est pas harmonisé avec cette liste.

La modification web recharge toutes les candidatures, trouve l’objet, change son statut et le renvoie entier (`candidatures.html:573–643`). PUT remplace tous les champs : les champs absents deviennent NULL. Aucune mise à jour partielle protectrice, historique de transitions, relance programmée ou relation à une offre.

### 10.2 Envoi de CV

`backend/app.py:399–520` contrôle entreprise, présence du fichier et extension PDF, construit le message et lit la pièce jointe en mémoire, puis utilise STARTTLS et Gmail. Après succès SMTP, il ajoute une candidature Envoyée.

**Défaut majeur : `email_destinataire = SMTP_USER` à la ligne 402.** L’adresse entreprise transmise par l’interface n’est pas lue. Le CV serait envoyé au compte expéditeur et ce compte serait enregistré comme contact de candidature. Cette conclusion découle du code ; aucun courriel réel n’a été envoyé.

Pas de taille maximale définie, validation du PDF limitée à son extension côté serveur, pas de timeout SMTP, authentification de route ou idempotence. Si SMTP réussit puis que SQLite échoue, l’API annonce une erreur alors que le courriel est parti ; une nouvelle tentative peut le renvoyer. `str(e)` est retourné au client en cas d’erreur.

Le dossier uploads est créé mais le fichier n’y est pas sauvegardé par cette route. Le dossier generated_cv n’est pas utilisé par le code d’envoi ; aucun générateur de CV n’est présent.

## 11. Résultats des vérifications et tests

### 11.1 Méthode

Python local 3.12. Sources analysées via AST sans `.pyc`. Classeurs lus ; bases inspectées en lecture seule. Flask chargé depuis le texte dans un espace mémoire isolé, sans lancer le serveur ; création de dossier neutralisée pendant ce chargement. Connexions socket bloquées pendant les essais des routes. Toutes les écritures fictives ont visé une sauvegarde SQLite séparée.

Les empreintes SHA-256 de tous les fichiers extraits avant et après les essais étaient identiques. Les chemins de l’analyse exploratoire ont été adaptés dans une chaîne en mémoire, sans édition du script.

### 11.2 Résultats observés

| Vérification | Résultat |
|---|---|
| Syntaxe de 14 fichiers Python | 14 réussites ; ne garantit pas l’absence d’erreurs d’exécution. |
| Modules locaux | Flask, flask-cors, pandas, openpyxl, requests, bs4 et matplotlib disponibles ; aucune installation. |
| Lecture des 9 classeurs | Réussie ; feuilles, colonnes, doublons et manquants inspectés. |
| Intégrité des 2 bases | ok ; base racine sans tables. |
| GET `/` et `/test-db` | HTTP 200. |
| GET entreprises/offres/candidatures | HTTP 200 ; 292/88/5 éléments. |
| GET statistiques | HTTP 200 ; chiffres du chapitre 8. |
| POST candidature fictive valide | HTTP 201 sur copie de test. |
| PUT candidature fictive | HTTP 200 ; requête partielle acceptée, tous les champs sont affectés selon le SQL. |
| DELETE candidature fictive | HTTP 200 sur copie de test. |
| PUT/DELETE ID absent | HTTP 404. |
| POST `{}` | HTTP 201 : candidature vide acceptée, défaut confirmé. |
| POST JSON null ou liste | HTTP 500 : défaut de validation du corps confirmé. |
| POST CV sans configuration et sans champs | HTTP 400 ; branche de rejet seulement. |
| Origine CORS fictive sur lecture des candidatures | Origine autorisée par la réponse ; politique large confirmée. |
| Classification isolée sur exemple synthétique | Exécution réussie ; précision non mesurée. |
| Analyse exploratoire | Exécution réussie, 103 lignes de sortie console. |
| Conservation des fichiers extraits | Empreintes identiques après essais. |

### 11.3 Non vérifié et raisons

- Google Places, sites d’entreprises et Stagiaires.ma : appels externes exclus par la demande ; clés, coûts, quotas, disponibilité et contrat actuel inconnus.
- SMTP Gmail : aucun envoi ; identifiants et délivrabilité non vérifiés.
- Interface : lecture HTML/JS/CSS sans navigateur ; rendu, clics et filtres non testés en interaction.
- PNG/PDF : présence inventoriée ; contenu visuel non audité et données du CV non extraites.
- Scripts d’import, nettoyage, audit exporteur et graphiques : code lu, exécution sur le projet exclue car elle écrit/remplace des fichiers.
- Charge, concurrence, déploiement et accessibilité : non testés.

### 11.4 Installation et exécution futures

Procédure déduite du code, sans installation ni démarrage de serveur pendant l’audit. Depuis la racine, dans PowerShell :

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install flask flask-cors pandas openpyxl requests beautifulsoup4 matplotlib
.\.venv\Scripts\python.exe backend\app.py
```

Dans un deuxième terminal, depuis la même racine :

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --bind 127.0.0.1 --directory dashboard
```

Ouvrir `http://127.0.0.1:8000/index.html`. La base livrée permet la consultation sans collecte ni recréation des tables. Les versions n’étant pas fixées, ces commandes ne constituent pas un environnement reproductible validé. La version Python minimale n’est pas déclarée.

Pour reconstruire les données : collecte/enrichissement, classification, audit, nettoyage, import SQLite, création candidatures, analyses. **Cette suite n’est pas exécutable telle quelle sans résoudre les chemins du chapitre 7.** `test_places_api.py` réalise un vrai appel Google. Corriger l’envoi de CV avant de configurer et d’utiliser SMTP.

## 12. Problèmes détectés avec gravité

Critique : secret exposé à traiter immédiatement. Élevée : fonction centrale incorrecte ou intégrité/confidentialité compromise dans les conditions décrites. Moyenne : fiabilité, qualité ou maintenabilité. Faible : défaut local mineur. Flask écoute par défaut sur la boucle locale ; l’absence de protection ne signifie pas une exposition actuelle à Internet.

| ID | Gravité | Emplacement | Problème et conséquence |
|---|---|---|---|
| P01 | Critique | `scripts/collect_entreprises.py:5`, `collect_entreprises_complete.py:6`, `test_places_api.py:4` | Clé Google littérale dans les sources distribuées. Validité/restrictions inconnues ; rotation et contrôle du compte recommandés. Valeur jamais reproduite ici. |
| P02 | Élevée | `backend/app.py:402` ; `envoyer_cv.html:258–260` | Destinataire fixé au compte SMTP, entreprise ignorée. |
| P03 | Élevée | `backend/app.py:18,140–291,399` | API sans authentification et CORS large ; lecture/modification des candidatures et sollicitation SMTP possibles par qui peut atteindre le service. |
| P04 | Élevée | `entreprises.html:196–247`, `offres.html:241–278`, `candidatures.html:363–396` | Données via innerHTML, URL non validées et événements inline : risque d’injection HTML/XSS. |
| P05 | Élevée | `entreprises.html:247` | JSON dans attribut délimité par apostrophes ; données avec apostrophes présentes, bouton CV susceptible d’être cassé. |
| P06 | Élevée | `backend/app.py:166–174,220–244` | JSON non validé : objet vide accepté, null/liste produisent 500 ; PUT partiel efface les champs omis. |
| P07 | Élevée | `classifier_entreprises.py:124–126`, `collect_offres_marrakech.py:97`, `nettoyage_donnees.py:12–13` | Sorties/entrées incohérentes ; reconstruction incomplète ou réutilisation de données anciennes. |
| P08 | Moyenne | `collect_entreprises.py:34–42`, `collect_entreprises_complete.py:45–53`, `test_places_api.py:18–27` | Pas de timeout Google ni traitement structuré des échecs HTTP/JSON et quotas. |
| P09 | Moyenne | `collect_entreprises.py:58–62`, `collect_entreprises_complete.py:72–76`, `collect_offres_marrakech.py:84–89` | Collecte vide : DataFrame sans colonnes, dédoublonnage Nom/ID susceptible de lever KeyError. |
| P10 | Moyenne | `collect_offres_stagiaires.py:5–8`, `collect_offres_marrakech.py:13,19–22,72` | Ville et paramètre divergents ; arrêt prématuré si pagination absente. |
| P11 | Moyenne | `classifier_entreprises.py:13–27,117–119` | Sous-chaînes larges, notamment it, recherchées dans nom/site/adresse ; faux positifs (capital contient it), priorité de règles sans évaluation. |
| P12 | Moyenne | `create_database.py:32–43` | Remplacement intégral des tables entreprises/offres, sans historique ou migration. |
| P13 | Moyenne | `create_database.py:18–43`, `create_candidatures_table.py:10–26` | Pas de relations entre sources, ni contraintes métier ou index dédiés. |
| P14 | Moyenne | `statistiques.html:399–434` | Anneau additionnant deux répartitions de la même population. |
| P15 | Moyenne | `backend/app.py:425,450,463–477,483–519` | PDF : extension seule, taille non bornée ; SMTP sans timeout/idempotence et absence d’atomicité envoi/enregistrement. |
| P16 | Moyenne | `backend/app.py:513–519,526` | Détails d’erreur exposés et debug actif au lancement direct, à changer avant mise en ligne. |
| P17 | Moyenne | `extract_emails.py:47–48`, `collect_entreprises_complete.py:147–148` | Exceptions silencieuses : absence d’email et erreur de visite indiscernables. |
| P18 | Moyenne | `nettoyage_donnees.py:178–188`, `generer_graphiques.py:206–208` | Dates invalides sans bilan ; conversion graphique moins tolérante aux futurs fichiers mal formés. |
| P19 | Moyenne | `backend/app.py:91–105,119–133` ; filtres des pages | Retour et rendu complets, sans pagination ; coût croissant avec le volume. |
| P20 | Moyenne | Scripts à chemins relatifs ; manifeste absent | Dépendance au dossier courant, versions non fixées et absence de tests automatisés. |
| P21 | Faible | `extract_emails.py:4`, variantes de collecte et CSS | Import inutilisé, extraction/collecte répétées, quelques styles redéfinis. |
| P22 | Faible | `docs/config.json`, `docs/configuration_api.md`, base racine | Configuration inactive, documentation vide et base homonyme source de confusion. |

Points positifs : SQL paramétré, chemin de base Flask robuste, ID absents traités en 404, timeouts des visites et de Stagiaires.ma, STARTTLS et secrets SMTP par environnement, conversion UTC explicite et séparation pages/API/données.

## 13. Fonctionnalités absentes ou incomplètes

- Collecte multisource annoncée, configuration dynamique du périmètre et orchestration complète.
- Rapprochement entreprises/offres et affichage du nom d’employeur dans les offres.
- Recherche géographique réelle, filtres date/expiration et mises à jour incrémentales.
- Doublons entre sources, contrôles de qualité bloquants et provenance datée.
- Authentification, séparation des utilisateurs et protection des données de candidature.
- Relances automatiques, historique des statuts et synchronisation du classeur de suivi.
- IA évaluée, recommandations, extraction de compétences et recherche sémantique.
- Génération du CV et connexion Power BI : aucun code trouvé.
- Déploiement, sauvegardes automatisées, intégration continue, logs structurés et tests automatisés : non trouvés.

## 14. Améliorations recommandées — non réalisées

Difficulté : faible = changement local ; moyenne = plusieurs composants et validation ; élevée = nouvelles données, architecture ou évaluation. Les nouveaux fichiers mentionnés sont des propositions futures.

### 14.1 Corrections urgentes

| Proposition | Intérêt | Difficulté | Fichiers concernés |
|---|---|---|---|
| Renouveler la clé et utiliser l’environnement ; restreindre son usage côté fournisseur | Protéger le compte et éviter la redistribution | Faible côté code, action externe nécessaire | Les 3 scripts contenant la clé ; documentation API |
| Utiliser/valider le destinataire entreprise et tester avec SMTP simulé | Restaurer la fonction CV et l’exactitude du suivi | Faible à moyenne | `backend/app.py`, `envoyer_cv.html` |
| Rendu DOM sûr, événements addEventListener et validation des URL | Réduire XSS et corriger le bouton CV | Moyenne | Pages entreprises/offres/candidatures |
| Valider objets JSON, champs, dates et statuts ; définir PUT/PATCH | Éviter lignes vides, 500 et effacement involontaire | Moyenne | `backend/app.py`, `candidatures.html` |
| Harmoniser entrées/sorties et désigner une seule base | Reconstruction fiable | Moyenne | Collecteurs, classification, audit, nettoyage, imports |
| Protéger les routes, limiter CORS et désactiver debug hors développement | Protéger les candidatures et l’envoi avant partage réseau | Moyenne | `backend/app.py`, pages et documentation |

### 14.2 Améliorations techniques et fonctionnelles

| Proposition | Intérêt | Difficulté | Fichiers concernés |
|---|---|---|---|
| Dépendances versionnées et guide de démarrage | Installation reproductible | Faible | Futur manifeste/README ; documentation API |
| Chemins ancrés sur la racine et fonctions main | Imports/tests sans effets de bord | Moyenne | Tous les scripts |
| Clients HTTP communs, timeouts, retry bornés, pagination et logs | Fiabilité des collectes | Moyenne | Collecteurs, extraction, futur module commun |
| Tests de réponses simulées, erreurs, collectes vides et doublons | Régression détectée sans appel externe | Moyenne | Futurs tests ; collecteurs et API |
| Identifiants source, provenance, date de collecte et upsert | Actualisation traçable | Moyenne à élevée | Collecteurs, import SQLite, schéma |
| Référentiel entreprises et rapprochement explicable des sources | Relier offres, contacts et candidatures | Élevée | Schéma, collecteurs et pages |
| Contrôles de qualité et rapport des rejets | Distinguer valeur absente, invalide et erreur de collecte | Moyenne | Audit, nettoyage et extraction |
| Deux graphiques email/site et filtres analytiques de dates | Indicateurs interprétables | Faible à moyenne | `statistiques.html`, API |
| Pagination et recherche serveur | Réduire transferts et rendu | Moyenne | API, pages entreprises/offres |
| Limites PDF, validation contenu, timeout et idempotence SMTP | Fiabiliser l’envoi | Moyenne | `backend/app.py`, `envoyer_cv.html` |
| Statuts harmonisés, offre ciblée, historique et relance manuelle | Suivi cohérent | Moyenne | Table candidatures, API et page |

### 14.3 Fonctionnalités pour une soutenance Data Science/IA

| Proposition | Intérêt et validation | Difficulté | Fichiers potentiels |
|---|---|---|---|
| Classification supervisée comparée aux règles | Jeu annoté, précision/rappel/F1 par secteur, analyse des erreurs ; ambition adaptée aux 292 entreprises | Moyenne à élevée | Classification, futur module/notebook et jeu annoté |
| Extraction de compétences et regroupement thématique | Expliquer les compétences demandées ; contrôler manuellement un échantillon et comparer à une approche simple | Moyenne | Nettoyage, futur module NLP, API et statistiques |
| Classement CV/offres explicable | Montrer compétences communes/manquantes ; évaluer la pertinence sur jugements humains et minimiser les données CV | Élevée | Futur moteur de recommandation, API et nouvelle page |
| Carte et exploration sectorielle | Lecture territoriale ; nécessite coordonnées fiables absentes du schéma actuel | Moyenne | Places, schéma et page entreprises |
| Tableau de bord du parcours de candidature | Délais/conversions par statut ; nécessite historique et données suffisantes | Moyenne | API, schéma candidatures, statistiques |
| Démonstration hors réseau avec données anonymisées | Soutenance stable sans quotas/API/SMTP, avec provenance et limites documentées | Moyenne | Futurs jeux de démo, simulations, tests et README |

Ne pas présenter la courbe de 88 offres comme une prévision du marché. Une composante IA devra séparer entraînement et évaluation et rendre ses limites visibles. Aucun de ces développements n’a été réalisé.

## 15. Fichiers à modifier en priorité lors de la prochaine phase

1. `scripts/collect_entreprises.py`, `collect_entreprises_complete.py`, `test_places_api.py` : secrets et robustesse HTTP ; rotation à traiter côté fournisseur.
2. `backend/app.py` : destinataire CV, validation, accès, erreurs, debug et limites d’envoi.
3. `dashboard/entreprises.html`, `offres.html`, `candidatures.html` : rendu sûr, bouton CV et gestion des erreurs.
4. `scripts/classifier_entreprises.py`, `collect_offres_marrakech.py`, `audit_donnees.py`, `nettoyage_donnees.py` : chemins et chaîne vérifiables.
5. `scripts/create_database.py`, `create_candidatures_table.py` : schéma, relations, contraintes et migrations ; préserver les candidatures réelles.
6. `dashboard/statistiques.html` : graphique de présence et indicateurs.
7. `dashboard/envoyer_cv.html`, `dashboard/js/app.js` et autres pages : configuration API commune et cohérence des formulaires.
8. `docs/config.json`, `docs/configuration_api.md`, futurs README/manifeste/tests : configuration active et reproduction documentée.

Cet ordre reste une proposition. Aucun fichier du projet n’a été modifié pendant l’audit.

## 16. Conclusion et état général

Le projet possède un socle concret : données exploitables, API locale de consultation, suivi de candidatures testé et interface web développée. Les résultats locaux confirment le fonctionnement de la base principale et des routes essentielles sur les données livrées.

Il reste un **prototype à consolider** : chaîne de collecte non entièrement reproductible, CV dirigé vers la mauvaise adresse, clé Google dans le code et validation/protection insuffisantes. Collectes et SMTP n’ont pas été validés en conditions réelles. L’interface a été étudiée par lecture, sans test navigateur.

La prochaine phase devrait traiter secrets, envoi, sécurité et cohérence du pipeline, puis stabiliser schéma et tests, avant d’ajouter une IA évaluée. Ce rapport peut être transmis avec l’archive à un futur intervenant ; il distingue code observé, tests effectués et limites de vérification.
