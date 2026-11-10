# Questions et réponses possibles du jury

## Projet et architecture

1. **Pourquoi ce projet ?** — Pour rassembler la recherche, le classement d'offres et le suivi dans un outil local destiné à la recherche de stage à Marrakech.
2. **Quelle est la problématique ?** — Les offres sont dispersées et leur suivi manuel est difficile; les données utilisées ne sont toutefois pas toutes récentes ou vérifiées.
3. **Pourquoi Flask ?** — Le projet utilise Python pour les services de données et Flask pour les pages et routes API, avec une intégration directe de Dash.
4. **Pourquoi SQLite ?** — SQLite permet une base locale simple à sauvegarder et sans serveur séparé. Pour une application distante à plusieurs utilisateurs, un stockage serveur persistant est préférable.
5. **Qu'est-ce qu'une API ?** — Une interface HTTP qui reçoit une requête et retourne des données structurées, ici souvent en JSON.
6. **Qu'est-ce que Dash ?** — Un framework Python basé sur Flask et Plotly. Le dashboard réagit aux filtres grâce à des callbacks.
7. **Qu'est-ce qu'un callback ?** — Une fonction déclenchée par un changement de composant ou un clic qui actualise une partie de la page.
8. **Comment le frontend communique-t-il avec Flask ?** — JavaScript appelle des routes `/api/...`, envoie le jeton CSRF pour les modifications et lit les réponses JSON.

## Données et collecte

9. **Combien d'enregistrements contient la base locale ?** — À l'instantané du 9 novembre 2026 : 292 entreprises, 88 offres et 5 candidatures. La base démo synthétique contient 5, 4 et 3.
10. **D'où viennent les 88 offres ?** — Le champ historique `source` vaut Stagiaires.ma pour les 88 lignes, mais la base n'a aucune identité source enregistrée ni journal d'import. Je ne peux donc pas prouver la provenance individuelle ni une permission de réutilisation.
11. **Les 88 offres sont-elles ouvertes ?** — Impossible à confirmer. La base a une valeur de statut, mais aucune date de dernière vérification; je vérifie le lien original avant candidature.
12. **Avez-vous collecté des offres durant cette validation ?** — Non. `collector_runs` et `collector_source_runs` sont vides; les tests des connecteurs utilisent des réponses simulées.
13. **Quelles sources sont réellement utilisées par les connecteurs ?** — Greenhouse, Lever, Ashby, SmartRecruiters, Jawb RSS/JSON, flux carrière RSS/Atom et CSV/XLSX sont représentés dans le code. Cela ne signifie pas qu'une collecte réelle a eu lieu.
14. **Une API publique autorise-t-elle la republication ?** — Non automatiquement. Le propriétaire doit confirmer la consultation automatisée, le stockage et le réaffichage dans cette application.
15. **Que signifie ETL ?** — Extraction d'une source, transformation/validation, puis chargement dans la base après contrôle.
16. **Comment évitez-vous les doublons ?** — Le connecteur calcule une identité et compare les contenus; les similitudes ambiguës passent par un staging et une validation humaine.
17. **Que sont les données manquantes importantes ?** — Les villes, quartiers, coordonnées et dernières vérifications d'offres sont manquants pour les 292 entreprises ou 88 offres correspondantes.
18. **Pourquoi ne pas remplir ces champs par estimation ?** — Cela créerait une fausse précision; le système laisse les valeurs inconnues et ne place pas de marqueurs non vérifiés.

## IA et fonctionnalités

