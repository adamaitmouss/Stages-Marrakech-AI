# GitHub, publication et déploiement

## État de cette livraison

- Aucun dépôt GitHub n'a été publié ni modifié pendant cette mission.
- Le fichier `render.yaml` décrit une démonstration configurée avec la base synthétique publique.
- Aucune URL de site hébergé n'a été testée; le projet n'est pas déclaré déployé.
- L'archive `PROJET_PUBLIC_AUTH.zip` est le seul paquet prévu pour distribution. Le projet local `PROJET_FINAL` et la sauvegarde privée ne sont pas publiables.

## Vérifications avant GitHub

- Revoir `.gitignore` et confirmer l'absence de `.env`, `.env.auth`, `private/`, `.venv`, `backups/`, uploads, CV, candidatures, bases locales privées, fichiers de compte et secrets.
- Ne publier que `database/stages_marrakech_public_demo.db` après contrôle de son marqueur synthétique et de ses volumes.
- Vérifier qu'aucun rapport, capture ou historique ne contient de coordonnées ou d'informations de candidat.
- Vérifier les licences des dépendances et garder l'attribution des données publiques.
- Recalculer `MANIFEST_PUBLIC_AUTH_SHA256.json` après toute reconstruction de l'archive.

## Limites d'authentification en ligne

Le cœur Flask lit un schéma de données partagé. Il n'associe pas les lignes `cvs` et `candidatures` à un identifiant utilisateur authentifié. Le profil privé de la passerelle n'autorise qu'un administrateur et l'inscription démo n'est adaptée qu'au jeu synthétique. Ne pas ouvrir l'inscription avec la base historique ni enregistrer des CV/candidatures privées sur une instance publique.

Avant une application multiutilisateur, il faudrait concevoir et tester une isolation complète côté serveur pour toutes les tables, routes API, téléchargements, Dashboard, historiques, exports et sauvegardes. Ce travail dépasse cette livraison et ne doit pas être simulé par l'écran Login.

## Conditions minimales de déploiement de la démo

1. Utiliser la base synthétique marquée et la config `PUBLIC_DEMO_MODE=true`.
2. Vérifier HTTPS, `TRUSTED_HOSTS`, cookies Secure et proxy de confiance.
3. Désactiver Gemini, SMTP, Maps et collecte externe par défaut.
4. Vérifier le stockage persistant de la base démo, les sauvegardes et les journaux de l'hébergeur.
5. Vérifier l'origine des tuiles cartographiques et leur disponibilité réseau.
6. Tester les routes après déploiement et archiver la vraie URL seulement après contrôle manuel.

Pour une passerelle sur Internet, utiliser un backend privé non joignable directement, HTTPS, PostgreSQL persistant avec TLS, secrets dans le gestionnaire de l'hébergeur, hôtes autorisés stricts et nombre exact de proxys de confiance. L'authentification ne suffit pas à justifier le déploiement de données de candidats.

## Procédure de remise

1. Décompresser `PROJET_PUBLIC_AUTH.zip` dans un répertoire de test.
2. Vérifier le manifeste et la base publique; ne pas copier `.env` local.
3. Installer les dépendances depuis les requirements du paquet.
4. Lancer les tests et le démarrage de démo.
5. Si un dépôt GitHub est demandé, créer le dépôt et y pousser seulement la copie publique après revue humaine. La mission actuelle n'a pas autorisé de publication externe.
