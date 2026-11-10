# Vérification manuelle avant soutenance

Aucun contrôle visuel n’a pu être conduit ici : le lancement du serveur local isolé a été rejeté automatiquement par la politique d’approbation de l’environnement. Effectuez ces contrôles dans Chrome ou Edge standard.

## Profil local privé
1. Lancez l’application avec le `.env` local existant. Ne le remplacez pas et ne publiez pas ses secrets.
2. Confirmez que `DATABASE` résolu est `database/stages_marrakech.db`, mode public désactivé.
3. Ouvrez Accueil, Entreprises, Offres, Chatbot, Matching et Analyses Dash; comparez les compteurs aux rapports.
4. Dans Dash, testez onglets/dataset, indicateur, date, secteur, type, entreprise, graphique, actualisation et export CSV temporaire.
5. Confirmez que « Activité de collecte » n’apparaît plus. Vérifiez que le Centre de collecte conserve aperçu, mapping, validations et historique.
6. Cliquez « Retour à l’application »; la fenêtre complète doit revenir sur Flask (`/index.html`) avec `target=_top`, sans iframe imbriqué.
7. Testez les largeurs 360, 768 et 1280 px. Vérifiez absence de débordement/coupe.
8. Les villes/quartiers sont vides dans les données historiques; n’interprétez pas de graphique géographique comme une observation réelle.

## Démo publique synthétique
1. Sélectionnez seulement `database/stages_marrakech_public_demo.db`, `PUBLIC_DEMO_MODE=true`, `PUBLIC_DEMO_DATA_CONFIRMED=true`.
2. Vérifiez la mention « données synthétiques » dans le Dashboard et les volumes de démonstration.
3. Confirmez qu’une écriture candidature/CV est refusée et que Gemini/SMTP/Maps restent désactivés. N’entrez aucune donnée personnelle.

## Parcours fonctionnels
- Accueil : navigation, KPI, liens et états vides.
- Entreprises/offres : recherche, filtres, détail, URL source, dates expirées/inconnues.
- Matching : profil fictif, score et explication; aucune compétence inventée.
- CV : profil fictif, répétitions formation/expérience, preview et téléchargement PDF.
- Candidature : enregistrement fictif « Non envoyée », statut et historique. N’envoyez ni email ni candidature externe.
- Carte : provenance des coordonnées et état sans marqueurs; points fictifs uniquement avec choix explicite.
- Centre : CSV de test/données fictives, aperçu, mapping, doublon, validation et staging dans environnement temporaire; ne lancez pas de collecte réseau.
- Alertes/chatbot : préférences fictives, compteur et requête SQLite locale.
- Gemini : vérifier seulement le message désactivé sans clé; ne pas activer facturation.

## Chatbot après correction CSRF

- Ouvrez l’assistant, envoyez deux questions locales, puis vérifiez que les échanges restent lisibles et que l’historique réapparaît après fermeture/réouverture et rechargement.
- Entrez une nouvelle ligne avec Maj+Entrée; Entrée envoie la question.
- Si la page possède un ancien jeton CSRF mais la session reste active, une écriture reçoit d’abord le 403 CSRF, l’interface récupère le jeton courant depuis `/api/auth/session`, puis réessaie une seule fois. Une session non authentifiée n’est jamais rétablie en arrière-plan : rechargez la page et reconnectez-vous.
- Sur un mobile, la fenêtre occupe l’écran; faites défiler séparément les messages et, si nécessaire, les commandes en bas. Vérifiez que le bouton Envoyer reste visible.
- Aucun rendu navigateur visuel n’a été validé lors de cette session; ce parcours reste à exécuter dans Chrome/Edge normal.

Avant capture, masquez chemins, notifications, emails, CV et toute donnée personnelle. Ajoutez des liens GitHub/HTTPS uniquement après création et test réels.
