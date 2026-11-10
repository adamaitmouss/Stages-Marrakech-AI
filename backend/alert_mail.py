"""Envoi facultatif d’alertes email, protégé par consentement et SMTP explicite."""
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from flask import current_app
from .db import connect, now


def _send_queued(path, force=False):
    config=current_app.config
    if not config.get('SMTP_ENABLED') or not config.get('SMTP_USER') or not config.get('SMTP_PASSWORD'):
        return
    vault=current_app.extensions['vault']
    with connect(path) as db:
        prefs=db.execute('SELECT email_enabled,email_payload,email_next_at,frequency FROM alert_preferences WHERE id=1').fetchone()
        if not prefs or not prefs['email_enabled'] or not prefs['email_payload']:return
        due=prefs['email_next_at']
        if not force and due and datetime.fromisoformat(due)>datetime.now(timezone.utc):return
        logs=db.execute("SELECT alert_id FROM alert_email_log WHERE status='queued' ORDER BY alert_id").fetchall()
        if not logs:return
        alert_ids=[r['alert_id'] for r in logs]
        placeholders=','.join('?' for _ in alert_ids)
        offers=db.execute(f'''SELECT a.id,a.score,a.explanation,o."Titre" AS title,o.entreprise_nom AS company,
            o.ville AS city,o.source,o."Date publication" AS published,o."Lien public" AS url
            FROM alerts a JOIN offres o ON o."ID"=a.offer_id WHERE a.id IN ({placeholders}) ORDER BY a.id''',alert_ids).fetchall()
        recipient=vault.decrypt(prefs['email_payload']).get('email','')
        db.executemany("UPDATE alert_email_log SET status='pending',attempted_at=? WHERE alert_id=? AND status='queued'",
                       [(now(),ident) for ident in alert_ids])
        db.execute('UPDATE alert_preferences SET email_next_at=NULL WHERE id=1')
    if not offers:return
    mail=EmailMessage();mail['From']=config['SMTP_USER'];mail['To']=recipient
    mail['Subject']=('Nouvelle offre' if len(offers)==1 else f'{len(offers)} nouvelles offres')+' correspondant à vos alertes'
    sections=[]
    for row in offers:
        sections.append('\n'.join([row['title'],f"Entreprise : {row['company'] or 'non renseignée'}",f"Ville : {row['city'] or 'non renseignée'}",
            f"Source : {row['source'] or 'non renseignée'}",f"Publication : {row['published'] or 'date inconnue'}",
            f"Score : {row['score']}/100",row['explanation'],f"Lien : {row['url'] or 'non disponible'}"]))
    mail.set_content('\n\n---\n\n'.join(sections))
    try:
        with smtplib.SMTP(config['SMTP_HOST'],config['SMTP_PORT'],timeout=20) as server:
            server.starttls(context=ssl.create_default_context());server.login(config['SMTP_USER'],config['SMTP_PASSWORD'])
            refused=server.send_message(mail)
            if refused:raise RuntimeError('destinataire refusé')
        status='sent';error=None
    except Exception as exc:
        status='uncertain';error=type(exc).__name__
    with connect(path) as db:
        db.executemany('UPDATE alert_email_log SET status=?,attempted_at=?,error_summary=? WHERE alert_id=?',
                       [(status,now(),error,ident) for ident in alert_ids])
        prefs=db.execute('SELECT email_enabled,frequency FROM alert_preferences WHERE id=1').fetchone()
        if prefs and prefs['email_enabled'] and status=='sent' and prefs['frequency'] in ('daily','weekly'):
            next_at=datetime.now(timezone.utc)+timedelta(days=7 if prefs['frequency']=='weekly' else 1)
            db.execute('UPDATE alert_preferences SET email_next_at=? WHERE id=1',(next_at.isoformat(timespec='seconds'),))


def deliver_new_alerts(path, alert_ids):
    with connect(path) as db:
        prefs=db.execute('SELECT email_enabled,frequency,email_next_at FROM alert_preferences WHERE id=1').fetchone()
        if not prefs or not prefs['email_enabled']:return
        for alert_id in alert_ids:
            db.execute("INSERT OR IGNORE INTO alert_email_log(alert_id,status,attempted_at) VALUES (?,'queued',?)",(alert_id,now()))
        if prefs['frequency'] in ('daily','weekly') and not prefs['email_next_at']:
            due=datetime.now(timezone.utc)+timedelta(days=7 if prefs['frequency']=='weekly' else 1)
            db.execute('UPDATE alert_preferences SET email_next_at=? WHERE id=1',(due.isoformat(timespec='seconds'),))
    if prefs['frequency']=='instant':_send_queued(path,force=True)


def deliver_due_alert_emails(path):
    _send_queued(path)
