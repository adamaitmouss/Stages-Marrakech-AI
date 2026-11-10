"""Connecteurs Jawb documentés. Les requêtes sont bornées et ne publient rien."""
import json
import re
import socket
import time
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import requests
from .schema import normalize_offer

BASE = 'https://jawb.ma'
TIMEOUT = (4, 12)
MAX_PAGES = 10
USER_AGENT = 'StagesMarrakechAI/1.0 (personal internship search; contact: local app)'


def _safe_jawb_url(value):
    url = urljoin(BASE + '/', value)
    p = urlparse(url)
    return p.scheme == 'https' and p.hostname == 'jawb.ma' and p.username is None and p.password is None


def _request(session, url, params=None):
    if not _safe_jawb_url(url):
        raise ValueError('Redirection hors du domaine Jawb refusée.')
    response = session.get(url, params=params, timeout=TIMEOUT, allow_redirects=False,
                           headers={'User-Agent': USER_AGENT, 'Accept': 'application/json, application/rss+xml, application/xml'})
    if 300 <= response.status_code < 400:
        raise ValueError('Redirection inattendue du flux Jawb.')
    response.raise_for_status()
    if len(response.content) > 4_000_000:
        raise ValueError('Réponse Jawb trop volumineuse.')
    return response


def _local(element):
    return element.tag.rsplit('}', 1)[-1].lower()


def parse_rss(xml_text):
    root = ET.fromstring(xml_text)
    items = [node for node in root.iter() if _local(node) in ('item', 'entry')]
    result = []
    for node in items[:50]:
        values = {}
        for child in node:
            key = _local(child)
            if key == 'link':
                values[key] = child.attrib.get('href') or (child.text or '').strip()
            elif key in ('title','description','summary','content','pubdate','published','updated','guid','id'):
                values[key] = child.text or ''
        result.append({'title': values.get('title'), 'description': values.get('description') or values.get('summary') or values.get('content'),
                       'url': values.get('link') or values.get('guid') or values.get('id'), 'source_id': values.get('guid') or values.get('id') or values.get('link'),
                       'published_at': values.get('pubdate') or values.get('published') or values.get('updated')})
    return result


def fetch_rss(session=None, city='Marrakech', profession=''):
    session = session or requests.Session()
    params = {'ville': city}
    if profession:
        params['metier'] = profession
    response = _request(session, BASE + '/rss.xml', params=params)
    return [o for raw in parse_rss(response.text) if (o := normalize_offer(raw, 'Jawb RSS'))]


def fetch_company_feed(session=None, company_ids=()):
    session = session or requests.Session()
    results = []
    for company_id in company_ids:
        company_id = str(company_id).strip()
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,120}',company_id):
            raise ValueError('Identifiant de société Jawb invalide.')
        next_url = BASE + f'/api/entreprises/{company_id}/offres.json'
        params = {'lang': 'fr', 'limit': 100, 'page': 1}
        pages = 0
        while next_url and pages < MAX_PAGES:
            response = _request(session, next_url, params=params)
            params = None
            data = response.json()
            if not isinstance(data, dict) or not isinstance(data.get('jobs', []), list):
                raise ValueError('Structure de réponse Jawb invalide.')
            company = data.get('company')
            company_name = company.get('name') if isinstance(company, dict) else company if isinstance(company, str) else ''
            for raw in data.get('jobs', [])[:100]:
                if isinstance(raw, dict):
                    raw = dict(raw)
                    raw['company'] = raw.get('company') or company_name
                    raw['url'] = raw.get('url') or raw.get('apply_url')
                    raw['source_id'] = raw.get('id') or raw.get('slug')
                    item = normalize_offer(raw, 'Jawb JSON')
                    if item:
                        results.append(item)
            next_value = data.get('next')
            next_url = urljoin(BASE + '/', next_value) if next_value else None
            if next_url and not _safe_jawb_url(next_url):
                raise ValueError('Lien de pagination Jawb hors domaine refusé.')
            pages += 1
            if next_url:
                time.sleep(0.2)
        if next_url:
            raise ValueError('Pagination Jawb supérieure à la limite locale de sécurité.')
    return results


def fetch_career_rss(session, name, url):
    """Flux d'entreprise fourni/autorisé par son propriétaire, HTTPS public seulement."""
    p = urlparse(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.hostname in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Flux carrière : URL HTTPS publique requise.')
    try:
        addresses = socket.getaddrinfo(p.hostname, None)
    except OSError as exc:
        raise ValueError('Nom de domaine du flux carrière introuvable.') from exc
    import ipaddress
    if any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('Adresse réseau privée refusée pour le flux carrière.')
    session = session or requests.Session()
    response = _request_generic(session, url)
    return [o for raw in parse_rss(response.text) if (o := normalize_offer(raw, name))]


def _request_generic(session, url):
    response = session.get(url, timeout=TIMEOUT, allow_redirects=False,
                           headers={'User-Agent': USER_AGENT, 'Accept': 'application/rss+xml, application/atom+xml, application/xml'})
    if 300 <= response.status_code < 400:
        raise ValueError('Redirection refusée pour éviter de sortir du flux autorisé.')
    response.raise_for_status()
    if len(response.content) > 4_000_000:
        raise ValueError('Flux carrière trop volumineux.')
    return response
