# Rapport Phase 7 — acquisition réelle contrôlée

## Conclusion

Le pipeline de démonstration et l’import local de fichiers sont validés sur des bases temporaires. La chaîne d’acquisition depuis une source web réelle n’a pas pu être autorisée pendant cette phase : aucun document ne couvre l’interrogation automatisée, le stockage local et le réaffichage des annonces dans Stages Marrakech AI. Aucune collecte web ni import réel n’a donc été exécuté. **Le critère principal d’acquisition réelle n’est pas déclaré atteint.**

## Recherche et décision sur les sources

- **Jawb** : API RSS/JSON accessible techniquement et documentée, mais le guide JSON est destiné à la page carrière de l’entreprise; les CGU protègent le contenu et n’accordent pas un droit général d’agrégation. Bloqué jusqu’à accord écrit spécifique.
- **Portail Open Data Maroc** : API de catalogue et jeux de données sous ODbL lorsque la fiche l’indique. Le thème Emploi consulté référence surtout des indicateurs/statistiques et des statistiques de concours, pas un flux exploitable d’offres de stages à Marrakech. Réutilisable pour analyses contextuelles sous attribution/ODbL, pas importé comme offres.
- **Trouve Ton Emploi / CAPPRAfrica** : piste la plus concrète pour des offres via API/export sous licence sur demande motivée. Aucun contrat, identifiant ou autorisation n’a été fourni.
- **ANAPEC** : portail public, mais aucune API/export avec droits de réutilisation appropriés n’a été confirmé dans la recherche. À contacter pour obtenir un flux officiel ou un export autorisé.
- **Jobsquare** : API annoncée pour connecter le logiciel de recrutement d’un client, clé sur demande. Cela ne vaut pas droit d’agrégation des offres d’autres entreprises.
- **LinkedIn, Emploi.ma, ReKrute et Stagiaires.ma** : exclus de la collecte automatisée en l’absence d’autorisation écrite adaptée; aucun contournement n’a été tenté.
- **Employeurs directs** : voie recommandée. Demander un flux ou un CSV/XLSX accompagné d’une licence couvrant consultation, stockage et affichage des annonces avec attribution.

Les liens et la matrice séparant consultation, stockage et affichage se trouvent dans [GUIDE_SOURCES_AUTORISEES.md](GUIDE_SOURCES_AUTORISEES.md). Aucune demande de permission n’a été envoyée au nom de l’utilisateur.

## Changements opérationnels

- Ajout d’un import local d’offres CSV/XLSX avec vérification de provenance, référence de licence, consentements distincts consultation/stockage/réaffichage, empreinte SHA-256 et limites de taille/lignes.
- Les offres passent par le staging et l’examen individuel avant import. Les URL sources sont conservées et les liens contenus dans le fichier ne sont jamais contactés.
- L’import reste possible lorsque la collecte externe est désactivée. Il exige la confirmation finale et crée une sauvegarde SQLite.
- Le registre et le Centre de collecte affichent les permissions séparément et, par source, les annonces détectées, nouvelles, modifiées, doublons, rejetées, importées, la date du dernier import et les erreurs. Les simulations sont marquées « DÉMO ».
- Les imports validés alimentent la liste Offres, le Matching, les alertes locales, l’assistant SQLite et les indicateurs Dash. Les anciennes candidatures et données restent conservées.
- La migration additive v5 ajoute les compteurs de rejet/import, la date d’import et les métadonnées de provenance. Elle a une sauvegarde préalable dédiée (`backups/avant_phase7_migration_20261106_151714_109334.db`, SHA-256 `8dbb807cd4e07776a8feebe518a7645030f092e2a86930451b5dda903050729f`).

## Données et validation

- Offres réelles importées en Phase 7 : **0**.
- Données réelles reçues avec licence : **0**.
- Offres synthétiques utilisées : uniquement dans les bases temporaires de test.
- La base livrée conserve 292 entreprises, 88 offres, 5 candidatures et 0 CV; `integrity_check` vaut `ok` avant et après migration. Le schéma est maintenant en version 5; aucun import ni aucune exécution de collecte n’apparaît. Le détail est consigné dans `reports/preservation_phase7.json`.
- Tests : les 91 tests Phase 6 restent présents; 5 tests Phase 7 couvrent l’attestation des trois droits, la validation d’URL HTTPS, l’import CSV de bout en bout, les rejets, l’idempotence, la synchronisation locale et le registre des permissions. Résultat complet : **96 réussis**, un avertissement de dépréciation du plugin Dash. Aucun test ne contacte Internet.
- Le rapport détaillé est dans [RAPPORT_TESTS_PHASE7.md](RAPPORT_TESTS_PHASE7.md).

## Étape requise pour une première acquisition réelle

Obtenir d’un employeur, de CAPPRAfrica, d’ANAPEC ou de Jawb un document qui précise les droits d’accès automatique, de stockage et de réaffichage, ainsi que la fréquence et l’attribution. Le document peut accompagner un fichier CSV/XLSX ou autoriser un flux/API. Après réception, l’utilisateur pourra enregistrer la référence, lancer un petit aperçu et valider les annonces individuellement. Tant que cette étape n’est pas faite, la base réelle ne reçoit aucune nouvelle offre.
