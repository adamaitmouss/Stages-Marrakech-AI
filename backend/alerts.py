"""Préférences et alertes d'offres explicables, dédupliquées et locales."""
import json
from datetime import date
from .matching import norm, skills_from
from .db import now


def preferences(db):
    row=db.execute('SELECT * FROM alert_preferences WHERE id=1').fetchone()
    value=dict(row) if row else {'domain':'','skills_json':'[]','city':'Marrakech','internship_type':'','contract_type':'','minimum_score':50,'frequency':'instant','enabled':0,'email_enabled':0,'updated_at':None}
    value['skills']=json.loads(value.pop('skills_json','[]'))
    return value


def validate_preferences(data):
    if not isinstance(data,dict):raise ValueError('Préférences d’alertes invalides.')
    skills=data.get('skills',[])
    if not isinstance(skills,list) or len(skills)>50 or any(not isinstance(s,str) or len(s.strip())>80 for s in skills):raise ValueError('Liste de compétences invalide.')
    score=data.get('minimum_score',50)
    if type(score) is not int or not 0<=score<=100:raise ValueError('Le score minimal doit être compris entre 0 et 100.')
    frequency=data.get('frequency','instant')
    if frequency not in ('instant','daily','weekly'):raise ValueError('Fréquence invalide.')
    return {'domain':str(data.get('domain','')).strip()[:120],'skills':list(dict.fromkeys(s.strip() for s in skills if s.strip())),
            'city':str(data.get('city','')).strip()[:100],'internship_type':str(data.get('internship_type','')).strip()[:100],
            'contract_type':str(data.get('contract_type','')).strip()[:100],'minimum_score':score,'frequency':frequency,
            'enabled':bool(data.get('enabled',False)),'email_enabled':bool(data.get('email_enabled',False))}


def score_offer(offer,prefs):
    if not prefs['enabled']:return None
    exp=str(offer.get('Date expiration') or '')[:10]
    try:
        if date.fromisoformat(exp)<date.today():return None
    except ValueError:pass
    text=' '.join(str(offer.get(k) or '') for k in ('Titre','Description','entreprise_nom','ville','competences'))
    normalized=norm(text)
    if prefs['city'] and offer.get('ville') and norm(prefs['city']) not in norm(offer['ville']):return None
    if prefs['contract_type'] and offer.get('Type contrat') and norm(prefs['contract_type']) not in norm(offer['Type contrat']):return None
    if prefs['internship_type'] and offer.get('Type stage') and norm(prefs['internship_type']) not in norm(offer['Type stage']):return None
    skills=prefs['skills'];matched=[s for s in skills if norm(s) in normalized or norm(s) in [norm(x) for x in skills_from(text)]]
    requirements=skills_from(text)
    if prefs['domain']:
        domain_match=norm(prefs['domain']) in normalized
    else:domain_match=0
    city_match=bool(prefs['city'] and offer.get('ville') and norm(prefs['city']) in norm(offer['ville']))
    if skills:
        skill_score=len(matched)/len(skills)
        score=round(skill_score*65+bool(domain_match)*20+bool(city_match)*15,1)
    else:
        score=round(bool(domain_match)*70+bool(city_match)*30,1)
    if score<prefs['minimum_score']:return None
    parts=[]
    if matched:parts.append('Compétences concordantes : '+', '.join(matched))
    if domain_match:parts.append('Domaine présent dans l’annonce')
    if city_match:parts.append('Ville concordante : '+str(offer.get('ville')))
    if not requirements and not skills:parts.append('Aucune compétence explicite détectée dans l’annonce; score limité au domaine et à la ville')
    return {'score':score,'explanation':'; '.join(parts) or 'Score calculé à partir du domaine, de la ville et des champs présents.', 'matched':matched}


def maybe_create_alert(db,offer_id):
    prefs=preferences(db)
    offer=db.execute('SELECT * FROM offres WHERE "ID"=?',(offer_id,)).fetchone()
    if not offer:return None
    result=score_offer(dict(offer),prefs)
    if not result:return None
    db.execute('INSERT OR IGNORE INTO alerts(offer_id,created_at,score,explanation) VALUES (?,?,?,?)',
               (offer_id,now(),result['score'],result['explanation']))
    return result
