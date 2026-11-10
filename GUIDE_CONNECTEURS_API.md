# Guide des connecteurs d’API Phase 8

## Connecteurs livrés

Le centre de collecte comprend des adaptateurs Greenhouse, Lever, Ashby et SmartRecruiters, en plus des connecteurs déjà présents et du flux RSS/Atom fourni par l’administrateur. Les adaptateurs convertissent leurs réponses en offre canonique puis réutilisent le staging, la validation individuelle, la déduplication et l’import SQLite déjà en place.

| Plateforme | Endpoint public utilisé | Règles de lecture |
|---|---|---|
| Greenhouse | `GET boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true` | Identifiant de board strict, annonces publiées, détails du contenu inclus. |
| Lever | `GET api.lever.co/v0/postings/{site}` ou `api.eu.lever.co`, `skip`/`limit` | Pagination bornée, uniquement annonces exposées par l’API publique. |
| Ashby | `GET api.ashbyhq.com/posting-api/job-board/{board}` | Seules les annonces `isListed=true` sont exposées dans le flux général. |
| SmartRecruiters | `GET api.smartrecruiters.com/v1/companies/{company}/postings` | `destination=PUBLIC`, pagination bornée. Aucun jeton ni clé n’est utilisé. |

Documentation fournisseur : [Greenhouse Job Board](https://docs.greenhouse.io/job-board), [Lever Postings API](https://github.com/lever/postings-api), [Ashby Job Postings API](https://developers.ashbyhq.com/docs/public-job-posting-api), [SmartRecruiters Posting API](https://developers.smartrecruiters.com/docs/posting-api). Ces pages documentent les interfaces destinées aux pages carrière d’employeurs; elles ne prouvent pas à elles seules un droit de stockage ou de redistribution pour cette application.

## Autorisation nécessaire par entreprise

Pour chaque board, renseigner le nom, les URL officielles, le fournisseur, l’identifiant vérifié, la ville, le secteur, la référence du document et la date de vérification. Cocher séparément les droits de consultation automatique, de stockage local et de réaffichage. La source ne peut être activée si un seul de ces éléments manque. Le réglage global de collecte externe doit également être activé pour lancer un aperçu.

Une URL publique ou un identifiant de board ne vaut pas accord. Le propriétaire doit autoriser le projet, la finalité d’agrégation, la conservation, l’affichage, l’attribution et la fréquence. Le registre conserve la référence fournie; stockez le document d’autorisation en lieu sûr.

## Limites de sécurité et de charge

- Les tests utilisent des réponses JSON simulées et ne contactent aucun fournisseur.
- Les URL de requête sont construites sur des hôtes HTTPS fixes; les redirections sont refusées.
- Les identifiants sont limités à des caractères sûrs; les requêtes ont un timeout et une limite de taille de réponse.
- Lever et SmartRecruiters sont paginés avec une limite de pages; le rythme entre pages est ralenti.
- Les erreurs HTTP, réponses mal formées et réponses vides apparaissent dans l’historique de collecte.
- Aucun scraping HTML, endpoint privé, authentification SmartRecruiters ou tâche Windows n’est activé.
- Les sources et l’automatisation restent désactivées par défaut.

## Lancer un aperçu après autorisation

1. Dans **Sites carrières**, ajoutez une seule entreprise avec ses liens et son identifiant exact.
2. Enregistrez la référence et les trois attestations après vérification du document du propriétaire.
3. Activez uniquement cette source, puis autorisez la collecte externe dans **APIs officielles**.
4. Cliquez **Prévisualiser les offres activées**. Vérifiez les champs, l’origine, les correspondances exactes d’entreprise et les doublons.
5. Approuvez ou écartez chaque ligne. L’import n’est disponible qu’après validation individuelle et confirmation des droits.

Les collectes planifiées s’exécutent localement et restent inactives tant qu’elles ne sont pas activées par l’administrateur.
