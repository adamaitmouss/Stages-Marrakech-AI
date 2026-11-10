"""Orchestrateur d'import public, incrémental, journalisé et jamais destructif."""
import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit
from .jawb import fetch_rss, fetch_company_feed, fetch_career_rss
from .platforms import FETCHERS
from .schema import identity_key, fingerprint, normalize_offer, content_hash
from ..db import connect, now, rows, backup_database


def get_setting(path, key, default=None):
    found = rows(path, 'SELECT value FROM collection_settings WHERE key=?', (key,))
    if not found:
        return default
    try:
        return json.loads(found[0]['value'])
    except (TypeError, ValueError):
        return default


def set_setting(db, key, value):
    db.execute('''INSERT INTO collection_settings(key,value,updated_at) VALUES (?,?,?)
                  ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at''',
               (key, json.dumps(value, ensure_ascii=False), now()))


def sources_config(path):
    return {
        'external_enabled': bool(get_setting(path, 'external_enabled', False)),
        'auto_enabled': bool(get_setting(path, 'auto_enabled', False)),
        'frequency': get_setting(path, 'frequency', 'daily'),
        'jawb_rss_enabled': bool(get_setting(path, 'jawb_rss_enabled', False)),
        'jawb_import_approved': bool(get_setting(path, 'jawb_import_approved', False)),
        'jawb_consult_allowed': bool(get_setting(path, 'jawb_consult_allowed', False)),
        'jawb_storage_allowed': bool(get_setting(path, 'jawb_storage_allowed', False)),
        'jawb_display_allowed': bool(get_setting(path, 'jawb_display_allowed', False)),
        'jawb_permission_ref': get_setting(path,'jawb_permission_ref',''),
        'career_import_approved': bool(get_setting(path, 'career_import_approved', False)),
        'jawb_company_ids': get_setting(path, 'jawb_company_ids', []),
        'career_feeds': get_setting(path, 'career_feeds', []),
        'career_boards': get_setting(path, 'career_boards', []),
    }


def set_sources_config(path, values):
    allowed = {'external_enabled','auto_enabled','frequency','jawb_rss_enabled','jawb_import_approved','jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed','jawb_permission_ref','career_import_approved','jawb_company_ids','career_feeds','career_boards'}
    with connect(path) as db:
        for key, value in values.items():
            if key not in allowed:
                continue
            if key in ('external_enabled','auto_enabled','jawb_rss_enabled','jawb_import_approved','jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed','career_import_approved') and type(value) is not bool:
                raise ValueError(f'Paramètre invalide : {key}.')
            if key == 'frequency' and value not in ('daily','weekly'):
                raise ValueError('Fréquence de collecte invalide.')
            if key == 'jawb_company_ids':
                if not isinstance(value,list) or len(value)>50 or any(not isinstance(v,str) or len(v)>120 for v in value):
                    raise ValueError('Identifiants Jawb invalides.')
            if key == 'career_feeds':
                if not isinstance(value,list) or len(value)>20 or any(not isinstance(v,dict) or len(str(v.get('name','')))>100 or len(str(v.get('url','')))>500 or len(str(v.get('permission_ref','')))>500 for v in value):
                    raise ValueError('Liste de flux carrière invalide.')
                for feed in value:
                    parsed=urlsplit(str(feed.get('url') or ''))
                    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:
                        raise ValueError('Chaque flux carrière doit utiliser une URL HTTPS publique sans identifiants intégrés.')
                    if any(type(feed.get(k,False)) is not bool for k in ('consultation_allowed','storage_allowed','display_allowed')):
                        raise ValueError('Les trois périmètres d’autorisation du flux carrière doivent être des cases distinctes.')
            if key == 'career_boards':
                if not isinstance(value, list) or len(value) > 100:
                    raise ValueError('Registre de sites carrières invalide (100 sources maximum).')
                required = ('name','official_url','career_url','platform','board_id','city','sector','permission_ref')
                for board in value:
                    if not isinstance(board, dict) or any(not isinstance(board.get(field, ''), str) or len(board.get(field, '')) > 500 for field in required):
                        raise ValueError('Champs du registre carrière invalides.')
                    if board.get('platform') not in ('greenhouse','lever','ashby','smartrecruiters','rss'):
                        raise ValueError('Plateforme ATS inconnue.')
                    if board.get('platform')!='rss' and not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', board.get('board_id','')):
                        raise ValueError('Identifiant de job board invalide.')
                    for url_key in ('official_url','career_url'):
                        parsed = urlsplit(board.get(url_key, ''))
                        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                            raise ValueError('Les URL officielles et carrières doivent être HTTPS, sans identifiants.')
                    for flag in ('consultation_allowed','storage_allowed','display_allowed','enabled'):
                        if type(board.get(flag, False)) is not bool:
                            raise ValueError('Les droits et l’activation de chaque entreprise doivent être explicites.')
                    if board.get('enabled') and (not board.get('permission_ref').strip() or not all(board.get(k) for k in ('consultation_allowed','storage_allowed','display_allowed'))):
                        raise ValueError('Une source ne peut être activée sans référence et trois droits attestés.')
                    if board.get('platform')=='lever' and board.get('region','global') not in ('global','eu'):
                        raise ValueError('Région Lever invalide.')
                    if board.get('last_verified_at'):
                        try:datetime.fromisoformat(board['last_verified_at'])
                        except ValueError:raise ValueError('Date de vérification de la source invalide.')
            if key=='jawb_permission_ref' and (not isinstance(value,str) or len(value)>500):
                raise ValueError('Référence de l’autorisation Jawb invalide.')
            set_setting(db,key,value)
    return sources_config(path)


