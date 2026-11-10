import hashlib
import io
import json
import re
import secrets
import time
import threading
import uuid
from datetime import date, datetime, timezone, timedelta
from flask import Blueprint, current_app, g, jsonify, request, session, send_file
from .db import connect, rows, now, request_database, request_backup_dir
from .validation import candidature, STATUSES, text, email, safe_url
from .cv_service import validate_cv, make_pdf, extract_pdf
from .matching import validate_profile, rank, local_profile, skills_from, norm
from .gemini_service import interpret, payload, anonymize, extract_profile as gemini_extract
from .application_service import insert_candidature, resolve_channel, send_cv
from .collectors.service import sources_config, set_sources_config, run_history, run_details, import_run, create_run, decide_staged_offer
from .collection_manager import start_run, ensure_scheduler, collection_summary
from .alerts import preferences as alert_preferences, validate_preferences as validate_alert_preferences
from .assistant import retrieve as assistant_retrieve, gemini_payload as assistant_gemini_payload, gemini_answer as assistant_gemini_answer
from .collectors.companies import parse_company_file, company_plan, import_companies
from .collectors.provided_offers import stage_provided_file
from .collectors.classification import classify_offer, filter_offer
from .gemini_search import enabled_status as gemini_search_status, run_grounded_search, validate_criteria, simulate_demo_workflow
from .collectors.schema import normalize_offer, identity_key

api = Blueprint('api', __name__, url_prefix='/api')


def _ai_session_digest():
    marker=session.setdefault('ai_search_session',secrets.token_urlsafe(32))
    account=getattr(g,'authenticated_user_id','')
    scoped=(str(account)+'|'+marker) if account else marker
    return hashlib.sha256(scoped.encode()).hexdigest()


def _redacted_prompt(prompt):
    value=re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}','[email retiré]',str(prompt or ''))
    value=re.sub(r'(?<!\w)(?:\+?\d[\d .()/-]{7,}\d)','[téléphone retiré]',value)
    return value[:2000]


def _ai_history(mode,criteria,status,result_count=0,model=None,error=None,queries=0):
    ident=str(uuid.uuid4());stamp=datetime.now(timezone.utc).isoformat(timespec='seconds')
    clean={k:v for k,v in criteria.items() if k!='prompt'}
    with connect(config()['DATABASE']) as db:
        db.execute('INSERT INTO gemini_search_history(id,session_digest,mode,prompt,criteria_json,model,status,started_at,finished_at,result_count,error_summary,search_queries) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
            (ident,_ai_session_digest(),mode,_redacted_prompt(criteria.get('prompt')),json.dumps(clean,ensure_ascii=False),model,status,stamp,stamp,result_count,error,queries))
    return ident


def _candidate_duplicate(path,candidate):
    title=str(candidate.get('title') or '').strip().lower();company=str(candidate.get('company') or '').strip().lower()
    if not title:return False
    with connect(path) as db:
        return db.execute("SELECT 1 FROM offres WHERE lower(trim(Titre))=? AND (trim(?)='' OR lower(trim(COALESCE(entreprise_nom,'')))=?) LIMIT 1",(title,company,company)).fetchone() is not None


def _grounded_worker(app,job_id,criteria,session_digest,confirm_cost,database_path,backup_dir):
    state=app.extensions['gemini_search_jobs'][job_id]
    try:
        with app.app_context():
            g.user_database_path=database_path
            g.user_backup_dir=backup_dir
            result=run_grounded_search(config(),criteria)
            for candidate in result['candidates']:
                candidate['possible_duplicate']=_candidate_duplicate(config()['DATABASE'],candidate)
                candidate['possibly_expired']=False
                if candidate.get('published_at'):
                    try:candidate['possibly_expired']=date.fromisoformat(candidate['published_at']) < date.today()-timedelta(days=30)
                    except ValueError:pass
            if state['cancel'].is_set():
                state.update(status='cancelled',message='Résultat écarté après votre demande d’arrêt; l’appel réseau déjà envoyé n’a pas pu être interrompu.')
                finish='cancelled';result_count=0
            else:
                state.update(status='completed',result=result)
                finish='completed';result_count=len(result['candidates'])
            with connect(config()['DATABASE']) as db:
                db.execute('UPDATE gemini_search_history SET status=?,finished_at=?,result_count=?,verified_count=0,search_queries=? WHERE id=?',(finish,datetime.now(timezone.utc).isoformat(timespec='seconds'),result_count,result.get('search_query_count',0),job_id))
    except Exception as exc:
        with app.app_context():
            g.user_database_path=database_path
            g.user_backup_dir=backup_dir
            state.update(status='failed',message='La recherche a échoué. Aucun résultat n’a été importé.')
            with connect(config()['DATABASE']) as db:
                db.execute('UPDATE gemini_search_history SET status=?,finished_at=?,error_summary=? WHERE id=?',('failed',datetime.now(timezone.utc).isoformat(timespec='seconds'),type(exc).__name__,job_id))


def config():
    values=current_app.config.copy()
    values['DATABASE']=request_database(values['DATABASE'])
    values['BACKUP_DIR']=request_backup_dir(values['BACKUP_DIR'])
    return values


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError('Un objet JSON est attendu.')
    return data


def companies():
    return rows(config()['DATABASE'], 'SELECT rowid AS id,* FROM entreprises')


def offers():
    values = rows(config()['DATABASE'], 'SELECT * FROM offres ORDER BY "Date publication" DESC')
    for o in values:
        o['application_url'] = safe_url(o.get('Lien public')) or safe_url(o.get('Lien annonce'))
        expiry = str(o.get('Date expiration') or '')[:10]
        try:
            o['availability'] = 'active' if date.fromisoformat(expiry) >= date.today() else 'expired'
        except ValueError:
            o['availability'] = 'unknown'
        o['statut_offre']=o['availability']
        o.update(classify_offer(o))
    priority = {'active': 0, 'unknown': 1, 'expired': 2}
    return sorted(values, key=lambda o: priority[o['availability']])


def get_offer(ident):
    for o in offers():
        if o['ID'] == ident:
            return o
    raise LookupError('Offre introuvable.')


def get_cv(ident):
    result = rows(config()['DATABASE'], 'SELECT * FROM cvs WHERE id=?', (ident,))
    if not result:
        raise LookupError('CV introuvable.')
    item = result[0]
    item['data'] = current_app.extensions['vault'].decrypt(item.pop('payload'))
    return item


