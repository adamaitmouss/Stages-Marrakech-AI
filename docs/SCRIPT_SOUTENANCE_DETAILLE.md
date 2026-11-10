# Script de soutenance détaillé

## Parcours recommandé de 6 à 8 minutes

Présentez les diapositives principales 1 à 8, 13, 15, 19, 24, 25, 30, 32, 33, 37, 38 et 42. Les diapositives restantes approfondissent les questions. Les diapositives 43 à 45 sont des annexes.

## Notes complètes par diapositive

## Diapositive 0 — Stages Marrakech AI
Statut : Parcours principal
- **Ce que je dois dire :** Je présente Stages Marrakech AI, un projet Python qui rassemble recherche d’offres, suivi et outils d’aide à la candidature. Les informations d’identité de la couverture restent à compléter.
- **Explication pédagogique :** La soutenance présente d’abord le besoin, puis les données, l’architecture et les limites mesurées.
- **Exemple concret :** Je m’appuie sur la base locale historique et sur les rapports vérifiés dans la copie finale.
- **Interprétation du résultat :** Les volumes décrivent l’instantané du 9 novembre 2026.
- **Localisation du code / source :** Aucun service externe ou déploiement n’est présenté comme opérationnel.
- **Transition :** Transition : je commence par le plan et le problème observé.

## Diapositive 1 — Plan de la présentation
Statut : Parcours principal
- **Ce que je dois dire :** Je vais du besoin utilisateur vers l’architecture, puis vers les données et les résultats.
- **Explication pédagogique :** Une API est l’interface entre le navigateur et le serveur; ETL désigne extraction, transformation et chargement.
- **Exemple concret :** La démonstration recommandée tient en six à sept minutes et s’appuie sur les diapositives 1, 2, 6, 8, 15, 19, 24, 25, 30, 32, 33, 37, 38 et 42.
- **Interprétation du résultat :** Les diapositives 43 à 45 servent d’annexes pendant les questions.
- **Localisation du code / source :** Le projet n’a pas réalisé de collecte réelle au cours de cette validation.
- **Transition :** Transition : le point de départ est la recherche de stage dispersée.

## Diapositive 2 — Contexte général
Statut : Parcours principal
- **Ce que je dois dire :** Le projet cible les étudiants qui cherchent une première expérience ou un stage de fin d’études.
- **Explication pédagogique :** Un répertoire local évite de répéter les mêmes recherches et facilite le suivi.
- **Exemple concret :** L’exemple concret est une recherche de stage Data à Marrakech avec une liste d’entreprises et d’offres.
- **Interprétation du résultat :** Le système organise les données présentes; il ne garantit pas leur actualité.
- **Localisation du code / source :** Le périmètre est un outil local et une démo synthétique, pas une plateforme employeur déployée.
- **Transition :** Transition : cette dispersion entraîne un suivi incomplet.

## Diapositive 3 — Problématique
Statut : Parcours principal
- **Ce que je dois dire :** Le problème comprend la recherche elle-même et la qualité de l’information disponible.
- **Explication pédagogique :** Une annonce copiée dans une base locale peut fermer sans que la base le sache.
- **Exemple concret :** Dans l’instantané audité, les 88 offres ont une date d’expiration enregistrée mais aucune date de dernière vérification.
- **Interprétation du résultat :** Le statut stocké ne permet pas de confirmer la disponibilité actuelle.
- **Localisation du code / source :** Cette limite influence les résultats et doit être dite clairement au jury.
- **Transition :** Transition : les objectifs cherchent à mieux organiser, sans promettre une donnée parfaite.

## Diapositive 4 — Objectifs du projet
Statut : Parcours principal
- **Ce que je dois dire :** Les objectifs couvrent un parcours depuis la découverte d’une entreprise jusqu’au suivi de candidature.
- **Explication pédagogique :** Le score de matching est un indicateur de similarité textuelle, pas une décision automatique.
- **Exemple concret :** Un étudiant peut comparer un profil fictif à des offres puis préparer un PDF de démonstration.
- **Interprétation du résultat :** L’application précise les inconnues plutôt que d’inventer une ville ou une date.
- **Localisation du code / source :** La limite d’isolation entre utilisateurs reste importante pour les données personnelles.
- **Transition :** Transition : la solution réunit des modules Python dans une application locale.

