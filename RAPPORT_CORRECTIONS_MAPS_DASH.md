# Rapport de corrections — Carte OpenStreetMap et retour Dash

**Projet :** Stages Marrakech AI  
**Date :** 6 novembre 2026  
**Périmètre :** carte des entreprises et navigation du dashboard Dash. Les parcours CV, Gemini, SMTP et matching n’ont pas été modifiés pour cette correction.

## Résumé

La page Carte affiche maintenant un fond interactif Leaflet/OpenStreetMap de Marrakech, sans clé Google. La carte reste visible même avec zéro entreprise géolocalisée. Aucun point d’entreprise n’a été inventé. Le lien « Retour à l’application » sort maintenant de l’iframe Dash et revient à la page Flask principale. Les données SQLite historiques sont identiques à la sauvegarde prise avant modification.

## Cause exacte du problème Dash

La page Flask `analyses.html` intègre `/analytics/` dans un iframe. Le lien de retour Dash ciblait `/index.html` sans attribut `target`, donc le navigateur chargeait Flask *dans l’iframe*. La sidebar/header imbriqués résultaient de cette navigation dans le cadre enfant, pas d’un doublon à masquer dans le CSS.

Le lien porte désormais `target="_top"` : il navigue dans la fenêtre principale. Les deux préfixes Dash sont explicitement configurés sur `/analytics/` (`requests_pathname_prefix` et `routes_pathname_prefix`), ce qui maintient les callbacks et ressources Dash sous la bonne route Flask.

## Carte et données géographiques

- Fond : Leaflet 1.9.4, fichiers distribués localement sous `dashboard/vendor/leaflet/`; tuiles OSM `https://tile.openstreetmap.org/{z}/{x}/{y}.png`.
- Centre initial : Marrakech (31.6295, -7.9811), avec zoom, déplacement et attribution OpenStreetMap visibles.
- Le conteneur étant construit avant son insertion dans la page, Leaflet pouvait calculer une taille nulle. Après son ajout au DOM, `invalidateSize()` recalcule le viewport; les tuiles et marqueurs sont alors placés correctement.
- Le chargement des tuiles est suivi : la page indique le succès ou l’indisponibilité du fond. Si une tuile échoue, l’état d’erreur reste prioritaire sur l’événement de fin de chargement. Le cas de panne a été simulé dans Chrome. Sur mobile, la hauteur est adaptée.
- Les marqueurs d’entreprise proviennent uniquement des coordonnées vérifiées avec provenance/date; popup avec nom, secteur, adresse, téléphone, site, itinéraire et accès à la fiche. Recherche et filtres nom/secteur/quartier sont conservés.
- Les trois points de démonstration restent facultatifs et explicitement fictifs. Ils ne sont jamais écrits dans SQLite.
- L’audit de SQLite (`292 entreprises`) trouve zéro latitude/longitude enregistrée et zéro ligne géographique vérifiée. Les neuf classeurs Excel contrôlés ne comportent pas de colonnes de latitude, longitude, coordonnées ou provenance géographique. Aucun champ de coordonnée existant n’a été rempli : les colonnes nécessaires étaient déjà dans le schéma.
- L’import CSV existant accepte les coordonnées vérifiées, contrôle plages, date, provenance et identifiant d’entreprise, puis sauvegarde SQLite avant écriture. Un test automatisé valide l’import sur une base jetable.
- Les liens Google Maps historiques restent inchangés. Google Places/Maps n’est pas appelé par l’affichage cartographique et aucune clé n’est requise.

Les tuiles OSM sont un service Internet externe fourni au mieux. L’application ne précharge pas de tuiles et ne crée pas de mode hors ligne. Garder l’attribution visible et respecter la [politique des tuiles OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/) (requêtes interactives normales, cache HTTP, pas de téléchargement en masse). Si le service est inaccessible, seul le fond distant manque; les données et liens locaux restent disponibles. Les tuiles standard peuvent changer ou être soumises à limitation par leur fournisseur.

