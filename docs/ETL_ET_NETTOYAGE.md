# ETL, import et nettoyage

## Flux implémenté

1. **Extraction** : connecteur ATS, flux RSS configuré ou fichier CSV/XLSX remis localement.
2. **Validation** : valeurs obligatoires, dates, URLs HTTPS publiques, droits par source et taille du fichier.
3. **Nettoyage et normalisation** : noms de colonnes mappés, texte borné/nettoyé, offres converties vers un schéma canonique.
4. **Déduplication** : clé d'identité, empreinte de contenu et comparaison avec les offres présentes. Une similarité inter-source est signalée à l'humain et n'est pas fusionnée automatiquement.
5. **Staging** : chaque offre attend une décision explicite. L'aperçu n'écrit pas de nouvelle offre dans la table principale.
6. **Chargement** : import incrémental après approbation, sauvegarde avant écriture, transaction SQLite et journal de provenance.
7. **Synchronisation** : les modules lisent les tables SQLite communes; les KPI sont calculés à partir de la base, et le Matching, le Chatbot et les Alertes consultent les mêmes offres.

## Contrôles de qualité

- `backend/validation.py` borne le texte et les emails, vérifie URL sûre et cohérence des candidatures.
- `backend/collectors/schema.py` normalise les offres, calcule une identité et une empreinte.
- `backend/collectors/provided_offers.py` vérifie les colonnes mappées des CSV/XLSX et prépare un aperçu.
- `backend/collectors/service.py` vérifie les permissions, logue la collecte, propose les doublons et applique les décisions manuelles.
- Les dates invalides, URL non publiques ou données incomplètes restent rejetées ou en attente; le pipeline ne fabrique pas de dates ou de coordonnées.

## Résultat actuel

Le code et les tests de fixtures valident le processus local, mais la base privée contient 0 run de collecte et 0 ligne d'identité de provenance. L'ETL est donc **testé sur réponses simulées et fichiers de test**, pas attesté comme collecte opérationnelle auprès de sources réelles. Aucun CSV/XLSX sous licence n'a été fourni pour cette livraison.

La liste des défauts de données à résoudre est dans `ETAT_DES_DONNEES.md`. Les 10 doublons de titre approximatifs ne sont pas fusionnés automatiquement, et 85 des 88 références d'entreprise d'offres ne correspondent pas à `entreprises.rowid`.
