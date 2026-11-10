# Rapport de récupération et de protection des données

Date : 9 novembre 2026

## Résultat

La base historique n'avait pas été supprimée. La base locale active est `database/stages_marrakech.db` : SQLite version 6, intégrité `ok`, 292 entreprises, 88 offres, 5 candidatures et aucune ligne CV. La base synthétique distincte `database/stages_marrakech_public_demo.db` contient 5 entreprises, 4 offres et 3 candidatures. Les relations de la base historique ne signalent aucune erreur.

Les volumes historiques ont été vérifiés en lecture seule. Une sauvegarde SQLite a été créée avant les changements dans `backups/before_soutenance_mission_20261108_235804/`; son intégrité et ses volumes 292/88/5 ont été contrôlés. Aucune donnée historique n'a été remplacée ni modifiée.

## Origine de l'affichage 5/4/3

Le serveur qui répond actuellement sur `127.0.0.1:5000` annonce `public_demo=true` sur `/api/auth/session` et sert une réponse Flask/Werkzeug. Il s'agit d'une instance en mode public synthétique, cohérente avec l'affichage 5/4/3. L'instance est déjà en écoute; les outils Windows disponibles n'ont pas révélé son PID. Elle n'a pas été arrêtée ni réutilisée. Le lanceur de soutenance refuse tout port occupé.

La résolution du chemin SQLite dans `backend/config.py` rend maintenant les chemins relatifs indépendants du dossier de lancement : ils sont ancrés sur la racine du projet. `LANCER_SOUTENANCE_LOCALE.bat` définit explicitement le profil privé et le chemin absolu de la base historique.

## Procédure sûre

1. Conserver ensemble la base `database/stages_marrakech.db` et son dossier `private/`.
2. Fermer volontairement l'application de démonstration depuis la fenêtre dans laquelle elle a été lancée, ou demander à l'administrateur de l'instance d'identifier son processus.
3. Lancer `LANCER_SOUTENANCE_LOCALE.bat`. Il vérifie Python, dépendances, profil privé, intégrité SQLite et disponibilité du port avant démarrage.
4. Vérifier dans l'application les statistiques 292/88/5 et le mode privé.

Le lanceur ne tue aucun processus, ne crée pas une nouvelle base si la base historique manque et ne modifie pas SQLite durant ses contrôles.