## Fichiers principaux modifiés

- `backend/analytics.py` : préfixes explicites et navigation retour dans la fenêtre principale.
- `backend/web.py` : service des fichiers Leaflet locaux et autorisation CSP des tuiles OSM.
- `dashboard/js/ui.js` : affichage Leaflet, attribution, statuts de tuiles, marqueurs vérifiés/fictifs et invalidation du viewport après insertion DOM; suppression du chargeur Google Maps devenu inutile.
- `dashboard/css/map-leaflet.css` : dimensions adaptatives et présentation des popups; importé depuis `dashboard/css/design.css`.
- `dashboard/vendor/leaflet/` : Leaflet 1.9.4, CSS/JS, images nécessaires et licence.
- `tests/test_map_dash.py` : cinq tests unitaires sur assets/CSP, liens historiques et absence de points réels, filtres/affichage, retour Dash et import CSV.
- `tests/browser_smoke.py` : parcours Chrome étendu; la coordonnée d’essai n’existe que dans une copie temporaire et anonymisée de la base.
- `README.md`, `GUIDE_TEST_MANUEL.md`, manifeste SHA-256 et ce rapport.

## Vérifications

- **Pytest : 72 réussis, 0 échec**, 1 avertissement de dépréciation venant du plugin Dash/pytest installé.
- **Chrome/Playwright : 20 contrôles réussis**, 0 erreur JavaScript. Le parcours Accueil → Dash → retour Flask est répété trois fois; chaque cycle vérifie URL, session, une seule sidebar/header et absence d’iframe après retour. Le graphique et le changement d’onglet Dash restent fonctionnels.
- Le navigateur a affiché la carte OSM : 60 requêtes de tuiles observées, y compris le scénario de panne simulée; les tuiles chargées normalement ont répondu HTTP 200. La page a affiché l’erreur lorsqu’elles ont été bloquées. Aucune requête Google/Places, Gemini, SMTP ou autre service externe n’a été observée.
- Test carte avec une coordonnée synthétique temporaire : marqueur, popup, itinéraire, fiche et trois points fictifs vérifiés. Puis coordonnées de fixture supprimées de la copie temporaire : Marrakech reste visible et affiche zéro marqueur entreprise. Blocage volontaire des tuiles : le message d’indisponibilité apparaît.
- **SQLite :** `integrity_check = ok`; les six tables et toutes leurs lignes/colonnes sont identiques à la sauvegarde préalable; comptes inchangés : 292 entreprises, 88 offres, 5 candidatures historiques.
- Aucune migration ou modification de la base principale n’a été nécessaire.

La seule limite du test navigateur reste Windows qui refuse l’écriture directe d’un téléchargement par Chrome automatisé (« Insufficient permissions »). L’événement de téléchargement et la réponse PDF HTTP ont été vérifiés séparément, comme dans le parcours Phase 4.

## Captures

- `reports/screenshots_maps_dash/01_retour_dash_accueil.png` : accueil après retour Dash.
- `reports/screenshots_maps_dash/02_carte_marqueur_fixture_synthetique.png` : clic et marqueur d’essai synthétique (copie temporaire de test uniquement).
- `reports/screenshots_maps_dash/03_carte_marrakech_zero_coordonnees.png` : fond Marrakech avec zéro coordonnée réelle.

## Installation et configuration externe

Aucune clé Google, facturation, compte SMTP ou privilège administrateur n’est requis. L’installation existante reste la même (`INSTALLER_WINDOWS.bat`, puis `LANCER_APPLICATION.bat`). Le fond cartographique exige une connexion Internet et un navigateur pouvant joindre les tuiles HTTPS d’OpenStreetMap. Pour obtenir de vrais marqueurs à l’avenir, une personne devra vérifier les coordonnées et importer le CSV selon `README.md`; aucun géocodage automatique n’est activé.
