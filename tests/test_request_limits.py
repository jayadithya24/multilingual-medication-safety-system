from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from backend.app.request_limits import RequestLimits
import pytest


def client():
    app = FastAPI()
    app.add_middleware(RequestLimits)
    @app.api_route('/voice-search', methods=['GET', 'POST'])
    async def voice(request: Request):
        return {'bytes': len(await request.body())}
    @app.get('/interaction')
    def interaction():
        return {'ok': True}
    return TestClient(app)


def test_public_compute_limit_cannot_be_bypassed_by_forwarded_ip():
    browser = client()
    for i in range(20):
        assert browser.get('/voice-search', headers={'X-Forwarded-For': str(i)}).status_code == 200
    response = browser.get('/voice-search')
    assert response.status_code == 429 and response.headers['retry-after']


def test_large_declared_or_streamed_upload_rejected_before_handler():
    browser = client()
    assert browser.post('/voice-search', content=b'x', headers={'Content-Length': str(11*1024*1024)}).status_code == 413
    def chunks():
        for _ in range(11):
            yield b'x' * 1024 * 1024
    assert browser.post('/voice-search', content=chunks()).status_code == 413
    assert browser.post('/voice-search', content=b'abc').json()['bytes'] == 3


def test_analysis_request_limit():
    browser = client()
    for _ in range(300):
        assert browser.get('/interaction').status_code == 200
    assert browser.get('/interaction').status_code == 429


@pytest.mark.parametrize('path,limit', [('/upload-image', 20), ('/prescription-ocr', 20),
    ('/voice-search', 20), ('/interaction', 300), ('/interaction/multi', 300), ('/auth/session', 60),
    ('/neo4j/graph', 300), ('/medicine/search', 300), ('/medicines', 300), ('/health', 300)])
def test_each_public_entrypoint_is_throttled_before_work(path, limit):
    app = FastAPI()
    app.add_middleware(RequestLimits)
    @app.post(path)
    def work():
        return {'ok': True}
    browser = TestClient(app)
    for _ in range(limit):
        assert browser.post(path).status_code == 200
    assert browser.post(path).status_code == 429


def test_mongo_limit_is_shared_across_workers(monkeypatch):
    import mongomock
    from backend.app import database
    monkeypatch.setattr(database, 'db', mongomock.MongoClient().db)
    monkeypatch.setenv('RATE_LIMIT_BACKEND', 'mongo')
    first, second = client(), client()
    for _ in range(10):
        assert first.get('/voice-search').status_code == 200
        assert second.get('/voice-search').status_code == 200
    assert first.get('/voice-search').status_code == 429
    assert second.get('/voice-search').status_code == 429


def test_cors_only_allows_explicit_local_origins():
    from backend.main import app
    browser = TestClient(app)
    for origin, expected in [('http://localhost:5173', 200), ('http://localhost:9999', 400), ('https://untrusted.example', 400)]:
        response = browser.options('/interaction', headers={'Origin': origin, 'Access-Control-Request-Method': 'GET'})
        assert response.status_code == expected
        if expected == 200:
            assert response.headers['access-control-allow-origin'] == origin
            assert response.headers['access-control-allow-credentials'] == 'true'
