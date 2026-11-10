import re
from datetime import date
from urllib.parse import urlparse

STATUSES = ['Non envoyée', 'Envoyée', 'Relancée', 'Entretien', 'Acceptée', 'Refusée']


def text(value, maximum=2000):
    if not isinstance(value, str) or len(value) > maximum:
        raise ValueError('Texte invalide ou trop long.')
    return value.strip()


def email(value):
    value = text(value, 254).lower()
    if not re.fullmatch(r'[A-Za-z0-9.!#$%&*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}', value):
        raise ValueError('Adresse email invalide ; une seule adresse est attendue.')
    return value


def safe_url(value):
    if not isinstance(value, str):
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme in ('https', 'http') and parsed.hostname and not parsed.username and not parsed.password:
        return value.strip()
    return None


def candidature(data, partial=False):
    allowed = {'nom_entreprise', 'secteur', 'email', 'telephone', 'date_candidature', 'statut', 'commentaire'}
    result = {}
    for key in allowed & data.keys():
        result[key] = text(data[key], 5000 if key == 'commentaire' else 300)
    if not partial:
        for key in ('nom_entreprise', 'date_candidature', 'statut'):
            if not result.get(key):
                raise ValueError('Entreprise, date et statut sont obligatoires.')
    if 'nom_entreprise' in result and not result['nom_entreprise']:
        raise ValueError('Le nom de l’entreprise est obligatoire.')
    if result.get('email'):
        result['email'] = email(result['email'])
    if 'statut' in result and result['statut'] not in STATUSES:
        raise ValueError('Statut inconnu.')
    if 'date_candidature' in result:
        try:
            date.fromisoformat(result['date_candidature'])
        except (ValueError, TypeError):
            raise ValueError('Date invalide : format AAAA-MM-JJ attendu.')
    if not result:
        raise ValueError('Aucune modification transmise.')
    return result
