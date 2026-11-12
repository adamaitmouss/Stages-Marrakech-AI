# Stages Marrakech — application locale modernisée

Flask + SQLite + HTML/CSS/JavaScript, avec CV PDF ReportLab, matching explicable et véritable dashboard Python Dash. Les données d’origine sont conservées. Aucun compte Gemini/Maps/SMTP n’est nécessaire au lancement.

État Phase 9 : migration SQLite additive version 6, intégrité vérifiée, 292 entreprises, 88 offres et 5 candidatures préservées. Greenhouse, Lever, Ashby, SmartRecruiters et RSS/Atom réutilisent le pipeline de prévisualisation contrôlée. La page **Recherche IA** distingue recherche locale SQLite, démonstration sur base temporaire et recherche Gemini Search optionnelle. Gemini et la collecte externe restent désactivés par défaut; aucun appel Google réel ni import d’offre réelle n’a été réalisé en Phase 9. CSV/XLSX et résultats Gemini autorisés passent par provenance, droits, staging et confirmation d’import.

La recherche Gemini peut être payante et une demande peut déclencher plusieurs recherches. Configurez-la uniquement après vérification de votre accès et de la facturation; voir `GUIDE_CONFIGURATION_API.md`. Pour les modes locaux et de démonstration, voir `GUIDE_GEMINI_SEARCH.md`.

## Profils de données séparés

- **Local privé** : `.env.example` sélectionne `database/stages_marrakech.db`, avec `PUBLIC_DEMO_MODE=false`. Cette base historique demeure uniquement dans l’environnement local privé. Le `.env` existant n’est pas écrasé par l’installateur.
- **Démonstration publique** : `.env.public-demo.example` sélectionne `database/stages_marrakech_public_demo.db` et active le mode lecture seule. Le dataset inclus contient des lignes fictives marquées `synthetic_public_demo`.
- Ne copiez jamais la base historique, les candidatures ou les CV dans l’archive publique. Le mode de démonstration exige un marqueur synthétique valide et bloque les mutations.

## Démarrer sous Windows

Décompressez la copie locale privée dans un dossier accessible à votre compte Windows. Installez Python 3.12 si nécessaire. Double-cliquez `INSTALLER_WINDOWS.bat` : il crée `.venv`, copie `.env.example` vers `.env` uniquement si `.env` n’existe pas et demande confirmation avant de télécharger les dépendances. Il n’a pas besoin des droits administrateur et ne modifie pas Python global. Pour l’usage quotidien avec Login et la base historique, double-cliquez `LANCER_MON_PROJET.bat`. `VERIFIER_INSTALLATION.bat` relance les contrôles sans modifier SQLite.

`LANCER_MON_PROJET.bat` force `AUTH_PROFILE=private` et le chemin absolu `database/stages_marrakech.db`; la passerelle, Flask et Dash utilisent ce même fichier. Le lancement crée automatiquement un secret aléatoire local, ignoré par Git, pour le canal privé entre les deux services. Aucun mot de passe technique n'est demandé. Le lanceur vérifie la base et refuse de démarrer si le port 5000 ou 5101 est occupé; il ne termine aucun processus existant. `LANCER_APPLICATION_AVEC_LOGIN.bat` appelle le même lanceur. `LANCER_SOUTENANCE_LOCALE.bat` reste disponible pour démarrer Flask directement, sans la passerelle Login.

Depuis PowerShell ouvert à la racine du dossier extrait, lancez :

```powershell
.\INSTALLER_WINDOWS.bat
.\VERIFIER_INSTALLATION.bat
.\LANCER_MON_PROJET.bat
```

Pour ouvrir l'application principale avec Login, utilisez `.\LANCER_MON_PROJET.bat`. Le compte local actif existant reste autorisé; Register reste présent mais la création de nouveaux comptes est désactivée car les candidatures et CV ne sont pas isolés par utilisateur.

