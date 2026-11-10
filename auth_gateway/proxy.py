from __future__ import annotations

import threading
from urllib.parse import urlsplit

import requests


HOP_HEADERS = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
               'te', 'trailers', 'transfer-encoding', 'upgrade', 'content-length', 'content-encoding', 'set-cookie'}


class BackendTunnel:
    """A loopback-only server-side session to the unchanged Flask application."""

    def __init__(self, base_url: str, profile: str, internal_secret: str):
        self.base_url = base_url.rstrip('/')
        self.profile = profile
        self.internal_secret = internal_secret
        self.http = requests.Session()
        self.http.trust_env = False
        self.backend_csrf = ''
        self.public_demo = False
        self.ready = False
        self.lock = threading.RLock()

    def initialize(self):
        with self.lock:
            if self.ready:
                return
            if len(self.internal_secret) < 48:
                raise RuntimeError('Secret interne local absent ou invalide; relancez le lanceur Windows.')
            response = self.http.post(
                self.base_url + '/api/internal/gateway-session', json={},
                headers={'X-Internal-Gateway-Secret': self.internal_secret, 'Origin': self.base_url}, timeout=5)
            response.raise_for_status()
            info = response.json()
            if not isinstance(info, dict) or not info.get('authenticated'):
                raise RuntimeError('Le backend local n’a pas créé la session de passerelle attendue.')
            self.public_demo = bool(info.get('public_demo'))
            if self.profile == 'demo' and not self.public_demo:
                raise RuntimeError('Profil refusé : les comptes ouverts ne peuvent utiliser qu’une base synthétique confirmée.')
            if self.profile in {'private', 'multi_user'} and self.public_demo:
                raise RuntimeError('Profil refusé : le mode privé ne peut pas pointer sur le backend de démonstration.')
            self.backend_csrf = str(info.get('csrf', ''))
            if not self.backend_csrf:
                raise RuntimeError('Le backend n’a pas fourni de jeton de session interne valide.')
            self.ready = True

    def request(self, path: str, method: str, query: str, body: bytes,
                headers: dict[str, str], external_origin: str | None):
        self.initialize()
        url = self.base_url + '/' + path.lstrip('/')
        if query:
            url += '?' + query
        parsed = urlsplit(self.base_url)
        forwarded = {'Origin': self.base_url}
        if external_origin:
            forwarded['Referer'] = self.base_url + '/'
        for key in ('Accept', 'Content-Type', 'User-Agent', 'Range', 'If-None-Match', 'If-Modified-Since', 'X-Internal-User-ID'):
            if key in headers:
                forwarded[key] = headers[key]
        if method not in {'GET', 'HEAD', 'OPTIONS'} and path.startswith('api/'):
            forwarded['X-CSRF-Token'] = self.backend_csrf
        with self.lock:
            response = self.http.request(method, url, data=body if body else None,
                                         headers=forwarded, timeout=(5, 60), allow_redirects=False)
            headers_out = [(k, v) for k, v in response.headers.items() if k.lower() not in HOP_HEADERS]
            location = response.headers.get('Location')
            if location:
                backend_origin = f'{parsed.scheme}://{parsed.netloc}'
                public_host = urlsplit(external_origin or '').netloc
                if location.startswith(backend_origin + '/') and public_host:
                    headers_out = [(k, public_host + location[len(backend_origin):] if k.lower() == 'location' else v)
                                   for k, v in headers_out]
            return response.status_code, headers_out, response.content
