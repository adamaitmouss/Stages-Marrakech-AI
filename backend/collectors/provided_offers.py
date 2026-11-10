"""Import d'offres à partir d'un fichier légalement transmis par un tiers."""
import csv
import hashlib
import io
import json
import re
import time
import unicodedata
from openpyxl import load_workbook
from .schema import normalize_offer, identity_key, parse_date
from ..db import connect, now


ALIASES = {
    'source': 'source', 'organisme': 'source', 'publisher': 'source',
    'id': 'source_id', 'id source': 'source_id', 'external id': 'source_id', 'reference': 'source_id',
    'title': 'title', 'titre': 'title', 'intitule': 'title', 'intitulé': 'title',
    'company': 'company', 'entreprise': 'company', 'employeur': 'company',
    'city': 'city', 'ville': 'city', 'location': 'city', 'localisation': 'city',
    'sector': 'sector', 'secteur': 'sector', 'metier': 'sector', 'métier': 'sector',
    'description': 'description', 'missions': 'description',
    'contract type': 'contract_type', 'type contrat': 'contract_type', 'type de contrat': 'contract_type',
    'internship type': 'internship_type', 'type stage': 'internship_type', 'type de stage': 'internship_type',
    'skills': 'skills', 'competences': 'skills', 'compétences': 'skills',
    'published at': 'published_at', 'date publication': 'published_at', 'date de publication': 'published_at',
    'expires at': 'expires_at', 'date expiration': 'expires_at', 'date limite': 'expires_at',
    'url': 'url', 'lien': 'url', 'lien source': 'url', 'url source': 'url', 'apply url': 'url',
}


