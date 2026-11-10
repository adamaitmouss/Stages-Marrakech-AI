"""Tâches ponctuelles et ordonnanceur daemon limité à la vie du serveur Flask."""
import threading
import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, timedelta, timezone
from .collectors.service import create_run, execute_run, import_run, sources_config, get_setting, set_setting
from .db import connect, now, rows

_lock=threading.Lock()
_workers=set()
_schedulers=set()
_loggers={}


def _scheduler_log(app, exc):
    try:
        root=Path(app.config.get('ROOT') or Path(app.config['DATABASE']).resolve().parent.parent)
        log_dir=root/'logs';log_dir.mkdir(parents=True,exist_ok=True)
        key=str(log_dir.resolve())
        if key not in _loggers:
            logger=logging.getLogger('stages.scheduler.'+str(abs(hash(key))))
            logger.setLevel(logging.INFO);logger.propagate=False
            logger.addHandler(RotatingFileHandler(log_dir/'collection_scheduler.log',maxBytes=1_000_000,backupCount=3,encoding='utf-8'))
            _loggers[key]=logger
        _loggers[key].error('%s: %s',type(exc).__name__,str(exc)[:1000])
    except Exception:
        pass


def start_run(app, mode, path=None, backup_dir=None):
    path=path or app.config['DATABASE'];backup_dir=backup_dir or app.config['BACKUP_DIR'];run_id=create_run(path,mode)
    def work():
        try:
            with app.app_context():
                from flask import g
                g.user_database_path=path;g.user_backup_dir=backup_dir
                execute_run(path,run_id,mode)
        finally:
            with _lock:_workers.discard(threading.current_thread())
    thread=threading.Thread(target=work,name=f'collect-{run_id}',daemon=True)
    with _lock:
        _workers.add(thread);thread.start()
    return run_id


def ensure_scheduler(app):
    path=app.config['DATABASE']
    with _lock:
        if path in _schedulers:return
        _schedulers.add(path)
    def loop():
        try:
            while True:
                try:
                    cfg=sources_config(path)
                    if cfg['auto_enabled'] and cfg['external_enabled']:
                        due=get_setting(path,'next_auto_at',None)
                        now_dt=datetime.now(timezone.utc)
                        if not due or datetime.fromisoformat(due)<=now_dt:
                            run_id=create_run(path,'automatic')
                            execute_run(path,run_id,'automatic')
                            permitted=[]
                            jawb_rights=cfg['jawb_import_approved'] and cfg['jawb_permission_ref'].strip() and all(cfg[k] for k in ('jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed'))
                            if jawb_rights:
                                if cfg['jawb_rss_enabled']:permitted.append('Jawb RSS')
                                if cfg['jawb_company_ids']:permitted.append('Jawb JSON')
                            if cfg['career_import_approved']:permitted.extend(x.get('name') or 'Flux carrière' for x in cfg['career_feeds'] if str(x.get('permission_ref') or '').strip() and all(x.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')))
                            permitted.extend(f"{x['platform'].title()} · {x['name']}" for x in cfg['career_boards'] if x.get('enabled') and str(x.get('permission_ref') or '').strip() and all(x.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')))
                            if permitted:
                                try:
                                    with app.app_context():
                                        with connect(path) as db:
                                            marks=','.join('?' for _ in permitted)
                                            db.execute(f"UPDATE collector_staging SET decision='approved' WHERE run_id=? AND source IN ({marks})",(run_id,*permitted))
                                        import_run(path,run_id,permitted,app.config['BACKUP_DIR'])
                                except ValueError as exc:_scheduler_log(app,exc)
                            interval=timedelta(days=7) if cfg['frequency']=='weekly' else timedelta(days=1)
                            with connect(path) as db:set_setting(db,'next_auto_at',(now_dt+interval).isoformat(timespec='seconds'))
                    with app.app_context():
                        from .alert_mail import deliver_due_alert_emails
                        deliver_due_alert_emails(path)
                except Exception as exc:
                    # Aucune clé d’API n’est utilisée; seules les erreurs de collecte sont journalisées.
                    _scheduler_log(app,exc)
                time.sleep(60)
        finally:
            with _lock:_schedulers.discard(path)
    thread=threading.Thread(target=loop,name='stages-collection-scheduler',daemon=True)
    thread.start()
    return thread


def collection_summary(path):
    from .collectors.catalog import source_catalog
    counts={t:rows(path,f'SELECT COUNT(*) AS n FROM "{t}"')[0]['n'] for t in ('entreprises','offres')}
    alert_count=rows(path,'SELECT COUNT(*) AS n FROM alerts WHERE is_read=0')[0]['n']
    run=rows(path,'SELECT * FROM collector_runs ORDER BY id DESC LIMIT 1')
    expired=rows(path,"SELECT COUNT(*) AS n FROM offres WHERE date(\"Date expiration\") < date('now') AND \"Date expiration\" IS NOT NULL")[0]['n']
    return {'counts':counts,'unread_alerts':alert_count,'last_run':run[0] if run else None,'sources':source_catalog(path),
            'next_run_at':get_setting(path,'next_auto_at',None),'expired_offers':expired,'settings':sources_config(path)}
