# Rapport des tests — authentification externe

Date : 9 novembre 2026

## Résultats

- Suite complète `pytest -q` : **164 réussis, 0 échec**, 64,70 s; un avertissement non bloquant Dash/pytest.
- Copie publique : **163 réussis, 1 ignoré, 0 échec**, 65,46 s; le contrôle du lanceur privé est ignoré car ce lanceur n'est pas distribué.
- Tests dédiés passerelle : **31 réussis** dans la suite complète.
- Compilation `compileall` de la passerelle et du point de collecte; `node --check` des scripts JavaScript existants : réussis.
- `LANCER_APPLICATION_AVEC_LOGIN.bat` : démarrage réussi en mode démo synthétique, backend lié à 127.0.0.1:5101 et passerelle à 127.0.0.1:5000; les deux serveurs se sont arrêtés via la fenêtre de test et les ports sont libres.
- Comparaison de **217 fichiers préexistants** suivis : aucune différence. SHA-256 historique `database/stages_marrakech.db` identique au départ (`11036604a8584b45331dca9419c74233dde35c8e5d4f83a85b1f64c9bb3f3e51`); intégrité `ok`, compteurs 292/88/5, zéro erreur FK.
- Parcours visuel local à largeur de 382 px : inscription fictive, Login, Mon compte, accès à l’application, Logout, puis requête API protégée refusée avec HTTP 401 après déconnexion. Le backend utilisait une copie temporaire synthétique; son fichier source et la base historique sont restés inchangés. Le compte visuel de test a été supprimé de sa base de test (0 utilisateur restant).

Le manifeste d’empreintes inclut 217 fichiers de code, documents et données préexistants non secrets. Il omet intentionnellement `.env`, `private/`, `.build_private/`, les logs, sauvegardes, caches et environnement virtuel; ces répertoires n’ont pas été lus ou modifiés pour établir cette preuve.

Vérifications dédiées prévues et exécutées sur bases temporaires ou synthétiques : inscription valide/invalide, email existant normalisé, hash scrypt sans mot de passe clair, connexion invalide et valide, CSRF, session expirée, Logout invalidant la session, accès direct protégé, pages/API/Dash/téléchargements, prévention du contournement des routes login historiques, limite de tentatives, persistance de compte/session, profil privé administrateur unique, interdiction d’inscription privée, cookies et liaison du proxy au Flask original.

Le test d’intégration utilise une copie temporaire du jeu public synthétique et vérifie les pages Flask, Dash, l’API Chatbot et le Matching via la passerelle. La base historique n’est pas utilisée par les tests.

## Non exécuté

Aucune publication, test d’hébergement, test d’intrusion externe, vérification email, mot de passe oublié, test PostgreSQL réel ou test de données privées multi-comptes (désactivé par conception). Le test visuel a utilisé un navigateur local à largeur mobile, pas un appareil physique. Une vérification visuelle réussie ne vaut pas audit de sécurité.