L’application est disponible sur [http://127.0.0.1:5000](http://127.0.0.1:5000). Connectez-vous avec le compte et le mot de passe déjà présents dans la base locale des comptes. Le mot de passe du compte n'est ni affiché ni réinitialisé par le lanceur. Flask sert les pages et l’API sur la même origine. Pour arrêter : Ctrl+C dans la fenêtre du serveur.

N’ouvrez pas directement les HTML par `file://` : ils ont besoin du serveur. Dash est intégré à Flask sur `/analytics/` et accessible depuis « Analyses Dash ». Le serveur écoute uniquement `127.0.0.1`, sans debug. Une publication Internet nécessiterait un déploiement HTTPS, une gestion de compte et un audit complémentaire ; aucun déploiement n’est effectué ici.

## Parcours disponibles

- **Accueil** : chiffres de SQLite, offres récentes, secteurs et accès rapides.
- **Entreprises** : recherche par nom, filtre secteur, coordonnées, liens Maps/site et candidature spontanée avec confirmation du contact.
- **Offres** : recherche, filtres stage/contrat, bouton Postuler et classement des dates d’expiration connues (actives en premier, expirées signalées). Une date absente ou illisible reste « Validité inconnue ». Le nom d’entreprise reste non renseigné lorsque seule l’identité source est connue.
- **Créateur de CV** : champs personnels, formation/expériences/projets/certifications répétables, compétences/langues, deux modèles, aperçu PDF réel généré par ReportLab et aperçu texte accessible, sauvegarde de versions et PDF téléchargeable avec texte sélectionnable. Chargez une ancienne version, modifiez-la, puis enregistrez une nouvelle version. Les périodes numériques inversées sont refusées. Les versions inutilisées se suppriment après confirmation ; celles liées au suivi sont protégées. « Charger un exemple fictif » ne sauvegarde rien sans votre action.
- **Optimiser mon CV pour une offre** : compare un CV enregistré à une offre SQLite, repère compétences communes et absentes, propose de réordonner des expériences/projets pertinents et, si des phrases du résumé citent déjà ces compétences, propose de les remonter. Chaque proposition peut être acceptée ou ignorée. Une acceptation change seulement le brouillon en mémoire; elle n’enregistre pas de nouvelle version automatiquement. Aucun fait n’est inventé et une compétence manquante n’est jamais ajoutée comme acquise.
- **Matching IA** : CV enregistré ou extraction PDF locale, champs modifiables, poids configurables, classement, compétences communes/manquantes, repère de niveau et détail de chaque contribution. Un profil fictif permet une démonstration sans clé. Les niveaux sont des repères sur les textes disponibles, pas des probabilités d’embauche.
- **Mes candidatures** : anciennes données conservées, création, recherche, filtres, changement de statut, notes, historique et tentatives SMTP. La suppression physique est volontairement bloquée pour conserver l’historique.
- **Carte** : Leaflet avec fond OpenStreetMap interactif centré sur Marrakech (zoom/déplacement), attribution visible et repli explicite si les tuiles sont indisponibles. Seules les coordonnées avec provenance/date vérifiées deviennent des marqueurs. Les liens Google Maps historiques restent accessibles ; trois points fictifs sont disponibles par une case explicite.
- **Analyses Dash** : onglets Offres/Entreprises/Candidatures, filtres période/secteur/type/contrat/entreprise quand les colonnes ou relations vérifiées existent, cinq types de graphique, KPI synchronisés au jeu et aux filtres, qualité des données, CSV filtré et téléchargement PNG. Le filtre secteur des offres utilise uniquement les relations d’entreprise explicitement vérifiées. Courbe réservée aux dates, histogramme réservé aux séries temporelles. Les coordonnées inconnues et compétences non structurées n’apparaissent pas comme données fiables. La section « Activité de collecte » a été retirée; le Centre de collecte et son historique restent dans l’application.
- **Centre de collecte** : simulation locale sans réseau, aperçus RSS/JSON seulement après autorisation, approbation individuelle et import CSV/XLSX de données d’offres légalement remises. La provenance, la référence d’autorisation, l’empreinte du fichier et les comptes de rejet/import sont journalisés. La collecte réseau et l’automatisation sont désactivées par défaut.
- **Phase 8** : registre des boards/carrières par entreprise, adaptateurs Greenhouse/Lever/Ashby/SmartRecruiters/RSS, classification explicable prudente, mapping des colonnes offres et entreprises. Consultez [RAPPORT_PHASE8.md](RAPPORT_PHASE8.md), [Guide API](GUIDE_CONNECTEURS_API.md), [Guide sites carrières](GUIDE_SITES_CARRIERES.md), [Guide CSV/Excel](GUIDE_IMPORT_CSV_EXCEL.md) et [rapport des tests](RAPPORT_TESTS_PHASE8.md). Les API publiques ne valent pas autorisation de réutilisation; configurez uniquement les sources couvertes par un accord adapté.
- **Recherche IA sur Internet** : recherche locale SQLite, démonstration complète sur base temporaire et connecteur Gemini Search optionnel avec citations Grounding. Les résultats sont des candidats, et leur staging/import exige un contrôle manuel, la référence d’autorisation et les droits de consultation, stockage et réaffichage. Gemini Search reste désactivé par défaut et peut être payant. Voir [RAPPORT_PHASE9.md](RAPPORT_PHASE9.md), [guide de recherche](GUIDE_GEMINI_SEARCH.md), [configuration API](GUIDE_CONFIGURATION_API.md) et [tests Phase 9](GUIDE_TEST_PHASE9.md).
- **Mes alertes** : alertes SQLite avec critères réglables, explication du score, compteur non lu et activation explicite. Les emails sont facultatifs, chiffrés localement et nécessitent consentement ainsi qu’une configuration SMTP explicite.
- **Assistant Stages Marrakech AI** : recherche locale par défaut sur les offres/entreprises SQLite. Gemini est facultatif avec prévisualisation et consentement distincts; aucun CV complet n’est transmis.

## Données, sauvegardes et confidentialité

Guides : [activation des collectes réelles](GUIDE_ACTIVATION_COLLECTE.md), [registre Phase 7 et autorisations](GUIDE_SOURCES_AUTORISEES.md), [rapport Phase 7](RAPPORT_PHASE7.md), [rapport de tests Phase 7](RAPPORT_TESTS_PHASE7.md), [alertes](GUIDE_ALERTES.md) et [assistant](GUIDE_CHATBOT_IA.md). Aucun droit de réutilisation pour une source d’offres en ligne n’est documenté; le parcours CSV/XLSX accepte un fichier légalement fourni avec validation des droits de consultation, stockage et réaffichage. Aucun appel Google Search réel n’a eu lieu en Phase 9.

Base principale : `database/stages_marrakech.db`. La base homonyme racine historique n’est pas utilisée. Le code n’efface ni offres, ni entreprises, ni anciennes candidatures.

La migration additive est exécutée au démarrage si nécessaire, avec sauvegarde SQLite préalable dans `backups/`. Les nouveaux champs restent vides lorsque l’information est inconnue. Les historiques de statut initiaux documentent l’état au moment de la migration, sans inventer les changements antérieurs.

Les profils CV enregistrés sont chiffrés avec Fernet dans la table `cvs`. La clé locale est `private/cv.key` ; le mot de passe est haché dans `private/auth.json`. Aucun CV ni candidature n’est servi sans connexion. Les anciens PDF et fichiers Excel restent présents sur disque, mais ne sont pas accessibles par les routes HTTP.

**Sauvegarde à conserver en privé : base SQLite ET dossier `private/`, ensemble.** Sans `cv.key`, les nouvelles versions chiffrées ne peuvent pas être relues. La base historique et les sauvegardes ne sont pas chiffrées intégralement ; le contrôle d’accès au dossier Windows et, si souhaité, le chiffrement du disque restent nécessaires. `.gitignore` exclut clés, bases, CV, sauvegardes et données de suivi. Le dossier de travail local contient vos données historiques; ne partagez pas son ZIP brut. Utilisez uniquement la copie `PROJET_PUBLIC.zip` assainie, dont la base est synthétique et qui exclut CV, candidatures réelles et `.env`.

L’application est un espace personnel local à compte unique. La clé de session est persistante dans `private/session.key`. Pour réinitialiser un mot de passe oublié : arrêter l’application, sauvegarder `private/`, renommer uniquement `private/auth.json`, puis redémarrer et créer un nouveau mot de passe. Ne supprimez pas `cv.key`.

Si une page ancienne renvoie un jeton CSRF expiré, l’interface récupère un jeton frais uniquement lorsque l’endpoint confirme que la session est toujours authentifiée, puis réessaie une fois. Une session déconnectée exige une reconnexion; la protection CSRF n’est pas désactivée.

Aucune donnée de CV n’est placée dans localStorage ; seul le thème clair/sombre y est conservé. Le profil non sauvegardé reste en mémoire de la page. Pas de journalisation des corps de requêtes ou CV. Aucun cache distant de profils. Authentification, cookie HttpOnly/SameSite Strict, CSRF pour les API d’écriture, contrôle d’origine, politique CSP et rendu DOM sans innerHTML protègent les interactions courantes. Les fichiers privés ne sont jamais servis par le serveur.

## Score de matching

Score indicatif, **pas une probabilité d’obtenir un stage**. Pondérations par défaut : compétences 40, formation/domaine 25, expériences/projets 15, localisation 10, opportunité 10. La somme doit être 100. Elles se règlent dans l’interface et sont validées côté serveur.

Les recommandations locales sont regroupées avec des seuils d’aide au tri : ≥70, 40–69 et <40; une offre incertaine reste dans le groupe intermédiaire. Ces catégories ne prédisent pas le recrutement. Consultez `GUIDE_MATCHING_IA.md`.

Le score final est la somme des contributions affichées : `composante entre 0 et 1 × poids`. Compétences : couverture des compétences repérées dans l’offre, avec quelques alias contrôlés. Formation/domaine et expérience/projets : similarité cosinus TF-IDF implémentée localement. Localisation : égalité normalisée avec une ville connue, sinon zéro signalé. Type : égalité avec le contrat demandé. Les données absentes ne sont pas inventées et les descriptions pauvres sont signalées comme incertaines. Ce moteur simple ne mesure ni aptitude réelle ni qualité du candidat ; il doit être évalué sur des jugements humains avant tout usage décisionnel.

Gemini peut extraire compétences/domaine à partir d’un texte professionnel relu et interpréter les rapprochements sur les huit offres de la présélection locale. Les réponses JSON sont vérifiées : compétence candidate existante et preuve citée dans l’offre. Le score reste calculé en Python ; les autres offres gardent leur score local. Les propositions sémantiques restent à relire : une validation JSON ne garantit pas leur justesse.

## Activer Gemini manuellement

Documentation officielle vérifiée le 3 novembre 2026 : [tarifs Gemini](https://ai.google.dev/gemini-api/docs/pricing), [fiche Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [SDK Python Google GenAI](https://googleapis.github.io/python-genai/). La fiche indique le modèle stable et les sorties structurées. La page tarifs liste l’entrée/sortie standard en niveau gratuit, mais les quotas et l’éligibilité dépendent du compte et peuvent changer. Le logiciel ne peut pas vérifier votre facturation Cloud ni garantir qu’une clé attachée à un compte payant reste gratuite.

1. Créez/vérifiez votre projet dans Google AI Studio, sans activer de facturation payante pour cette démonstration.
2. Consultez les conditions du niveau gratuit et les quotas actuels. Le niveau gratuit peut utiliser le contenu pour améliorer les produits Google.
3. Dans votre `.env` local : renseignez `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.5-flash-lite`, `GEMINI_ENABLED=true` et `GEMINI_FREE_TIER_CONFIRMED=true` après vérification.
4. Redémarrez Flask. Dans Matching, relisez/anonymisez les champs, prévisualisez **exactement** le contenu à envoyer et cochez le consentement. Les coordonnées structurées ne sont pas envoyées ; emails/téléphones/URL sont filtrés, mais vous devez retirer manuellement noms et détails identifiants dans les textes libres.

Timeout 20 secondes ; aucun retry automatique en cas de quota/429 ou indisponibilité. Fallback local et message explicite. Aucun modèle payant alternatif n’est choisi automatiquement. Une liste contrôlée limite actuellement ce mode à Flash-Lite 3.5 ; pour un autre modèle, mettez à jour la validation de `gemini_service.py` après vérification de sa documentation/tarification. Aucune requête Gemini réelle n’a été faite pendant le développement.

## Candidature externe et SMTP

Sur une offre, choisissez un CV et vérifiez le récapitulatif. « Ouvrir la page » ne crée pas de statut Envoyée. Vous devez ensuite confirmer avoir réellement postulé. Vous pouvez aussi confirmer l’enregistrement À préparer (statut Non envoyée). Le double clic sur une offre/CV réutilise l’entrée existante.

Les offres ne sont pas reliées automatiquement aux entreprises Places. Un email d’offre n’est utilisable que si une relation explicite vérifiée, une adresse validée et les coordonnées de la même entreprise concordent. Aucune correspondance approximative n’est créée sur la base livrée. Pour une candidature spontanée, choisissez une adresse déjà connue de la fiche entreprise et confirmez l’avoir vérifiée sur le site officiel.

SMTP est **désactivé par défaut**. Après vérification manuelle de votre compte (et mot de passe d’application si le fournisseur le demande), renseignez dans `.env` `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, puis `SMTP_ENABLED=true`. Redémarrez. L’envoi exige une confirmation explicite. Le destinataire provient du contact validé, jamais automatiquement de SMTP_USER. Le CV est généré depuis une version sauvegardée ; pas de fichier arbitraire envoyé à une adresse devinée.

Pièces importées : PDF lisible, non chiffré, 5 Mo maximum et 15 pages maximum. Requête HTTP limitée à 6 Mo. Pas d’OCR. Timeout SMTP 20 secondes, STARTTLS avec validation TLS. Chaque envoi porte une clé d’idempotence persistante et une empreinte de la requête. Les tentatives pending/sent/uncertain sont consultables ; aucune répétition automatique. Une panne après acceptation SMTP peut laisser un statut incertain : vérifier la boîte d’envoi avant de créer une nouvelle tentative. Un courriel accepté par SMTP n’est pas une garantie de réception ou de lecture.

## Carte et coordonnées

Le mode local et les liens existants ne nécessitent aucune clé. **Aucune coordonnée n’a été inventée ou ajoutée aux 292 entreprises.** Les futurs collecteurs Places demandent `places.id`, `places.location` et `nextPageToken`, stockent provenance/date, et restent bloqués sans `--allow-external`.

Pour importer un CSV vérifié par vos soins, sans réseau :

```powershell
.\.venv\Scripts\python.exe scripts\import_coordinates.py chemin\coordonnees.csv --confirm-verified
```

Colonnes UTF-8 : `entreprise_id,place_id,latitude,longitude,source,verified_at,quartier,ville`. `entreprise_id` est l’ID de la liste API (rowid existant). Vérifiez chaque rapprochement ; la commande sauvegarde la base puis valide plages, date, provenance et identité. Ne réutilisez pas les points fictifs comme coordonnées réelles.

La carte affichée utilise les tuiles raster standard d’OpenStreetMap via HTTPS et n’a besoin d’aucune clé Google ni de requête Places. L’attribution OpenStreetMap reste affichée. Le fond dépend d’Internet et du service communautaire, fourni au mieux, sans garantie de disponibilité : en cas d’indisponibilité, un message est affiché et les fiches/liens locaux restent accessibles. Le client ne précharge pas les tuiles et ne propose pas de mode hors ligne. Respectez la [politique officielle des tuiles OSM](https://operations.osmfoundation.org/policies/tiles/) : usage interactif normal, cache HTTP et attribution, pas de téléchargement en masse ou de préchargement. Les points d’entreprise ne sont affichés que si leur provenance et date de vérification sont présentes. Google Places demeure optionnel, désactivé par défaut, et n’est pas appelé par cette carte.

Sources : [Text Search New et champs facturés](https://developers.google.com/maps/documentation/places/web-service/text-search), [tarifs Maps Platform](https://developers.google.com/maps/billing-and-pricing/pricing), [contrôle des coûts et quotas](https://developers.google.com/maps/billing-and-pricing/manage-costs), [sécurisation des clés Maps](https://developers.google.com/maps/api-security-best-practices). Les conditions de stockage/attribution et rafraîchissement des données Places doivent être vérifiées avant une nouvelle collecte. Aucun service Cloud ou facturable n’est activé par l’application.

## Pipeline historique

Les scripts ont gardé leur rôle, avec chemins ancrés sur la racine et exécution sous main. Collectes/enrichissements écrivent dans `data_raw` ; audit et nettoyage lisent `data_raw`, puis produisent `data_clean`. Les analyses consomment les fichiers nettoyés. Aucun script de collecte ne s’exécute à l’import.

Le fichier historique `docs/config.json` est conservé comme trace des sources prévues ; il ne lance aucune collecte et n’est pas la configuration active. Les réglages de l’application sont dans `.env` et `backend/config.py`.

Les trois clés Google littérales ont été retirées. **La clé précédemment distribuée doit être révoquée/renouvelée dans votre compte Google : le code ne peut pas annuler cette exposition passée.** Ne remettez pas l’ancienne clé. Nouvelle variable : `GOOGLE_PLACES_API_KEY`. Les commandes de collecte exigent `--allow-external`, qui constitue une autorisation manuelle pour la commande concernée. Ne les lancez qu’après évaluation des coûts, quotas et conditions des sources.

`scripts/create_database.py` appelle désormais un import Excel non destructif : sauvegarde, validation des identifiants, ajout/mise à jour sur Nom pour entreprises et ID pour offres, aucune suppression et aucune modification des candidatures. Les noms ne constituent pas un identifiant universel fiable : contrôlez les homonymes avant réimport. Les fichiers Excel nettoyés continuent d’être produits par le pipeline séparé ; modifier un Excel ne change pas automatiquement SQLite.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

Le contrôle de livraison du 9 novembre 2026 sur la copie locale préparée a réussi **164 tests pytest** en 51,94 s, avec un avertissement non bloquant Dash/pytest. La copie publique a déjà réussi **163 tests avec 1 test ignoré** (test du lanceur privé absent de cette copie). Les tests utilisent des bases temporaires et des fixtures; ils ne prouvent pas une collecte réelle, un service externe ou une sécurité en production. Les résultats et limites sont dans `docs/RAPPORT_VALIDATION_DEFINITIVE.md`.

La présentation de 45 diapositives a été exportée puis inspectée sur ses rendus. Le contrôle dans le navigateur de l'application n'a pas abouti : le serveur de la copie préparée s'est arrêté car elle ne contenait pas son propre environnement `.venv`. Installez les dépendances via `INSTALLER_WINDOWS.bat`, puis suivez `docs/GUIDE_LANCEMENT_SOUTENANCE.md`. Les captures intégrées sont historiques et ne constituent pas une validation navigateur de cette livraison. Le fichier PPTX a passé les contrôles structurels; l'ouverture dans Microsoft PowerPoint n'a pas été attestée.

## Limites connues

Espace personnel local, pas une plateforme multiutilisateur déployée. Les CV PDF visent le français/latin ; mise en page arabe RTL et OCR non intégrés. Le modèle ATS est textuel à une colonne, sans garantie sur tous les logiciels ATS. SMTP/Maps/Gemini n’ont pas été appelés en réel et le matching n’est pas évalué sur un corpus annoté. Consultez `docs/RAPPORT_VALIDATION_DEFINITIVE.md` pour les résultats mesurés et limites restantes.

