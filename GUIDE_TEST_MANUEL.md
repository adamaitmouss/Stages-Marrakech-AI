# Guide de test manuel — Stages Marrakech AI

## Mises à jour après correction finale

- Le test automatique confirme que l’API refuse un jeton CSRF périmé, puis accepte deux échanges chatbot avec le jeton récupéré depuis une session toujours authentifiée. Vérifiez en navigateur la même reprise, la reconnexion d’une session réellement expirée, l’historique, Entrée/Maj+Entrée et l’interface mobile plein écran.
- Le Matching IA présente les groupes « Très compatibles », « Potentiellement compatibles » et « À explorer ». Les seuils 70/40 sont des outils de tri explicites; contrôlez les champs manquants/incertains et ne les présentez pas comme une chance d’embauche.
- Le compte final est de 126 tests réussis en mode local et 126 dans la copie synthétique publique. La visualisation manuelle est encore requise.
- Mise à jour du 9 novembre 2026 : 133 tests réussis en local; 132 réussis et 1 test ignoré dans la copie publique. Le lancement soutenance vérifie le mode privé et refuse le port occupé. Le contrôle navigateur s'est authentifié, mais a expiré sur le parcours de démonstration Recherche IA; la validation visuelle complète reste manuelle.

Ce guide vérifie les parcours de l’application sur Windows. Les tests utilisent la base contenue dans le projet : elle comprend les données historiques. Pour les essais qui ajoutent un CV ou une candidature, faites-les dans une **copie privée du dossier extrait** afin de garder intacte votre installation principale.

## 1. Installer et démarrer

1. Décompressez `Projet_Stages_Marrakech_maps_dash.zip` dans un dossier privé.
2. Double-cliquez `INSTALLER_WINDOWS.bat`. Confirmez le téléchargement des dépendances lorsque Windows le demande. Le script garde tout `.env` déjà présent.
3. Pour les données historiques locales, démarrez `LANCER_SOUTENANCE_LOCALE.bat`. Le serveur existant sur le port 5000 doit être fermé proprement avant de continuer. Pour la démo publique, utilisez `LANCER_APPLICATION.bat` depuis la copie publique.
4. Double-cliquez `VERIFIER_INSTALLATION.bat` pour vérifier Python, les modules, les fichiers et SQLite.
5. Vous pouvez aussi utiliser `LANCER_APPLICATION.bat`, ou ouvrir PowerShell à la racine et exécuter :

   ```powershell
   .\INSTALLER_WINDOWS.bat
   .\VERIFIER_INSTALLATION.bat
   .\LANCER_APPLICATION.bat
   ```

6. Ouvrez `http://127.0.0.1:5000`. Au premier lancement, créez un mot de passe personnel (12 caractères minimum). Gardez-le privé.
7. Le tableau d’accueil local doit afficher **292 entreprises, 88 offres, 5 candidatures**. Dans le paquet public, les chiffres sont synthétiques : **5, 4, 3**.

**Résultat attendu :** l’application et Dash sont servis depuis le même serveur local. Il n’y a ni requête Gemini, ni email, ni chargement Google Maps automatique. Si vous annulez l’installation des dépendances, le lanceur explique les éléments manquants; relancez `INSTALLER_WINDOWS.bat` et acceptez le téléchargement.

## 2. Vérifier les huit pages

Depuis la barre latérale, ouvrez chaque page et revenez à l’accueil avant la suivante.

### Accueil

1. Vérifiez les cartes de statistiques, les offres récentes et les accès rapides.
2. Cliquez sur « Trouver mon matching » puis revenez par la navigation.

**Attendu :** cartes et listes chargées à partir des données; aucun squelette de chargement ne reste bloqué.

### Entreprises

1. Saisissez un nom partiel dans la recherche.
2. Choisissez un secteur puis réinitialisez le filtre.
3. Ouvrez une fiche ou un lien existant sans envoyer de candidature.

