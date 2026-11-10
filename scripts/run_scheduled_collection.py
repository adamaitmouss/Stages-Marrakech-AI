"""Lance un cycle planifié seulement si sources, droits et automatisation sont activés."""
from backend.web import create_app
from backend.collectors.service import create_run, execute_run, sources_config, import_run
from backend.db import connect


def main():
    app=create_app({'DISABLE_BACKGROUND_SCHEDULER':True})
    path=app.config['DATABASE']
    options = sources_config(path)
    if not options['external_enabled'] or not options['auto_enabled']:
        print('Collecte planifiée ignorée : activation externe et mode automatique requis dans l’application.')
        return 2
    run_id = create_run(path, 'automatic')
    result = execute_run(path, run_id, 'automatic')
    print(f"Aperçu de collecte terminé : statut={result['status']}, sources={len(result.get('sources', []))}, offres={result.get('fetched_count', 0)}.")
    if result['status']!='previewed':return 1
    permitted=[]
    jawb_rights=options['jawb_import_approved'] and options['jawb_permission_ref'].strip() and all(options[k] for k in ('jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed'))
    if jawb_rights:
        if options['jawb_rss_enabled']:permitted.append('Jawb RSS')
        if options['jawb_company_ids']:permitted.append('Jawb JSON')
    if options['career_import_approved']:
        permitted.extend(x.get('name') or 'Flux carrière' for x in options['career_feeds'] if str(x.get('permission_ref') or '').strip() and all(x.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')))
    permitted.extend(f"{x['platform'].title()} · {x['name']}" for x in options['career_boards'] if x.get('enabled') and str(x.get('permission_ref') or '').strip() and all(x.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')))
    if not permitted:
        print('Aucune source avec autorisation écrite configurée : résultat conservé en aperçu, sans import.')
        return 0
    with app.app_context():
        with connect(path) as db:
            marks=','.join('?' for _ in permitted)
            db.execute(f"UPDATE collector_staging SET decision='approved' WHERE run_id=? AND source IN ({marks})",(run_id,*permitted))
        imported=import_run(path,run_id,permitted,app.config['BACKUP_DIR'])
    print(f"Import planifié terminé : {imported['new_offers']} nouvelle(s), {imported['updated_offers']} modifiée(s), {imported['unchanged_offers']} inchangée(s).")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
