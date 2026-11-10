# Rapport Phase 8 — connecteurs officiels et import contrôlé

## Résultat opérationnel

Les adaptateurs Greenhouse, Lever, Ashby et SmartRecruiters sont intégrés au pipeline Phase 7, avec un registre d’entreprises, le flux carrière RSS/Atom, la prévisualisation, le staging, l’approbation individuelle, la déduplication et l’import incrémental. Les offres importées réutilisent les modules existants de matching, recherche locale du chatbot, alertes et KPI Dash.

**Aucune offre réelle nouvelle n’a été collectée ni importée en Phase 8.** Aucun employeur, board ou justificatif n’a été fourni. Aucune source ATS n’est configurée, la collecte externe est désactivée et l’automatisation est désactivée. Les tests de connecteurs sont des simulations locales; ils ne constituent pas une acquisition réelle.

## Connecteurs et droits

- Greenhouse : Job Board API pour les annonces publiées; l’accès public GET n’est pas pris comme une licence d’agrégation.
- Lever : Postings API avec pagination bornée; la documentation décrit les offres publiées accessibles via l’API.
- Ashby : Public Job Postings API; seules les offres avec `isListed=true` sont incluses.
- SmartRecruiters : requête `destination=PUBLIC` uniquement. Aucun jeton, clé ni scope pouvant exposer des annonces internes n’est utilisé.
- RSS/Atom : URL HTTPS officielle fournie par l’administrateur.
- Import CSV/XLSX : fichier local transmis légalement, référence et droits séparés, empreinte SHA-256.

Documentation fournisseur : [Greenhouse](https://docs.greenhouse.io/job-board), [Lever](https://github.com/lever/postings-api), [Ashby](https://developers.ashbyhq.com/docs/public-job-posting-api), [SmartRecruiters](https://developers.smartrecruiters.com/docs/posting-api). Leur disponibilité technique ne prouve pas à elle seule l’autorisation de collecte, stockage et réaffichage dans cette application. Aucune autorisation spécifique à Stages Marrakech AI n’a été vérifiée.

## Fonctionnalités livrées

- Registre administrable : entreprise, site officiel, page carrière, plateforme, identifiant, ville, secteur, date de vérification et référence de droits.
- Activation bloquée sans référence et trois attestations séparées; collecte externe et planificateur désactivés par défaut.
- Requêtes HTTPS sur hôtes ATS connus, redirections refusées, limites de temps, taille et pagination; SmartRecruiters public uniquement; offres Ashby non listées écartées.
- Schéma commun et classification expliquée, avec niveau d’incertitude; le type inconnu n’est jamais transformé automatiquement en stage. Filtres API pour lieu, type, secteur, sous-type et rémunération renseignée.
- Mapping colonne → champ pour CSV/XLSX des entreprises et offres; aperçu des colonnes, erreurs de date/URL, staging et validation avant écriture.
- Association proposée uniquement par nom exact et unique; aucune fusion par ressemblance seule, aucune fiche provisoire créée automatiquement. Une offre non associée reste possible.
- Les collectes planifiées restent locales, activables par l’utilisateur, sans tâche Windows. Erreurs planifiées consignées dans `logs/collection_scheduler.log`.

## Données et préservation

| Mesure | État livré |
|---|---:|
| Version SQLite | 5 (aucune migration Phase 8 nécessaire) |
| Entreprises | 292 |
| Offres | 88 |
| Candidatures | 5 |
| Intégrité SQLite | `ok` |
| Boards configurés | 0 |
| Collecte externe | désactivée |
| Automatisation | désactivée |
| Offres réelles importées Phase 8 | 0 |

Une sauvegarde de contrôle a été créée avant toute écriture SQLite Phase 8 : `backups/avant_phase8_20261108_184635_644194.db`, SHA-256 `c493de1e46f39684449af0210f4c1232e79c8e4fe272096414f16481d0a5d868`. La base métier n’a pas été migrée ni modifiée pendant les essais; ceux-ci se sont déroulés sur bases temporaires.

## Validation

Les **107 tests passent**. Les 11 ajouts couvrent les quatre connecteurs mockés, pagination, réponses vides/HTTP erronées, parsing JSON, mapping CSV/XLSX, classification prudente, garde d’autorisation, association exacte d’une entreprise et chaîne d’intégration complète. Voir [RAPPORT_TESTS_PHASE8.md](RAPPORT_TESTS_PHASE8.md).

## Activation ultérieure

Pour importer une première offre réelle, obtenir d’abord le document de l’employeur autorisant explicitement l’accès automatisé, la conservation et le réaffichage avec attribution. Configurer un seul board, faire un aperçu, approuver les annonces une par une, puis confirmer l’import. Sans ce document, utiliser l’import CSV/XLSX d’un fichier légalement transmis.

Guides : [API et connecteurs](GUIDE_CONNECTEURS_API.md), [sites carrières](GUIDE_SITES_CARRIERES.md), [import CSV/Excel](GUIDE_IMPORT_CSV_EXCEL.md), [registre Phase 7](GUIDE_SOURCES_AUTORISEES.md).
