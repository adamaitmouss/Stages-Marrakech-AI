# Registre des sources et des autorisations — Phase 7

Vérification des pages officielles : 6 novembre 2026. Le registre sépare l’accès technique, le droit de consultation automatique, le droit de stockage et le droit de réaffichage. Une page publique ou une API testable ne vaut pas licence de réutilisation. Les statuts ci-dessous concernent ce projet et ses usages prévus; aucune autorisation spécifique de l’utilisateur n’a été fournie.

| Source | Accès technique et contenu | Consultation automatique | Stockage | Réaffichage dans l’application | Décision Phase 7 |
|---|---|---|---|---|---|
| Jawb RSS/JSON | RSS public des 50 annonces récentes; JSON par employeur, paginé | Le guide technique donne les limites (5 min), mais décrit le JSON pour la page carrière de l’employeur; agrégation par une application tierce non accordée | Non documenté pour cet usage | Non documenté pour cet usage | Connecteurs restent verrouillés. Demander l’accord écrit de Jawb et/ou de l’employeur qui possède les annonces. |
| Flux carrière d’employeur | Flux RSS/Atom HTTPS remis par l’employeur | Oui uniquement dans le périmètre écrit du propriétaire | À confirmer dans l’accord | À confirmer dans l’accord (titre, extraits, lien, durée) | Meilleure option directe si l’employeur remet son flux et les droits requis. |
| Fichier CSV/XLSX d’un employeur ou organisme | Fichier remis directement, import local sans requête réseau | À confirmer selon la licence et le mode de remise | Consentement explicite exigé dans l’interface | Consentement explicite exigé; conserver l’URL source et l’attribution | Parcours prêt. Aucun fichier autorisé n’a été remis pour cette phase. |
| Portail Open Data Maroc | API de catalogue CKAN et ressources téléchargeables | Oui pour les jeux publiés sous les termes applicables | Oui sous ODbL lorsque la fiche du jeu l’indique | Oui avec attribution et obligations ODbL, dont partage à l’identique des bases dérivées | Les jeux du thème Emploi consultés sont surtout des statistiques et concours; ils ne constituent pas un flux d’annonces de stage Marrakech. Utiles au contexte analytique, pas à l’import d’offres. |
| Trouve Ton Emploi / CAPPRAfrica | API et exports Excel proposés sous licence sur demande motivée | Licence et périmètre à demander | Dépend de la formule et du contrat | Dépend de la licence et du contrat | Piste prioritaire pour une demande API/export; aucun accès ni contrat reçu. |
| ANAPEC | Portail public d’emploi; aucune API publique de réutilisation identifiée dans cette vérification | Non établi | Non établi | Non établi | Demander un export/flux officiel et les droits d’usage avant intégration; aucun scraping. |
| Jobsquare API | API pour connecter le logiciel de recrutement d’un client; clé sur demande | Possible pour le compte client approuvé selon documentation/contrat | À confirmer | Intégration générale d’annonces non établie | Piste uniquement pour des offres d’un employeur client; pas un flux public d’agrégation. |
| LinkedIn (configuration historique) | API soumise à approbation; contrat de crawl séparé | Le crawling est interdit sans autorisation expresse | Aucun droit établi | Consentement du détenteur et termes API applicables | Exclu; ne pas automatiser ni utiliser d’extracteur. |
| Emploi.ma | Site web | Conditions limitent à une consultation personnelle/privée | Extraction de base non autorisée sans accord exprès écrit | Diffusion publique non autorisée sans accord | Bloqué. |
| ReKrute | Site web | Usage privé sans permission | Extraction de base soumise à accord exprès écrit préalable | Non établi sans accord | Bloqué. |
| Stagiaires.ma | Site/application; ancien endpoint présent dans l’historique du projet | Aucune permission/API-feed de réutilisation confirmée | Non établi | Non établi | Non connecté; l’endpoint historique ne constitue pas une permission. |

