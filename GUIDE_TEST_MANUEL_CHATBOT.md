# Guide de test manuel du chatbot

Lancer d'abord l'application locale avec `LANCER_SOUTENANCE_LOCALE.bat`, après avoir libéré le port 5000. Connectez-vous avec le compte local existant. Aucun appel externe n'est nécessaire.

1. Ouvrir le chatbot et poser une question sur les offres présentes. Vérifier les titres, employeurs, informations de validité et lien source disponibles.
2. Demander le nombre d'entreprises enregistré. Vérifier que la réponse distingue le décompte de la base d'une mesure du marché actuel.
3. Poser une question sans résultat. Vérifier que l'assistant indique clairement l'absence de résultat et n'invente pas d'offre.
4. Fermer puis rouvrir le chatbot : l'historique doit réapparaître. Cliquer « Nouvelle conversation » et confirmer pour effacer uniquement l'historique assistant.
5. Vérifier Entrée pour envoyer, Maj+Entrée pour une nouvelle ligne, l'indicateur de chargement et le message d'erreur en cas d'interruption réseau.
6. Simuler une ancienne page avec un jeton CSRF périmé pendant que la session reste valide : l'application renouvelle le jeton une fois. Avec une session expirée, elle demande de se reconnecter.
7. Si le profil affiche Gemini, examiner l'aperçu exact et le consentement avant tout envoi. Garder Gemini désactivé pour une soutenance sans autorisation explicite.
8. Comparer les suggestions de matching et vérifier les catégories ainsi que les mentions d'incertitude.
9. Réduire la fenêtre à une largeur mobile et vérifier que le fil de discussion défile séparément du formulaire.

Le parcours navigateur automatisé n'ayant pas dépassé l'étape Recherche IA, ces contrôles restent à effectuer manuellement avant de présenter une validation visuelle complète.