@api.get('/entreprises')
def get_companies():
    return jsonify(companies())


@api.get('/offres')
def get_offers():
    values=offers()
    location=request.args.get('location');kind=request.args.get('kind');domain=request.args.get('domain')
    subtype=request.args.get('subtype')
    paid=request.args.get('paid')=='true' if request.args.get('paid') in ('true','false') else None
    if any((location,kind,domain,subtype,paid is not None)):
        values=[o for o in values if filter_offer(o,location=location,kind=kind,domain=domain,subtype=subtype,paid=paid)]
    return jsonify(values)


@api.get('/statistiques')
def statistics():
    co, of = companies(), offers()
    ca = rows(config()['DATABASE'], 'SELECT * FROM candidatures')
    def count(values, key, label):
        out = {}
        for item in values:
            value = item.get(key) or 'Non renseigné'
            out[value] = out.get(value, 0)+1
        return [{label: k, 'nombre': v} for k,v in sorted(out.items(), key=lambda kv: -kv[1])]
    responses = sum(c.get('statut') in ('Entretien', 'Acceptée', 'Refusée') for c in ca)
    contacted = sum(c.get('statut') in ('Envoyée', 'Relancée', 'Entretien', 'Acceptée', 'Refusée') for c in ca)
    return jsonify(total_entreprises=len(co), total_offres=len(of), total_candidatures=len(ca),
                   total_secteurs=len({c['Secteur'] for c in co if c['Secteur']}),
                   entreprises_avec_email=sum(bool((c.get('Emails') or '').strip()) for c in co),
                   entreprises_avec_site=sum(bool((c.get('Site Web') or '').strip()) for c in co),
                   entreprises_par_secteur=count(co, 'Secteur', 'secteur'), offres_par_stage=count(of, 'Type stage', 'type_stage'),
                   offres_par_contrat=count(of, 'Type contrat', 'type_contrat'), candidatures_par_statut=count(ca, 'statut', 'statut'),
                   response_rate=round(responses/contacted*100, 1) if contacted else None,
                   response_definition='(Entretien + Acceptée + Refusée) / (Envoyée + Relancée + Entretien + Acceptée + Refusée), selon le statut actuel.',
                   recent_offers=of[:4])


@api.get('/candidatures')
def get_applications():
    return jsonify(rows(config()['DATABASE'], 'SELECT * FROM candidatures ORDER BY id DESC'))


@api.post('/candidatures')
def create_application():
    data = candidature(body())
    with connect(config()['DATABASE']) as db:
        ident = insert_candidature(db, data)
    return jsonify(id=ident, message='Candidature enregistrée.'), 201


@api.route('/candidatures/<int:ident>', methods=['PUT', 'PATCH'])
def update_application(ident):
    values = candidature(body(), partial=True)
    with connect(config()['DATABASE']) as db:
        old = db.execute('SELECT * FROM candidatures WHERE id=?', (ident,)).fetchone()
        if old is None:
            raise LookupError('Candidature introuvable.')
        values['updated_at'] = now()
        db.execute(f"UPDATE candidatures SET {','.join(k+'=?' for k in values)} WHERE id=?", (*values.values(), ident))
        if 'statut' in values and values['statut'] != old['statut']:
            db.execute('INSERT INTO candidature_history(candidature_id,old_status,new_status,changed_at) VALUES (?,?,?,?)',
                       (ident, old['statut'], values['statut'], now()))
    return jsonify(message='Candidature mise à jour.')


@api.delete('/candidatures/<int:ident>')
def delete_application(ident):
    # Conservation de l’historique : suppression physique remplacée par un archivage explicite.
    raise ValueError('Suppression désactivée pour conserver votre historique. Utilisez les statuts et les notes.')


@api.get('/candidatures/<int:ident>/history')
def history(ident):
    return jsonify(rows(config()['DATABASE'], 'SELECT * FROM candidature_history WHERE candidature_id=? ORDER BY id', (ident,)))


@api.get('/attempts')
def attempts():
    return jsonify(rows(config()['DATABASE'], 'SELECT id,status,created_at,candidature_id,error_code FROM send_attempts ORDER BY id DESC'))


@api.get('/cvs')
def list_cvs():
    return jsonify(rows(config()['DATABASE'], 'SELECT id,name,template,created_at,updated_at FROM cvs ORDER BY id DESC'))


@api.post('/cvs')
def save_cv():
    data = body()
    cv = validate_cv(data.get('data'))
    name = text(data.get('name', ''), 150)
    template = data.get('template', 'modern')
    if not name or template not in ('modern', 'ats'):
        raise ValueError('Nom de version ou modèle invalide.')
    encrypted = current_app.extensions['vault'].encrypt(cv)
    with connect(config()['DATABASE']) as db:
        ident = db.execute('INSERT INTO cvs(name,template,payload,created_at,updated_at) VALUES (?,?,?,?,?)',
                           (name, template, encrypted, now(), now())).lastrowid
    return jsonify(id=ident), 201


@api.get('/cvs/<int:ident>')
def read_cv(ident):
    return jsonify(get_cv(ident))


@api.delete('/cvs/<int:ident>')
def delete_cv(ident):
    with connect(config()['DATABASE']) as db:
        if not db.execute('SELECT 1 FROM cvs WHERE id=?', (ident,)).fetchone():
            raise LookupError('CV introuvable.')
        if db.execute('SELECT 1 FROM candidatures WHERE cv_id=?', (ident,)).fetchone():
            raise ValueError('Ce CV est utilisé dans le suivi ; conservez sa version.')
        db.execute('DELETE FROM cvs WHERE id=?', (ident,))
    return jsonify(message='Version du CV supprimée.')


