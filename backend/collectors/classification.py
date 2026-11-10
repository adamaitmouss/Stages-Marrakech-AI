"""Classement explicable d'offres. Une absence d'indice reste une valeur inconnue."""
import re
import unicodedata


def _text(value):
    value = unicodedata.normalize('NFKD', str(value or '').casefold())
    return ''.join(c for c in value if not unicodedata.combining(c))


def classify_offer(offer):
    title = _text(offer.get('title') or offer.get('Titre'))
    description = _text(offer.get('description') or offer.get('Description'))
    contract = _text(offer.get('contract_type') or offer.get('Type contrat'))
    city = _text(offer.get('city') or offer.get('ville'))
    text = f'{title} {description} {contract}'
    stage = any(re.search(pattern, text) for pattern in (r'\bstage\b', r'\bintern(ship)?\b', r'\bpfe\b'))
    employment = any(re.search(pattern, text) for pattern in (r'\bcdi\b', r'\bcdd\b', r'\bfull.?time\b', r'\bpermanent\b', r'\bpremier emploi\b'))
    if stage:
        kind = 'stage_pfe' if re.search(r'\bpfe\b|fin d.etudes|fin d.etude', text) else 'stage'
        confidence = 'élevée' if re.search(r'\bstage\b|\bintern(ship)?\b', title) or contract in ('stage','intern','internship') else 'à vérifier'
        evidence = 'motif de stage présent dans le titre, contrat ou description'
    elif employment:
        kind, confidence, evidence = 'emploi', 'élevée', 'type de contrat ou titre d’emploi explicite'
    else:
        kind, confidence, evidence = 'inconnu', 'incertaine', 'aucun indice explicite de stage ou d’emploi'
    subtype=('stage_pfe' if kind=='stage_pfe' else 'stage_initiation' if stage and re.search(r'initiation|observation|decouverte',text)
             else 'stage_technique' if stage and re.search(r'technique|technicien|engineering|developpement|developer|informatique',text)
             else 'stage_autre' if stage else None)
    if not stage and re.search(r'premier emploi|first job|junior|debutant',text):
        kind='premier_emploi';confidence='élevée';evidence='terme premier emploi, junior ou débutant présent dans le titre ou la description'
    internship_type = {'stage_pfe':'Stage PFE','stage_initiation':'Stage d’initiation','stage_technique':'Stage technique','stage_autre':'Stage'}.get(subtype)
    moroccan_cities={'marrakech','rabat','casablanca','fes','meknes','tanger','agadir','oujda','tetouan','kenitra','safi','el jadida','beni mellal','laayoune','dakhla'}
    is_morocco='maroc' in city or 'morocco' in city or any(re.search(rf'\b{re.escape(name)}\b',city) for name in moroccan_cities)
    location = 'Marrakech' if 'marrakech' in city else ('Maroc' if is_morocco else 'autre / inconnu')
    domain = next((name for patterns,name in [
        ((r'\bdata\b',r'\bscience des donnees\b',r'\bmachine learning\b',r'\bai\b',r'intelligence artificielle'),'data_science'),
        ((r'\bdeveloper\b',r'\bdeveloppeur\b',r'\bdevelopment\b',r'\bdeveloppement\b',r'\bsoftware\b'),'developpement'),
        ((r'\bpython\b',r'\bjava\b',r'\binformatique\b',r'\bcomputer science\b'),'informatique'),
        ((r'\bmarketing\b',r'\bdigital\b',r'\bseo\b'),'marketing')]
        if any(re.search(pattern, text) for pattern in patterns)), 'autre / inconnu')
    paid = True if re.search(r'remunere|remuneration|paid|salary|stipend', text) else False if re.search(r'non remunere|unpaid',text) else None
    return {'opportunity_type':kind,'internship_type_classified':internship_type,'internship_subtype':subtype,
            'classification_confidence':confidence,'classification_evidence':evidence,
            'location_group':location,'is_morocco':is_morocco,'domain_group':domain,'paid':paid}


def filter_offer(offer, *, location=None, kind=None, domain=None, paid=None, subtype=None):
    labels = classify_offer(offer)
    if location and (labels['location_group'] != location if location=='Marrakech' else not labels['is_morocco'] if location=='Maroc' else labels['location_group'] != location): return False
    if kind and labels['opportunity_type'] != kind: return False
    if domain and labels['domain_group'] != domain: return False
    if subtype and labels['internship_subtype'] != subtype:return False
    if paid is True and labels['paid'] is not True: return False
    return True