## Diapositive 5 — Solution proposée
Statut : Parcours principal
- **Ce que je dois dire :** La solution utilise un backend Flask, une interface web et plusieurs services réutilisant SQLite.
- **Explication pédagogique :** Le Dashboard et les pages métier consomment la même base configurée.
- **Exemple concret :** Une nouvelle offre approuvée peut ensuite être visible par la recherche et les modules qui lisent la table offres.
- **Interprétation du résultat :** Les connecteurs externes restent désactivés sans preuve de permission.
- **Localisation du code / source :** La chaîne complète existe dans le code, mais la base actuelle n’enregistre aucun run de collecte.
- **Transition :** Transition : le développement a avancé par étapes, avec tests et conservation des données.

## Diapositive 6 — Méthode de réalisation
Statut : Parcours principal
- **Ce que je dois dire :** Le projet a évolué par étapes et ses rapports historiques restent disponibles pour retracer les décisions.
- **Explication pédagogique :** Les tests temporaires évitent d’utiliser les candidatures historiques pendant les scénarios.
- **Exemple concret :** Le résultat de cette mission est une copie préparée, séparée des originaux.
- **Interprétation du résultat :** Les données historiques sont préservées et vérifiées.
- **Localisation du code / source :** Aucun changement de design ou d’architecture cœur n’a été nécessaire pour cette livraison.
- **Transition :** Transition : voici les composants et leurs échanges.

## Diapositive 7 — Architecture générale
Statut : Parcours principal
- **Ce que je dois dire :** Le navigateur appelle Flask en JSON; Flask transmet aux services Python et SQLite.
- **Explication pédagogique :** Staging signifie que les propositions de données restent en attente avant leur intégration principale.
- **Exemple concret :** Dash est un module intégré au serveur Flask, pas une base séparée.
- **Interprétation du résultat :** Exemple : une question Chatbot interroge SQLite et renvoie des résultats au navigateur.
- **Localisation du code / source :** Le backend sert une seule base par configuration de lancement.
- **Transition :** Transition : les outils choisis s’alignent avec ce flux.

## Diapositive 8 — Stack technique
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Chaque outil correspond à un rôle concret dans le code.
- **Explication pédagogique :** Pandas traite des tableaux; Plotly produit les graphiques; ReportLab compose les documents PDF.
- **Exemple concret :** L’exemple CSV est lu et mappé avant d’entrer dans la base.
- **Interprétation du résultat :** Le fichier requirements fixe les principales dépendances de l’application.
- **Localisation du code / source :** Les versions indiquées sont celles déclarées localement, pas une affirmation de support futur.
- **Transition :** Transition : l’arborescence sépare ces responsabilités.

## Diapositive 9 — Structure du projet
Statut : Approfondissement facultatif
- **Ce que je dois dire :** La structure d’origine est conservée pour ne pas casser les imports.
- **Explication pédagogique :** Les fichiers HTML du frontend sont servis par Flask.
- **Exemple concret :** Les dossiers privés et les secrets appartiennent uniquement à la copie locale.
- **Interprétation du résultat :** Pour la version publiable, utiliser le ZIP synthétique séparé.
- **Localisation du code / source :** L’environnement virtuel est régénérable avec le lanceur d’installation.
- **Transition :** Transition : regardons la fabrique Flask qui assemble l’application.

## Diapositive 10 — Backend Flask
Statut : Approfondissement facultatif
- **Ce que je dois dire :** La fonction create_app construit l’application et injecte les paramètres du profil.
- **Explication pédagogique :** Une fabrique facilite les tests avec des bases temporaires.
- **Exemple concret :** Le point d’entrée lance uniquement sur l’interface locale et coupe le mode debug.
- **Interprétation du résultat :** Dans VS Code, ouvrir backend/web.py ligne 15 puis backend/app.py ligne 8.
- **Localisation du code / source :** Le lanceur vérifie le profil et le fichier SQLite avant démarrage.
- **Transition :** Transition : la page web appelle ces routes par JSON.

