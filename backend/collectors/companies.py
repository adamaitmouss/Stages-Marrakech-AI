"""Prévisualisation et import CSV/XLSX non destructif de fiches obtenues légalement."""
import csv
import hashlib
import io
import json
import math
import re
import unicodedata
from datetime import datetime,timezone
from openpyxl import load_workbook
from ..db import connect,now,backup_database
from ..validation import safe_url, email


ALIASES={
 'nom':'name','name':'name','entreprise':'name','company':'name',
 'source':'source','source id':'source_id','external id':'source_id','place id':'source_id',
 'adresse':'address','address':'address','telephone':'phone','téléphone':'phone','phone':'phone',
 'site web':'website','website':'website','google maps':'maps','maps_url':'maps','secteur':'sector','sector':'sector',
 'ville':'city','city':'city','latitude':'latitude','longitude':'longitude','geo source':'geo_source','category':'sector',
 'geo verified at':'geo_verified_at','verified at':'geo_verified_at','email':'emails','e mail':'emails','emails':'emails','email professionnel':'emails'
}


def _norm(value):
    value=unicodedata.normalize('NFKD',str(value or '').casefold())
    value=''.join(c for c in value if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+',' ',value).strip()


def normalize_sector(value):
    original=str(value or '').strip()[:200]
    key=_norm(original)
    groups={
        'Informatique':{'informatique','it','technologie','technologies','developpement logiciel'},
        'Data Science et IA':{'data science','intelligence artificielle','ia','machine learning','big data'},
        'Marketing digital':{'marketing digital','marketing numerique','digital marketing'},
        'Banque et finance':{'banque','finance','banque et finance'},
        'Comptabilité':{'comptabilite','comptabilite et audit'},
        'Tourisme et hôtellerie':{'tourisme','hotellerie','hotellerie et restauration'},
        'Logistique':{'logistique','transport'},
        'Industrie':{'industrie','industriel'},
        'Commerce':{'commerce','vente','distribution'},
        'Centre d’appels':{'centre d appels','centre appel','call center'},
    }
    return next((label for label,values in groups.items() if key in values),original)


def parse_company_file(filename,content,mapping=None,include_report=False):
    if len(content)>5*1024*1024:raise ValueError('Le fichier dépasse 5 Mo.')
    ext=filename.lower().rsplit('.',1)[-1]
    if ext=='csv':
        text=content.decode('utf-8-sig')
        sample=text[:4096];dialect=csv.Sniffer().sniff(sample,delimiters=',;\t')
        raw=list(csv.DictReader(io.StringIO(text),dialect=dialect))
    elif ext in ('xlsx','xlsm'):
        wb=load_workbook(io.BytesIO(content),read_only=True,data_only=True)
        ws=wb.active;iterator=ws.iter_rows(values_only=True)
        try:headers=[str(v or '').strip() for v in next(iterator)]
        except StopIteration:headers=[]
        raw=[dict(zip(headers,row)) for row in iterator]
        wb.close()
    else:raise ValueError('Choisissez un fichier CSV ou Excel .xlsx.')
    if not raw:raise ValueError('Le fichier ne contient aucune ligne à importer.')
    custom={}
    allowed=set(ALIASES.values())
    for header,target in (mapping or {}).items():
        target=str(target or '').strip()
        if target not in allowed:raise ValueError(f'Champ de destination entreprise invalide : {target}.')
        custom[_norm(header)]=target
    normalized=[];errors=[]
    headers=list(raw[0].keys()) if raw else []
    report={'columns':{str(k):custom.get(_norm(k)) or ALIASES.get(_norm(k)) for k in headers},
        'recognized_columns':[str(k) for k in headers if custom.get(_norm(k)) or ALIASES.get(_norm(k))],
        'unmapped_columns':[str(k) for k in headers if not (custom.get(_norm(k)) or ALIASES.get(_norm(k)))],
        'missing_columns':[field for field in ('name','source') if field not in [custom.get(_norm(k)) or ALIASES.get(_norm(k)) for k in headers]]}
    for index,item in enumerate(raw,2):
        vals={custom.get(_norm(k)) or ALIASES.get(_norm(k),''):v for k,v in item.items() if k is not None}
        name=str(vals.get('name') or '').strip();source=str(vals.get('source') or '').strip()
        if len(name)<2 or len(name)>300 or not re.search(r'[\w]',name,flags=re.UNICODE) or not source or len(source)>120:
            errors.append({'row':index,'error':'Le nom et la provenance sont obligatoires.'});continue
        website=safe_url(str(vals.get('website') or '').strip()) or None
        maps=safe_url(str(vals.get('maps') or '').strip()) or None
        if vals.get('website') and not website:errors.append({'row':index,'error':'URL de site web invalide.'});continue
        if vals.get('maps') and not maps:errors.append({'row':index,'error':'URL Maps invalide.'});continue
        emails=[]
        try:
            emails=list(dict.fromkeys(email(x.strip()) for x in re.split(r'[,;\n]',str(vals.get('emails') or '')) if x.strip()))
        except ValueError:
            errors.append({'row':index,'error':'Adresse email professionnelle invalide.'});continue
        lat=lon=None;geo_source=None;verified=None
        if vals.get('latitude') not in (None,'') or vals.get('longitude') not in (None,''):
            try:lat=float(vals['latitude']);lon=float(vals['longitude'])
            except (TypeError,ValueError):errors.append({'row':index,'error':'Latitude/longitude invalides.'});continue
            geo_source=str(vals.get('geo_source') or '').strip();verified=str(vals.get('geo_verified_at') or '').strip()
            if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180 or not geo_source or not verified:
                errors.append({'row':index,'error':'Coordonnées hors plage ou provenance/date de vérification manquante.'});continue
            try:datetime.fromisoformat(verified.replace('Z','+00:00'))
            except ValueError:errors.append({'row':index,'error':'Date de vérification invalide.'});continue
        if any(len(str(vals.get(field) or ''))>limit for field,limit in [('address',600),('phone',100),('sector',200),('city',100),('source_id',180)]):
            errors.append({'row':index,'error':'Un champ dépasse la longueur autorisée.'});continue
        external=str(vals.get('source_id') or '').strip()
        if not external:
            external=hashlib.sha256('|'.join(_norm(x) for x in (source,name,vals.get('address'),vals.get('city'))).encode()).hexdigest()
        normalized.append({'name':name,'source':source,'source_id':external,'address':str(vals.get('address') or '').strip(),
            'phone':str(vals.get('phone') or '').strip()[:100],'emails':', '.join(emails),'website':website,'maps':maps,'sector':normalize_sector(vals.get('sector')),
            'city':str(vals.get('city') or '').strip()[:100],'latitude':lat,'longitude':lon,'geo_source':geo_source,'geo_verified_at':verified})
    if not normalized and errors:raise ValueError('Aucune ligne valide. Vérifiez les erreurs du fichier.')
    return (normalized,errors,report) if include_report else (normalized,errors)


def company_plan(path,items):
    result={'new':0,'update':0,'uncertain':0,'errors':[],'rows':[]}
    with connect(path) as db:
        for item in items:
            found=db.execute('SELECT company_rowid FROM company_source_identity WHERE source=? AND external_id=?',(item['source'],item['source_id'])).fetchone()
            company=None
            if found:company=db.execute('SELECT rowid,* FROM entreprises WHERE rowid=?',(found[0],)).fetchone()
            if company is None:
                exact=db.execute("SELECT rowid,* FROM entreprises WHERE lower(trim(\"Nom\"))=lower(trim(?)) AND lower(trim(COALESCE(\"Adresse\",'')))=lower(trim(?))",(item['name'],item['address'])).fetchall()
                if len(exact)==1:company=exact[0]
            candidates=db.execute('SELECT rowid,"Nom","Adresse" FROM entreprises WHERE lower(trim("Nom"))=lower(trim(?))',(item['name'],)).fetchall()
            if company:result['update']+=1;action='update'
            else:
                result['new']+=1;action='new'
                if candidates:result['uncertain']+=len(candidates)
            result['rows'].append({'name':item['name'],'source':item['source'],'action':action,
                'possible_duplicates':len(candidates) if action=='new' else 0,
                'possible_duplicate_names':[c['Nom'] for c in candidates] if action=='new' else [],
                'missing_fields':[name for name,value in [('Adresse',item['address']),('Secteur',item['sector']),('Site web',item['website']),('Email',item.get('emails')),('Ville',item['city'])] if not value]})
    return result


def import_companies(path,backup_dir,items,run_id=None):
    plan=company_plan(path,items);backup_database(path,backup_dir,'avant_import_entreprises');stamp=now();created=updated=uncertain=0
    with connect(path) as db:
        for item,row_plan in zip(items,plan['rows']):
            identity=db.execute('SELECT company_rowid FROM company_source_identity WHERE source=? AND external_id=?',(item['source'],item['source_id'])).fetchone()
            company=db.execute('SELECT rowid FROM entreprises WHERE rowid=?',(identity[0],)).fetchone() if identity else None
            if company is None:
                exact=db.execute("SELECT rowid FROM entreprises WHERE lower(trim(\"Nom\"))=lower(trim(?)) AND lower(trim(COALESCE(\"Adresse\",'')))=lower(trim(?))",(item['name'],item['address'])).fetchall()
                if len(exact)==1:company=exact[0]
            values=(item['name'],item['address'] or None,item['phone'] or None,item.get('emails') or None,item['website'],item['maps'],item['sector'] or None,item['city'] or None,
                    item['latitude'],item['longitude'],item['geo_verified_at'],item['geo_source'])
            if company:
                rowid=company[0];updated+=1
                db.execute('''UPDATE entreprises SET "Nom"=?,"Adresse"=COALESCE(NULLIF(?,''),"Adresse"),"Téléphone"=COALESCE(NULLIF(?,''),"Téléphone"),Emails=COALESCE(NULLIF(?,''),Emails),
                    "Site Web"=COALESCE(NULLIF(?,''),"Site Web"),"Google Maps"=COALESCE(NULLIF(?,''),"Google Maps"),
                    "Secteur"=COALESCE(NULLIF(?,''),"Secteur"),ville=COALESCE(NULLIF(?,''),ville),
                    latitude=COALESCE(?,latitude),longitude=COALESCE(?,longitude),geo_verified_at=COALESCE(NULLIF(?,''),geo_verified_at),geo_source=COALESCE(NULLIF(?,''),geo_source)
                    WHERE rowid=?''',(*values,rowid))
            else:
                cursor=db.execute('''INSERT INTO entreprises("Nom","Adresse","Téléphone",Emails,"Site Web","Google Maps","Secteur",ville,latitude,longitude,geo_verified_at,geo_source)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',values);rowid=cursor.lastrowid;created+=1
            db.execute('''INSERT INTO company_source_identity(company_rowid,source,external_id,first_seen,last_seen) VALUES (?,?,?,?,?)
                ON CONFLICT(source,external_id) DO UPDATE SET company_rowid=excluded.company_rowid,last_seen=excluded.last_seen''',
                (rowid,item['source'],item['source_id'],stamp,stamp))
            if row_plan['possible_duplicates']:
                candidates=db.execute('SELECT rowid FROM entreprises WHERE rowid<>? AND lower(trim("Nom"))=lower(trim(?))',(rowid,item['name'])).fetchall()
                for candidate in candidates:
                    uncertain+=1
                    db.execute('''INSERT OR IGNORE INTO company_duplicate_candidates(run_id,company_rowid,candidate_rowid,score,status,created_at) VALUES (?,?,?,?,?,?)''',
                               (run_id,rowid,candidate[0],0.7,'review',stamp))
        if run_id:
            db.execute('UPDATE collector_runs SET new_companies=?,updated_companies=?,status=?,finished_at=? WHERE id=?',
                       (created,updated,'imported',stamp,run_id))
    return {'new_companies':created,'updated_companies':updated,'uncertain_duplicates':uncertain,'backup_created':True}
