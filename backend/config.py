import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def settings(overrides=None):
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env', override=False)
    values = dict(
        ROOT=ROOT, DATABASE=os.getenv('DATABASE', str(ROOT / 'database/stages_marrakech.db')),
        PRIVATE_DIR=os.getenv('PRIVATE_DIR', str(ROOT / 'private')), BACKUP_DIR=os.getenv('BACKUP_DIR', str(ROOT / 'backups')),
        TRUSTED_HOSTS=[x.strip() for x in os.getenv('TRUSTED_HOSTS','127.0.0.1,localhost,[::1]').split(',') if x.strip()],
        PUBLIC_DEMO_MODE=os.getenv('PUBLIC_DEMO_MODE','false').lower()=='true',
        PUBLIC_DEMO_DATA_CONFIRMED=os.getenv('PUBLIC_DEMO_DATA_CONFIRMED','false').lower()=='true',
        TRUST_PROXY=os.getenv('TRUST_PROXY','false').lower()=='true',
        MAX_CONTENT_LENGTH=6 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict',
        SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE', 'false').lower() == 'true',
        SMTP_ENABLED=os.getenv('SMTP_ENABLED', 'false').lower() == 'true',
        SMTP_HOST=os.getenv('SMTP_HOST', 'smtp.gmail.com'), SMTP_PORT=int(os.getenv('SMTP_PORT', '587')),
        SMTP_USER=os.getenv('SMTP_USER', ''), SMTP_PASSWORD=os.getenv('SMTP_PASSWORD', ''),
        GEMINI_ENABLED=os.getenv('GEMINI_ENABLED', 'false').lower() == 'true',
        GEMINI_API_KEY=os.getenv('GEMINI_API_KEY', ''), GEMINI_MODEL=os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite'),
        GEMINI_FREE_TIER_CONFIRMED=os.getenv('GEMINI_FREE_TIER_CONFIRMED', 'false').lower() == 'true',
        GEMINI_SEARCH_ENABLED=os.getenv('GEMINI_SEARCH_ENABLED', 'false').lower() == 'true',
        GEMINI_SEARCH_MODEL=os.getenv('GEMINI_SEARCH_MODEL', 'gemini-3.8-flash'),
        GEMINI_SEARCH_BILLING_CONFIRMED=os.getenv('GEMINI_SEARCH_BILLING_CONFIRMED', 'false').lower() == 'true',
        GEMINI_SEARCH_MAX_SESSION=int(os.getenv('GEMINI_SEARCH_MAX_SESSION', '2')),
        GEMINI_SEARCH_MAX_DAILY=int(os.getenv('GEMINI_SEARCH_MAX_DAILY', '5')),
        GEMINI_SEARCH_COOLDOWN_SECONDS=int(os.getenv('GEMINI_SEARCH_COOLDOWN_SECONDS', '60')),
        GEMINI_SEARCH_TIMEOUT_MS=int(os.getenv('GEMINI_SEARCH_TIMEOUT_MS', '30000')),
        MAPS_ENABLED=os.getenv('MAPS_ENABLED', 'false').lower() == 'true', MAPS_BROWSER_KEY=os.getenv('MAPS_BROWSER_KEY', ''),
        MATCH_WEIGHTS={'skills': 40, 'education': 25, 'experience': 15, 'location': 10, 'opportunity': 10},
        TESTING=False,
    )
    if overrides:
        values.update(overrides)
    for key in ('DATABASE', 'PRIVATE_DIR', 'BACKUP_DIR'):
        path = Path(values[key]).expanduser()
        values[key] = str(path.resolve() if path.is_absolute() else (ROOT / path).resolve())
    return values