@api.post('/cvs/optimize')
def optimize_cv():
    data = body()
    cv_id, offer_id = data.get('cv_id'), data.get('offer_id')
    if type(cv_id) is not int or type(offer_id) is not int:
        raise ValueError('Sélectionnez un CV enregistré et une offre existante.')
    cv = get_cv(cv_id)['data']
    offer = get_offer(offer_id)
    description = str(offer.get('Titre') or '') + '\n' + str(offer.get('Description') or '')
    required = skills_from(description)
    cv_text = ' '.join(str(cv.get(key) or '') for key in ('title', 'summary', 'technical', 'soft', 'languages'))
    for section in ('education', 'experience', 'projects', 'certifications'):
        cv_text += ' ' + ' '.join(' '.join(str(item.get(k) or '') for k in ('title', 'organization', 'period', 'description'))
                                  for item in cv.get(section, []))
    existing = skills_from(cv_text)
    matched = [skill for skill in required if skill in existing]
    missing = [skill for skill in required if skill not in existing]
    evidence = []
    for section in ('experience', 'projects', 'education', 'certifications'):
        for index, item in enumerate(cv.get(section, [])):
            text_value = ' — '.join(str(item.get(k) or '').strip() for k in ('title', 'organization', 'period', 'description') if item.get(k))
            related = [skill for skill in matched if skill in skills_from(text_value)]
            if related:
                suggested = (str(item.get('title') or '').strip() + ': ' + str(item.get('description') or '').strip()).strip(': ')
                evidence.append({'section': section, 'entry_index': index, 'skills': related, 'source': text_value[:700],
                                 'original': {key: item.get(key, '') for key in ('title','organization','period','description')},
                                 'suggested_rewrite': suggested[:700],
                                 'suggestion': 'Placez cet élément près du début de la section. Cette proposition réorganise uniquement votre texte; précisez un résultat mesuré seulement s’il est vérifiable.'})
    summary_suggestion = None
    summary = str(cv.get('summary') or '').strip()
    sentences = [part.strip() for part in re.split(r'(?<=[.!?])\s+', summary) if part.strip()]
    relevant_sentences = [part for part in sentences if set(skills_from(part)).intersection(matched)]
    other_sentences = [part for part in sentences if part not in relevant_sentences]
    proposed_summary = ' '.join(relevant_sentences + other_sentences)
    if relevant_sentences and proposed_summary != summary:
        summary_suggestion = {'source': summary, 'proposed': proposed_summary,
                              'skills': sorted(set(skills_from(' '.join(relevant_sentences))).intersection(matched)),
                              'suggestion': 'Cette proposition ne fait que déplacer des phrases existantes qui mentionnent déjà une compétence commune.'}
    recommendations = []
    if matched:
        recommendations.append('Faites apparaître en premier les compétences déjà présentes dans votre CV et retrouvées dans cette offre : ' + ', '.join(matched) + '.')
    if missing:
        recommendations.append('Compétences de l’offre non repérées dans ce CV : ' + ', '.join(missing) + '. Ajoutez-les uniquement si vous les maîtrisez réellement ; sinon, identifiez-les comme pistes à développer, jamais comme acquis.')
    if evidence:
        recommendations.append('Organisez les expériences et projets contenant ces éléments avant les rubriques moins liées à l’offre.')
    if not recommendations:
        recommendations.append('Aucune compétence du vocabulaire contrôlé n’a pu être rapprochée. Relisez la description et adaptez le CV uniquement avec des informations exactes.')
    recommendations.append('Pour reformuler, conservez les faits de vos expériences et précisez votre contribution et les résultats mesurés uniquement s’ils sont vérifiables. Aucun texte du CV n’a été modifié.')
    return jsonify(offer={'id': offer_id, 'title': offer.get('Titre')}, matched=matched, missing=missing,
                   evidence=evidence, summary_suggestion=summary_suggestion, recommendations=recommendations,
                   disclaimer='Conseils locaux fondés sur les textes disponibles ; ils ne vérifient pas vos compétences et ne modifient pas le CV.')


@api.get('/cvs/<int:ident>/pdf')
def cv_pdf(ident):
    cv = get_cv(ident)
    return send_file(io.BytesIO(make_pdf(cv['data'], cv['template'])), mimetype='application/pdf',
                     download_name=f'CV_{ident}.pdf', as_attachment=request.args.get('download') == '1')


@api.post('/cvs/preview')
def preview_cv():
    data = body()
    return send_file(io.BytesIO(make_pdf(data.get('data'), data.get('template', 'modern'))), mimetype='application/pdf')


@api.post('/cvs/export')
def prepare_pdf_export():
    data=body()
    content=make_pdf(data.get('data'),data.get('template','modern'))
    exports=current_app.extensions.setdefault('pdf_exports',{})
    for key in list(exports):
        if exports[key][0] < time.monotonic():
            exports.pop(key,None)
    while len(exports)>=8:
        exports.pop(next(iter(exports)))
    token=secrets.token_urlsafe(32)
    exports[token]=(time.monotonic()+120,content)
    return jsonify(token=token)


@api.get('/cvs/export/<token>')
def download_pdf_export(token):
    entry=current_app.extensions.get('pdf_exports',{}).pop(token,None)
    if not entry or entry[0]<time.monotonic():
        raise LookupError('Téléchargement expiré. Générez à nouveau votre PDF.')
    return send_file(io.BytesIO(entry[1]),mimetype='application/pdf',download_name='CV_Stages_Marrakech.pdf',as_attachment=True)


@api.post('/profile/extract')
def extract_profile():
    file = request.files.get('cv')
    if file is None or not file.filename.lower().endswith('.pdf'):
        raise ValueError('Sélectionnez un PDF.')
    value = extract_pdf(file.read())
    return jsonify(text=value, profile=local_profile(value), message='Extraction locale. Vérifiez les compétences et complétez votre formation et vos projets.')


@api.post('/profile/gemini/preview')
def profile_gemini_preview():
    value = anonymize(text(body().get('reviewed_text',''), 15000))
    if not value:
        raise ValueError('Saisissez uniquement le texte professionnel à analyser.')
    return jsonify(text=value, digest=hashlib.sha256(value.encode()).hexdigest())


@api.post('/profile/gemini')
def profile_gemini():
    data=body()
    value=anonymize(text(data.get('reviewed_text',''),15000))
    if not value or data.get('consent') is not True or data.get('digest') != hashlib.sha256(value.encode()).hexdigest():
        raise ValueError('Relisez et confirmez le texte anonymisé avant transmission.')
    try:
        return jsonify(mode='gemini',profile=gemini_extract(config(),value),notice='Propositions Gemini à vérifier ; aucun diplôme ou expérience ajouté.')
    except Exception as exc:
        return jsonify(mode='local',profile=local_profile(value),notice='Gemini indisponible ou quota atteint : extraction locale, sans domaine inventé.')