**Attendu :** la liste et le compteur se filtrent; les coordonnées absentes restent indiquées comme absentes. Les liens web/Maps connus sont visibles.

### Offres

1. Recherchez un mot du titre.
2. Filtrez par type de stage et type de contrat.
3. Vérifiez les badges « Active », « Expirée » ou « Validité inconnue ».
4. Ouvrez le parcours « Postuler » sans ouvrir de site externe et sans lancer d’email.

**Attendu :** les dates d’expiration connues donnent la priorité aux offres actives; les dates manquantes ne sont pas estimées. Le parcours affiche l’entreprise comme inconnue lorsqu’aucun lien vérifié n’existe.

### Matching IA

1. Cliquez sur « Utiliser un profil fictif ».
2. Gardez le mode « Analyser sans clé API » et lancez le classement.
3. Ouvrez « Comprendre le score » sur plusieurs cartes.
4. Comparez le score, le niveau, les compétences communes/manquantes et les contributions.
5. Cliquez sur « Postuler » sur une offre, choisissez le CV si demandé, puis quittez sans confirmer d’envoi.

**Attendu :** les résultats sont classés et expliqués; les scores restent des estimations de compatibilité, pas des probabilités de recrutement. Une offre à description pauvre peut être marquée incertaine.

**Gemini :** n’utilisez pas « Analyser avec Gemini » lors du test local. Un test réel exige une clé, une vérification du compte/quota, la relecture du texte et un consentement explicite. Les tests automatisés utilisent uniquement des mocks.

### Créateur de CV

1. Cliquez sur « Charger un exemple fictif » ou saisissez un CV de démonstration.
2. Vérifiez le nom, le titre, les accents, l’email et la ville.
3. Ajoutez au moins une expérience et un projet; ajoutez puis supprimez une autre section répétable.
4. Changez le modèle entre Moderne et Professionnel · ATS.
5. Vérifiez l’aperçu PDF réel à droite et l’option « Aperçu texte accessible ».
6. Enregistrez sous un nom de test, par exemple « Démo Phase 4 ».
7. Modifiez le titre ou le résumé puis enregistrez une autre version. Vérifiez que les deux versions apparaissent.
8. Téléchargez le PDF, ouvrez-le dans un lecteur et contrôlez accents, marges, sections vides et pagination.
9. Chargez la version initiale et confirmez que son contenu n’a pas changé.

**Attendu :** le PDF à l’écran est généré par le même service que l’export. La nouvelle sauvegarde crée une version distincte; aucune version n’est supprimée sans confirmation.

### Optimiser mon CV pour une offre

1. Dans le Créateur de CV, chargez une version enregistrée.
2. Dans « Optimiser mon CV pour une offre », sélectionnez cette version et une offre.
3. Lancez l’analyse et vérifiez les compétences communes, les compétences à vérifier/développer et les passages source.
4. Pour chaque proposition, cliquez sur « Ignorer » ou « Accepter ».
5. Si vous acceptez une suggestion d’expérience/projet, vérifiez que l’élément remonte dans sa section du brouillon.
6. Si vous acceptez une proposition de résumé, vérifiez qu’elle ne contient que les phrases existantes réordonnées.
7. N’enregistrez une nouvelle version que si vous souhaitez garder le brouillon modifié; rechargez la version précédente pour confirmer qu’elle est intacte.

**Attendu :** aucun changement n’est sauvegardé automatiquement. Aucune compétence manquante n’est ajoutée comme acquise et aucun résultat chiffré/expérience n’est inventé.

### Mes candidatures

1. Vérifiez la présence des cinq candidatures historiques.
2. Dans « Offres », ouvrez « Postuler » et choisissez « Enregistrer à préparer » avec un CV de démonstration.
3. Retournez à la page Candidatures; recherchez la nouvelle entrée et filtrez « Non envoyée ».
4. Modifiez son statut, ajoutez une note et ouvrez son historique.

