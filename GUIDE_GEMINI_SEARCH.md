# Guide — Recherche IA sur Internet

## Ouvrir la page

Connectez-vous à l’application puis choisissez **Recherche IA** dans la navigation.

### Recherche locale

Saisissez une demande et cliquez sur **Chercher dans mes données locales**. La recherche ne quitte pas SQLite et n’interroge pas Google. Elle peut uniquement retrouver les offres déjà enregistrées.

### Démonstration

Cliquez sur **Tester le parcours de démonstration**. Le résultat est fictif et porte une étiquette visible. Le programme crée une base temporaire, vérifie staging, import, Matching, Chatbot, alertes, dashboard et intégrité SQLite, puis supprime cette base. Le compteur indique explicitement que la base principale n’a pas été touchée.

### Recherche Gemini

Par défaut, le bouton est désactivé. Il devient utilisable uniquement après configuration serveur décrite dans `GUIDE_CONFIGURATION_API.md`. Avant chaque requête, cochez la confirmation de coût. Google Search Grounding est une fonction potentiellement payante; une demande peut déclencher plusieurs recherches facturables.

Les liens, dates, résumés et autres champs retournés restent des **candidats à vérifier**. Ouvrez la page source vous-même et vérifiez qu’il s’agit bien de l’annonce, qu’elle est encore pertinente et que l’organisme autorise séparément la consultation, le stockage et le réaffichage des champs repris.

## Staging et import

Un résultat sans lien direct présent dans les sources citées ne peut pas être placé dans le staging. Pour l’ajouter, confirmez la vérification manuelle, fournissez la référence d’autorisation et cochez chacun des trois droits. Le parcours crée alors un run dans le Centre de collecte et utilise son dédoublonnage et son import existants. L’import SQLite est une étape séparée; vérifiez le résultat avant de confirmer.

La déclaration des droits dans l’interface est une attestation de l’administrateur, pas une vérification juridique automatique. En l’absence d’autorisation suffisante, gardez le lien pour consultation manuelle et n’enregistrez pas l’offre.

## Limites

- Aucun accès automatique aux pages annonce; les URL ne sont pas suivies côté serveur.
- Aucune annonce n’est « active » simplement parce qu’elle apparaît dans Google.
- L’arrêt empêche la restitution du résultat, mais ne peut pas annuler une requête déjà envoyée à Google.
- Les plafonds locaux (2 appels par session/jour, 5 appels/jour au total, délai de 60 s) ne garantissent pas un coût maximal auprès de Google.
- Le planificateur n’est pas activé et aucune tâche Windows n’est créée.
- L’historique conserve le prompt expurgé, critères, modèle, statut et compteurs, mais pas les résultats web complets.

