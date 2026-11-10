# Guide — configuration facultative de Gemini Search

La configuration reste désactivée dans le projet livré. Aucune clé API n’est incluse. Les recherches locales et la démonstration temporaire fonctionnent sans compte Gemini.

## Avant l’activation

1. Vérifiez dans la documentation Google que le modèle et Google Search Grounding restent disponibles pour votre projet.
2. Vérifiez le niveau de facturation et le tarif Grounding de votre compte. La documentation tarifaire consultée indique une facturation à l’usage et plusieurs recherches peuvent être comptées pour un seul prompt.
3. Vérifiez les droits de chaque source que vous comptez stocker ou réafficher. Grounding/citation n’accorde pas de licence de réutilisation.
4. Conservez les plafonds locaux bas et essayez d’abord une seule recherche manuelle.

## Paramètres `.env`

Copiez les paramètres ci-dessous dans le fichier `.env` local du projet et remplacez la clé par une clé serveur Gemini obtenue par vos soins. Ne la collez jamais dans le navigateur, dans le code source ou dans un rapport.

```dotenv
GEMINI_API_KEY=votre_cle_serveur
GEMINI_SEARCH_MODEL=gemini-3.8-flash
GEMINI_SEARCH_ENABLED=true
GEMINI_SEARCH_BILLING_CONFIRMED=true
GEMINI_SEARCH_MAX_SESSION=2
GEMINI_SEARCH_MAX_DAILY=5
GEMINI_SEARCH_COOLDOWN_SECONDS=60
GEMINI_SEARCH_TIMEOUT_MS=30000
```

`GEMINI_SEARCH_BILLING_CONFIRMED=true` est une attestation locale que vous avez vérifié l’accès payant; l’application ne vérifie pas votre compte ni votre moyen de paiement. Elle n’active pas la facturation Cloud, ne change pas les quotas et ne commande aucun paiement.

Redémarrez l’application. La page **Recherche IA** expose seulement si la clé est configurée, jamais sa valeur. Chaque recherche exige aussi une confirmation de coût dans l’interface.

## Désactivation

Fermez l’application et définissez `GEMINI_SEARCH_ENABLED=false` ou retirez la clé du `.env`, puis redémarrez. Cela désactive la fonctionnalité immédiatement. Aucune exécution planifiée n’est installée.

Tarifs et noms de modèles évoluent. Consultez les documents officiels [Google Search Grounding](https://ai.google.dev/gemini-api/docs/google-search) et [tarifs Gemini API](https://ai.google.dev/gemini-api/docs/pricing.md) avant chaque activation.

