"""Score déterministe : chaque composante et contribution sont retournées."""
import math
import re
import unicodedata
from collections import Counter

VOCABULARY = ['python', 'sql', 'excel', 'power bi', 'pandas', 'numpy', 'machine learning', 'data science',
              'javascript', 'html', 'css', 'react', 'flask', 'django', 'java', 'php', 'laravel', 'git',
              'marketing', 'seo', 'communication', 'comptabilité', 'finance', 'audit', 'vente', 'commerce',
              'rh', 'recrutement', 'logistique', 'tourisme', 'hôtellerie', 'anglais', 'français', 'arabe',
              'gestion', 'design', 'canva', 'photoshop', 'réseaux sociaux', 'management']
ALIASES = {'js': 'javascript', 'powerbi': 'power bi', 'ml': 'machine learning', 'comptabilite': 'comptabilite',
           'english': 'anglais', 'french': 'francais', 'human resources': 'rh'}
STOP = set('de la le les des du un une et en a au pour dans avec sur ou the and of to is stage emploi recherche entreprise'.split())


def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(value).lower()) if not unicodedata.combining(c))


def tokens(value):
    return [t for t in re.findall(r'[a-z0-9+#]+', norm(value)) if len(t) > 1 and t not in STOP]


def canonical(skill):
    return ALIASES.get(norm(skill).strip(), norm(skill).strip())


def has_term(term, value):
    return bool(re.search(r'(?<!\w)' + re.escape(norm(term)) + r'(?!\w)', norm(value)))


def skills_from(value):
    return [s for s in VOCABULARY if has_term(s, value)]


def local_profile(value):
    return {'skills': skills_from(value), 'education': '', 'experience': '', 'domain': '', 'location': '', 'opportunity': 'Stage'}


def validate_profile(data):
    if not isinstance(data, dict):
        raise ValueError('Profil invalide.')
    skills = data.get('skills', [])
    if not isinstance(skills, list) or len(skills) > 100 or any(not isinstance(s, str) or len(s) > 100 for s in skills):
        raise ValueError('Liste de compétences invalide.')
    result = {'skills': list(dict.fromkeys(s.strip() for s in skills if s.strip()))}
    for field in ('education', 'experience', 'domain', 'location', 'opportunity'):
        value = data.get(field, '')
        if not isinstance(value, str) or len(value) > 6000:
            raise ValueError('Champ de profil invalide.')
        result[field] = value.strip()
    return result


def cosine(a, b, corpus):
    aa, bb = Counter(tokens(a)), Counter(tokens(b))
    if not aa or not bb:
        return 0.0
    sets = [set(tokens(c)) for c in corpus]
    def vector(counter):
        return {t: n * (math.log((len(sets)+1)/(1+sum(t in s for s in sets)))+1) for t, n in counter.items()}
    va, vb = vector(aa), vector(bb)
    return sum(v * vb.get(t, 0) for t,v in va.items()) / (math.sqrt(sum(v*v for v in va.values())) * math.sqrt(sum(v*v for v in vb.values())))


def rank(profile, offers, weights, interpretations=None):
    profile = validate_profile(profile)
    required = {'skills', 'education', 'experience', 'location', 'opportunity'}
    if set(weights) != required or any(type(v) not in (int, float) or not 0 <= v <= 100 for v in weights.values()) or abs(sum(weights.values())-100) > .01:
        raise ValueError('Les cinq pondérations doivent totaliser 100.')
    corpus = [' '.join([str(o.get('Titre') or ''), str(o.get('Description') or '')]) for o in offers]
    results = []
    for offer, description in zip(offers, corpus):
        requirements = skills_from(description)
        matched = [r for r in requirements if any(canonical(r) == canonical(s) for s in profile['skills'])]
        interpretation = (interpretations or {}).get(str(offer['ID']), {})
        for pair in interpretation.get('pairs', []):
            if pair['offer_skill'] not in matched:
                matched.append(pair['offer_skill'])
            if pair['offer_skill'] not in requirements:
                requirements.append(pair['offer_skill'])
        missing = [r for r in requirements if r not in matched]
        city = offer.get('ville') or ''
        components = {
            'skills': len(matched)/len(requirements) if requirements else 0,
            'education': cosine(profile['education']+' '+profile['domain'], description, corpus),
            'experience': cosine(profile['experience'], description, corpus),
            'location': float(bool(city and profile['location'] and norm(city) == norm(profile['location']))),
            'opportunity': float(bool(profile['opportunity'] and norm(profile['opportunity']) == norm(offer.get('Type contrat') or ''))),
        }
        contributions = {k: round(components[k]*weights[k], 2) for k in weights}
        uncertain = len(tokens(offer.get('Description') or '')) < 30 or not requirements or not city
        results.append({
            'offer': offer, 'score': round(sum(contributions.values()), 1), 'components': {k: round(v*100, 2) for k,v in components.items()},
            'weights': weights, 'contributions': contributions, 'matched': matched, 'missing': missing, 'uncertain': uncertain,
            'explanation': interpretation.get('explanation') or f'{len(matched)} compétence(s) retrouvée(s) sur {len(requirements)} repérée(s). Comparaison textuelle du domaine et des projets.',
            'recommendation': interpretation.get('recommendation') or ('Précisez vos projets liés à '+', '.join(missing[:4])+', uniquement si vous les avez réalisés.' if missing else 'Ajoutez des exemples concrets et vérifiables de vos projets.'),
            'limitations': 'Localisation inconnue : composante à zéro.' if not city else '',
        })
    return sorted(results, key=lambda item: (-item['score'], item['offer']['ID']))