def selection(data):
    profile = validate_profile(data.get('profile'))
    if not profile['skills'] and not (profile['education'] or profile['experience'] or profile['domain']):
        raise ValueError('Renseignez au moins une compétence, formation, expérience ou domaine.')
    weights = data.get('weights') or config()['MATCH_WEIGHTS']
    results = rank(profile, offers(), weights)
    shortlist = [r['offer'] for r in results[:8]]
    sent = payload(profile, shortlist)
    digest = hashlib.sha256(json.dumps(sent, sort_keys=True).encode()).hexdigest()
    return profile, weights, results, sent, digest


@api.post('/matching/preview')
def matching_preview():
    _, _, _, sent, digest = selection(body())
    return jsonify(payload=sent, digest=digest)


@api.post('/matching')
def matching():
    data = body()
    profile, weights, results, sent, digest = selection(data)
    mode, notice = 'local', 'Analyse locale, sans transmission externe.'
    if data.get('mode') == 'gemini':
        if data.get('consent') is not True:
            raise ValueError('Votre consentement explicite est obligatoire avant Gemini.')
        if data.get('digest') != digest:
            raise ValueError('Le profil ou les offres ont changé. Relisez le contenu à transmettre.')
        try:
            interpretations = interpret(config(), sent)
            results = rank(profile, offers(), weights, interpretations)
            mode, notice = 'gemini', 'Gemini a interprété les 8 premières offres de la présélection locale. Scores calculés localement ; les autres offres restent en mode local.'
        except Exception as exc:
            code = getattr(exc, 'code', None)
            notice = ('Quota Gemini atteint (429). ' if code == 429 or '429' in str(exc) else 'Gemini indisponible ou réponse non vérifiable. ') + 'Résultats locaux conservés ; aucune nouvelle tentative automatique.'
    return jsonify(mode=mode, notice=notice, results=results, disclaimer='Score indicatif, pas une probabilité d’obtenir le stage.')


@api.get('/offres/<int:ident>/application')
def application_context(ident):
    offer = get_offer(ident)
    company = next((c for c in companies() if c['id'] == offer.get('entreprise_ref')), None)
    return jsonify(offer=offer, channel=resolve_channel(offer, company), cvs=list_cvs().json)


@api.post('/offres/<int:ident>/apply')
def apply(ident):
    data = body()
    offer = get_offer(ident)
    cv_id = data.get('cv_id')
    if type(cv_id) is not int:
        raise ValueError('Sélectionnez un CV enregistré.')
    cv = get_cv(cv_id)
    action = data.get('action')
    company = next((c for c in companies() if c['id'] == offer.get('entreprise_ref')), None)
    channel = resolve_channel(offer, company)
    if action not in ('prepare', 'external_confirmed', 'smtp'):
        raise ValueError('Action de candidature inconnue.')
    if data.get('confirmed') is not True:
        raise ValueError('Confirmation explicite obligatoire.')
    if action == 'external_confirmed' and channel['type'] != 'external':
        raise ValueError('Canal externe indisponible.')
    application = dict(nom_entreprise=offer.get('entreprise_nom') or f"Entreprise non renseignée (source ID {offer['Entreprise ID']})",
                       offre_id=ident, offre_titre=offer['Titre'], cv_id=cv_id, source=offer.get('source') or 'Stagiaires.ma',
                       commentaire=text(data.get('message', ''), 5000))
    if action == 'smtp':
        if channel['type'] != 'smtp':
            raise ValueError('Aucun email de recrutement fiable lié à cette offre.')
        return jsonify(send_cv(config(), make_pdf(cv['data'], cv['template']), channel['email'],
                               text(data.get('subject', 'Candidature - '+offer['Titre']), 200), application['commentaire'],
                               application, request.headers.get('Idempotency-Key')))
    with connect(config()['DATABASE']) as db:
        # Évite le double clic et le doublon offre/CV ; l’envoi externe doit être confirmé par l’utilisateur.
        db.execute('BEGIN IMMEDIATE')
        old = db.execute('SELECT id,statut FROM candidatures WHERE offre_id=? AND cv_id=? ORDER BY id DESC LIMIT 1', (ident,cv_id)).fetchone()
        if old:
            if action == 'external_confirmed' and old['statut'] == 'Non envoyée':
                db.execute('UPDATE candidatures SET statut=?,canal=?,updated_at=?,date_candidature=? WHERE id=?',
                           ('Envoyée', 'external_confirmed', now(), date.today().isoformat(), old['id']))
                db.execute('INSERT INTO candidature_history(candidature_id,old_status,new_status,changed_at) VALUES (?,?,?,?)',
                           (old['id'], old['statut'], 'Envoyée', now()))
            return jsonify(id=old['id'], duplicate=True)
        application.update(statut='Envoyée' if action == 'external_confirmed' else 'Non envoyée',
                           canal='external_confirmed' if action == 'external_confirmed' else 'prepare', date_candidature=date.today().isoformat())
        new_id = insert_candidature(db, application)
    return jsonify(id=new_id, message='Déclaration de candidature enregistrée.' if action == 'external_confirmed' else 'Candidature à préparer enregistrée.'), 201


@api.post('/envoyer-cv')
def send_company_cv():
    data = body()
    if data.get('confirmed') is not True or data.get('email_confirmed') is not True:
        raise ValueError('Confirmez le destinataire et l’envoi avant de continuer.')
    company_id = data.get('entreprise_id')
    company = next((c for c in companies() if c['id'] == company_id), None)
    if not company:
        raise LookupError('Entreprise introuvable.')
    recipient = email(data.get('email', ''))
    if recipient not in [e.strip().lower() for e in (company.get('Emails') or '').split(',')]:
        raise ValueError('L’adresse ne correspond pas aux coordonnées connues de cette entreprise.')
    if type(data.get('cv_id')) is not int:
        raise ValueError('Sélectionnez un CV enregistré.')
    cv = get_cv(data['cv_id'])
    application = dict(nom_entreprise=company['Nom'], secteur=company['Secteur'], cv_id=cv['id'], source='Google Places / validation manuelle du contact',
                       commentaire=text(data.get('message', ''), 5000))
    return jsonify(send_cv(config(), make_pdf(cv['data'], cv['template']), recipient, data.get('subject', ''),
                           application['commentaire'], application, request.headers.get('Idempotency-Key')))


