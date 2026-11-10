# Lancement et parcours de soutenance

## Choisir le bon profil

| Besoin | Lanceur | Base attendue | Attention |
|---|---|---|---|
| Usage quotidien local avec Login | `LANCER_MON_PROJET.bat` | `database/stages_marrakech.db` | Profil privé; Register ne crée pas de nouveaux comptes tant que l'isolation des données n'existe pas |
| Soutenance directe sans passerelle Login | `LANCER_SOUTENANCE_LOCALE.bat` | `database/stages_marrakech.db` | Session locale simple; mêmes données historiques |

Ne choisissez pas le lanceur sur le seul écran de connexion. Le profil et le chemin de base doivent être vérifiés avant la démonstration.

## Préparation Windows

1. Ouvrez le dossier `PROJET_FINAL` dans l'Explorateur puis dans VS Code.
2. Si `.venv` n'existe pas, lancez `INSTALLER_WINDOWS.bat`, puis attendez la fin de l'installation des dépendances. Cette opération peut nécessiter Internet pour télécharger les paquets.
3. Pour l'application principale avec Login, exécutez `LANCER_MON_PROJET.bat`.
4. Le lanceur prépare automatiquement le canal privé entre les deux services; aucun mot de passe technique n'est demandé. Connectez-vous ensuite avec les identifiants habituels de l'écran Login.
5. Lisez les informations de démarrage avant d'ouvrir le navigateur. Elles doivent afficher le profil `private`, le chemin absolu `database/stages_marrakech.db`, les compteurs lus et le résultat d'intégrité SQLite.
6. L'application locale s'ouvre sur `http://127.0.0.1:5000`. Dash utilise `http://127.0.0.1:5000/analytics/`.
7. Si le port 5000 est occupé, fermez le serveur que vous avez lancé précédemment. Le lanceur refuse un service inconnu; ne terminez pas un processus dont vous ne connaissez pas l'origine.

La vérification du lanceur ouvre SQLite en lecture seule. L'application peut effectuer des migrations au démarrage si le schéma est ancien; l'instantané fourni est version 6. Gardez la sauvegarde intacte et ne faites pas de démonstration de saisie sur la base historique.

## Connexion et sécurité

Après le démarrage, connectez-vous avec le compte actif déjà configuré. La passerelle et Flask établissent leur session de service par un secret aléatoire local, créé automatiquement et réservé à l'interface de boucle locale; ce n'est pas le mot de passe du compte. Le profil privé restreint l'accès à ce compte et désactive la création de nouveaux comptes. L'écran Register reste présent, mais la création est désactivée tant que candidatures et CV ne sont pas isolés par utilisateur. N'affichez pas `.env`, `private/`, `auth_gateway/data/` ni les tables contenant les coordonnées de contact des candidatures.

`LANCER_APPLICATION_AVEC_LOGIN.bat` appelle désormais `LANCER_MON_PROJET.bat` et utilise le profil historique. Les serveurs refusent de démarrer si les ports 5000 ou 5101 sont déjà occupés; aucun processus inconnu n'est arrêté. Fermez uniquement la fenêtre du serveur que vous avez lancé précédemment.

## Parcours de démonstration en 6 à 7 minutes

1. **0:00–0:30 — Profil et volumes** : montrez le profil local, le chemin de la base et les compteurs rapportés par le contrôle.
2. **0:30–1:10 — Entreprises** : filtrez par secteur et signalez que ville/quartier et coordonnées sont absents de l'instantané.
3. **1:10–1:50 — Offres** : montrez le titre, la source et le lien; précisez que les offres historiques ne sont pas vérifiées en temps réel.
4. **1:50–2:20 — Matching** : utilisez un profil fictif et expliquez les compétences communes/manquantes. Le score n'est pas une probabilité d'embauche.
5. **2:20–3:00 — Chatbot local** : demandez un nombre ou une recherche qui peut être répondue à partir de SQLite; gardez Gemini désactivé.
6. **3:00–3:40 — Dash** : ouvrez `/analytics/`, changez un filtre, comparez l'indicateur avec les tables.
7. **3:40–4:15 — Carte et qualité** : montrez le fond cartographique sans prétendre qu'il existe des coordonnées vérifiées.
8. **4:15–5:00 — ETL** : montrez le registre des sources, l'aperçu et l'étape de validation; aucune collecte réelle n'est enregistrée.
9. **5:00–5:40 — Code** : dans VS Code, ouvrez `backend/api.py` avec `Ctrl+P`, puis allez à une ligne de `GUIDE_CODE_SOURCE_SOUTENANCE.md` avec `Ctrl+G`.
10. **5:40–6:20 — Tests et limites** : montrez le dernier rapport, l'état des données, et la limite d'isolation de CV/candidatures.

Pour montrer le CV Builder ou le suivi des candidatures, utilisez seulement une base temporaire et des informations fictives. N'envoyez aucune candidature réelle.

## Arrêt

Revenez à la fenêtre du lanceur et appuyez sur `Ctrl+C`. Fermez le navigateur ensuite. Ne modifiez pas le répertoire `backups/`.