def _header(value):
    text = unicodedata.normalize('NFKD', str(value or '').casefold())
    text = ''.join(c for c in text if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def _rows(filename, content):
    if len(content) > 5 * 1024 * 1024:
        raise ValueError('Le fichier dépasse 5 Mo.')
    extension = filename.lower().rsplit('.', 1)[-1]
    if extension == 'csv':
        text = content.decode('utf-8-sig')
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
        return list(csv.DictReader(io.StringIO(text), dialect=dialect))
    if extension in ('xlsx', 'xlsm'):
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        try:
            worksheet = workbook.active
            iterator = worksheet.iter_rows(values_only=True)
            headers = [str(value or '').strip() for value in next(iterator)]
            return [dict(zip(headers, row)) for row in iterator]
        except StopIteration:
            return []
        finally:
            workbook.close()
    raise ValueError('Choisissez un fichier CSV ou Excel .xlsx.')


TARGET_FIELDS={'source':'source','source_id':'source_id','title':'title','company':'company','city':'city','sector':'sector',
              'description':'description','contract_type':'contract_type','internship_type':'internship_type','skills':'skills',
              'published_at':'published_at','expires_at':'expires_at','url':'url'}


def parse_provided_offers(filename, content, source_name, mapping=None, include_report=False):
    source = str(source_name or '').strip()
    if len(source) < 3 or len(source) > 60:
        raise ValueError('Indiquez le nom du producteur ou de l’organisme (3 à 60 caractères).')
    raw = _rows(filename, content)
    if len(raw) > 10000:
        raise ValueError('Le fichier dépasse la limite de 10 000 lignes.')
    if not raw:
        raise ValueError('Le fichier ne contient aucune annonce.')
    custom={}
    for header,target in (mapping or {}).items():
        target=str(target or '').strip()
        if target not in TARGET_FIELDS:
            raise ValueError(f'Champ de destination invalide dans le mapping : {target}.')
        custom[_header(header)]=TARGET_FIELDS[target]
    offers, errors = [], []
    headers=list(raw[0].keys()) if raw else []
    recognized={str(header):custom.get(_header(header)) or ALIASES.get(_header(header)) for header in headers}
    for line, row in enumerate(raw, 2):
        fields = {}
        for key, value in row.items():
            normalized_key = _header(key)
            field = custom.get(normalized_key) or ALIASES.get(normalized_key)
            if field:
                fields[field] = value
        url = str(fields.get('url') or '').strip()
        source_id = str(fields.get('source_id') or '').strip()
        if not fields.get('title'):
            errors.append({'row': line, 'error': 'Titre obligatoire.'})
            continue
        if not url or not re.match(r'^https://[^\s/]+(?:/|$)', url, flags=re.I):
            errors.append({'row': line, 'error': 'URL source HTTPS obligatoire.'})
            continue
        bad_dates=[key for key in ('published_at','expires_at') if fields.get(key) and parse_date(fields.get(key)) is None]
        if bad_dates:
            errors.append({'row':line,'error':'Date illisible : '+', '.join(bad_dates)+'.'})
            continue
        item = dict(fields)
        item['source_id'] = source_id
        normalized = normalize_offer(item, source)
        if not normalized:
            errors.append({'row': line, 'error': 'Annonce invalide ou URL source incorrecte.'})
            continue
        if not identity_key(normalized):
            errors.append({'row': line, 'error': 'Identifiant source ou URL canonique manquant.'})
            continue
        offers.append(normalized)
    report={'columns':recognized,'recognized_columns':[x for x,v in recognized.items() if v],
            'unmapped_columns':[x for x,v in recognized.items() if not v],
            'missing_columns':[x for x in ('title','url') if x not in recognized.values()]}
    return (offers, errors, report) if include_report else (offers, errors)


def stage_provided_file(path, filename, content, source_name, permission_ref,
                        consultation_allowed, storage_allowed, display_allowed, mapping=None):
    for label, allowed in [('consultation', consultation_allowed), ('stockage', storage_allowed), ('réaffichage', display_allowed)]:
        if allowed is not True:
            raise ValueError(f'Le droit de {label} doit être confirmé avant le staging du fichier.')
    reference = str(permission_ref or '').strip()
    if len(reference) < 3 or len(reference) > 500:
        raise ValueError('Une référence de licence ou d’autorisation (3 à 500 caractères) est requise.')
    started = time.perf_counter()
    source = 'Fichier fourni — ' + str(source_name).strip()
    offers, errors, column_report = parse_provided_offers(filename, content, source, mapping, include_report=True)
    stamp = now()
    metadata = {
        'kind': 'provided_file', 'source_name': source,
        'permission_ref': reference, 'consultation_allowed': True,
        'storage_allowed': True, 'display_allowed': True,
        'filename': re.sub(r'[^A-Za-z0-9._-]+', '_', str(filename))[:120],
        'file_sha256': hashlib.sha256(content).hexdigest(),
        'parse_errors': errors[:1000], 'file_duplicate_rows': 0,
        'column_report':column_report,'column_mapping':mapping or {},
    }
    with connect(path) as db:
        cursor = db.execute('''INSERT INTO collector_runs
            (mode,status,started_at,finished_at,source_count,fetched_count,source_metadata_json,error_summary,duration_ms,error_count,duplicates,rejected_offers)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ('file-import', 'previewed', stamp, stamp, 1, len(offers),
             json.dumps(metadata, ensure_ascii=False),
             f"{len(errors)} ligne(s) rejetée(s) lors de la validation du fichier." if errors else None,
             round((time.perf_counter() - started) * 1000), len(errors),0,len(errors)))
        run_id = cursor.lastrowid
        duplicate_rows=0
        for offer in offers:
            cursor=db.execute('''INSERT OR IGNORE INTO collector_staging(run_id,source,identity_key,payload_json)
                          VALUES (?,?,?,?)''',
                       (run_id, source, identity_key(offer), json.dumps(offer, ensure_ascii=False)))
            if not cursor.rowcount:duplicate_rows+=1
        metadata['file_duplicate_rows']=duplicate_rows
        db.execute('UPDATE collector_runs SET source_metadata_json=?,duplicates=? WHERE id=?',
                   (json.dumps(metadata,ensure_ascii=False),duplicate_rows,run_id))
        staged_count = db.execute('SELECT COUNT(*) FROM collector_staging WHERE run_id=?', (run_id,)).fetchone()[0]
        db.execute('''INSERT INTO collector_source_runs
            (run_id,source,status,started_at,finished_at,fetched_count,error_summary,duration_ms,duplicates,rejected_offers)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (run_id, source, 'previewed', stamp, stamp, len(offers),
             f'{len(errors)} ligne(s) rejetée(s) pendant le parsing.' if errors else None,
             round((time.perf_counter() - started) * 1000),duplicate_rows,len(errors)))
    return {'id': run_id, 'status': 'previewed', 'fetched_count': len(offers),
            'staged_count':staged_count,'duplicate_rows':duplicate_rows,
            'rejected_rows': len(errors), 'errors': errors, 'file_sha256': metadata['file_sha256'],
            'column_report':column_report}