## Vérifications officielles

- [Jawb — guide API](https://jawb.ma/en/api-recrutement) : flux RSS/JSON, limite de consultation et usage sur page carrière; [CGU Jawb](https://jawb.ma/cgu) : contenu protégé et reproduction/usage soumis à autorisation.
- [Open Data Maroc — thème Emploi](https://www.data.gov.ma/data/fr/dataset/?groups=emploi), [licence de réutilisation](https://www.data.gov.ma/fr/node/14) et [mode d’exploitation](https://www.data.gov.ma/fr/Comment_exploiter_les_donn%C3%A9es) : API de catalogue et licences par jeu. Les fiches consultées ne fournissent pas un flux général de postes de stage.
- [Trouve Ton Emploi — accès API et licence](https://skills.capprafrica.org/fr/nos-outils) : accès de recherche sous licence sur demande; documentation API fournie sur demande.
- [Jobsquare — intégration API](https://www.jobsquare.ma/aide-recruteur/api-integrations/) : clé demandée pour connecter le logiciel d’un recruteur.
- [ANAPEC](https://www.anapec.ma/) : le portail n’a pas fait apparaître d’API officielle avec droits d’agrégation dans cette recherche; ce statut est « non établi », pas une interdiction supposée.
- [LinkedIn — accord utilisateur](https://www.linkedin.com/legal/user-agreement) et [conditions de crawl](https://www.linkedin.com/legal/crawling-terms) : automatisation sans autorisation expresse interdite.
- [Conditions Emploi.ma](https://www.emploi.ma/conditions-generales-utilisation) et [mentions ReKrute](https://www.rekrute.com/fr/mentions-legales.html).

Le portail Open Data rappelle qu’il faut mentionner la source et respecter les conditions de la licence; chaque ressource doit être examinée séparément. Les obligations ODbL peuvent inclure la mise à disposition de la base adaptée sous les mêmes conditions.

## Sources à contacter et droits à demander

1. Employeurs marrakchis ciblés : flux carrière ou export CSV/XLSX; accès automatique, identifiants des annonces, stockage local, mise à jour, réaffichage des titres/extraits et liens directs, durée de conservation et attribution.
2. CAPPRAfrica / Trouve Ton Emploi : licence/API ou export portant explicitement sur consultation automatisée, téléchargement local, affichage dans une application personnelle, limites de fréquence, périmètre Maroc/Marrakech, frais et conservation.
3. ANAPEC : flux ou export d’offres autorisé, documentation de l’API, fréquence, stockage/cache, affichage, attribution et éventuelles limites à l’usage personnel.
4. Jawb et les employeurs qui y publient : autorisation couvrant précisément l’agrégation par cette application, la copie locale et le réaffichage avec lien vers l’annonce.
5. Jobsquare : seulement si un employeur participant fournit son compte/flux; préciser la propriété des annonces et l’affichage hors de l’ATS.

LinkedIn, Emploi.ma, ReKrute et Stagiaires.ma restent exclus jusqu’à permission écrite spécifique; ne pas tenter de contourner leurs restrictions.

## Référence de permission à archiver

Conserver le document ou contrat séparément; dans le Centre de collecte, enregistrer une référence, pas un secret. L’autorisation doit répondre oui à chacune des trois questions : consultation automatique autorisée? stockage local autorisé? réaffichage avec provenance autorisé? Le champ de référence est une attestation de l’utilisateur, pas une validation juridique automatisée. Un accord verbal ou une URL de page publique ne suffit pas.

Pour votre demande au titulaire, précisez également les offres visées (stages/PFE à Marrakech), la cadence envisagée, les champs requis, la durée de conservation, la conduite en cas de fermeture d’annonce, les liens/attributions à afficher, les éventuelles restrictions d’usage personnel/commercial et le contact chargé des retraits. Ne transmettez aucune clé API, mot de passe ou donnée de candidat dans la demande.
