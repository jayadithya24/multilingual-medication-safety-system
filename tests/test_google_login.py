import mongomock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.app.routes import auth
from backend.app import auth as auth_core
from backend.app.services import google_auth_service


@pytest.fixture
def client(monkeypatch):
    collection = mongomock.MongoClient().meds.users
    collection.create_index('username', unique=True)
    collection.create_index('google_sub', unique=True, sparse=True)
    monkeypatch.setattr(auth, 'users_collection', collection)
    monkeypatch.setattr(auth_core, 'users_collection', collection)
    monkeypatch.setattr(auth, 'verify_google_credential', lambda token: {
        'sub': 'google-test-id', 'email': 'test@example.invalid', 'name': 'Google Test',
    })
    app = FastAPI()
    app.include_router(auth.router)
    return TestClient(app), collection


def login(client):
    return client.post('/auth/google', json={'credential': 'test-credential-for-unit-test', 'mode': 'register'})


def test_google_login_requires_registration(client):
    browser, users = client
    response = browser.post('/auth/google', json={'credential': 'test-credential-for-unit-test', 'mode': 'login'})
    assert response.status_code == 401
    assert users.count_documents({}) == 0


def test_patient_password_login_requires_mongo_registration(client):
    browser, users = client
    for username in ('unknown@example.invalid', 'patient', 'doctor'):
        response = browser.post('/auth/patient-token', data={'username': username, 'password': 'test-password'})
        assert response.status_code == 401
    users.insert_one({'username': 'registered@example.invalid', 'role': 'patient', 'hashed_password': auth.get_password_hash('test-password')})
    assert browser.post('/auth/patient-token', data={'username': 'registered@example.invalid', 'password': 'wrong'}).status_code == 401
    assert browser.post('/auth/patient-token', data={'username': 'registered@example.invalid', 'password': 'test-password'}).status_code == 200


def test_google_creates_and_reuses_patient(client):
    browser, users = client
    first = login(browser)
    assert first.status_code == 200
    assert first.json()['role'] == 'patient'
    assert login(browser).status_code == 200
    assert users.count_documents({}) == 1
    user = users.find_one()
    assert user['google_sub'] == 'google-test-id'
    assert 'hashed_password' not in user


def test_google_does_not_take_over_password_account(client):
    browser, users = client
    users.insert_one({'username': 'test@example.invalid', 'role': 'patient', 'hashed_password': 'existing'})
    assert login(browser).status_code == 409
    assert 'google_sub' not in users.find_one()


def test_google_links_only_after_correct_password(client):
    browser, users = client
    users.insert_one({'username': 'test@example.invalid', 'role': 'patient', 'patient_id': 'P001', 'age': 50, 'hashed_password': auth.get_password_hash('existing-password')})
    payload = {'credential': 'test-credential-for-unit-test', 'mode': 'login'}
    assert browser.post('/auth/google', json=payload).json()['detail']['code'] == 'google_link_required'
    assert browser.post('/auth/google', json={**payload, 'password': 'wrong-password'}).status_code == 401
    assert 'google_sub' not in users.find_one()
    assert browser.post('/auth/google', json={**payload, 'password': 'existing-password'}).status_code == 200
    assert users.count_documents({}) == 1
    assert users.find_one()['patient_id'] == 'P001'
    assert users.find_one()['age'] == 50
    assert browser.post('/auth/google', json=payload).status_code == 200


@pytest.mark.parametrize('fields', [{'disabled': True, 'role': 'patient'}, {'role': 'doctor'}])
def test_google_rejects_disabled_or_nonpatient(client, fields):
    browser, users = client
    users.insert_one({'username': 'test@example.invalid', 'google_sub': 'google-test-id', **fields})
    assert login(browser).status_code == 403


def test_google_requires_configuration(monkeypatch):
    monkeypatch.delenv('GOOGLE_CLIENT_ID', raising=False)
    with pytest.raises(Exception) as failure:
        google_auth_service.verify_google_credential('invalid')
    assert failure.value.status_code == 503


@pytest.mark.parametrize('change', [{'aud': 'wrong'}, {'email_verified': False}, {'iss': 'untrusted'}, {'sub': ''}])
def test_google_rejects_untrusted_claims(monkeypatch, change):
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'expected-client')
    claims = {'aud': 'expected-client', 'iss': 'https://accounts.google.com', 'sub': 'id', 'email': 'test@example.invalid', 'email_verified': True, **change}
    monkeypatch.setattr(google_auth_service.id_token, 'verify_oauth2_token', lambda *args: claims)
    with pytest.raises(Exception) as failure:
        google_auth_service.verify_google_credential('invalid')
    assert failure.value.status_code == 401


def test_google_rejects_invalid_signature(monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'expected-client')
    def invalid(*args):
        raise ValueError('invalid signature or expired token')
    monkeypatch.setattr(google_auth_service.id_token, 'verify_oauth2_token', invalid)
    with pytest.raises(Exception) as failure:
        google_auth_service.verify_google_credential('invalid')
    assert failure.value.status_code == 401
