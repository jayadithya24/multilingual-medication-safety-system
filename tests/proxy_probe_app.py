"""Test-only observation route; never imported by the normal server entrypoint."""
import os

if not os.getenv('MONGO_DB', '').startswith('mmss_proxy_probe_'):
    raise RuntimeError('Proxy probe requires its own disposable database.')

from fastapi import Request
from backend.main import app


@app.get('/__proxy_probe')
def proxy_probe(request: Request):
    return {'client': request.client.host, 'scheme': request.url.scheme,
            'worker': os.getpid()}
