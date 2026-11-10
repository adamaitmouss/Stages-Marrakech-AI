# Guide — Alertes d’offres

Les alertes sont enregistrées dans SQLite et sont désactivées par défaut. Ouvrez **Mes alertes**, choisissez domaine, compétences, ville, type de stage/contrat et score minimal, puis activez les alertes. Le score est explicable et indicatif : compétences (jusqu’à 65 points), domaine (20) et ville (15). Les critères manquants restent inconnus; aucune offre n’est inventée.

Une alerte ne peut être créée qu’à partir d’une offre importée, non expirée, qui correspond au seuil. Une contrainte unique empêche les répétitions. Les cartes montrent titre, entreprise connue, ville, source, date, score et explication, avec actions de lecture, suppression et candidature.

Les alertes locales apparaissent après l’import d’une offre correspondante. Les emails sont facultatifs et désactivés par défaut. Pour les activer :

1. Configurez `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` et `SMTP_ENABLED=true` dans votre `.env`, puis redémarrez Flask. N’affichez ni ne partagez ce fichier.
2. Dans **Mes alertes**, saisissez votre adresse, cochez l’activation email et relisez/cocher le consentement explicite avant d’enregistrer.
3. La destination est chiffrée dans SQLite avec la clé locale du dossier `private`. Désactiver les emails annule les alertes en attente.

La fréquence **Dès import**, **Quotidienne** ou **Hebdomadaire** règle le regroupement email. Les envois quotidiens/hebdomadaires sont traités lorsque l’application Flask est ouverte; le poste doit donc rester allumé et connecté. Une panne SMTP est marquée comme incertaine et n’est pas renvoyée automatiquement afin d’éviter les doublons. Le SMTP reste indépendant de l’envoi de candidature.
