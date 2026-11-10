# Rapport des tests finaux

## Résumé

- Avant correction : 123 réussis au dernier rapport.
- Contrôle précédent, avant la mission ultime : **125 réussis, 0 échec** dans chaque copie. Contrôle actuel après correction : 126 tests dans chaque copie (voir l’addendum daté ci-dessous).
- Tests ciblés Dash/collecte (4 modules) : 37 réussis, 0 échec, 12,47 s.
- Tests de régression : absence du panneau et callbacks, filtre/graph conservés, lien `_top`, lecture DB, mention synthétique.
- Smoke d’intégration sur copies temporaires : local 292/88/5; public synthétique 5/4/3; routes Dash, KPI, assistant local, aperçu CV PDF, carte sans coordonnées et mode public lecture seule vérifiés.

## Couverture

| Domaine | Vérification | Résultat |
|---|---|---|
| Flask/pages/API | Authentification, CSRF, pages et statistiques | Tests automatisés; smoke isolé |
| Entreprises/offres | Lecture 292/88 sur copie, filtres et expirations | Réussi |
| Dash | Routes, callbacks, filtres, KPI, export; panneau absent | Réussi |
| Centre collecte/ETL | CSV/XLSX, autorisations, mapping, doublons, staging/import/historique | Fixtures réussies; réseau réel non appelé |
| Matching | Scores, poids, signaux et champs absents | Réussi sur données test |
| CV/PDF | Deux modèles, extraction, versions, preview/téléchargement | Réussi; API PDF isolée |
| Candidatures | Création, changement statut et historique | Réussi en DB temporaire; pas d’envoi |
| Carte | Coordonnées sourcées et points fictifs distingués | API/tests réussis; historique sans coordonnées vérifiées |
| Alertes | Préférences, génération, compteur, lecture/dédoublonnage | Réussi; SMTP non appelé |
| Chatbot | Retrieval SQLite et réponse locale | Réussi; smoke sur copie historique |
| Gemini | Clé absente/désactivation et contrats mockés | Réussi; aucun appel réel |
| Migrations | Idempotence, intégrité et sauvegarde | Réussi sur fixtures; DB réelle v6 intacte |
| Sécurité | CSRF, XSS, validation, CSV, mode public lecture seule | Tests réussis; pas de test d’intrusion |
| Responsive | Breakpoint CSS présent | Visuel Chrome/Edge manuel restant |

## Bases

Les deux bases actives et toutes les sauvegardes historiques inspectées ont `integrity_check=ok`. Les essais d’écriture ont utilisé des fixtures ou copies temporaires. L’historique original n’a pas été modifié.

## Non exécuté

Aucun contrôle visuel n’a été réalisé. La demande de lancement d’un serveur local isolé pour ouvrir le navigateur a été rejetée automatiquement par la politique d’approbation de l’environnement (`sandbox_approval`); le navigateur n’a donc pas été connecté. L’affichage OSM, mobile, lecteur PDF et compatibilité Office ne sont pas déclarés visuellement validés. Aucun site, email réel, collecte internet, appel Gemini ou publication n’a été réalisé.

Commandes de contrôle final :

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m compileall -q backend scripts tests
node --check dashboard/js/ui.js
```

Voir `GUIDE_VERIFICATION_MANUELLE.md` pour les essais restants.

## Mise à jour — contrôle final, 8 novembre 2026

- Suite complète actualisée après corrections : **126 réussis, 0 échec** sur le projet privé (44,95 s) et **126 réussis, 0 échec** sur la copie publique (44,53 s). Un avertissement Dash `PytestRemovedIn10Warning`, sans échec. Les fixtures forcent maintenant le profil privé pour isoler les tests des variables `.env` de la copie démo.

## Mise à jour — mission de restauration et chatbot, 9 novembre 2026

- Suite complète locale : **133 réussis, 0 échec**, 46,19 s; un avertissement Dash non bloquant.
- Copie publique : **132 réussis, 1 ignoré, 0 échec**, 45,38 s. Le test du lanceur de base historique est ignoré car le lanceur et la base privée sont exclus de la copie publique.
- `node --check dashboard/js/ui.js` et `python -m compileall -q backend scripts tests` réussis.
- Le test navigateur démarre Chrome et s'authentifie sur la base temporaire, mais échoue ensuite à attendre le texte `MODE DÉMONSTRATION` de Recherche IA. L'ensemble du parcours navigateur et le rendu visuel restent non validés.
- L'instance détectée sur le port 5000 répond `public_demo=true`; son PID n'a pas été exposé. Elle n'a pas été arrêtée. Le nouveau lanceur de soutenance refuse le port occupé.
- Base historique toujours intègre en lecture seule : 292/88/5, v6. Aucun appel externe ou Gemini.
- Nouveau test de session : un jeton CSRF erroné reçoit le 403 attendu; un jeton renouvelé via la session authentifiée permet deux questions locales successives et leur historique. Les protections restent actives.
- `node --check dashboard/js/ui.js` et `python -m compileall -q backend scripts tests` : réussis sur l’état final.
- Les données actives vérifiées en lecture seule : locale privée 292/88/5, SQLite v6/intégrité `ok`; démo synthétique séparée 5/4/3. Pas d’écriture sur les bases originales.
- Un lancement de `tests/browser_smoke.py` a été interrompu après absence de réponse du processus; le contrôle visuel Chrome/Edge/mobile n’est donc **pas validé**. Le test ne constitue pas une preuve d’affichage. La checklist reste dans `GUIDE_VERIFICATION_MANUELLE.md`.
- Aucun appel Gemini réel, recherche Internet réelle, collecte autorisée réelle, SMTP, candidature externe, test d’intrusion ou déploiement n’a été effectué.
- Archive publique reconstruite et relue : 130 fichiers, seule base SQLite = démo synthétique, aucun `.env` ou chemin privé, 0 motif de clé connu et intégrité ZIP valide.