## Diapositive 11 — Frontend et API
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Le helper frontend centralise les appels à l’API et la gestion de réponses.
- **Explication pédagogique :** JSON est un format texte qui transporte objets et listes entre navigateur et serveur.
- **Exemple concret :** Une modification envoie un jeton CSRF; si la session expire, le code tente un renouvellement sûr.
- **Interprétation du résultat :** Le helper améliore aussi la lisibilité des erreurs utilisateur.
- **Localisation du code / source :** Le code UI est conservé; seules les références documentaires ont été ajoutées à la copie finale.
- **Transition :** Transition : les modules partagent une base SQLite.

## Diapositive 12 — Base SQLite
Statut : Parcours principal
- **Ce que je dois dire :** SQLite est le fichier de données sur lequel les routes et Dashboard travaillent.
- **Explication pédagogique :** La version vient de PRAGMA user_version; elle n’a pas été supposée à partir d’un ancien rapport.
- **Exemple concret :** Les volumes sont calculés par COUNT(*) directement dans chaque base.
- **Interprétation du résultat :** Le jeu public porte un marqueur synthétique et contient des données fictives.
- **Localisation du code / source :** La copie privée n’a pas été écrasée par la base publique.
- **Transition :** Transition : les liens entre tables ont des limites à expliquer.

## Diapositive 13 — Relations et contraintes
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Un modèle relationnel décrit comment des tables peuvent être reliées par des identifiants.
- **Explication pédagogique :** La base déclare une seule relation FK importante entre l’historique et la candidature.
- **Exemple concret :** La relation entreprise-offre est seulement un champ applicatif et 85 lignes ne se rapprochent pas des rowid.
- **Interprétation du résultat :** Le contrôle FK renvoie zéro erreur parce qu’il ne vérifie que les contraintes déclarées.
- **Localisation du code / source :** Je conserve les données et signale le défaut au lieu de deviner des correspondances.
- **Transition :** Transition : l’origine des enregistrements est tout aussi importante.

## Diapositive 14 — Origine des données
Statut : Parcours principal
- **Ce que je dois dire :** L’instantané historique contient le volume annoncé, confirmé par SQLite.
- **Explication pédagogique :** Les 88 offres ont une étiquette source, mais pas de ligne de provenance individuelle ni de journal de pipeline.
- **Exemple concret :** Les 5 candidatures sont privées; aucune donnée de contact n’est affichée dans la présentation.
- **Interprétation du résultat :** Une ligne dans l’ancienne base ne prouve ni la collecte ni le droit actuel de réaffichage.
- **Localisation du code / source :** Aucune collecte réelle nouvelle n’a été exécutée dans cette mission.
- **Transition :** Transition : le code possède des connecteurs, mais chacun reste soumis aux droits.

## Diapositive 15 — Connecteurs et autorisations
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Le tableau distingue l’existence du connecteur de la permission de réutiliser les données.
- **Explication pédagogique :** Une API accessible techniquement peut être destinée à la page carrière de l’employeur plutôt qu’à un agrégateur tiers.
- **Exemple concret :** Le propriétaire doit confirmer consultation automatique, stockage et réaffichage.
- **Interprétation du résultat :** Tous les tests fournisseurs sont simulés et ne contactent pas les plateformes.
- **Localisation du code / source :** La documentation Jawb présente le JSON comme outil de page carrière de l’entreprise; ses CGU réservent le contenu. Sources : https://jawb.ma/en/api-recrutement et https://jawb.ma/cgu
- **Transition :** Transition : voici un extrait réel d’un connecteur.

