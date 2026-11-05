"""Validate browser origins before the application can accept requests."""
import os
from urllib.parse import urlsplit


def browser_origins():
    production = os.getenv('ENVIRONMENT', '').strip().lower() == 'production'
    raw = os.getenv('BROWSER_ORIGINS', '')
    if not raw.strip() and not production:
        raw = ','.join(f'http://{host}:{port}' for host in ('localhost', '127.0.0.1')
                       for port in (5173, 5174, 5175, 8000))
    origins = tuple(item.strip() for item in raw.split(',') if item.strip())
    if production and not origins:
        raise RuntimeError('Production requires explicit HTTPS BROWSER_ORIGINS.')
    for origin in origins:
        parsed = urlsplit(origin)
        if (parsed.scheme not in (('https',) if production else ('http', 'https'))
                or not parsed.hostname or parsed.username or parsed.password
                or parsed.path or parsed.query or parsed.fragment or '*' in origin):
            raise RuntimeError('BROWSER_ORIGINS must contain exact origins without paths; production requires HTTPS.')
        try:
            parsed.port
        except ValueError as error:
            raise RuntimeError('Invalid BROWSER_ORIGINS port.') from error
    return origins
