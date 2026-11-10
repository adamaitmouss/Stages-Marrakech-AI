# État vérifié des données

**Instantané contrôlé le 9 novembre 2026.** Cette note décrit les bases présentes, sans modifier leurs enregistrements.

## Bases et volumes

| Profil | Chemin relatif | Schéma | Entreprises | Offres | Candidatures | Contrôle SQLite |
|---|---|---:|---:|---:|---:|---|
| Local privé | `database/stages_marrakech.db` | 6 | 292 | 88 | 5 | `integrity_check=ok`, 0 erreur FK |
| Démo publique | `database/stages_marrakech_public_demo.db` | 6 | 5 | 4 | 3 | `integrity_check=ok`, 0 erreur FK |

Le lanceur local principal `LANCER_MON_PROJET.bat` fixe `AUTH_PROFILE=private`, `AUTH_APP_DATABASE` et `DATABASE` vers la base historique privée. Le profil public utilise explicitement le fichier synthétique et son marqueur. Le fichier vide `stages_marrakech.db` à la racine n'est pas référencé par le code ni les lanceurs.

## Qualité descriptive de la base privée

Les taux utilisent le dénominateur de la table entière. Une valeur est manquante lorsqu'elle est `NULL` ou vide après suppression des espaces.

| Table / champ | Manquants | Lecture |
|---|---:|---|
| Entreprises / téléphone | 10 / 292 (3,4 %) | Quelques contacts sont absents |
| Entreprises / site web | 56 / 292 (19,2 %) | La fiche n'a pas toujours un site renseigné |
| Entreprises / email | 147 / 292 (50,3 %) | 145 entreprises ont un champ `Emails` non vide; ce contrôle ne vérifie pas la délivrabilité ni l'autorisation de contact |
| Entreprises / ville et quartier | 292 / 292 (100 %) chacun | Aucune ville ou quartier n'est stocké dans ces colonnes |
| Entreprises / latitude et longitude | 292 / 292 (100 %) chacun | Aucun point géographique validé dans ces colonnes |
| Entreprises / source de géocodage et date de vérification | 292 / 292 (100 %) chacun | Pas de provenance de coordonnées |
| Offres / type de stage | 22 / 88 (25,0 %) | La classification du type n'est pas complète |
| Offres / date de dernière vérification | 88 / 88 (100 %) | La fraîcheur des annonces n'est pas documentée |
| Offres / ville, compétences et date de collecte | 88 / 88 (100 %) chacun | Ces attributs ne sont pas stockés pour les offres historiques |

Les 88 lignes d'offres ont toutes une date de publication, une date d'expiration, un champ source et au moins un champ de lien non vide. Le champ `source` contient `Stagiaires.ma` sur les 88 lignes. Le registre historique ne contient aucune identité de source par offre ni exécution enregistrée du collecteur. Le libellé `active` présent en base n'est donc pas une preuve qu'une annonce est encore ouverte. Les dates de publication observées vont du 27 août au 25 septembre 2026.

Les titres d'offres présentent 10 lignes excédentaires dans des groupes de titres normalisés identiques. Ce signal ne prouve pas que les annonces sont le même poste; le nettoyage ne fusionne donc pas ces lignes. Aucun nom d'entreprise n'est dupliqué après normalisation simple de casse et d'espaces.

Sur la relation `offres."Entreprise ID"` vers `entreprises.rowid`, 85 lignes sur 88 ne trouvent pas de correspondance. Le schéma ne déclare pas de clé étrangère sur ce champ. Les enregistrements historiques sont conservés et cette faiblesse de relation doit rester visible.

Les 5 candidatures contiennent des champs de contact privés. Elles restent dans la copie locale et la sauvegarde privée. Le rapport ne publie aucune valeur personnelle. La table `cvs` contient 0 CV enregistré dans cet instantané.

## Provenance et limites

- Entreprises : la table ne contient pas de champ général de provenance; `company_source_identity` contient 0 ligne.
- Offres : champ historique `source=Stagiaires.ma`, mais aucun journal de collecte, identité externe ou horodatage de dernière vérification; les droits de stockage/réaffichage ne sont pas établis par une URL source.
- Collecte : `collector_runs` et `collector_source_runs` contiennent chacun 0 ligne. Aucune collecte réelle n'est démontrée par le journal.
- Offres actuellement ouvertes : **non déterminé**. Le statut stocké peut être ancien et les annonces n'ont pas été vérifiées en ligne.
- Redistribution historique démontrée : **0 entreprise sur 292 et 0 offre sur 88** ont une autorisation documentée de réaffichage/redistribution dans le projet. La copie publiable reste donc limitée aux données synthétiques 5 entreprises / 4 offres; elle n'est pas une extraction historique.
- Secteurs des entreprises : Informatique 98, Autre 83, Hôtellerie 22, Tourisme 19, Construction 18, Industrie 14, Logistique 11, Marketing 8, RH 2 et Commerce 2. La catégorie « Autre » représente 28,4 % du répertoire.
- Coordonnées : aucun couple latitude/longitude n'est présent dans la base privée; une carte peut donc afficher un fond cartographique sans marqueur d'entreprise vérifié.

Le contrôle utilise des requêtes SQLite en lecture seule. Les informations individuelles de candidatures, de CV et de conversations ne sont pas exposées dans ce document.