## Diapositive 16 — Exemple d’appel API
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Le connecteur construit l’URL Greenhouse depuis un identifiant de board validé.
- **Explication pédagogique :** La fonction _request refuse les hôtes non autorisés, les redirections et les réponses trop grandes.
- **Exemple concret :** Le parseur convertit ensuite les champs vers une structure commune.
- **Interprétation du résultat :** Les tests remplacent la réponse HTTP par une fixture; aucune requête réelle ne figure dans le résultat.
- **Localisation du code / source :** La documentation officielle décrit l’accès GET public pour les annonces; elle ne donne pas une permission générale d’agrégation. Source : https://docs.greenhouse.io/job-board
- **Transition :** Transition : un fichier fourni suit aussi un aperçu avant import.

## Diapositive 17 — Import CSV et Excel
Statut : Approfondissement facultatif
- **Ce que je dois dire :** L’import local accepte CSV ou XLSX remis par une source autorisée.
- **Explication pédagogique :** Le mapping relie les noms de colonnes du fichier au schéma canonique.
- **Exemple concret :** La prévisualisation permet de rejeter une URL ou une date incorrecte sans écrire dans la table offres.
- **Interprétation du résultat :** Un exemple de démonstration doit utiliser un fichier fictif et une base temporaire.
- **Localisation du code / source :** Aucun fichier sous licence n’a été fourni pour l’instantané final.
- **Transition :** Transition : ces étapes composent le pipeline ETL.

## Diapositive 18 — Pipeline ETL
Statut : Approfondissement facultatif
- **Ce que je dois dire :** ETL signifie extraction, transformation, chargement.
- **Explication pédagogique :** Le manager commence par vérifier le réglage global et la liste des sources autorisées.
- **Exemple concret :** Chaque résultat va d’abord dans collector_staging; l’import final passe par une autre fonction.
- **Interprétation du résultat :** Un exemple concret est une offre CSV qui reste pending jusqu’à la décision de l’utilisateur.
- **Localisation du code / source :** La base historique auditée ne comporte encore aucun run réel.
- **Transition :** Transition : la transformation évite de fabriquer des valeurs.

## Diapositive 19 — Nettoyage des données
Statut : Approfondissement facultatif
- **Ce que je dois dire :** La fonction nettoie un texte et borne sa taille avant de produire le schéma canonique.
- **Explication pédagogique :** Une URL est normalisée en supprimant paramètres et fragment, mais seuls HTTPS et hôtes valides sont acceptés.
- **Exemple concret :** Les dates non interprétables deviennent nulles; le pipeline n’invente pas de dates de publication.
- **Interprétation du résultat :** L’ancien script Pandas nettoie les fichiers Excel en supprimant espaces et doublons, mais ce n’est pas une preuve que les 88 offres historiques sont passées par ce script.
- **Localisation du code / source :** Ouvrir backend/collectors/schema.py lignes 18 à 47 et scripts/nettoyage_donnees.py.
- **Transition :** Transition : les contrôles produisent des statistiques de qualité.

## Diapositive 20 — Déduplication et qualité
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Un doublon de nom ou de titre est un signal, pas toujours la même entité ou annonce.
- **Explication pédagogique :** Aucun nom d’entreprise n’est dupliqué après casse et espaces; dix offres supplémentaires partagent un titre normalisé déjà présent.
- **Exemple concret :** La ville, le quartier, les coordonnées et le contrôle de fraîcheur manquent entièrement dans les champs concernés.
- **Interprétation du résultat :** 85 références sur 88 ne rapprochent pas par rowid.
- **Localisation du code / source :** Le nettoyage ne modifie pas la base; il décrit les limites observées.
- **Transition :** Transition : l’analyse exploratoire situe les secteurs et les dates.

## Diapositive 21 — Analyse exploratoire
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Les volumes de secteur sont calculés par regroupement SQL sur la colonne Secteur.
- **Explication pédagogique :** Le graphique montre les cinq catégories les plus nombreuses; Autre est une catégorie déjà présente en base.
- **Exemple concret :** Le nombre total des secteurs listés inclut RH et Commerce en plus des catégories affichées.
- **Interprétation du résultat :** L’absence de ville interdit de conclure sur la répartition géographique.
- **Localisation du code / source :** Les valeurs ne doivent pas être interprétées comme une mesure du marché de l’emploi actuel.
- **Transition :** Transition : les limites du dataset influencent la lecture des KPI.