**Attendu :** le statut initial est « Non envoyée »; la modification crée une entrée d’historique. Une candidature liée au CV est affichée. N’appuyez pas sur un bouton d’envoi réel pendant ce test.

### Analyses Dash

1. Ouvrez « Analyses Dash » et attendez le chargement du graphique.
2. Passez successivement par Offres, Entreprises et Candidatures.
3. Changez l’indicateur, le type de graphique, la période et les filtres disponibles.
4. Pour les Offres, essayez type de stage et contrat. Le filtre secteur n’est actif que pour les annonces reliées à une entreprise avec relation explicitement vérifiée.
5. Vérifiez les KPI et la qualité des données après chaque filtre.
6. Exportez les données filtrées en CSV puis ouvrez-le dans un tableur.
7. Essayez une combinaison courbe/catégorie pour voir le message qui explique l’incompatibilité.

**Attendu :** les KPI de la population active suivent les filtres; les autres totaux restent des comptes SQLite globaux. Les taux de réponse et leurs définitions sont affichés. Le CSV contient la population filtrée et neutralise les formules dangereuses.

### Carte des entreprises

1. Attendez le fond OpenStreetMap centré sur Marrakech; vérifiez l’attribution en bas de la carte.
2. Essayez le zoom, le déplacement, la recherche par nom et le filtre secteur.
3. Ouvrez la fiche d’un marqueur si des coordonnées vérifiées sont présentes. Vérifiez nom, secteur, adresse, téléphone, site et lien d’itinéraire.
4. Si aucune coordonnée n’est vérifiée, vérifiez que le fond cartographique reste visible, qu’aucun marqueur d’entreprise ne s’affiche et que le message le précise.
5. Cochez les points de démonstration pour afficher les trois marqueurs fictifs, ouvrez-en un, puis décochez-les.
6. Si le réseau est coupé, vérifiez le message d’indisponibilité des tuiles et l’accès aux fiches/liens locaux.

**Attendu sur la base livrée :** zéro coordonnée réelle avec provenance/date de vérification; les liens Google Maps historiques restent accessibles depuis les fiches. Le fond OSM nécessite Internet. Les marqueurs de démonstration sont clairement fictifs et ne sont pas enregistrés.

## 3. Vérifier le responsive et le thème

Dans Chrome ou Edge, utilisez les outils de développement du navigateur et testez des largeurs d’environ 390 px, 768 px et 1366 px. Répétez sur Accueil, Créateur de CV, Matching et Dash. Vérifiez ensuite le thème sombre avec le bouton de thème.

**Correction Maps/Dash :** Chrome a validé 20 contrôles, dont le parcours Dash → Flask répété trois fois, la carte avec une fixture géographique temporaire, puis la carte sans aucune coordonnée réelle. Aucun appel Google, email ni autre service externe n’a été fait; seules les tuiles OSM ont été chargées (requêtes OSM réussies en HTTP 200; une panne a également été simulée). Les captures sont dans `reports/screenshots_maps_dash/`.

**À vérifier manuellement :** répétez à 768 px et 1366 px, testez le thème sombre, puis vérifiez que le lecteur PDF intégré affiche la page dans une fenêtre Chrome ou Edge normale. Le lecteur interne Chromium n’a pas fourni de rendu fiable en capture headless. Le flux HTTP PDF est valide; le téléchargement natif de Chrome automatisé est refusé par Windows dans cet environnement.

## 4. Relancer les tests automatisés

Depuis la racine du projet :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

**Résultat attendu :** 72 tests passent. Les tests ne touchent pas la base utilisée par l’application et bloquent le réseau externe.

## 5. Nettoyer les données de démonstration

Si vous avez utilisé une copie, vous pouvez la supprimer après vérification. Si vous avez testé dans votre installation réelle, supprimez uniquement les CV de démonstration non liés à une candidature depuis le Créateur de CV après confirmation. Les candidatures historiques ne doivent pas être supprimées; les changements de statut et notes sont conservés dans le suivi.

