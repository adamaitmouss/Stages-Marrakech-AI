"""Registre des sources, licences et mesures d'exécution connues."""
import json
from .service import sources_config
from ..db import rows


LEGAL_REVIEW_DATE = '2026-11-06'

# Ces entrées distinguent les possibilités d'accès des autorisations d'usage pour
# ce projet. Un accès public n'est jamais une preuve de droits de réutilisation.
CATALOG = [
    {'name':'Simulation locale','official_url':None,
     'access_type':'Fixture embarquée; aucune requête réseau',
     'fields':'Une offre fictive de démonstration, isolée de toute donnée réelle',
     'consultation_permission':'Sans objet; données synthétiques du projet',
     'storage_permission':'Pas de stockage dans les offres réelles',
     'display_permission':'Toujours affichée comme démonstration',
     'reuse_status':'Données fictives, jamais une annonce réelle', 'minimum_interval_seconds':None,
     'technical_status':'Simulation locale disponible; réseau désactivé',
     'authorization_status':'demonstration', 'legal_reviewed_at':None},
    {'name':'Jawb RSS','official_url':'https://jawb.ma/en/api-recrutement',
     'access_type':'RSS public, dernières 50 annonces; filtres ville/métier',
     'fields':'Titre, description, lien, identifiant et date; détails selon les annonces',
     'consultation_permission':'Aucune pour agrégation automatique; guide destiné aux pages carrière employeur',
     'storage_permission':'Non documentée pour ce projet', 'display_permission':'Non documentée pour ce projet',
     'reuse_status':'À autoriser par écrit pour consultation agrégée, stockage et réaffichage',
     'minimum_interval_seconds':300,'technical_status':'Connecteur présent; verrouillé sans autorisation',
     'authorization_status':'pending', 'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'Jawb JSON','official_url':'https://jawb.ma/en/api-recrutement',
     'access_type':'JSON public paginé par identifiant d’entreprise',
     'fields':'Entreprise, identifiant, titre, description, ville, contrat, métier, dates, URL de candidature',
     'consultation_permission':'Le guide décrit le flux pour le site carrière de l’entreprise; agrégation externe non établie',
     'storage_permission':'Non documentée pour ce projet', 'display_permission':'Non documentée pour ce projet',
     'reuse_status':'Accord écrit spécifique requis avant usage dans cette application',
     'minimum_interval_seconds':300,'technical_status':'Connecteur présent; verrouillé sans autorisation',
     'authorization_status':'pending', 'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'Flux carrière fourni','official_url':None,
     'access_type':'Flux RSS/Atom HTTPS fourni par l’utilisateur',
     'fields':'Champs réellement présents dans le flux',
     'consultation_permission':'À confirmer auprès de chaque propriétaire',
     'storage_permission':'À confirmer auprès de chaque propriétaire',
     'display_permission':'À confirmer auprès de chaque propriétaire',
     'reuse_status':'Autorisation séparée documentée par flux', 'minimum_interval_seconds':None,
     'technical_status':'Connecteur prêt après autorisation', 'authorization_status':'pending',
     'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'Fichier CSV/XLSX fourni','official_url':None,
     'access_type':'Import local d’un export remis par l’employeur, organisme ou titulaire',
     'fields':'Titre, employeur, ville, description, type, compétences, dates, identifiant et URL source',
     'consultation_permission':'À confirmer selon la licence ou l’accord transmis avec le fichier',
     'storage_permission':'À confirmer explicitement avant staging/import',
     'display_permission':'À confirmer explicitement pour afficher l’annonce et son lien source',
     'reuse_status':'Parcours prêt; aucune source ni licence reçue actuellement',
     'minimum_interval_seconds':None,'technical_status':'Import local disponible, sans appel réseau',
     'authorization_status':'permission_required', 'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'Portail Open Data Maroc','official_url':'https://data.gov.ma/data/fr/dataset/?groups=emploi',
     'access_type':'Portail/API CKAN et fichiers CSV/XLS/XLSX selon les jeux',
     'fields':'Dans la rubrique Emploi consultée : statistiques, indicateurs et statistiques d’emplois publics; pas de flux général d’offres de stage',
     'consultation_permission':'Oui pour chaque jeu et ressource publiés sous licence applicable',
     'storage_permission':'Oui sous licence ODbL lorsque cette licence est indiquée sur le jeu',
     'display_permission':'Oui avec attribution et respect des obligations ODbL, dont partage à l’identique des bases adaptées',
     'reuse_status':'Licence ouverte vérifiée sur les jeux concernés; contenu consulté non adapté aux annonces ciblées',
     'minimum_interval_seconds':None,'technical_status':'API de catalogue documentée; aucune offre de stage connectée',
     'authorization_status':'licensed_non_offer_data', 'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'Trouve Ton Emploi / CAPPRAfrica','official_url':'https://skills.capprafrica.org/fr/nos-outils',
     'access_type':'API et exports Excel proposés selon licence sur demande motivée',
     'fields':'Offres en cours et liens source annoncés dans l’accès; dictionnaire détaillé selon licence',
     'consultation_permission':'À demander; pas de licence octroyée à ce projet',
     'storage_permission':'Dépend de l’offre souscrite et du contrat; pas d’accord reçu',
     'display_permission':'Dépend de la licence et des conditions de réaffichage; pas d’accord reçu',
     'reuse_status':'Piste prioritaire à contacter pour licence API / export', 'minimum_interval_seconds':None,
     'technical_status':'API annoncée, documentation envoyée sur demande; non configurée',
     'authorization_status':'license_required', 'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'ANAPEC','official_url':'https://www.anapec.ma/',
     'access_type':'Portail d’emploi; aucune API/export public de réutilisation identifié',
     'fields':'Offres publiées sur le portail, selon fiches accessibles aux candidats',
     'consultation_permission':'Consultation manuelle publique possible; droit d’interrogation automatisée non établi',
     'storage_permission':'Non établie', 'display_permission':'Non établie',
     'reuse_status':'Demander un accord écrit, un flux ou un export autorisé', 'minimum_interval_seconds':None,
     'technical_status':'Non connecté; aucun scraping', 'authorization_status':'permission_required',
     'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'Jobsquare API','official_url':'https://www.jobsquare.ma/aide-recruteur/api-integrations/',
     'access_type':'API pour connecter un logiciel de recrutement; clé à demander',
     'fields':'Flux de recrutement du compte client, à préciser avec l’éditeur',
     'consultation_permission':'Clé API sur demande pour l’intégration du logiciel du client',
     'storage_permission':'À confirmer contractuellement', 'display_permission':'Usage d’intégration client; affichage public agrégé non établi',
     'reuse_status':'Peut convenir au flux d’un recruteur propriétaire, pas à l’agrégation générale sans accord',
     'minimum_interval_seconds':None,'technical_status':'Non configuré; clé non demandée',
     'authorization_status':'license_required', 'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'LinkedIn (source historique)','official_url':'https://www.linkedin.com/legal/user-agreement',
     'access_type':'Plateforme web; API seulement via produits et programmes approuvés',
     'fields':'Aucun champ connecté au pipeline d’offres',
     'consultation_permission':'Collecte automatisée interdite sans autorisation expresse; candidature API soumise à approbation',
     'storage_permission':'Aucun droit pour cette application; dépendrait des termes API et programme approuvé',
     'display_permission':'Aucun droit établi pour annonces agrégées; consentement/propriété du contenu requis',
     'reuse_status':'Exclu sans autorisation écrite LinkedIn et droits sur le contenu',
     'minimum_interval_seconds':None,'technical_status':'Non intégré; aucun scraping',
     'authorization_status':'blocked', 'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'Stagiaires.ma','official_url':'https://www.stagiaires.ma/',
     'access_type':'Site/application; ancien endpoint observé dans un script historique',
     'fields':'Aucun champ utilisé par le pipeline contrôlé',
     'consultation_permission':'Droit d’accès automatisé non établi', 'storage_permission':'Non établie',
     'display_permission':'Non établie', 'reuse_status':'À contacter; endpoint historique non considéré comme autorisation',
     'minimum_interval_seconds':None,'technical_status':'Non connecté; aucun scraping',
     'authorization_status':'permission_required', 'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'Emploi.ma','official_url':'https://www.emploi.ma/conditions-generales-utilisation',
     'access_type':'Site web', 'fields':'Aucun champ connecté',
     'consultation_permission':'Usage autorisé à titre personnel et privé seulement selon CGU',
     'storage_permission':'Non autorisée sans accord écrit exprès préalable',
     'display_permission':'Non autorisée pour diffusion publique sans accord',
     'reuse_status':'Exclu: CGU restreignent extraction de base et diffusion', 'minimum_interval_seconds':None,
     'technical_status':'Non intégré', 'authorization_status':'blocked', 'legal_reviewed_at':LEGAL_REVIEW_DATE},
    {'name':'ReKrute','official_url':'https://www.rekrute.com/fr/mentions-legales.html',
     'access_type':'Site web', 'fields':'Aucun champ connecté',
     'consultation_permission':'Usage privé uniquement sans accord spécifique',
     'storage_permission':'Extraction de base soumise à accord exprès écrit préalable',
     'display_permission':'Non établie sans accord',
     'reuse_status':'Exclu sans autorisation écrite préalable', 'minimum_interval_seconds':None,
     'technical_status':'Non intégré', 'authorization_status':'blocked', 'legal_reviewed_at':LEGAL_REVIEW_DATE},
    *[{'name':name,'official_url':url,'access_type':'API publique de publications pour les pages carrière des employeurs',
       'fields':'Annonces publiées accessibles; champs selon la configuration du board',
       'consultation_permission':'Accès technique public; autorisation de consultation automatique à confirmer par entreprise',
       'storage_permission':'Non accordée par la seule disponibilité de l’API; document justificatif requis',
       'display_permission':'Non accordée par la seule disponibilité de l’API; document justificatif requis',
       'reuse_status':'Verrouillé tant que les trois droits ne sont pas documentés pour un board précis',
       'minimum_interval_seconds':300,'technical_status':'Connecteur mockable; aucun réseau sans configuration et autorisation',
       'authorization_status':'pending','legal_reviewed_at':LEGAL_REVIEW_DATE}
      for name,url in [('Greenhouse Job Board API','https://docs.greenhouse.io/job-board'),
                       ('Lever Postings API','https://github.com/lever/postings-api'),
                       ('Ashby Job Postings API','https://developers.ashbyhq.com/docs/public-job-posting-api'),
                       ('SmartRecruiters Posting API','https://developers.smartrecruiters.com/docs/posting-api')]],
]