## Diapositive 22 — Limites du dataset
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Une base peut être intègre au niveau du fichier tout en ayant une provenance ou une couverture incomplète.
- **Explication pédagogique :** Le contrôle SQLite valide la structure, pas la justesse ni l’actualité du contenu.
- **Exemple concret :** Exemple : l’application peut classer une offre comme active selon une date enregistrée, mais cette date n’est pas une vérification externe.
- **Interprétation du résultat :** Les contacts privés ne sont jamais présentés dans la soutenance.
- **Localisation du code / source :** Les futures actions doivent commencer par la permission des sources et la réconciliation des identifiants.
- **Transition :** Transition : les KPI sont calculés depuis ces tables et ces limites.

## Diapositive 23 — KPI de l’instantané
Statut : Parcours principal
- **Ce que je dois dire :** Les KPI présentés sont lus depuis SQLite et ne sont pas codés en dur.
- **Explication pédagogique :** Une candidature est un enregistrement privé, pas une offre.
- **Exemple concret :** Le nombre de runs à zéro permet de distinguer l’historique d’une collecte récente.
- **Interprétation du résultat :** Le KPI doit être accompagné de la date de l’instantané et du statut de vérification.
- **Localisation du code / source :** Les valeurs ont été vérifiées avec des requêtes COUNT sur la base locale et la base démo.
- **Transition :** Transition : Dash met ces indicateurs à jour selon les filtres.

## Diapositive 24 — Dashboard Dash
Statut : Parcours principal
- **Ce que je dois dire :** Dash utilise des callbacks Python pour recalculer la figure et les KPI.
- **Explication pédagogique :** Un filtre d’entreprise modifie l’exploration sans changer le contenu de la base.
- **Exemple concret :** L’export CSV reprend le jeu filtré selon le callback.
- **Interprétation du résultat :** Le dashboard omet la section Activité de collecte comme demandé dans les corrections précédentes.
- **Localisation du code / source :** Le compteur de candidatures peut contenir des informations privées; ne pas projeter de lignes nominatives.
- **Transition :** Transition : un callback montre la logique de mise à jour.

## Diapositive 25 — Callback Dash
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Le décorateur associe les composants d’entrée aux sorties graphiques et KPI.
- **Explication pédagogique :** La fonction relit la base puis applique les filtres dans load_data.
- **Exemple concret :** Le bloc calcule aussi les états de candidature et signale les valeurs manquantes.
- **Interprétation du résultat :** Le retour contient figure, composants KPI et résumé qualité.
- **Localisation du code / source :** Code : backend/analytics.py lignes 158 à 180; test : test_dash_real_routes_and_callbacks.
- **Transition :** Transition : la capture suivante montre l’interface réellement conservée.

## Diapositive 26 — Interface d’accueil
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Cette image est une capture d’interface présente dans le projet, pas une capture prise pendant le contrôle final.
- **Explication pédagogique :** Elle montre les principaux accès du parcours et les indicateurs d’accueil.
- **Exemple concret :** Les annonces et dates affichées sur une capture statique peuvent être périmées.
- **Interprétation du résultat :** Le jeu de données réel est décrit séparément par les requêtes SQLite du rapport.
- **Localisation du code / source :** Aucune information de candidat n’est visible dans cette capture.
- **Transition :** Transition : la recherche passe par les pages entreprises et offres.

## Diapositive 27 — Recherche entreprises et offres
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Les pages récupèrent d’abord l’API locale puis filtrent les lignes côté navigateur.
- **Explication pédagogique :** Un filtre ne recompose pas l’offre; il masque seulement les lignes qui ne correspondent pas.
- **Exemple concret :** L’URL de candidature passe par la validation safe_url du backend.
- **Interprétation du résultat :** Si ville ou type n’est pas renseigné, le système affiche un état manquant au lieu de deviner.
- **Localisation du code / source :** Ouvrir dashboard/js/ui.js lignes 85 à 104 et backend/api.py lignes 94 à 110.
- **Transition :** Transition : les coordonnées suivent une règle plus stricte.

