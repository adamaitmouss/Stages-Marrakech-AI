# Guide de validation Phase 9

## Tests automatisés

À la racine du projet, lancez :

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Les tests Gemini utilisent des clients simulés et les tests interdisent l’ouverture de connexions réseau. Ils ne consomment pas de requêtes Search Grounding.

## Contrôles manuels locaux

1. Démarrez l’application et ouvrez **Recherche IA**.
2. Vérifiez que le badge indique Gemini indisponible et que le bouton externe est désactivé tant que la configuration reste par défaut.
3. Lancez une recherche locale; l’écran doit dire qu’elle utilise SQLite seulement.
4. Lancez la démonstration; confirmez les étiquettes fictives, l’intégrité `ok` et « Base principale modifiée : non ».
5. Vérifiez l’historique et testez sa suppression après confirmation.
6. Ne testez une recherche Gemini réelle qu’après avoir suivi `GUIDE_CONFIGURATION_API.md` et décidé explicitement d’assumer une éventuelle facturation.
7. N’ajoutez au staging que des offres vérifiées manuellement avec autorisation documentée. Vérifiez le Centre de collecte, puis importez seulement après confirmation.

Le rapport Phase 9 doit être actualisé si des appels, candidats ou imports réels sont réalisés ultérieurement.