@api.get('/map')
def map_data():
    data = companies()
    verified = [c for c in data if c.get('geo_verified_at') and c.get('geo_source') and
                type(c.get('latitude')) in (int,float) and type(c.get('longitude')) in (int,float) and
                -90 <= c['latitude'] <= 90 and -180 <= c['longitude'] <= 180]
    return jsonify(companies=data, verified=verified, maps_enabled=config()['MAPS_ENABLED'] and bool(config()['MAPS_BROWSER_KEY']),
                   browser_key=config()['MAPS_BROWSER_KEY'] if config()['MAPS_ENABLED'] else '',
                   notice='Aucun géocodage automatique. Seules les coordonnées avec provenance et date de vérification sont affichées.')


@api.get('/collect/summary')
def collect_summary():
    return jsonify(collection_summary(config()['DATABASE']))


@api.post('/collect/offers/file/preview')
def collect_provided_offers_preview():
    upload=request.files.get('file')
    if upload is None or not upload.filename:raise ValueError('Sélectionnez un fichier CSV ou Excel.')
    try:mapping=json.loads(request.form.get('mapping') or '{}')
    except (TypeError,ValueError):raise ValueError('Mapping de colonnes JSON invalide.')
    if not isinstance(mapping,dict):raise ValueError('Le mapping doit être un objet colonne → champ.')
    value=stage_provided_file(config()['DATABASE'],upload.filename,upload.read(),
        request.form.get('source_name'),request.form.get('permission_ref'),
        request.form.get('consultation_allowed')=='true',request.form.get('storage_allowed')=='true',
        request.form.get('display_allowed')=='true',mapping)
    value['run']=run_details(config()['DATABASE'],value['id'])
    return jsonify(value),201


