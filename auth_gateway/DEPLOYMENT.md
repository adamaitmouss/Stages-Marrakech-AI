# Déploiement — exigences avant activation

`wsgi.py` et `gunicorn.conf.py` constituent le point d’entrée du service passerelle. Pour les utiliser, configurez `AUTH_ENV=production`, `AUTH_COOKIE_SECURE=true`, un `AUTH_SESSION_SECRET` secret d’au moins 32 caractères, `AUTH_DATABASE_URL=postgresql://…?sslmode=require` vers un stockage persistant avec TLS, `AUTH_TRUSTED_PROXY_HOPS` et `AUTH_ALLOWED_HOSTS` exacts, et `AUTH_TRUSTED_PRIVATE_BACKEND=true` uniquement si `AUTH_BACKEND_URL` cible réellement un service privé. Le nombre de proxy approuvés configure ProxyFix; le premier hôte non approuvé est refusé.

Le backend Flask existant doit être lié au réseau interne de l’hébergeur, sans route Internet publique. La passerelle et le backend doivent partager un réseau privé contrôlé. Une URL publique vers l’application d’origine permettrait de contourner l’authentification; cette configuration ne serait donc pas acceptable.

Le déploiement n’est pas activable avec les seuls fichiers du projet : aucun hébergeur, DNS, TLS, service PostgreSQL ni réseau interne n’a été configuré ou testé. Utilisez uniquement une base marquée `synthetic_public_demo` avec l’inscription. N’utilisez pas les tables CV/candidatures historiques pour plusieurs comptes; aucune isolation par étudiant n’existe.