## Diapositive 28 — Carte interactive
Statut : Approfondissement facultatif
- **Ce que je dois dire :** La carte utilise Leaflet et les tuiles publiques OpenStreetMap.
- **Explication pédagogique :** Une carte de fond ne prouve pas qu’un marqueur d’entreprise est exact.
- **Exemple concret :** Le frontend sépare les points vérifiés des éventuels points de démonstration et les étiquette.
- **Interprétation du résultat :** Dans l’instantané local, toutes les coordonnées manquent; aucun point réel ne doit apparaître.
- **Localisation du code / source :** OpenStreetMap est une ressource externe au chargement; aucun service Places n’a été appelé.
- **Transition :** Transition : l’écran Login possède également des limites d’isolation.

## Diapositive 29 — Authentification et confidentialité
Statut : Parcours principal
- **Ce que je dois dire :** La connexion protège l’accès mais ne crée pas d’espaces de données séparés par compte.
- **Explication pédagogique :** La passerelle indépendante possède des comptes scrypt et un proxy côté serveur, mais l’application existante conserve une base partagée.
- **Exemple concret :** Pour la soutenance, le profil historique reste réservé à son utilisateur local.
- **Interprétation du résultat :** La démo avec inscription utilise exclusivement des données synthétiques.
- **Localisation du code / source :** Le cœur doit être conçu et testé pour l’isolation avant d’enregistrer des CV privés sur une instance publique.
- **Transition :** Transition : le CV Builder produit un document local.

## Diapositive 30 — Créateur de CV
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Le formulaire transmet les champs au backend, qui valide puis chiffre le CV au repos.
- **Explication pédagogique :** ReportLab compose un document PDF à partir des valeurs validées.
- **Exemple concret :** Une version de démonstration doit contenir des renseignements fictifs.
- **Interprétation du résultat :** Les tests vérifient extraction du texte, aperçus et rejets de champs invalides.
- **Localisation du code / source :** La base privée auditée n’a aucun CV enregistré au moment du contrôle.
- **Transition :** Transition : le Matching compare ensuite le profil et les offres.

## Diapositive 31 — Matching IA
Statut : Parcours principal
- **Ce que je dois dire :** Le profil passe par une validation, puis les exigences sont extraites du texte de l’offre.
- **Explication pédagogique :** Les composantes couvrent compétences, formation, expérience, localisation et type d’opportunité.
- **Exemple concret :** Les pondérations totalisent 100; une ville absente laisse la composante localisation à zéro.
- **Interprétation du résultat :** Exemple pédagogique : 3 compétences repérées sur 4 contribuent au score, sans prédire un recrutement.
- **Localisation du code / source :** Tests : matching local explicable et profils représentatifs dans tests/test_application.py.
- **Transition :** Transition : le Chatbot utilise les mêmes offres SQLite.

## Diapositive 32 — Chatbot local
Statut : Parcours principal
- **Ce que je dois dire :** Le mode local récupère des résultats depuis SQLite et présente le contexte de sa réponse.
- **Explication pédagogique :** Le service peut compter les entreprises ou chercher des annonces pertinentes.
- **Exemple concret :** L’historique des messages du profil privé est chiffré à l’enregistrement.
- **Interprétation du résultat :** Un exemple sûr est de demander le nombre d’offres sur une base temporaire.
- **Localisation du code / source :** Aucune réponse Chatbot ne prouve qu’une offre est encore ouverte.
- **Transition :** Transition : Gemini peut compléter mais ne remplace pas les contrôles.

## Diapositive 33 — Gemini et recherche IA
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Gemini est un chemin facultatif distinct du moteur local.
- **Explication pédagogique :** La recherche exige une clé, les réglages d’activation, une confirmation du coût et des quotas.
- **Exemple concret :** Les résultats de recherche passent par une vérification humaine avant tout import.
- **Interprétation du résultat :** Les tests utilisent des réponses simulées et vérifient les erreurs/quota.
- **Localisation du code / source :** Aucune recherche Gemini réelle n’a été lancée et aucun service payant n’a été utilisé.
- **Transition :** Transition : les alertes et candidatures suivent des règles locales.

