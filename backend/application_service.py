"""Candidatures et SMTP : confirmation, provenance et idempotence persistante."""
import hashlib
import json
import smtplib
import ssl
from datetime import date
from email.message import EmailMessage
from .db import connect, now
from .validation import email, text, safe_url


def insert_candidature(db, data):
    values = dict(data, created_at=now(), updated_at=now())
    keys = list(values)
    cursor = db.execute(f"INSERT INTO candidatures ({','.join(keys)}) VALUES ({','.join('?' for _ in keys)})", tuple(values[k] for k in keys))
    ident = cursor.lastrowid
    db.execute('INSERT INTO candidature_history(candidature_id,old_status,new_status,changed_at) VALUES (?,?,?,?)',
               (ident, None, values.get('statut', 'Non envoyée'), now()))
    return ident


def resolve_channel(offer, company=None):
    if (offer.get('email_verified') == 1 and offer.get('relation_verified') == 1 and company
            and offer.get('entreprise_ref') == company.get('id')):
        try:
            target = email(offer.get('recruitment_email', ''))
            known = [e.strip().lower() for e in (company.get('Emails') or '').split(',')]
            if target in known:
                return {'type': 'smtp', 'email': target, 'label': 'Contact vérifié lié à cette entreprise'}
        except ValueError:
            pass
    link = safe_url(offer.get('Lien public')) or safe_url(offer.get('Lien annonce'))
    if link:
        return {'type': 'external', 'url': link, 'label': 'Candidature sur le site source'}
    return {'type': 'unavailable', 'label': 'Coordonnées de candidature indisponibles'}


def send_cv(config, content, recipient, subject, message, application, key):
    if not config['SMTP_ENABLED']:
        raise ValueError('SMTP désactivé. Activez-le manuellement après vérification de votre configuration.')
    if not config['SMTP_USER'] or not config['SMTP_PASSWORD']:
        raise ValueError('Configuration SMTP incomplète.')
    recipient = email(recipient)
    subject = text(subject, 200)
    message = text(message, 10000)
    if not subject or not message or '\n' in subject or '\r' in subject:
        raise ValueError('Sujet et message valides obligatoires.')
    if not isinstance(key, str) or not 16 <= len(key) <= 100:
        raise ValueError('Identifiant unique d’envoi obligatoire.')
    digest = hashlib.sha256(json.dumps([recipient, subject, message, application], sort_keys=True).encode()+content).hexdigest()
    with connect(config['DATABASE']) as db:
        db.execute('BEGIN IMMEDIATE')
        existing = db.execute('SELECT * FROM send_attempts WHERE idempotency_key=?', (key,)).fetchone()
        if existing:
            if existing['payload_hash'] != digest:
                raise ValueError('Cet identifiant correspond à un autre envoi.')
            return {'status': existing['status'], 'id': existing['candidature_id'], 'duplicate': True}
        db.execute('INSERT INTO send_attempts(idempotency_key,payload_hash,status,created_at) VALUES (?,?,?,?)',
                   (key, digest, 'pending', now()))
    mail = EmailMessage()
    mail['From'] = config['SMTP_USER']
    mail['To'] = recipient
    mail['Subject'] = subject
    mail.set_content(message)
    mail.add_attachment(content, maintype='application', subtype='pdf', filename='CV.pdf')
    try:
        with smtplib.SMTP(config['SMTP_HOST'], config['SMTP_PORT'], timeout=20) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(config['SMTP_USER'], config['SMTP_PASSWORD'])
            refused = server.send_message(mail)
            if refused:
                raise RuntimeError('SMTP_RECIPIENT_REFUSED')
        with connect(config['DATABASE']) as db:
            ident = insert_candidature(db, {**application, 'email': recipient, 'email_validated': 1, 'statut': 'Envoyée',
                                           'date_candidature': date.today().isoformat(), 'canal': 'smtp'})
            db.execute('UPDATE send_attempts SET status=?,candidature_id=? WHERE idempotency_key=?', ('sent', ident, key))
        return {'status': 'sent', 'id': ident, 'duplicate': False}
    except Exception:
        # Même en cas d’échec réseau, un serveur peut avoir accepté le message.
        # Aucune répétition automatique : l’utilisateur doit vérifier sa boîte d’envoi.
        with connect(config['DATABASE']) as db:
            db.execute('UPDATE send_attempts SET status=?,error_code=? WHERE idempotency_key=?',
                       ('uncertain', 'DELIVERY_OR_SAVE_UNCERTAIN', key))
        return {'status': 'uncertain', 'id': None, 'duplicate': False,
                'message': 'Envoi ou enregistrement incertain. Vérifiez la boîte d’envoi avant toute nouvelle tentative.'}
