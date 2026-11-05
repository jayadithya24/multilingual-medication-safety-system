"""Read-only deployment gate. Run before starting any public backend process."""
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check():
    from backend.app.origin_config import browser_origins
    errors = []
    if os.getenv('ENVIRONMENT', '').strip().lower() != 'production':
        errors.append('ENVIRONMENT must be explicitly set to production.')
    try:
        origins = browser_origins()
        if not origins or any(not value.startswith('https://') for value in origins):
            errors.append('Explicit HTTPS BROWSER_ORIGINS are required.')
    except (ValueError, RuntimeError):
        errors.append('BROWSER_ORIGINS is missing or invalid for production.')
    if os.getenv('USE_MONGOMOCK', '').lower() in ('true', '1', 'yes'):
        errors.append('USE_MONGOMOCK must be disabled.')
    if not (os.getenv('MONGO_URI', '') or os.getenv('MONGODB_URI', '')).strip():
        errors.append('MONGO_URI must be configured through deployment secrets.')
    if os.getenv('ENABLE_RESEARCH_ML_API', '').lower() == 'true':
        errors.append('Research ML APIs must remain disabled.')
    trusted = os.getenv('FORWARDED_ALLOW_IPS', '').strip()
    if not trusted or '*' in trusted or any(not x.strip() for x in trusted.split(',')):
        errors.append('FORWARDED_ALLOW_IPS must explicitly name trusted proxies; wildcard/empty values are forbidden.')
    try:
        uri = urlsplit(os.getenv('MONGO_URI') or os.getenv('MONGODB_URI', ''))
        options = {k.lower(): v[-1].lower() for k, v in parse_qs(uri.query).items()}
        if not uri.username or not uri.password:
            errors.append('MongoDB requires credentials in the deployment URI.')
        tls = options.get('tls', options.get('ssl', 'true' if uri.scheme == 'mongodb+srv' else 'false'))
        if tls != 'true' or any(options.get(k) == 'true' for k in ('tlsinsecure', 'tlsallowinvalidcertificates', 'tlsallowinvalidhostnames')):
            errors.append('MongoDB requires TLS with certificate and hostname verification.')
    except ValueError:
        errors.append('MongoDB URI is invalid.')
    return errors


if __name__ == '__main__':
    from backend.env_loader import load_project_env
    load_project_env()
    problems = check()
    for problem in problems:
        print('FAIL:', problem)
    if problems:
        raise SystemExit(1)
    print('Configuration preflight passed. Verify actual HTTPS proxy, backups and account-security prerequisites separately.')