@api.route('/collect/settings',methods=['GET','POST'])
def collect_settings():
    if request.method=='GET':return jsonify(sources_config(config()['DATABASE']))
    data=body()
    if data.get('jawb_import_approved') is True and data.get('rights_confirmed') is not True:
        raise ValueError('Confirmez que vous avez vérifié les droits de réutilisation et de stockage de Jawb.')
    if data.get('jawb_import_approved') is True and not str(data.get('jawb_permission_ref') or '').strip():
        raise ValueError('Une référence à l’autorisation écrite de Jawb est nécessaire; sinon la source reste bloquée.')
    if data.get('jawb_import_approved') is True and not all(data.get(k) is True for k in ('jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed')):
        raise ValueError('Confirmez séparément les droits Jawb de consultation, stockage et réaffichage.')
    if data.get('career_import_approved') is True and data.get('career_rights_confirmed') is not True:
        raise ValueError('Confirmez les droits du propriétaire des flux carrière avant stockage local.')
    if data.get('career_import_approved') is True:
        feeds=data.get('career_feeds')
        if not isinstance(feeds,list) or not feeds or any(not str(x.get('permission_ref') or '').strip() or not all(x.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')) for x in feeds):
            raise ValueError('Chaque flux carrière doit avoir sa référence et ses trois droits explicitement confirmés.')
    values={k:v for k,v in data.items() if k in {'external_enabled','auto_enabled','frequency','jawb_rss_enabled','jawb_import_approved','jawb_consult_allowed','jawb_storage_allowed','jawb_display_allowed','jawb_permission_ref','career_import_approved','jawb_company_ids','career_feeds','career_boards'}}
    result=set_sources_config(config()['DATABASE'],values)
    if result['auto_enabled'] and result['external_enabled'] and not config().get('DISABLE_BACKGROUND_SCHEDULER'):
        ensure_scheduler(current_app._get_current_object())
    return jsonify(result)


@api.route('/collect/runs',methods=['GET','POST'])
def collect_runs():
    path=config()['DATABASE']
    if request.method=='GET':return jsonify(runs=run_history(path),summary=collection_summary(path))
    mode=body().get('mode','simulation')
    if mode not in ('simulation','preview'):raise ValueError('Mode invalide. Choisissez simulation ou preview.')
    ident=start_run(current_app._get_current_object(),mode,config()['DATABASE'],config()['BACKUP_DIR'])
    return jsonify(id=ident,status='running',mode=mode),202


@api.get('/collect/runs/<int:ident>')
def collect_run_detail(ident):
    value=run_details(config()['DATABASE'],ident)
    if value is None:raise LookupError('Collecte introuvable.')
    return jsonify(value)


@api.post('/collect/runs/<int:ident>/staged/<int:stage_id>/decision')
def collect_stage_decision(ident,stage_id):
    data=body()
    return jsonify(decide_staged_offer(config()['DATABASE'],ident,stage_id,data.get('decision')))


@api.post('/collect/runs/<int:ident>/import')
def collect_run_import(ident):
    data=body();selected=data.get('sources')
    if not isinstance(selected,list) or not selected or any(not isinstance(s,str) for s in selected):
        raise ValueError('Sélectionnez les sources à importer.')
    if data.get('rights_confirmed') is not True:
        raise ValueError('Confirmez les droits d’import et de stockage local des offres sélectionnées.')
    with connect(config()['DATABASE']) as db:
        run=db.execute('SELECT mode FROM collector_runs WHERE id=?',(ident,)).fetchone()
    if run and run['mode']=='file-import':
        return jsonify(import_run(config()['DATABASE'],ident,selected,config()['BACKUP_DIR'],allow_provided_file=True))
    if run and run['mode']=='gemini-search':
        outcome=import_run(config()['DATABASE'],ident,selected,config()['BACKUP_DIR'],allow_gemini_search=True)
        with connect(config()['DATABASE']) as db:
            meta=db.execute('SELECT source_metadata_json FROM collector_runs WHERE id=?',(ident,)).fetchone()
            try:job_id=json.loads(meta['source_metadata_json'] or '{}').get('job_id') if meta else None
            except (ValueError,TypeError):job_id=None
            if job_id:db.execute('UPDATE gemini_search_history SET imported_count=imported_count+? WHERE id=?',(int(outcome.get('imported',0)),job_id))
        return jsonify(outcome)
    return jsonify(import_run(config()['DATABASE'],ident,selected,config()['BACKUP_DIR']))


@api.get('/ai-search/status')
def ai_search_status():
    ready=gemini_search_status(config())
    with connect(config()['DATABASE']) as db:
        day=db.execute("SELECT COUNT(*) FROM gemini_search_history WHERE mode='gemini' AND started_at>=?",(date.today().isoformat(),)).fetchone()[0]
        own=db.execute("SELECT COUNT(*) FROM gemini_search_history WHERE mode='gemini' AND session_digest=? AND started_at>=?",(_ai_session_digest(),date.today().isoformat())).fetchone()[0]
        recent=db.execute("SELECT started_at FROM gemini_search_history WHERE mode='gemini' AND session_digest=? ORDER BY started_at DESC LIMIT 1",(_ai_session_digest(),)).fetchone()
    cooldown=0
    if recent:
        try:cooldown=max(0,int(ready['cooldown_seconds']-(datetime.now(timezone.utc)-datetime.fromisoformat(recent['started_at'])).total_seconds()))
        except (ValueError,TypeError):pass
    ready.update(daily_used=day,session_used=own,cooldown_remaining=cooldown,
        can_search=ready['enabled'] and day<ready['max_daily'] and own<ready['max_session'] and cooldown==0,
        billing_notice='Google Search Grounding peut entraîner une facturation. Une demande peut effectuer plusieurs recherches facturables; les plafonds locaux ne garantissent pas un coût maximal.')
    return jsonify(ready)


@api.post('/ai-search/local')
def ai_search_local():
    data=body();criteria=validate_criteria(data);result=assistant_retrieve(config()['DATABASE'],criteria['prompt'])
    ident=None if config().get('PUBLIC_DEMO_MODE') else _ai_history('local',criteria,'completed',len(result.get('offers',[])),model='SQLite local')
    return jsonify(mode='local',is_demo=False,history_id=ident,result=result)


@api.post('/ai-search/demo')
def ai_search_demo():
    data=body();criteria=validate_criteria(data)
    synthetic={'title':'Stage PFE de démonstration — Python et SQL','company':'Entreprise fictive de démonstration',
        'city':'Marrakech','summary':'Résultat synthétique pour tester staging, validation, import et synchronisations. Aucune annonce réelle.',
        'skills':['Python','SQL']}
    workflow=simulate_demo_workflow(synthetic,config()['ROOT'])
    ident=None if config().get('PUBLIC_DEMO_MODE') else _ai_history('demo',criteria,'completed',1,model='Simulation locale')
    return jsonify(mode='demo',is_demo=True,candidates=[{**synthetic,'source_name':'Simulation locale','source_url':None,
        'published_at':None,'verification_status':'donnée synthétique','importable':False,'possible_duplicate':False}],
        workflow=workflow,history_id=ident)


@api.post('/ai-search/gemini')
def ai_search_gemini():
    data=body();criteria=validate_criteria(data);ready=gemini_search_status(config())
    if not ready['enabled']:raise ValueError('Gemini Search est désactivé. '+' '.join(ready['reasons']))
    if data.get('confirm_cost') is not True:raise ValueError('Confirmez que vous acceptez une éventuelle facturation Google Search Grounding.')
    digest=_ai_session_digest();stamp=datetime.now(timezone.utc).isoformat(timespec='seconds');day=date.today().isoformat()
    with connect(config()['DATABASE']) as db:
        db.execute('BEGIN IMMEDIATE')
        daily=db.execute("SELECT COUNT(*) FROM gemini_search_history WHERE mode='gemini' AND started_at>=?",(day,)).fetchone()[0]
        own=db.execute("SELECT COUNT(*) FROM gemini_search_history WHERE mode='gemini' AND session_digest=? AND started_at>=?",(digest,day)).fetchone()[0]
        latest=db.execute("SELECT started_at FROM gemini_search_history WHERE mode='gemini' AND session_digest=? ORDER BY started_at DESC LIMIT 1",(digest,)).fetchone()
        if daily>=ready['max_daily'] or own>=ready['max_session']:raise ValueError('Plafond logiciel Gemini Search atteint; réessayez un autre jour.')
        if latest:
            try:
                if (datetime.now(timezone.utc)-datetime.fromisoformat(latest['started_at'])).total_seconds()<ready['cooldown_seconds']:
                    raise ValueError('Veuillez respecter le délai entre deux recherches.')
            except ValueError as exc:
                if str(exc).startswith('Veuillez'):raise
        ident=str(uuid.uuid4());db.execute('INSERT INTO gemini_search_history(id,session_digest,mode,prompt,criteria_json,model,status,started_at) VALUES (?,?,?,?,?,?,?,?)',
            (ident,digest,'gemini',_redacted_prompt(criteria['prompt']),json.dumps({k:v for k,v in criteria.items() if k!='prompt'},ensure_ascii=False),ready['model'],'running',stamp))
    job={'status':'running','cancel':threading.Event(),'session_digest':digest,'result':None,'message':'Recherche en cours. Les sources seront à vérifier manuellement.'}
    current_app.extensions['gemini_search_jobs'][ident]=job
    app=current_app._get_current_object();cfg=config();threading.Thread(target=_grounded_worker,args=(app,ident,criteria,digest,True,cfg['DATABASE'],cfg['BACKUP_DIR']),daemon=True).start()
    return jsonify(id=ident,status='running',message=job['message']),202


@api.get('/ai-search/jobs/<ident>')
def ai_search_job(ident):
    job=current_app.extensions['gemini_search_jobs'].get(ident)
    if not job or job['session_digest']!=_ai_session_digest():raise LookupError('Recherche introuvable ou expirée.')
    return jsonify(id=ident,status=job['status'],message=job.get('message'),result=job.get('result'))


@api.post('/ai-search/jobs/<ident>/cancel')
def ai_search_cancel(ident):
    job=current_app.extensions['gemini_search_jobs'].get(ident)
    if not job or job['session_digest']!=_ai_session_digest():raise LookupError('Recherche introuvable ou expirée.')
    job['cancel'].set()
    if job['status']=='running':job['message']='Arrêt demandé; l’appel externe déjà commencé peut encore se terminer.'
    return jsonify(status=job['status'],message=job['message'])


@api.post('/ai-search/jobs/<ident>/stage')
def ai_search_stage(ident):
    data=body();job=current_app.extensions['gemini_search_jobs'].get(ident)
    if not job or job['session_digest']!=_ai_session_digest() or job['status']!='completed':raise LookupError('Résultats introuvables ou expirés.')
    result=job.get('result') or {};candidate=next((x for x in result.get('candidates',[]) if x.get('candidate_id')==data.get('candidate_id')),None)
    if not candidate or not candidate.get('source_url'):raise ValueError('Le résultat n’a pas de lien direct cité; il reste consultable dans les sources et ne peut pas entrer au staging.')
    if data.get('manual_verified') is not True or not data.get('permission_ref') or not all(data.get(k) is True for k in ('consultation_allowed','storage_allowed','display_allowed')):
        raise ValueError('Vérifiez manuellement l’annonce et documentez l’autorisation ainsi que les droits de consultation, stockage et réaffichage.')
    source='Gemini Search · '+str(candidate.get('source_name') or 'source vérifiée')[:150]
    offer=normalize_offer({'source_id':'gemini-'+candidate['candidate_id'],'title':candidate['title'],'company':candidate.get('company') or '',
        'city':candidate.get('city') or '', 'description':candidate.get('summary') or candidate['title'],'contract_type':'Stage' if 'stage' in str(candidate.get('opportunity_type') or '').lower() else 'Emploi',
        'internship_type':candidate.get('opportunity_type') or '', 'published_at':candidate.get('published_at'),'url':candidate['source_url'],'skills':candidate.get('skills') or []},source)
    run_id=create_run(config()['DATABASE'],'gemini-search');stamp=now()
    metadata={'kind':'gemini_search','job_id':ident,'source_name':source,'manual_verified':True,'permission_ref':str(data['permission_ref'])[:500],
        'consultation_allowed':True,'storage_allowed':True,'display_allowed':True,'candidate_id':candidate['candidate_id']}
    with connect(config()['DATABASE']) as db:
        db.execute('UPDATE collector_runs SET status="previewed",finished_at=?,fetched_count=1,source_metadata_json=? WHERE id=?',(stamp,json.dumps(metadata,ensure_ascii=False),run_id))
        db.execute('INSERT INTO collector_source_runs(run_id,source,status,started_at,finished_at,fetched_count) VALUES (?,?,?,?,?,1)',(run_id,source,'previewed',stamp,stamp))
        staged_row=db.execute('INSERT INTO collector_staging(run_id,source,identity_key,payload_json,decision) VALUES (?,?,?,?,"pending")',(run_id,source,identity_key(offer),json.dumps(offer,ensure_ascii=False)))
        db.execute('UPDATE gemini_search_history SET verified_count=verified_count+1 WHERE id=?',(ident,))
    return jsonify(id=run_id,stage_id=staged_row.lastrowid,status='previewed',source=source,offer=offer,possible_duplicate=_candidate_duplicate(config()['DATABASE'],candidate)),201


@api.get('/ai-search/history')
def ai_search_history():
    return jsonify(items=rows(config()['DATABASE'],'SELECT id,mode,prompt,criteria_json,model,status,started_at,finished_at,result_count,verified_count,imported_count,search_queries,error_summary FROM gemini_search_history WHERE session_digest=? ORDER BY started_at DESC LIMIT 100',(_ai_session_digest(),)))


@api.delete('/ai-search/history')
def ai_search_clear_history():
    if body().get('confirm') is not True:raise ValueError('Confirmez la suppression de l’historique local.')
    with connect(config()['DATABASE']) as db:cur=db.execute('DELETE FROM gemini_search_history WHERE session_digest=?',(_ai_session_digest(),))
    return jsonify(deleted=cur.rowcount)


@api.post('/collect/companies/import')
def collect_companies_import():
    upload=request.files.get('file')
    if upload is None or not upload.filename:raise ValueError('Sélectionnez un fichier CSV ou Excel.')
    content=upload.read()
    try:mapping=json.loads(request.form.get('mapping') or '{}')
    except (TypeError,ValueError):raise ValueError('Mapping de colonnes JSON invalide.')
    if not isinstance(mapping,dict):raise ValueError('Le mapping doit être un objet colonne → champ.')
    items,errors,column_report=parse_company_file(upload.filename,content,mapping,include_report=True)
    plan=company_plan(config()['DATABASE'],items);plan['errors']=errors
    plan['column_report']=column_report
    if request.form.get('apply')!='true':return jsonify(mode='preview',**plan)
    if request.form.get('rights_confirmed')!='true':raise ValueError('Confirmez que ces données peuvent être stockées et réutilisées localement.')
    run_id=create_run(config()['DATABASE'],'company-import-preview')
    result=import_companies(config()['DATABASE'],config()['BACKUP_DIR'],items,run_id)
    return jsonify(mode='imported',plan=plan,result=result)


@api.get('/alerts/preferences')
def get_alert_preferences():
    with connect(config()['DATABASE']) as db:value=alert_preferences(db)
    value['email_recipient_saved']=bool(value.pop('email_payload',None))
    return jsonify(value)


@api.put('/alerts/preferences')
def put_alert_preferences():
    incoming=body();values=validate_alert_preferences(incoming)
    encrypted_recipient=None
    if values['email_enabled']:
        if incoming.get('email_consent') is not True:
            raise ValueError('Confirmez explicitement votre accord pour les emails d’alerte.')
        if not config()['SMTP_ENABLED'] or not config()['SMTP_USER'] or not config()['SMTP_PASSWORD']:
            raise ValueError('Configurez SMTP dans .env puis redémarrez avant d’activer les emails.')
        recipient=incoming.get('email_recipient','').strip() if isinstance(incoming.get('email_recipient',''),str) else ''
        if recipient:
            encrypted_recipient=current_app.extensions['vault'].encrypt({'email':email(recipient)})
        else:
            saved=rows(config()['DATABASE'],'SELECT email_payload FROM alert_preferences WHERE id=1')
            encrypted_recipient=saved[0]['email_payload'] if saved else None
            if not encrypted_recipient:raise ValueError('Saisissez un destinataire email pour activer les alertes.')
    with connect(config()['DATABASE']) as db:
        db.execute('''UPDATE alert_preferences SET domain=?,skills_json=?,city=?,internship_type=?,contract_type=?,minimum_score=?,frequency=?,enabled=?,email_enabled=?,email_payload=?,updated_at=? WHERE id=1''',
                   (values['domain'],json.dumps(values['skills'],ensure_ascii=False),values['city'],values['internship_type'],values['contract_type'],values['minimum_score'],values['frequency'],int(values['enabled']),int(values['email_enabled']),encrypted_recipient,now()))
        if not values['email_enabled']:
            db.execute("UPDATE alert_email_log SET status='cancelled',attempted_at=? WHERE status='queued'",(now(),))
            db.execute('UPDATE alert_preferences SET email_next_at=NULL WHERE id=1')
        saved=alert_preferences(db);saved['email_recipient_saved']=bool(saved.pop('email_payload',None))
    if values['email_enabled']:
        ensure_scheduler(current_app._get_current_object())
    return jsonify(saved)


@api.get('/alerts')
def get_alerts():
    return jsonify(rows(config()['DATABASE'],'''SELECT a.id,a.offer_id,a.created_at,a.score,a.explanation,a.is_read,el.status AS email_status,
        o."Titre" AS title,o.entreprise_nom AS company,o.ville AS city,o.source,
        o."Date publication" AS published_at,o."Lien public" AS url,o."Lien annonce" AS fallback_url,
        o."Type stage" AS internship_type,o."Type contrat" AS contract_type
        FROM alerts a JOIN offres o ON o."ID"=a.offer_id LEFT JOIN alert_email_log el ON el.alert_id=a.id ORDER BY a.created_at DESC LIMIT 200'''))


@api.get('/alerts/count')
def alert_count():
    return jsonify(unread=rows(config()['DATABASE'],'SELECT COUNT(*) AS n FROM alerts WHERE is_read=0')[0]['n'])


@api.post('/alerts/<int:ident>/read')
def mark_alert_read(ident):
    with connect(config()['DATABASE']) as db:
        cur=db.execute('UPDATE alerts SET is_read=1 WHERE id=?',(ident,))
        if not cur.rowcount:raise LookupError('Alerte introuvable.')
    return jsonify(ok=True)


@api.post('/alerts/read-all')
def mark_alerts_read():
    with connect(config()['DATABASE']) as db:db.execute('UPDATE alerts SET is_read=1')
    return jsonify(ok=True)


@api.delete('/alerts/<int:ident>')
def delete_alert(ident):
    with connect(config()['DATABASE']) as db:db.execute('DELETE FROM alerts WHERE id=?',(ident,))
    return ('',204)


def assistant_cv_profile():
    with connect(config()['DATABASE']) as db:row=db.execute('SELECT payload FROM cvs ORDER BY updated_at DESC,id DESC LIMIT 1').fetchone()
    if not row:return None
    data=current_app.extensions['vault'].decrypt(row['payload'])
    def values(key):
        items=data.get(key) or []
        return ' '.join(' '.join(str(v) for v in item.values()) if isinstance(item,dict) else str(item) for item in items)
    skills=[s.strip() for s in re.split(r'[,;\n]',str(data.get('technical') or '')) if s.strip()]
    return {'skills':skills[:100],'education':values('education'),'experience':values('experience')+' '+values('projects'),
            'domain':str(data.get('title') or ''),'location':str(data.get('city') or ''),'opportunity':'Stage'}


@api.get('/assistant/history')
def assistant_history():
    vault=current_app.extensions['vault'];result=[]
    for row in rows(config()['DATABASE'],'SELECT id,role,message,created_at FROM assistant_messages ORDER BY id DESC LIMIT 30'):
        try:row['message']=vault.decrypt(row['message']).get('text','')
        except Exception:row['message']='Message local illisible.'
        result.append(row)
    return jsonify(messages=list(reversed(result)))


@api.get('/assistant/status')
def assistant_status():
    current = config()
    model = str(current.get('GEMINI_MODEL') or '')
    reasons = []
    if current.get('PUBLIC_DEMO_MODE'):
        reasons.append('Gemini est désactivé en démonstration publique.')
    if not current.get('GEMINI_ENABLED'):
        reasons.append('Le mode Gemini n’est pas activé.')
    if not str(current.get('GEMINI_API_KEY') or '').strip():
        reasons.append('Aucune clé Gemini n’est configurée.')
    if not current.get('GEMINI_FREE_TIER_CONFIRMED'):
        reasons.append('Le responsable n’a pas confirmé les conditions et quotas de son compte.')
    if model != 'gemini-3.5-flash-lite':
        reasons.append('Le modèle configuré n’est pas autorisé par la configuration actuelle.')
    return jsonify(local_available=True, gemini_available=not reasons, model=model if not reasons else None,
                   reasons=reasons)


@api.delete('/assistant/history')
def clear_assistant_history():
    with connect(config()['DATABASE']) as db:db.execute('DELETE FROM assistant_messages')
    return ('',204)


def assistant_preview_data(question):
    profile=assistant_cv_profile() if any(x in norm(str(question)) for x in ('mon cv','mon profil','correspond')) else None
    found=assistant_retrieve(config()['DATABASE'],question,profile)
    sent=assistant_gemini_payload(question,found)
    digest=hashlib.sha256(json.dumps(sent,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return found,sent,digest


@api.post('/assistant/preview')
def assistant_preview():
    data=body();found,sent,digest=assistant_preview_data(data.get('question'))
    return jsonify(mode='gemini',payload=sent,digest=digest,summary={'offers':len(sent['offers']),'includes_cv':False,'contains_user_question':True,
        'note':'La question anonymisée et au plus cinq extraits d’offres publiques seront transmis. Aucun CV, téléphone, adresse ou candidature privée n’est transmis.'},local_result=found)


@api.post('/assistant/chat')
def assistant_chat():
    data=body();question=data.get('question');mode=data.get('mode','local')
    if mode not in ('local','gemini'):raise ValueError('Mode assistant invalide.')
    found,sent,digest=assistant_preview_data(question);notice_text='Recherche locale dans SQLite. Aucun service externe utilisé.'
    if mode=='gemini':
        if data.get('consent') is not True or data.get('digest')!=digest:
            raise ValueError('Prévisualisez exactement les données et confirmez leur transmission à Gemini.')
        try:
            ai=assistant_gemini_answer(config(),sent,{o['id'] for o in sent['offers']})
            found['answer']=ai['answer'];found['offers']=[o for o in found['offers'] if o['id'] in ai['offer_ids']]
            notice_text='Résumé Gemini des offres locales. Les fiches et liens restent la source de référence.'
        except Exception:
            notice_text='Gemini indisponible ou non vérifiable : réponse locale affichée, sans nouvelle tentative.'
    vault=current_app.extensions['vault']
    if not config().get('PUBLIC_DEMO_MODE'):
        with connect(config()['DATABASE']) as db:
            db.execute('INSERT INTO assistant_messages(role,message,created_at) VALUES (?,?,?)',('user',vault.encrypt({'text':question}),now()))
            db.execute('INSERT INTO assistant_messages(role,message,created_at) VALUES (?,?,?)',('assistant',vault.encrypt({'text':found['answer']}),now()))
    return jsonify(**found,mode='gemini' if mode=='gemini' and notice_text.startswith('Résumé') else 'local',notice=notice_text)