def _runtime_fields(source, previous):
    if not previous:
        return {'last_execution':None,'last_status':'not_run','detected_offers':0,
                'new_offers_last_run':0,'modified_offers_last_run':0,'duplicates_last_run':0,
                'rejected_offers_last_run':0,'imported_offers_last_run':0,'last_import_at':None,'error':None}
    return {'last_execution':previous.get('finished_at'),'last_status':previous.get('status'),
            'detected_offers':previous.get('fetched_count') or 0,
            'new_offers_last_run':previous.get('new_offers') or 0,
            'modified_offers_last_run':previous.get('updated_offers') or 0,
            'duplicates_last_run':previous.get('duplicates') or 0,
            'rejected_offers_last_run':previous.get('rejected_offers') or 0,
            'imported_offers_last_run':previous.get('imported_offers') or 0,
            'last_import_at':previous.get('imported_at'),'error':previous.get('error_summary')}


def source_catalog(path):
    cfg=sources_config(path)
    runs=rows(path,'''SELECT s.*,r.imported_at FROM collector_source_runs s
        JOIN collector_runs r ON r.id=s.run_id
        JOIN (SELECT source,MAX(id) id FROM collector_source_runs GROUP BY source) latest ON latest.id=s.id''')
    by_source={item['source']:item for item in runs}
    configured={x.get('name') or 'Flux carrière':x for x in cfg.get('career_feeds',[])}
    boards={f"{x.get('platform','').title()} · {x.get('name','')}":x for x in cfg.get('career_boards',[])}
    result=[]
    known={item['name'] for item in CATALOG}
    for item in CATALOG:
        value=dict(item);source=value['name'];previous=by_source.get(source)
        if source=='Jawb RSS':value['configured']=cfg['jawb_rss_enabled']
        elif source=='Jawb JSON':value['configured']=bool(cfg['jawb_company_ids'])
        elif source=='Flux carrière':value['configured']=bool(cfg['career_feeds'])
        elif source.startswith(('Greenhouse ','Lever ','Ashby ','SmartRecruiters ')):
            prefix=source.split(' ',1)[0].lower()
            value['configured']=any(x.get('platform')==prefix for x in cfg.get('career_boards',[]))
        else:value['configured']=False
        if source in ('Jawb RSS','Jawb JSON'):
            attested=cfg['jawb_import_approved'] and bool(cfg['jawb_permission_ref'].strip())
            for key,label in [('jawb_consult_allowed','consultation'),('jawb_storage_allowed','stockage'),('jawb_display_allowed','réaffichage')]:
                value[f'{key}_attested']=bool(cfg[key])
                value[{'jawb_consult_allowed':'consultation_permission','jawb_storage_allowed':'storage_permission','jawb_display_allowed':'display_permission'}[key]]=('Attestation utilisateur enregistrée; accord non vérifié par l’application' if attested and cfg[key] else 'Non attestée')
            value['authorization_status']='user_attested' if attested and all(cfg[k] for k in ('jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed')) else 'pending'
            if attested:value['reuse_status']='Référence utilisateur présente; validité et périmètre à vérifier avant activation'
        value.update(_runtime_fields(source,previous));result.append(value)
    for name,feed in configured.items():
        previous=by_source.get(name)
        value={'name':name,'official_url':feed.get('url'),'access_type':'Flux carrière HTTPS fourni par l’utilisateur',
            'fields':'Champs effectivement présents dans le flux',
            'consultation_permission':'Attestation utilisateur enregistrée; vérifier le document' if feed.get('consultation_allowed') else 'Non attestée',
            'storage_permission':'Attestation utilisateur enregistrée; vérifier le document' if feed.get('storage_allowed') else 'Non attestée',
            'display_permission':'Attestation utilisateur enregistrée; vérifier le document' if feed.get('display_allowed') else 'Non attestée',
            'reuse_status':'Autorisation à documenter pour ce flux',
            'minimum_interval_seconds':None,'technical_status':'connecteur prêt' if feed.get('permission_ref') else 'bloqué sans autorisation',
            'authorization_status':'user_attested' if feed.get('permission_ref') and all(feed.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')) else 'pending',
            'legal_reviewed_at':None,'configured':True}
        value.update(_runtime_fields(name,previous));result.append(value);known.add(name)
    for source,board in boards.items():
        previous=by_source.get(source)
        permitted=bool(board.get('permission_ref')) and all(board.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed'))
        value={'name':source,'official_url':board.get('career_url'),'access_type':board.get('platform','').title()+' job board '+board.get('board_id',''),
            'fields':'Champs normalisés du connecteur ATS; classification selon les données publiées',
            'consultation_permission':'Référence enregistrée; vérifier la portée du document' if board.get('consultation_allowed') else 'Non attestée',
            'storage_permission':'Référence enregistrée; vérifier la portée du document' if board.get('storage_allowed') else 'Non attestée',
            'display_permission':'Référence enregistrée; vérifier la portée du document' if board.get('display_allowed') else 'Non attestée',
            'reuse_status':'Autorisation utilisateur documentée; vérification finale reste à sa charge',
            'minimum_interval_seconds':300,'technical_status':'activé' if board.get('enabled') and permitted else 'désactivé / droits incomplets',
            'authorization_status':'user_attested' if permitted else 'pending','legal_reviewed_at':board.get('last_verified_at') or None,
            'configured':True,'company':board.get('name'),'city':board.get('city'),'sector':board.get('sector'),'enabled':bool(board.get('enabled'))}
        value.update(_runtime_fields(source,previous));result.append(value);known.add(source)
    for name,previous in by_source.items():
        if name in known or name in configured:continue
        metadata=rows(path,'SELECT source_metadata_json FROM collector_runs WHERE id=(SELECT run_id FROM collector_source_runs WHERE source=? ORDER BY id DESC LIMIT 1)',(name,))
        extra={}
        if metadata:
            try:extra=json.loads(metadata[0]['source_metadata_json'] or '{}')
            except (ValueError,TypeError):pass
        value={'name':name,'official_url':None,'access_type':'Fichier fourni localement',
            'fields':'Offres normalisées depuis CSV/XLSX',
            'consultation_permission':'Fichier fourni par l’utilisateur; accord attesté et référencé' if extra.get('permission_ref') else 'À confirmer',
            'storage_permission':'Attestation enregistrée' if extra.get('storage_allowed') else 'Non attestée',
            'display_permission':'Attestation enregistrée' if extra.get('display_allowed') else 'Non attestée',
            'reuse_status':'Fichier fourni; vérifier la licence/source indiquée dans l’historique',
            'minimum_interval_seconds':None,'technical_status':'Import local uniquement',
            'authorization_status':'provided_file' if extra.get('permission_ref') else 'pending',
            'legal_reviewed_at':None,'configured':False}
        value.update(_runtime_fields(name,previous));result.append(value)
    return result
