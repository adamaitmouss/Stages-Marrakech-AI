# Guide de lancement local pour la soutenance

## Avant de commencer

Gardez la base historique `database/stages_marrakech.db` et le dossier `private/` ensemble. L'application utilise le compte local configuré sur ce poste. Le lancement ne demande pas de droits administrateur et n'appelle aucun service externe.

## Lancement

1. Fermez votre serveur de démonstration depuis sa fenêtre de lancement. Si vous ne savez pas quelle fenêtre le contrôle, demandez à la personne qui a lancé le serveur d'identifier son processus; ne terminez pas un processus au hasard.
2. Double-cliquez `LANCER_SOUTENANCE_LOCALE.bat`.
3. Vérifiez que les contrôles affichent la base locale, le mode privé, SQLite intègre et le port libre.
4. Ouvrez `http://127.0.0.1:5000`. L'accueil doit montrer 292 entreprises, 88 offres et 5 candidatures.
5. Arrêtez le serveur avec Ctrl+C dans la fenêtre qui l'exécute.

Si une vérification échoue, le lanceur s'arrête avant de lancer Flask. Il ne supprime, remplace ou migre aucune base. Un port occupé signifie qu'une application écoute déjà sur 5000; identifiez-la et arrêtez-la proprement avant de réessayer.

Les contrôles de lancement lisent SQLite en mode lecture seule, vérifient `integrity_check`, les tables, les liens et le marqueur de données synthétiques. Le mode privé impose le chemin absolu `database/stages_marrakech.db` de ce dossier de projet.