def _connector_options(path):
    cfg=sources_config(path)
    choices=[]
    jawb_rights=cfg['jawb_import_approved'] and cfg['jawb_permission_ref'].strip() and all(cfg[k] for k in ('jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed'))
    if cfg['jawb_rss_enabled'] and jawb_rights:
        choices.append(('Jawb RSS',lambda:fetch_rss(city='Marrakech')))
    if cfg['jawb_company_ids'] and jawb_rights:
        choices.append(('Jawb JSON',lambda:fetch_company_feed(company_ids=cfg['jawb_company_ids'])))
    for entry in cfg['career_feeds'] if cfg['career_import_approved'] else []:
        if not str(entry.get('permission_ref') or '').strip() or not all(entry.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')):continue
        choices.append((entry.get('name') or 'Flux carrière',lambda e=entry:fetch_career_rss(None,e.get('name') or 'Flux carrière',e.get('url') or '')))
    for entry in cfg['career_boards']:
        if not entry.get('enabled') or not entry.get('permission_ref') or not all(entry.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')):
            continue
        if entry['platform']=='rss':
            source_name=f"{entry['platform'].title()} · {entry['name']}"
            choices.append((source_name,lambda e=entry,n=source_name:fetch_career_rss(None,n,e['career_url'])))
            continue
        fetcher=FETCHERS[entry['platform']]
        args={'greenhouse': (entry['board_id'],entry['name']), 'lever': (entry['board_id'],entry['name']),
              'ashby': (entry['board_id'],entry['name']), 'smartrecruiters': (entry['board_id'],entry['name'])}[entry['platform']]
        if entry['platform']=='lever':
            choices.append((f"{entry['platform'].title()} · {entry['name']}",lambda f=fetcher,a=args,r=entry.get('region','global'):f(*a,region=r)))
        else:
            choices.append((f"{entry['platform'].title()} · {entry['name']}",lambda f=fetcher,a=args:f(*a)))
    return cfg,choices


def create_run(path, mode):
    if mode not in ('simulation','preview','automatic','company-import-preview','gemini-search'):
        raise ValueError('Mode de collecte inconnu.')
    stamp=now()
    with connect(path) as db:
        cur=db.execute('INSERT INTO collector_runs(mode,status,started_at) VALUES (?,?,?)',(mode,'running',stamp))
        run_id=cur.lastrowid
    return run_id


def execute_run(path, run_id, mode):
    errors=[];fetched=0;run_started=time.perf_counter()
    try:
        if mode=='simulation':
            # Fixture pédagogique uniquement: aucun réseau et aucune écriture dans la table offres.
            raw={'id':'demo-python-sql','title':'  Stage de démonstration Python et SQL  ',
                   'company':'Entreprise fictive de démonstration','city':'Marrakech','sector':'Data Science',
                   'description':'<p>Offre fictive créée pour vérifier le parcours de collecte et alertes. Python et SQL.</p>',
                   'contract_type':'Stage','internship_type':'Stage PFE','skills':['Python','SQL'],
                   'published_at':None,'expires_at':None,'url':'https://example.invalid/offre-demo'}
            item=normalize_offer(raw,'Simulation locale')
            item['sector']='Data Science'
            with connect(path) as db:
                db.execute('''INSERT INTO collector_staging(run_id,source,identity_key,payload_json) VALUES (?,?,?,?)''',
                           (run_id,'Simulation locale',identity_key(item),json.dumps(item,ensure_ascii=False)))
                db.execute('UPDATE collector_runs SET status=?,finished_at=?,source_count=1,fetched_count=1,duration_ms=? WHERE id=?',('simulated',now(),round((time.perf_counter()-run_started)*1000),run_id))
            return {'id':run_id,'mode':mode,'status':'simulated','fetched_count':1,'sources':[{'source':'Simulation locale','status':'simulated','fetched_count':1,'error':None}]}

        cfg,connectors=_connector_options(path)
        if not cfg['external_enabled']:
            raise ValueError('Collecte externe désactivée. Activez-la explicitement dans Centre de collecte.')
        if not connectors:
            raise ValueError('Aucune source activée et autorisée. Ajoutez une source dont les trois droits sont documentés.')
        with connect(path) as db:
            db.execute('UPDATE collector_runs SET source_count=? WHERE id=?',(len(connectors),run_id))
        source_results=[]
        for source,fetch in connectors:
            started=now();source_clock=time.perf_counter();items=[];err=None
            previous=rows(path,'SELECT finished_at FROM collector_source_runs WHERE source=? AND finished_at IS NOT NULL ORDER BY id DESC LIMIT 1',(source,))
            cooling=False
            if previous:
                try:cooling=(datetime.now(timezone.utc)-datetime.fromisoformat(previous[0]['finished_at'])).total_seconds()<300
                except (TypeError,ValueError):pass
            try:
                if cooling:
                    status='skipped';err='Actualisation ignorée : cette source a déjà été interrogée au cours des cinq dernières minutes.'
                    raise StopIteration
                items=fetch()
                fetched+=len(items)
                for item in items:
                    key=identity_key(item)
                    if not key:
                        continue
                    with connect(path) as db:
                        db.execute('''INSERT OR IGNORE INTO collector_staging(run_id,source,identity_key,payload_json)
                                      VALUES (?,?,?,?)''',(run_id,item['source'],key,json.dumps(item,ensure_ascii=False)))
                status='previewed'
            except StopIteration:
                pass
            except Exception as exc:
                status='failed';err=type(exc).__name__+': '+str(exc)[:500];errors.append(source+': '+err)
            with connect(path) as db:
                db.execute('''INSERT INTO collector_source_runs(run_id,source,status,started_at,finished_at,fetched_count,error_summary,duration_ms)
                              VALUES (?,?,?,?,?,?,?,?)''',(run_id,source,status,started,now(),len(items),err,round((time.perf_counter()-source_clock)*1000)))
            source_results.append({'source':source,'status':status,'fetched_count':len(items),'error':err})
        final='previewed' if any(x['status']=='previewed' for x in source_results) else 'failed'
        with connect(path) as db:
            db.execute('UPDATE collector_runs SET status=?,finished_at=?,fetched_count=?,error_summary=? WHERE id=?',
                       (final,now(),fetched,'\n'.join(errors)[:3000] or None,run_id))
            db.execute('UPDATE collector_runs SET duration_ms=?,error_count=? WHERE id=?',(round((time.perf_counter()-run_started)*1000),len(errors),run_id))
        return {'id':run_id,'mode':mode,'status':final,'fetched_count':fetched,'errors':errors,'sources':source_results}
    except Exception as exc:
        with connect(path) as db:
            db.execute('UPDATE collector_runs SET status=?,finished_at=?,error_summary=? WHERE id=?',
                       ('failed',now(),type(exc).__name__+': '+str(exc)[:1000],run_id))
            db.execute('UPDATE collector_runs SET duration_ms=?,error_count=1 WHERE id=?',(round((time.perf_counter()-run_started)*1000),run_id))
        return {'id':run_id,'mode':mode,'status':'failed','fetched_count':fetched,'errors':[str(exc)[:500]]}


def _existing_offer(db, source, identity):
    if identity.get('source_id'):
        row=db.execute('SELECT offer_id FROM offer_source_identity WHERE source=? AND external_id=?',(source,identity['source_id'])).fetchone()
        if row:return row[0]
    if identity.get('url'):
        row=db.execute('SELECT offer_id FROM offer_source_identity WHERE source=? AND canonical_url=?',(source,identity['canonical_url'])).fetchone()
        if row:return row[0]
    return None


def _exact_company(db, name):
    name=str(name or '').strip()
    if not name:return None
    matches=db.execute('SELECT rowid,"Nom" FROM entreprises WHERE lower(trim("Nom"))=lower(trim(?))',(name,)).fetchall()
    return matches[0] if len(matches)==1 else None


def _alert_match(db, offer_id):
    from ..alerts import maybe_create_alert
    return maybe_create_alert(db,offer_id)


def _offer_status(expires_at):
    if not expires_at:return 'unknown'
    try:return 'expired' if datetime.fromisoformat(expires_at.replace('Z','+00:00')).date()<datetime.now(timezone.utc).date() else 'active'
    except (ValueError,TypeError):return 'unknown'


def import_run(path, run_id, allow_sources=(), backup_dir=None, allow_simulation=False, allow_provided_file=False, allow_gemini_search=False):
    cfg=sources_config(path)
    permitted=set(allow_sources)
    run_metadata={}
    with connect(path) as db:
        run_check=db.execute('SELECT mode,source_metadata_json FROM collector_runs WHERE id=?',(run_id,)).fetchone()
    provided_file=bool(allow_provided_file and run_check and run_check['mode']=='file-import')
    if run_check:
        try: run_metadata=json.loads(run_check['source_metadata_json'] or '{}')
        except (ValueError,TypeError): run_metadata={}
    gemini_search=bool(allow_gemini_search and run_check and run_check['mode']=='gemini-search' and run_metadata.get('kind')=='gemini_search'
        and run_metadata.get('manual_verified') is True and run_metadata.get('permission_ref')
        and all(run_metadata.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')))
    if not cfg['external_enabled'] and not provided_file and not gemini_search and not (allow_simulation and run_check and run_check['mode']=='gemini-search' and run_metadata.get('kind')=='demo'):
        raise ValueError('Collecte externe désactivée.')
    if run_check and run_check['mode']=='file-import':
        if not allow_provided_file:
            raise ValueError('Utilisez la confirmation d’import du fichier fourni.')
        try:run_metadata=json.loads(run_check['source_metadata_json'] or '{}')
        except (ValueError,TypeError):run_metadata={}
        if (run_metadata.get('kind')!='provided_file' or not run_metadata.get('permission_ref')
                or not all(run_metadata.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed'))):
            raise ValueError('La provenance et les droits du fichier doivent être documentés avant import.')
        if permitted!={run_metadata.get('source_name')}:
            raise ValueError('La source sélectionnée ne correspond pas à celle déclarée pour le fichier.')
    elif allow_provided_file:
        raise ValueError('Cette collecte n’est pas un fichier fourni.')
    if not provided_file and not gemini_search:
        if not allow_simulation and 'Jawb RSS' not in permitted and 'Jawb JSON' not in permitted and not any(s not in ('Jawb RSS','Jawb JSON','Simulation locale') for s in permitted):
            raise ValueError('Confirmez explicitement les droits d’import des sources avant écriture SQLite.')
        if ('Jawb RSS' in permitted or 'Jawb JSON' in permitted) and (not cfg['jawb_import_approved'] or not cfg['jawb_permission_ref'].strip() or not all(cfg[k] for k in ('jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed'))):
            raise ValueError('Les autorisations Jawb de consultation, stockage et affichage doivent être documentées et confirmées séparément.')
        authorized_feeds={str(x.get('name') or 'Flux carrière') for x in cfg['career_feeds'] if str(x.get('permission_ref') or '').strip() and all(x.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed'))}
        authorized_feeds.update(f"{x['platform'].title()} · {x['name']}" for x in cfg['career_boards'] if x.get('enabled') and x.get('permission_ref') and all(x.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')))
        requested_feeds={s for s in permitted if s not in ('Jawb RSS','Jawb JSON','Simulation locale')}
        if requested_feeds and not requested_feeds.issubset(authorized_feeds):
            raise ValueError('Une autorisation documentée est requise pour chaque source carrière importée.')
    if gemini_search and permitted != {run_metadata.get('source_name')}:
        raise ValueError('La source sélectionnée ne correspond pas à la source vérifiée pour cet import.')
    backup_database(path, backup_dir or Path(path).resolve().parent.parent/'backups','avant_collecte_offres')
    with connect(path) as db:
        db.execute('BEGIN IMMEDIATE')
        run=db.execute('SELECT * FROM collector_runs WHERE id=?',(run_id,)).fetchone()
        if not run or run['status'] not in ('previewed','simulated'):
            raise ValueError('Cette collecte ne contient pas de résultats à importer.')
        staged=db.execute("SELECT * FROM collector_staging WHERE run_id=? AND decision='approved'",(run_id,)).fetchall()
        new_count=updated_count=unchanged_count=review_count=0
        duplicate_count=int(run_metadata.get('file_duplicate_rows') or 0) if provided_file else 0
        expired_count=0;approved_count=0;new_alert_ids=[];by_source={}
        for row in staged:
            if row['source'] not in permitted:continue
            item=json.loads(row['payload_json']);source=item['source']
            stats=by_source.setdefault(source,{'new':0,'updated':0,'unchanged':0,'duplicates':0})
            if source=='Simulation locale' and not allow_simulation:
                raise ValueError('Les données de simulation ne peuvent jamais être importées dans l’application réelle.')
            offer_id=_existing_offer(db,source,item);stamp=now();item_hash=content_hash(item);offer_status=_offer_status(item.get('expires_at'))
            if offer_id:
                source_identity=db.execute('SELECT content_hash FROM offer_source_identity WHERE source=? AND offer_id=?',(source,offer_id)).fetchone()
                changed=not source_identity or not source_identity['content_hash'] or source_identity['content_hash']!=item_hash
                company=_exact_company(db,item.get('company'))
                db.execute('''UPDATE offres SET Titre=COALESCE(NULLIF(?,''),Titre),Description=COALESCE(NULLIF(?,''),Description),
                    "Type contrat"=COALESCE(NULLIF(?,''),"Type contrat"),"Type stage"=COALESCE(NULLIF(?,''),"Type stage"),
                    "Date publication"=COALESCE(?,"Date publication"),"Date expiration"=COALESCE(?,"Date expiration"),
                    "Lien annonce"=COALESCE(NULLIF(?,''),"Lien annonce"),"Lien public"=COALESCE(NULLIF(?,''),"Lien public"),source=?,entreprise_nom=COALESCE(NULLIF(?,''),entreprise_nom),
                    "Entreprise ID"=COALESCE(?,"Entreprise ID"),ville=COALESCE(NULLIF(?,''),ville),competences=COALESCE(NULLIF(?,''),competences),
                    collected_at=?,last_verified_at=?,statut_offre=? WHERE "ID"=?''',
                    (item['title'],item['description'],item['contract_type'],item['internship_type'],item['published_at'],item['expires_at'],item.get('job_url') or item['url'],item.get('apply_url') or item['url'],source,item['company'],company['rowid'] if company else None,item['city'],', '.join(item['skills']),stamp,stamp,offer_status,offer_id))
                if changed:
                    updated_count+=1;stats['updated']+=1;prior_alert=db.execute('SELECT id FROM alerts WHERE offer_id=?',(offer_id,)).fetchone()
                    alert_result=_alert_match(db,offer_id)
                    if alert_result and not prior_alert:
                        alert_row=db.execute('SELECT id FROM alerts WHERE offer_id=?',(offer_id,)).fetchone()
                        if alert_row:new_alert_ids.append(alert_row['id'])
                else:unchanged_count+=1;stats['unchanged']+=1
                db.execute('UPDATE offer_source_identity SET last_seen=?,content_hash=? WHERE source=? AND offer_id=?',(stamp,item_hash,source,offer_id))
            else:
                offer_id=db.execute('SELECT COALESCE(MAX("ID"),0)+1 FROM offres').fetchone()[0]
                company=_exact_company(db,item.get('company'))
                db.execute('''INSERT INTO offres("ID","Titre","Description","Type contrat","Type stage","Date publication","Date expiration","Lien annonce","Lien public","Entreprise ID",source,entreprise_nom,ville,competences,collected_at,last_verified_at,statut_offre)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (offer_id,item['title'],item['description'] or None,item['contract_type'] or None,item['internship_type'] or None,item['published_at'],item['expires_at'],item.get('job_url') or item['url'],item.get('apply_url') or item['url'],company['rowid'] if company else None,source,item['company'] or None,item['city'] or None,', '.join(item['skills']) or None,stamp,stamp,offer_status))
                new_count+=1;stats['new']+=1
                db.execute('''INSERT INTO offer_source_identity(offer_id,source,external_id,canonical_url,first_seen,last_seen,content_hash)
                    VALUES (?,?,?,?,?,?,?)''',(offer_id,source,item['source_id'] or None,item['canonical_url'],stamp,stamp,item_hash))
                existing=db.execute('SELECT "ID",Titre,entreprise_nom,ville,Description FROM offres WHERE "ID"<>?',(offer_id,)).fetchall()
                target=fingerprint(item)
                candidates=[old['ID'] for old in existing if fingerprint({'company':old['entreprise_nom'],'title':old['Titre'],'city':old['ville'],'description':old['Description']})==target]
                for candidate_id in candidates:
                    duplicate_count+=1;review_count+=1;stats['duplicates']+=1
                    db.execute('''INSERT OR IGNORE INTO collector_duplicate_candidates(run_id,offer_id,candidate_offer_id,score,status,created_at)
                        VALUES (?,?,?,?,?,?)''',(run_id,offer_id,candidate_id,0.85,'review',stamp))
                alert_result=_alert_match(db,offer_id)
                if alert_result:
                    alert_row=db.execute('SELECT id FROM alerts WHERE offer_id=?',(offer_id,)).fetchone()
                    if alert_row:new_alert_ids.append(alert_row['id'])
            if offer_status=='expired':expired_count+=1
            db.execute("UPDATE collector_staging SET decision='imported' WHERE id=?",(row['id'],));approved_count+=1
        if provided_file and duplicate_count:
            file_source=run_metadata.get('source_name')
            source_stats=by_source.setdefault(file_source,{'new':0,'updated':0,'unchanged':0,'duplicates':0})
            source_stats['duplicates']+=duplicate_count
        pending_count=db.execute("SELECT COUNT(*) FROM collector_staging WHERE run_id=? AND decision='pending'",(run_id,)).fetchone()[0]
        final_status='imported' if approved_count and not pending_count else 'previewed'
        imported_at=now()
        rejected_total=db.execute("SELECT COUNT(*) FROM collector_staging WHERE run_id=? AND decision='rejected'",(run_id,)).fetchone()[0]
        rejected_total+=len(run_metadata.get('parse_errors') or []) if provided_file else 0
        db.execute('''UPDATE collector_runs SET status=?,finished_at=?,new_offers=?,updated_offers=?,unchanged_offers=?,duplicates=?,review_offers=?,expired_offers=?,imported_at=?,imported_offers=?,rejected_offers=? WHERE id=?''',
            (final_status,imported_at,new_count,updated_count,unchanged_count,duplicate_count,review_count,expired_count,imported_at,approved_count,rejected_total,run_id))
        run_sources=db.execute('SELECT DISTINCT source FROM collector_source_runs WHERE run_id=?',(run_id,)).fetchall()
        for source_row in run_sources:
            source=source_row['source'];stats=by_source.get(source,{'new':0,'updated':0,'unchanged':0,'duplicates':0})
            source_rejected=db.execute("SELECT COUNT(*) FROM collector_staging WHERE run_id=? AND source=? AND decision='rejected'",(run_id,source)).fetchone()[0]
            if provided_file and source==run_metadata.get('source_name'):
                source_rejected+=len(run_metadata.get('parse_errors') or [])
            imported_source=stats['new']+stats['updated']+stats['unchanged']
            source_status='imported' if imported_source else 'reviewed' if source_rejected else 'previewed'
            db.execute('''UPDATE collector_source_runs SET status=?,new_offers=?,updated_offers=?,duplicates=?,rejected_offers=?,imported_offers=?,imported_at=? WHERE run_id=? AND source=?''',
                (source_status,stats['new'],stats['updated'],stats['duplicates'],source_rejected,imported_source,imported_at,run_id,source))
    if new_alert_ids:
        from ..alert_mail import deliver_new_alerts
        deliver_new_alerts(path,new_alert_ids)
    return {'id':run_id,'status':final_status,'new_offers':new_count,'updated_offers':updated_count,
            'unchanged_offers':unchanged_count,'duplicates':duplicate_count,'review_offers':review_count,'expired_offers':expired_count,'imported':approved_count,'rejected_offers':rejected_total,'imported_at':imported_at}


def run_history(path, limit=50):
    return rows(path,'SELECT * FROM collector_runs ORDER BY id DESC LIMIT ?', (max(1,min(int(limit),100)),))


def run_details(path, run_id):
    run=rows(path,'SELECT * FROM collector_runs WHERE id=?',(run_id,))
    if not run:return None
    sources=rows(path,'SELECT source,status,started_at,finished_at,fetched_count,new_offers,updated_offers,duplicates,error_summary,duration_ms FROM collector_source_runs WHERE run_id=? ORDER BY id',(run_id,))
    staged=rows(path,'SELECT id,source,identity_key,payload_json,decision FROM collector_staging WHERE run_id=? ORDER BY id',(run_id,))
    for item in staged:
        offer=json.loads(item.pop('payload_json'));item['offer']=offer
        from .classification import classify_offer
        item['classification']=classify_offer(offer)
        item['missing_fields']=offer.get('missing_fields',[])
        existing=rows(path,'SELECT offer_id,content_hash FROM offer_source_identity WHERE source=? AND ((external_id IS NOT NULL AND external_id=?) OR (canonical_url IS NOT NULL AND canonical_url=?)) LIMIT 1',
                      (item['source'],offer.get('source_id'),offer.get('canonical_url')))
        item['existing_offer_id']=existing[0]['offer_id'] if existing else None
        item['content_state']='modified' if existing and existing[0].get('content_hash') and existing[0]['content_hash']!=content_hash(offer) else 'unchanged' if existing else 'new'
        item['possible_duplicates']=0
        item['company_match']={'status':'unidentified','company_id':None,'company_name':None,'candidates':[]}
        if offer.get('company'):
            exact=rows(path,'SELECT rowid AS id,"Nom" AS name FROM entreprises WHERE lower(trim("Nom"))=lower(trim(?))',(offer['company'],))
            if len(exact)==1:item['company_match']={'status':'exact_existing_match','company_id':exact[0]['id'],'company_name':exact[0]['name'],'candidates':[]}
            elif len(exact)>1:item['company_match']={'status':'ambiguous_exact_matches','company_id':None,'company_name':None,'candidates':[x['name'] for x in exact]}
            else:
                item['company_match']={'status':'no_exact_match','company_id':None,'company_name':None,'candidates':[]}
                possible=rows(path,'SELECT "Nom" AS name FROM entreprises WHERE lower("Nom") LIKE lower(?) LIMIT 5',('%'+offer['company']+'%',))
                item['company_match']['candidates']=[x['name'] for x in possible]
        if not existing:
            target=fingerprint(offer)
            candidates=rows(path,'SELECT "ID",Titre,entreprise_nom,ville,Description FROM offres')
            item['possible_duplicates']=sum(1 for old in candidates if fingerprint({'company':old['entreprise_nom'],'title':old['Titre'],'city':old['ville'],'description':old['Description']})==target)
    return {'run':run[0],'sources':sources,'staged':staged}


def decide_staged_offer(path,run_id,stage_id,decision):
    if decision not in ('approved','rejected'):raise ValueError('Décision invalide.')
    with connect(path) as db:
        cur=db.execute("UPDATE collector_staging SET decision=? WHERE id=? AND run_id=? AND decision='pending'",
                       (decision,stage_id,run_id))
        if not cur.rowcount:raise LookupError('Annonce absente de cette collecte ou déjà traitée.')
    return {'id':stage_id,'decision':decision}
