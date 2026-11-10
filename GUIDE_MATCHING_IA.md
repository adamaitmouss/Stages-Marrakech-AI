# Guide du matching et des recommandations

## Matching local

Ouvrez **Matching IA**, chargez un CV enregistré ou importez un PDF, puis relisez le texte extrait. L’extraction est locale. Les compétences reconnues proviennent d’un vocabulaire contrôlé; corrigez les faux positifs et complétez formation, projets, ville et type de stage. Les DOCX ne sont pas pris en charge par le parcours de matching actuel.

Lancez **Analyser sans clé API**. Le serveur compare le profil et les offres de la base réellement sélectionnée. Le classement renvoie les compétences communes et absentes, les contributions par critère, les poids, les critères incertains et une explication. Les compétences absentes du CV ne signifient pas qu’elles sont inconnues de la personne: ce sont des termes non repérés dans le texte.

Le score est une somme reproductible sur 100, avec pondérations initiales : compétences 40, formation/domaine 25, expériences/projets 15, ville 10 et type d’opportunité 10. La couverture des compétences est comparée aux termes détectés dans l’annonce. Domaine et expérience utilisent une similarité TF-IDF/cosinus locale. Ville et type ne contribuent que si les deux côtés sont renseignés et égaux après normalisation. La localisation absente est signalée comme incertaine; aucune ville n’est déduite.

Un score indicatif n’est pas une probabilité de recrutement. Les résultats ne sont pas évalués sur un jeu d’étiquettes établi par des recruteurs. Une annonce ancienne n’est pas déclarée active sans information de validité. Les offres historiques peuvent avoir une entreprise ou une ville inconnue.

## Conseils CV par offre

Dans **Créateur de CV**, sélectionnez une version enregistrée et une offre. L’analyse locale rapproche les compétences du CV et de la description, propose les éléments textuels à mettre en valeur et n’écrit jamais dans le fichier original. Chaque suggestion doit être acceptée ou ignorée. Enregistrez une nouvelle version pour conserver les changements que vous avez acceptés.

Pour lancer une analyse Gemini, il faut que le service soit activé dans `.env`; le profil actuel est désactivé. Les données à envoyer sont prévisualisées et le consentement explicite est requis. Consultez `GUIDE_CLE_GEMINI.md`. Aucun envoi réel n’a été testé.

## Groupes et filtres

Les résultats sont séparés en trois groupes lisibles : « Très compatibles » (≥70 et analyse suffisamment documentée), « Potentiellement compatibles » (40–69 ou données incertaines) et « À explorer » (<40). Ce sont des seuils heuristiques locaux, visibles dans l’interface, pas des probabilités ni une évaluation de recruteur. Les champs du profil (compétences, domaine, ville, type) et les pondérations modifient le classement. Des listes de filtres indépendantes pour la source et le type ne sont pas présentes. Les fiches d’offres conservent le lien source et l’action de préparation de candidature. La base publique ne contient pas de CV privé.
