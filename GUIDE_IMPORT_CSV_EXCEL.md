# Guide d’import CSV et Excel Phase 8

## Formats et étapes

Les fichiers CSV UTF-8 et Excel `.xlsx`/`.xlsm` sont lus localement. Aucun lien du fichier n’est appelé. Taille maximale : 5 Mo; maximum 10 000 lignes pour les offres. L’aperçu indique les colonnes reconnues, celles à mapper, les champs obligatoires absents et les lignes rejetées. Le mapping s’écrit `{"nom de colonne":"champ canonique"}`.

### Champs offres

`title`, `company`, `city`, `sector`, `description`, `contract_type`, `internship_type`, `skills`, `published_at`, `expires_at`, `source_id`, `url`.

Exemple : `{"Company":"company","Job Title":"title","Location":"city","Apply URL":"url"}`. Le titre et une URL HTTPS d’annonce sont requis. Les dates illisibles et les URL HTTP ou malformées sont rejetées. Les doublons de lignes et identités déjà connues sont détectés avant l’import.

### Champs entreprises

`name`, `source`, `source_id`, `address`, `phone`, `website`, `emails`, `sector`, `city`, `maps`, `latitude`, `longitude`, `geo_source`, `geo_verified_at`.

Exemple : `{"Company Name":"name","Issuer":"source","City":"city","Website":"website"}`. Une latitude/longitude exige provenance et date de vérification. Les correspondances exactes peuvent être mises à jour; les ressemblances restent à vérifier.

## Provenance et droits

Pour les offres, indiquer le producteur, la référence de licence/accord, et attester séparément la consultation, le stockage et le réaffichage. Le SHA-256, le nom de fichier nettoyé, les rejets et la provenance sont conservés dans l’historique. Pour les entreprises, le parcours conserve la source et n’ajoute pas de coordonnées géographiques non fournies ou non vérifiées.

L’aperçu est non destructif. Les annonces passent ensuite en staging et doivent être approuvées individuellement avant l’import SQLite. Une sauvegarde précède chaque écriture. L’import est incrémental et ne supprime aucune candidature ni donnée historique.
