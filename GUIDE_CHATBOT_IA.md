# Guide — Assistant Stages Marrakech AI

Le bouton flottant ouvre l’assistant. Le mode **local** est sélectionné par défaut : il recherche les offres et entreprises réellement enregistrées dans SQLite et ne contacte aucun service externe. Les filtres pris en charge couvrent villes, compétences, dates, domaines et entreprises. Si aucune annonce ne correspond, l’assistant le dit et n’en crée pas.

Les réponses d’offres comportent la source, la date connue, un lien et la date de dernière actualisation des données. Les informations absentes restent indiquées comme inconnues. L’historique de conversation est chiffré côté serveur.

Le mode **Gemini** reste facultatif. Avant l’appel, l’assistant affiche une prévisualisation des champs transmis. Il faut la relire puis cocher explicitement le consentement. Le texte du CV n’est pas transmis; seul un résumé local dérivé du CV peut servir à filtrer des annonces en mode local. Le serveur limite Gemini à des extraits d’offres publiques retrouvées, valide les identifiants renvoyés et retombe sur la réponse locale si le service est indisponible. Une clé/configuration Gemini valide est requise dans `.env`; consultez les quotas et conditions de votre compte avant usage.

Questions possibles : « stages Python et SQL à Marrakech », « offres récentes en Data Science », « entreprises dans l’informatique » ou « offres qui correspondent à mon CV ». La recherche dépend de la qualité et de l’actualité de la base; aucun accès web n’est improvisé par le chatbot.
