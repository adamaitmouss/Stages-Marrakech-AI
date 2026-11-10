"""Connecteurs publics d'ATS. Les fonctions de parsing sont pures et testables hors réseau."""
import re
import time
from urllib.parse import urlparse

import requests

from .jawb import TIMEOUT, USER_AGENT
from .schema import normalize_offer

MAX_PAGES = 20
PAGE_SIZE = 100
MAX_RESPONSE_BYTES = 4_000_000


def _token(value, label='Identifiant de job board'):
    value = str(value or '').strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,120}', value):
        raise ValueError(f'{label} invalide.')
    return value


def _request(session, url, params=None):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in {
        'boards-api.greenhouse.io', 'api.lever.co', 'api.eu.lever.co',
        'api.ashbyhq.com', 'api.smartrecruiters.com'
    } or parsed.username or parsed.password:
        raise ValueError('URL du connecteur externe refusée.')
    response = session.get(url, params=params, timeout=TIMEOUT, allow_redirects=False,
                           headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    if 300 <= response.status_code < 400:
        raise ValueError('Redirection du connecteur refusée.')
    response.raise_for_status()
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError('Réponse du connecteur trop volumineuse.')
    return response


def parse_greenhouse(data, company, source):
    jobs = data.get('jobs') if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        raise ValueError('Réponse Greenhouse invalide.')
    result = []
    for raw in jobs[:PAGE_SIZE * MAX_PAGES]:
        if not isinstance(raw, dict):
            continue
        location = raw.get('location') or {}
        item = normalize_offer({'source_id': raw.get('id'), 'title': raw.get('title'),
            'company': company, 'city': location.get('name') if isinstance(location, dict) else location,
            'description': raw.get('content'), 'published_at': raw.get('updated_at'),
            'job_url': raw.get('absolute_url') or raw.get('url'),
            'apply_url': raw.get('applyUrl') or raw.get('absolute_url') or raw.get('url')}, source)
        if item:
            result.append(item)
    return result


def fetch_greenhouse(board, company, session=None):
    board = _token(board)
    session = session or requests.Session()
    response = _request(session, f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs', {'content': 'true'})
    return parse_greenhouse(response.json(), company, f'Greenhouse · {company}')


def parse_lever(data, company, source):
    if not isinstance(data, list):
        raise ValueError('Réponse Lever invalide.')
    result = []
    for raw in data[:PAGE_SIZE]:
        if not isinstance(raw, dict):
            continue
        categories = raw.get('categories') or {}
        result.append(normalize_offer({'source_id': raw.get('id'), 'title': raw.get('text'),
            'company': company, 'city': categories.get('location'),
            'sector': categories.get('team') or categories.get('department'),
            'description': raw.get('descriptionPlain') or raw.get('description'),
            'contract_type': categories.get('commitment'), 'job_url':raw.get('hostedUrl') or raw.get('applyUrl'),
            'apply_url':raw.get('applyUrl') or raw.get('hostedUrl'),
            'published_at': raw.get('createdAt')}, source))
    return [x for x in result if x]


def fetch_lever(site, company, session=None, region='global'):
    site = _token(site, 'Identifiant Lever')
    if region not in ('global', 'eu'):
        raise ValueError('Région Lever invalide.')
    host = 'api.eu.lever.co' if region == 'eu' else 'api.lever.co'
    session = session or requests.Session()
    result = []
    for page in range(MAX_PAGES):
        skip = page * PAGE_SIZE
        response = _request(session, f'https://{host}/v0/postings/{site}',
                            {'mode': 'json', 'skip': skip, 'limit': PAGE_SIZE})
        batch = parse_lever(response.json(), company, f'Lever · {company}')
        result.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        time.sleep(0.1)
    else:
        raise ValueError('Pagination Lever supérieure à la limite locale.')
    return result


def parse_ashby(data, company, source):
    jobs = data.get('jobs') if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        raise ValueError('Réponse Ashby invalide.')
    result = []
    for raw in jobs[:PAGE_SIZE * MAX_PAGES]:
        if not isinstance(raw, dict) or raw.get('isListed') is not True:
            continue
        address = raw.get('address') or {}
        postal = address.get('postalAddress') or {}
        location = raw.get('location') or postal.get('addressLocality') or ''
        if postal.get('addressCountry'):
            location = f'{location}, {postal["addressCountry"]}'.strip(', ')
        workplace=raw.get('workplaceType') or ('Remote / hybride' if raw.get('isRemote') else '')
        description=raw.get('descriptionPlain') or raw.get('descriptionHtml') or ''
        if workplace:description=f'{description}\nMode de travail : {workplace}'
        result.append(normalize_offer({'source_id': raw.get('id') or raw.get('jobId'),
            'title': raw.get('title'), 'company': company, 'city': location,
            'sector': raw.get('department') or raw.get('team'),
            'description': description,
            'contract_type': raw.get('employmentType'), 'published_at': raw.get('publishedAt'),
            'job_url': raw.get('jobUrl') or raw.get('applyUrl'),
            'apply_url':raw.get('applyUrl') or raw.get('jobUrl')}, source))
    return [x for x in result if x]


def fetch_ashby(board, company, session=None):
    board = _token(board)
    session = session or requests.Session()
    response = _request(session, f'https://api.ashbyhq.com/posting-api/job-board/{board}')
    return parse_ashby(response.json(), company, f'Ashby · {company}')


def parse_smartrecruiters(data, company, source):
    postings = data.get('content') if isinstance(data, dict) else None
    if not isinstance(postings, list):
        raise ValueError('Réponse SmartRecruiters invalide.')
    result = []
    for raw in postings[:PAGE_SIZE]:
        if not isinstance(raw, dict):
            continue
        location = raw.get('location') or {}
        result.append(normalize_offer({'source_id': raw.get('id'), 'title': raw.get('name'),
            'company': company, 'city': ', '.join(str(location.get(k)) for k in ('city','region','country') if location.get(k)),
            'sector': raw.get('department', {}).get('label') if isinstance(raw.get('department'), dict) else '',
            'description': raw.get('jobAd', {}).get('sections', {}).get('jobDescription', {}).get('text') if isinstance(raw.get('jobAd'), dict) else '',
            'contract_type': raw.get('typeOfEmployment', {}).get('label') if isinstance(raw.get('typeOfEmployment'), dict) else '',
            'published_at': raw.get('releasedDate'),
            'job_url': raw.get('ref') or raw.get('applyUrl'),
            'apply_url':raw.get('applyUrl') or raw.get('ref')}, source))
    return [x for x in result if x]


def fetch_smartrecruiters(company_id, company, session=None):
    company_id = _token(company_id, 'Identifiant SmartRecruiters')
    session = session or requests.Session()
    result = []
    for page in range(MAX_PAGES):
        offset = page * PAGE_SIZE
        response = _request(session, f'https://api.smartrecruiters.com/v1/companies/{company_id}/postings',
                            {'destination': 'PUBLIC', 'limit': PAGE_SIZE, 'offset': offset})
        data = response.json()
        batch = parse_smartrecruiters(data, company, f'SmartRecruiters · {company}')
        result.extend(batch)
        total = data.get('totalFound', 0) if isinstance(data, dict) else 0
        if not batch or offset + PAGE_SIZE >= int(total or 0) or len(batch) < PAGE_SIZE:
            break
        time.sleep(0.1)
    else:
        raise ValueError('Pagination SmartRecruiters supérieure à la limite locale.')
    return result


FETCHERS = {'greenhouse': fetch_greenhouse, 'lever': fetch_lever,
            'ashby': fetch_ashby, 'smartrecruiters': fetch_smartrecruiters}
