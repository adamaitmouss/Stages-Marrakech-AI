# Sources de données et collecte

## État réellement constaté

Le registre exécuté par `backend/collectors/catalog.py` sépare l'accès technique, la permission de consultation, le stockage et le réaffichage. Dans la base privée contrôlée le 9 novembre 2026, `collector_runs=0`, `collector_source_runs=0`, `offer_source_identity=0` et `company_source_identity=0`. Le centre de collecte et ses connecteurs sont présents, mais aucune acquisition réelle par ce pipeline n'est inscrite.

| Source | Connecteur / fichier | Champs normalisés | Droits observés pour ce projet | Statut de fonctionnement |
|---|---|---|---|---|
| Greenhouse Job Board | `backend/collectors/platforms.py`, `fetch_greenhouse` | Identifiant, titre, description, localisation et URL d'annonce disponibles dans l'API | API publique prévue pour les pages carrière de l'employeur; permission de stockage et réaffichage à obtenir pour chaque board | Connecteur avec tests mockés; aucun board autorisé/configuré ni appel réel constaté |
| Lever Postings | `fetch_lever` | Annonces, texte, lieu, URL et pagination selon le flux | Droits d'agrégation, stockage et réaffichage à confirmer par employeur | Tests mockés; aucune collecte réelle |
| Ashby Job Postings | `fetch_ashby` | Annonces publiées, type, lieu, description, URL; `isListed` est contrôlé | La documentation vise le flux carrière du propriétaire; aucun droit général d'agrégation n'est démontré | Tests mockés; aucune collecte réelle |
| SmartRecruiters | `fetch_smartrecruiters` | Annonces publiques et pagination | Accès API technique ne prouve pas le droit de réutilisation; autorisation requise par entreprise | Tests mockés; aucune collecte réelle |
| Jawb RSS | `backend/collectors/jawb.py`, `fetch_rss` | Titre, résumé, date, lien, ville et métier selon le flux | Le guide Jawb décrit le feed comme contenu à afficher sur le site carrière de l'entreprise. L'agrégation par l'application, le stockage et le réaffichage nécessitent un accord spécifique | Connecteur verrouillé si les trois droits ne sont pas attestés; aucune collecte réelle |
| Jawb JSON employeur | `fetch_company_feed` | Employeur, identifiant, titre, ville, type, dates et URL | La documentation cible la page carrière de l'entreprise; agrégation tiers non accordée | Connecteur présent et paginé; aucun identifiant autorisé constaté |
| Flux RSS/Atom fourni par un employeur | `fetch_career_rss` | Champs réellement exposés dans le flux | Accord du propriétaire requis pour consultation automatique, stockage et réaffichage | Prêt après consignation des trois attestations; aucun flux fourni |
| CSV/XLSX fourni | `backend/collectors/provided_offers.py` | Titre, entreprise, URL, dates, ville, type et compétences mappés selon colonnes présentes | Licence ou accord à vérifier; import local seulement, sans requête réseau | Aperçu, validation et staging implémentés; aucun export autorisé remis |
| Open Data Maroc | Catalogue décrit dans le registre | Jeux statistiques selon licence de chaque jeu | Réutilisation selon la licence affichée et avec attribution | Aucune source d'offres Marrakech connectée; les jeux repérés ne sont pas un flux général de stages |
| ANAPEC, CAPPRAfrica/Trouve Ton Emploi, Jobsquare | Références dans le registre, aucun connecteur configuré pour cette mission | À préciser selon l'accord ou l'export fourni | Droits à obtenir avant toute automatisation | Pistes à contacter, aucun accès/contrat reçu |
| Stagiaires.ma historique | Valeur du champ `source` des 88 anciennes offres | La base conserve une étiquette source et des liens | Droit de stockage et de réaffichage non documenté | Données historiques; pas de journal d'import ni de date de dernière vérification |
| Google Places | `scripts/places_client.py` | Identifiant, nom, adresse, téléphone, site, lien Maps, localisation | Clé de service requise; utilisation et coût à vérifier dans le compte fournisseur | Code de commande présent; aucun appel réel effectué durant la validation |
| Gemini Search | `backend/gemini_search.py`, `backend/api.py` | Résultats avec source/grounding puis aperçu staged | Clé, option activée, consentement et configuration de facturation requis | Tests de contrat simulés; aucune requête Gemini réelle pendant cette mission |

Les documents fournisseurs décrivent les API comme outils pour les pages carrière des entreprises. Une API accessible sans authentification ne suffit pas à autoriser la copie ou la republication dans une application tierce. Pour Greenhouse, la documentation indique que les GET Job Board sont publics sans authentification. Pour Ashby et SmartRecruiters, la documentation vise les annonces de l'organisation pour construire son site carrière. Pour Jawb, la page API demande explicitement l'affichage sur le site de l'entreprise et les CGU réservent l'utilisation du contenu. Le périmètre juridique doit rester confirmé par écrit avec le titulaire avant activation.

Sources officielles consultées le 9 novembre 2026 : [Jawb API](https://jawb.ma/en/api-recrutement), [CGU Jawb](https://jawb.ma/cgu), [Greenhouse Job Board API](https://docs.greenhouse.io/job-board), [Ashby Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api), [SmartRecruiters Posting API](https://developers.smartrecruiters.com/docs/posting-api). Voir aussi `../GUIDE_SOURCES_AUTORISEES.md` et `../GUIDE_CONNECTEURS_API.md` pour le registre détaillé déjà maintenu.

## Parcours ETL réel

```text
Source configurée → Extraction bornée → Validation des champs/URLs → Normalisation
→ Détection de doublons → Staging → Décision humaine ligne par ligne
→ Import SQLite incrémental → API Flask / Dash / Matching / Chatbot / Alertes
```

`backend/collectors/service.py` bloque les connecteurs externes lorsque la collecte globale, la source ou une des permissions manque. `execute_run` enregistre le résultat et les erreurs. `import_run` vérifie le staging et les droits avant une transaction avec sauvegarde. Les connecteurs sont couverts par des fixtures; ils n'appellent pas de sources réelles dans les tests.

## Parcours d'autorisation recommandé

Obtenir du propriétaire une preuve qui couvre explicitement la consultation automatique, le stockage local, le réaffichage avec attribution/lien, la fréquence, le périmètre Marrakech/PFE, la durée de conservation et le retrait des annonces. Archiver la preuve hors du dépôt et référencer son identifiant dans le centre de collecte. Pour une première démonstration, privilégier un CSV/XLSX remis par l'organisme avec licence documentée. Une validation d'interface seule n'est pas une vérification juridique automatique.