## Diapositive 34 — Alertes et candidatures
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Les alertes comparent les critères configurés avec les champs disponibles de l’offre.
- **Explication pédagogique :** Une clé unique empêche de créer plusieurs alertes identiques pour la même offre.
- **Exemple concret :** Les candidatures ont un historique de changement de statut.
- **Interprétation du résultat :** Les tests ne soumettent pas de vrais dossiers et n’envoient pas d’email à un recruteur.
- **Localisation du code / source :** Les 5 lignes historiques restent privées et ne sont pas montrées au jury.
- **Transition :** Transition : l’intégration partage les données via SQLite.

## Diapositive 35 — Chaîne d’intégration
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Le pipeline prévu commence par une source autorisée et vérifie le contenu.
- **Explication pédagogique :** Staging et approbation séparent une suggestion de la table des offres utilisées.
- **Exemple concret :** Une fois importée, l’offre SQLite devient disponible aux fonctions locales qui consultent cette table.
- **Interprétation du résultat :** La chaîne est testée avec fixtures, mais n’a pas été exécutée sur une source réelle.
- **Localisation du code / source :** La base historique contient zéro run; la chaîne complète n’est donc pas déclarée réalisée en production.
- **Transition :** Transition : les tests précisent exactement ce qui a été vérifié.

## Diapositive 36 — Tests logiciels
Statut : Approfondissement facultatif
- **Ce que je dois dire :** La suite totale contient 164 tests réussis et un avertissement non bloquant lié à un hook Dash/pytest ancien.
- **Explication pédagogique :** Les tests couvrent Flask, Dash, PDF, Matching, ETL, alertes, candidature, carte et passerelle.
- **Exemple concret :** Les connecteurs utilisent des mocks et fixtures; ils ne valident pas la disponibilité réelle des fournisseurs.
- **Interprétation du résultat :** L’intégrité SQLite et les clés étrangères ont été contrôlées séparément.
- **Localisation du code / source :** Aucun test de réseau payant ou de soumission externe n’a été exécuté.
- **Transition :** Transition : voici le résultat de la préparation et les limitations restantes.

## Diapositive 37 — Résultats vérifiés
Statut : Parcours principal
- **Ce que je dois dire :** Les chiffres proviennent des bases et des tests, non d’une valeur codée en dur dans l’interface.
- **Explication pédagogique :** L’empreinte de la base privée préparée correspond à celle de la copie initiale avant nettoyage.
- **Exemple concret :** Le script d’intégrité a retrouvé les 217 fichiers préexistants suivis sans différence.
- **Interprétation du résultat :** L’archive publique contient la base synthétique unique et aucun chemin privé listé.
- **Localisation du code / source :** Les historiques et sauvegardes restent dans la copie locale.
- **Transition :** Transition : la publication et l’hébergement sont volontairement distingués du code prêt.

## Diapositive 38 — GitHub et déploiement
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Le fichier render.yaml sert une configuration de démonstration et choisit le jeu public synthétique.
- **Explication pédagogique :** Une configuration de déploiement n’est pas un site en ligne.
- **Exemple concret :** Aucun dépôt GitHub ni URL déployée n’a été créé durant cette mission.
- **Interprétation du résultat :** Pour une démo distante, il faut TLS, hôtes autorisés, persistance et vérification des routes.
- **Localisation du code / source :** L’authentification ne rend pas la base privée adaptée à plusieurs utilisateurs.
- **Transition :** Transition : les difficultés principales viennent des données et des droits.

## Diapositive 39 — Difficultés rencontrées
Statut : Approfondissement facultatif
- **Ce que je dois dire :** Le principal risque de collecte est de confondre endpoint technique et autorisation.
- **Explication pédagogique :** Les références d’entreprise manquantes et les doublons de titres demandent une vérification humaine.
- **Exemple concret :** Le profil demo et le profil privé n’ont pas les mêmes données ni les mêmes droits.
- **Interprétation du résultat :** La passerelle Login ne transforme pas le cœur en application multiutilisateur.
- **Localisation du code / source :** Le dossier final reste une copie; les originaux sont conservés.
- **Transition :** Transition : les prochaines améliorations doivent viser les preuves et la sécurité.

