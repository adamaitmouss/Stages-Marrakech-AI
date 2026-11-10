# Configurer une clé Gemini localement

Gemini est facultatif. Le chatbot, l’extraction de compétences PDF et le matching local restent utilisables sans clé. L’environnement contrôlé le 8 novembre 2026 n’avait pas de clé configurée et `GEMINI_ENABLED` était désactivé. Le SDK officiel `google-genai` est installé. Aucune requête réelle n’a été envoyée.

## Création et vérification

1. Ouvrez [Google AI Studio — API Keys](https://aistudio.google.com/api-keys) et connectez-vous vous-même à votre compte Google.
2. Créez ou sélectionnez un projet, puis créez une clé si votre compte et votre région le permettent.
3. Dans la console Google, vérifiez les restrictions de clé, le projet auquel elle appartient, les quotas, les conditions de traitement des données et l’état de facturation.
4. Consultez la [documentation des clés](https://ai.google.dev/gemini-api/docs/api-key), les [modèles disponibles](https://ai.google.dev/gemini-api/docs/models) et la [tarification](https://ai.google.dev/gemini-api/docs/pricing). L’éligibilité gratuite, les quotas et les modèles peuvent dépendre du compte et changer. Ce guide ne promet ni accès gratuit ni quota illimité.
5. Ne collez pas la clé dans une conversation, un rapport, une capture ou PowerPoint. Modifiez uniquement le `.env` privé local, jamais `.env.example` :

```dotenv
GEMINI_API_KEY=votre_cle_locale
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_ENABLED=true
GEMINI_FREE_TIER_CONFIRMED=true
```

Le code actuel accepte `gemini-3.5-flash-lite` pour le service Matching/CV. Avant de l’activer, confirmez dans votre compte que ce modèle précis est disponible et examinez le prix/quota associé. Le service de recherche Web possède des variables séparées et reste désactivé par défaut; il peut engendrer des frais multiples. Ne mettez pas `GEMINI_SEARCH_BILLING_CONFIRMED=true` sans avoir explicitement vérifié votre configuration de facturation et accepté ce risque.

6. Vérifiez que `.env` apparaît dans `.gitignore`. Gardez la clé hors de l’archive publique, des sauvegardes partagées et des captures. Redémarrez l’application locale.
7. Après votre accord explicite à un test réel, prévisualisez les données dans l’interface avant chaque transfert. Pour un CV, retirez noms, coordonnées, adresses et détails sensibles. Le niveau gratuit peut appliquer des conditions de traitement différentes du niveau payant; consultez les conditions Google avant d’envoyer des données personnelles. Le matching local n’envoie rien.

## Vérifier sans révéler la clé

Le diagnostic local affiche seulement si le SDK, la configuration, la clé et le mode sont présents. Les tests automatisés utilisent des réponses simulées. Un test simulé ne valide ni la clé, ni les quotas, ni l’accès du compte au modèle. Le statut « opérationnel en réel » ne peut être confirmé qu’après une requête autorisée et réussie, qui n’a pas été faite.

Erreurs usuelles : clé invalide ou révoquée; modèle indisponible pour le projet; quota dépassé (429); restrictions d’API ou de région; facturation requise; problème réseau. L’application revient aux résultats locaux sans relance automatique.

## Révocation

Si une clé a été publiée ou partagée, révoquez-la immédiatement dans AI Studio/Google Cloud, créez-en une nouvelle, remplacez-la dans le `.env` local, puis redémarrez. Ne publiez pas l’ancienne valeur dans un ticket ou un rapport.
