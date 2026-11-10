"""Schéma canonique et validations de contenu public."""
import hashlib
import html
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit


FIELDS = ('source', 'source_id', 'source_job_id', 'title', 'company', 'city', 'sector', 'description',
          'contract_type', 'internship_type', 'skills', 'published_at', 'expires_at', 'url', 'job_url', 'apply_url', 'missing_fields', 'status')


def clean_text(value, limit=12000):
    if value is None:
        return ''
    value = html.unescape(re.sub(r'<[^>]*>', ' ', str(value)))
    return re.sub(r'\s+', ' ', value).strip()[:limit]


def canonical_url(value):
    if not value:
        return ''
    try:
        parts = urlsplit(str(value).strip())
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
            return ''
        host = parts.hostname.lower().removeprefix('www.')
        path = re.sub('/+$', '', parts.path or '/')
        return urlunsplit(('https', host, path, '', ''))
    except ValueError:
        return ''


def parse_date(value):
    if not value:
        return None
    if isinstance(value,(int,float)) and value>0:
        try:
            from datetime import timedelta
            seconds=float(value)/1000 if value>10**11 else float(value)
            return (datetime(1970,1,1,tzinfo=timezone.utc)+timedelta(seconds=seconds)).isoformat(timespec='seconds')
        except (OverflowError,ValueError):return None
    value = str(value).strip()
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat(timespec='seconds')


def normalize_offer(item, source):
    title = clean_text(item.get('title') or item.get('titre') or item.get('titre_en') or item.get('titre_ar'), 500)
    raw_job_url = str(item.get('job_url') or item.get('url') or item.get('link') or '').strip()
    raw_apply_url = str(item.get('apply_url') or item.get('url') or item.get('link') or raw_job_url).strip()
    dedupe_url = canonical_url(raw_job_url) or canonical_url(raw_apply_url)
    if not dedupe_url:
        return None
    if not canonical_url(raw_job_url):raw_job_url=raw_apply_url
    if not canonical_url(raw_apply_url):raw_apply_url=raw_job_url
    raw_url = raw_job_url
    description = clean_text(item.get('description'), 12000)
    if not title or not dedupe_url:
        return None
    skills = item.get('skills') or item.get('competences') or []
    if isinstance(skills, str):
        skills = [clean_text(x, 100) for x in re.split(r'[,;|]', skills) if clean_text(x, 100)]
    if not isinstance(skills, (list, tuple)):
        skills = []
    published=parse_date(item.get('published_at') or item.get('created_at') or item.get('pubDate'))
    expires=parse_date(item.get('expires_at') or item.get('expiresAt'))
    status='unknown'
    if expires:
        try:status='expired' if datetime.fromisoformat(expires).date()<datetime.now(timezone.utc).date() else 'active'
        except ValueError:status='unknown'
    company=clean_text(item.get('company') or item.get('entreprise'), 300)
    city=clean_text(item.get('city') or item.get('ville'), 100)
    description=clean_text(item.get('description'), 12000)
    contract=clean_text(item.get('contract_type') or item.get('type_contrat'), 100)
    internship=clean_text(item.get('internship_type') or item.get('type_stage'), 100)
    missing=[name for name,value in [('Entreprise',company),('Ville',city),('Description',description),
             ('Type de contrat',contract),('Type de stage',internship),('Date de publication',published)] if not value]
    return {
        'source': clean_text(source, 80),
        'source_id': clean_text(item.get('source_id') or item.get('id') or item.get('guid') or '', 180),
        'source_job_id': clean_text(item.get('source_job_id') or item.get('source_id') or item.get('id') or '', 180),
        'title': title,
        'company': company,
        'city': city,
        'sector': clean_text(item.get('sector') or item.get('metier') or item.get('secteur'), 120),
        'description': description,
        'contract_type': contract,
        'internship_type': internship,
        'skills': list(dict.fromkeys(skills))[:100],
        'published_at': published,
        'expires_at': expires,
        'url': raw_url,
        'job_url': raw_job_url,
        'apply_url': raw_apply_url,
        'canonical_url': dedupe_url,
        'missing_fields':missing,
        'status':status,
    }


def identity_key(offer):
    return offer['source_id'] or offer['canonical_url']


def fingerprint(offer):
    def norm(s):
        s = unicodedata.normalize('NFKD', str(s or '').casefold())
        s = ''.join(c for c in s if not unicodedata.combining(c))
        return re.sub(r'[^a-z0-9]+', ' ', s).strip()
    text = '|'.join(norm(offer.get(k)) for k in ('company','title','city','description'))
    return hashlib.sha256(text.encode()).hexdigest()


def content_hash(offer):
    values={key:offer.get(key) for key in ('title','company','city','sector','description','contract_type',
        'internship_type','skills','published_at','expires_at','canonical_url','job_url','apply_url')}
    return hashlib.sha256(__import__('json').dumps(values,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