## Diapositive 40 — Limites et suite du travail
Statut : Parcours principal
- **Ce que je dois dire :** Les améliorations proposées commencent par les risques directement mesurés.
- **Explication pédagogique :** Une provenance par offre rendrait la fraîcheur et les droits auditable.
- **Exemple concret :** La relation de 85 offres sur 88 doit être réconciliée avec une source fiable.
- **Interprétation du résultat :** Une ouverture multiutilisateur exige une architecture et des tests d’accès par utilisateur.
- **Localisation du code / source :** L’objectif n’est pas de revendiquer aujourd’hui une collecte ou un déploiement non validé.
- **Transition :** Transition : je conclus sur ce qui est réellement livré.

## Diapositive 41 — Conclusion
Statut : Parcours principal
- **Ce que je dois dire :** Stages Marrakech AI réunit une interface, des services de données et des outils d’aide à la candidature.
- **Explication pédagogique :** La base historique est conservée; les volumes et limites viennent d’une lecture réelle SQLite.
- **Exemple concret :** La suite automatisée valide les scénarios locaux, tandis qu’aucune collecte réelle ou URL déployée n’est présentée.
- **Interprétation du résultat :** L’évolution prioritaire est une provenance meilleure et une isolation réelle des données personnelles.
- **Localisation du code / source :** Je remercie le jury et réponds aux questions à partir du code et des rapports.
- **Transition :** Transition : fin de la présentation principale.

## Diapositive 42 — Annexe — extraits de code
Statut : Annexe à ouvrir pendant les questions
- **Ce que je dois dire :** Cette annexe sert à retrouver rapidement les points d’entrée devant le jury.
- **Explication pédagogique :** Un import de données passe par parsing, droits, staging et importRun; le raccourci d’une ligne ne résume pas les contrôles.
- **Exemple concret :** Par exemple, ouvrir backend/collectors/service.py et aller à la ligne 139.
- **Interprétation du résultat :** Le guide source contient 17 domaines, des extraits exacts et les tests associés.
- **Localisation du code / source :** Les lignes sont issues de l’arborescence de la copie finale.
- **Transition :** Transition : l’index CSV liste les symboles et leurs lignes.

## Diapositive 43 — Annexe — index du code
Statut : Annexe à ouvrir pendant les questions
- **Ce que je dois dire :** L’index a été construit à partir de l’AST Python et de repères vérifiés pour HTML, JavaScript, CSS et scripts Windows.
- **Explication pédagogique :** AST signifie arbre syntaxique abstrait; il permet de repérer des fonctions Python et leurs lignes.
- **Exemple concret :** Exemple : Ctrl+P puis backend/matching.py; Ctrl+G puis ligne 67.
- **Interprétation du résultat :** Les extraits du guide sont copiés directement depuis les fichiers de la préparation.
- **Localisation du code / source :** Ce repère n’est valide qu’avec la version livrée.
- **Transition :** Transition : la dernière annexe aide à répondre aux questions récurrentes.

## Diapositive 44 — Annexe — questions du jury
Statut : Annexe à ouvrir pendant les questions
- **Ce que je dois dire :** Le document questions-réponses contient quarante questions avec réponses alignées sur le code.
- **Explication pédagogique :** Une réponse académique distingue toujours le code présent, un test simulé et un service utilisé en production.
- **Exemple concret :** Un exemple de réponse honnête est : les connecteurs existent, mais aucun run réel n’est inscrit.
- **Interprétation du résultat :** Le guide de lancement recommande un parcours sans API payante ni modification de la base privée.
- **Localisation du code / source :** Gardez les annexes ouvertes pour justifier une réponse par fichier et ligne.
- **Transition :** Fin des annexes.