19. **Comment fonctionne le matching ?** — Il compare les compétences du profil avec celles repérées dans les offres, applique des pondérations et renvoie un classement avec éléments communs/manquants.
20. **Le score prédit-il une embauche ?** — Non. Il sert à ordonner les annonces et reste indicatif; il ne mesure pas la probabilité d'être recruté.
21. **Quel est le rôle de Gemini ?** — Un mode facultatif peut interpréter/rechercher des informations, mais il dépend d'une clé, de la configuration, du consentement et du contrôle des résultats.
22. **Avez-vous fait une recherche Gemini réelle ?** — Non. Les tests mockent les contrats et la configuration reste facultative. Aucune requête payante n'a été lancée.
23. **Comment fonctionne le Chatbot ?** — Le mode local recherche dans les entreprises et offres SQLite, puis formate une réponse. Le mode externe est distinct et n'est pas requis.
24. **Comment les alertes sont-elles produites ?** — Le code valide les préférences, score les offres et évite les doublons; l'envoi email nécessite une configuration et un consentement distincts.
25. **Que fait le créateur de CV ?** — Il valide des champs, peut chiffrer une version enregistrée et générer un PDF local avec ReportLab.
26. **Avez-vous testé une vraie candidature ?** — Non. Les tests couvrent la préparation, la confirmation et l'idempotence sur bases temporaires ou SMTP simulé.

## Sécurité et limites

27. **Comment protégez-vous les sessions ?** — Cookies HttpOnly/SameSite, vérification CSRF, contrôle d'origine et mot de passe haché; la passerelle garde le cookie interne côté serveur.
28. **Chaque utilisateur a-t-il son propre CV ?** — Pas dans le cœur existant. Les tables CV et candidatures ne sont pas cloisonnées par compte; le profil privé de la passerelle se limite à un administrateur.
29. **L'inscription publique est-elle prête ?** — Non pour des données personnelles. Le profil inscription autorisée ne doit servir qu'à la démonstration synthétique.
30. **Comment protégez-vous SQLite ?** — L'application choisit le fichier via configuration, utilise des requêtes paramétrées, maintient des sauvegardes avant migrations/imports et sépare la base publique de la base locale.
31. **La clé API est-elle dans Git ?** — Non, les exemples ne contiennent pas de secrets; les fichiers `.env` sont exclus du paquet public.
32. **Que montre la carte ?** — Un fond OSM et uniquement les coordonnées avec provenance vérifiée. La base locale auditée n'a aucun couple latitude/longitude.
33. **Pourquoi autant de références d'offre sont-elles orphelines ?** — 85 `Entreprise ID` ne correspondent pas à `entreprises.rowid`. Le schéma ne possède pas de contrainte FK sur cette relation; je la signale plutôt que de deviner les correspondances.

## Tests et déploiement

34. **Quels tests ont été exécutés ?** — La suite pytest couvre Flask, Dash, matching, PDF, ETL, alertes, candidatures, carte, sécurité et démonstration publique; elle utilise des fixtures et mocks pour les services externes.
35. **Le projet est-il déployé ?** — Non. `render.yaml` prépare une démo synthétique, mais aucune URL n'a été créée ou testée pendant cette livraison.
36. **Quelle est la limite d'un plan d'hébergement gratuit ?** — Le stockage du disque peut être éphémère et les ressources limitées; il faut vérifier la persistance réelle auprès de l'hébergeur avant d'y placer une base.
37. **Que faudrait-il pour plusieurs utilisateurs ?** — Une vraie isolation tenant côté backend et base, contrôles d'accès sur chaque route/fichier/export, tests d'autorisation, stockage sécurisé, récupération de compte et audit indépendant.
38. **Que feriez-vous ensuite ?** — Obtenir des permissions écrites par source, réconcilier les références d'entreprise, vérifier la fraîcheur des annonces, compléter la provenance et concevoir l'isolation multiutilisateur avant une ouverture publique.
39. **Que signifient les résultats de tests ?** — Ils attestent des scénarios codés sous fixtures, pas de disponibilité des sources réelles, de conformité juridique ni de sécurité en production.
40. **Comment avez-vous préservé l'historique ?** — Une copie de sauvegarde et des empreintes ont été créées avant le nettoyage; la base originale et les fichiers historiques sont restés inchangés.
