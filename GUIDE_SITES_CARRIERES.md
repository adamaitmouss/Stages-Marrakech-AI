# Guide du registre des sites carrières

Le registre ne découvre pas d’entreprises ni de pages carrière. L’utilisateur ajoute les cibles qu’il a vérifiées; aucun nom, URL ou identifiant de board n’est inventé.

## Ajouter une source

Dans **Centre de collecte → Sites carrières**, fournir :

- le nom et le site officiel de l’entreprise;
- l’URL de la page carrière ou du flux RSS/Atom officiel;
- Greenhouse, Lever, Ashby, SmartRecruiters ou RSS;
- l’identifiant exact du board pour une API ATS;
- la ville et le secteur;
- la référence documentaire et la date de vérification;
- les trois autorisations distinctes : consultation automatique, stockage et réaffichage.

Un board sans droits complets peut être enregistré comme candidat désactivé. Le serveur refuse son activation et le collecteur ne l’interroge pas. Une source autorisée peut être désactivée depuis sa ligne de registre.

## Cibles à examiner

Les domaines à prioriser sont ceux définis dans le cahier Phase 8 : informatique, données et IA, développement, marketing digital, banque/finance, tourisme/hôtellerie, logistique et commerce. L’application ne préremplit aucune liste d’employeurs faute de cibles fournies et d’autorisation documentée. Confirmer directement le site officiel, le fournisseur ATS et le contact pouvant accorder les droits.

## Association à une fiche entreprise existante

Au moment de l’aperçu, le système propose une association seulement si le nom correspond exactement à une fiche unique SQLite. En cas de plusieurs correspondances identiques, de nom différent ou d’absence de nom, il n’associe rien automatiquement. Une offre non associée reste importable sans fiche complète. Une ressemblance partielle peut apparaître comme piste à examiner, mais ne déclenche jamais de fusion. Les fiches provisoires ne sont pas créées automatiquement.

Une annonce est affichée comme expirée si une date valide le prouve; sans date elle reste de validité inconnue. La disparition d’une annonce d’un flux n’entraîne pas de suppression automatique et ne suffit pas à certifier son retrait.
