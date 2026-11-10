# Guide d’activation des collectes réelles — Phase 7

## Situation à la livraison

La collecte réseau et la planification restent désactivées. Aucune source web d’offres de stage n’a un accord d’agrégation, de stockage et de réaffichage documenté pour ce projet. Aucun appel aux sites/API de recrutement n’a été fait pendant la Phase 7. Pour les conditions par source, consulter le [registre Phase 7](GUIDE_SOURCES_AUTORISEES.md).

## Importer une source remise légalement

Un employeur ou organisme peut transmettre un CSV ou XLSX assorti d’une licence/autorisation. Dans **Centre de collecte des données** :

1. Indiquez le producteur et la référence de la licence ou de l’accord.
2. Confirmez séparément les droits de consultation, de stockage local et de réaffichage. Ne cochez que ce que le document autorise.
3. Choisissez le fichier et prévisualisez. Le fichier est traité localement; aucun lien contenu dans ses lignes n’est contacté.
4. Relisez chaque annonce : titre, entreprise, ville, champs manquants, état de validité et correspondances/doublons possibles. Les lignes malformées apparaissent dans les rejets.
5. Validez individuellement les annonces à conserver et rejetez les autres. Confirmez explicitement l’import SQLite.
6. Le journal garde le producteur, la référence déclarée, le nom de fichier, son empreinte SHA-256, les compteurs et la date. Le lien original reste attaché à l’offre.

Colonnes CSV/XLSX prises en charge : `titre`, `id source`, `entreprise`, `ville`, `description`, `type de stage`, `type de contrat`, `compétences`, `date de publication`, `date limite`, `secteur` et `url`. Le titre et l’URL HTTPS originale sont nécessaires; l’ID source est recommandé. Les CSV UTF-8 et XLSX jusqu’à 5 Mo et 10 000 lignes sont acceptés. Aucun scrape, géocodage ou appel payant n’est déclenché.

Le système déduplique par source + identifiant ou URL canonique. Une offre proche d’une annonce déjà présente est signalée pour revue, sans fusion automatique. Les offres approuvées apparaissent dans Offres, l’assistant local, le Matching, les alertes admissibles et les KPI Dash. L’import crée une sauvegarde avant de modifier la base.

## Activer un flux web après permission

L’accès technique ne suffit pas. Attendez un accord écrit qui couvre explicitement le mode de consultation, le stockage et le réaffichage dans cette application. Dans Centre de collecte, activez alors uniquement cette source, ajoutez la référence d’autorisation et cochez la confirmation. Lancez un petit aperçu, contrôlez les lignes, puis approuvez chacune avant l’import. N’activez jamais une source bloquée dans le registre.

Pour Jawb, le connecteur respecte un intervalle minimal de cinq minutes, une limite de pagination et le dernier état valide en cas de panne. Le guide officiel Jawb décrit le JSON dans le contexte de la page carrière employeur; il ne constitue pas en lui-même une autorisation d’agrégation par cette application.

## Planification locale

Le mode automatique reste désactivé au départ. Après autorisation écrite et test manuel d’une source, activez la planification dans le Centre de collecte et choisissez quotidien ou hebdomadaire. L’ordonnanceur intégré fonctionne uniquement quand l’application Flask reste ouverte.

La tâche Windows facultative du projet fonctionne au compte courant, sans privilèges administrateur et sans service permanent. Son installation requiert la saisie `OUI` :

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\INSTALLER_PLANIFICATEUR_WINDOWS.ps1 -Frequency daily
```

Remplacez `daily` par `weekly` pour l’exécution hebdomadaire. La tâche ne contacte que les connecteurs explicitement activés avec leurs références d’autorisation. L’ordinateur doit être sous tension et la session Windows ouverte. Pour arrêter, désactivez l’automatisation dans l’application et supprimez la tâche Windows depuis le Planificateur de tâches.

## Aucun accès autorisé?

Conservez le mode simulation uniquement pour la démonstration et utilisez le parcours CSV/XLSX fourni par un employeur/organisme. Ne transformez pas une page publique, un ancien endpoint ou une annonce visible en autorisation. Aucune offre de démonstration n’est écrite dans la base réelle.
