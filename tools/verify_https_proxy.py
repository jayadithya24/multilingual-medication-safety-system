"""Local Caddy/TLS + two real Uvicorn processes + disposable real MongoDB test.

No mocks, public listener, system certificate installation or existing-data writes.
Requires a verified portable Caddy binary; see docs/HTTPS_PROXY_TEST.md.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time

import requests
from requests.adapters import HTTPAdapter
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.env_loader import load_project_env


class SourceAdapter(HTTPAdapter):
    def __init__(self, source):
        self.source = source
        super().__init__()

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source, 0)
        return super().init_poolmanager(*args, **kwargs)


def session(source, certificate):
    client = requests.Session()
    client.trust_env = False
    client.verify = str(certificate)
    adapter = SourceAdapter(source)
    client.mount('https://', adapter)
    client.mount('http://', adapter)
    return client


def certificate_files(directory):
    now = datetime.now(timezone.utc)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'MMSS loopback test only')])
    certificate = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),
            x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(key, hashes.SHA256()))
    cert_path, key_path = directory / 'certificate.pem', directory / 'private-key.pem'
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    return cert_path, key_path


def remove_test_database(mongo, database_name):
    if not database_name.startswith('mmss_proxy_probe_') or len(database_name.removeprefix('mmss_proxy_probe_')) != 16:
        raise RuntimeError('Refusing cleanup of a non-probe database.')
    try:
        mongo.drop_database(database_name)
        return {'disposable_database_removed': True, 'disposable_records_removed': True}
    except OperationFailure:
        # Some managed accounts permit data writes but not dropDatabase.
        # This database was proven empty before this run took ownership.
        db = mongo[database_name]
        for name in db.list_collection_names():
            if name.startswith('system.'):
                continue
            try:
                db.drop_collection(name)
            except OperationFailure:
                db[name].delete_many({})
                if db[name].count_documents({}) != 0:
                    raise RuntimeError('Disposable records could not be removed.')
        remaining = [n for n in db.list_collection_names() if not n.startswith('system.')]
        return {'disposable_database_removed': not remaining, 'disposable_records_removed': True,
                'remaining_empty_collections': remaining,
                'cleanup_note': 'dropDatabase unavailable; removed collections or emptied test records instead.'}


def run(caddy):
    load_project_env()
    run_id = secrets.token_hex(8)
    database_name = 'mmss_proxy_probe_' + run_id
    directory = ROOT / 'artifacts/proxy-test' / run_id
    directory.mkdir(parents=True)
    results = {'run_id': run_id, 'time_utc': datetime.now(timezone.utc).isoformat(),
               'mock_database': False, 'tls_verification': True, 'public_exposure': False,
               'checks': [], 'passed': False}
    processes, handles, clients = [], [], []
    mongo = None
    owns_database = False
    private_key = None
    try:
        if not caddy.is_file():
            raise RuntimeError('Caddy executable missing; see test plan.')
        for port in (18081, 18082, 18443):
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', port))  # Fail rather than replace an existing server.
        uri = os.environ.get('MONGO_URI') or os.environ.get('MONGODB_URI')
        if not uri:
            raise RuntimeError('Configured MongoDB URI required.')
        mongo = MongoClient(uri, serverSelectionTimeoutMS=10000)
        mongo.admin.command('ping')
        db = mongo[database_name]
        if db.list_collection_names():
            raise RuntimeError('Refusing to reuse an existing database.')
        owns_database = True
        cert, private_key = certificate_files(directory)
        base = 'https://127.0.0.1:18443'
        env = os.environ.copy()
        env.update(ENVIRONMENT='production', USE_MONGOMOCK='false', MONGO_DB=database_name,
                   BROWSER_ORIGINS=base, RATE_LIMIT_BACKEND='mongo', WARM_UP_OCR='false',
                   ENABLE_RESEARCH_ML_API='false', FIREBASE_SERVICE_ACCOUNT_FILE='',
                   FIREBASE_SERVICE_ACCOUNT_JSON='', GOOGLE_CLIENT_ID='')
        env.pop('PYTEST_CURRENT_TEST', None)
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        def start(command, name, child_env=env):
            output = (directory / (name + '.log')).open('w', encoding='utf-8')
            handles.append(output)
            process = subprocess.Popen(command, cwd=ROOT, env=child_env, stdout=output,
                                       stderr=subprocess.STDOUT, creationflags=creationflags)
            processes.append(process)

        for port in (18081, 18082):
            start([sys.executable, '-m', 'uvicorn', 'proxy_probe_app:app', '--app-dir', 'tests',
                   '--host', '127.0.0.1', '--port', str(port), '--proxy-headers',
                   '--forwarded-allow-ips', '127.0.0.1', '--no-access-log'], str(port))
        config = directory / 'Caddyfile'
        config.write_text('''{
    admin off
    auto_https off
    persist_config off
    storage file_system {
        root "%s"
    }
}
https://127.0.0.1:18443 {
    bind 127.0.0.1
    tls "%s" "%s"
    reverse_proxy 127.0.0.1:18081 127.0.0.1:18082 {
        lb_policy round_robin
        header_up X-Forwarded-For {http.request.remote.host}
        header_up X-Forwarded-Proto https
        header_up -Forwarded
    }
}
''' % ((directory / 'caddy-data').as_posix(), cert.as_posix(), private_key.as_posix()), encoding='utf-8')
        start([str(caddy), 'run', '--config', str(config), '--adapter', 'caddyfile'], 'caddy')
        first, second = session('127.0.0.2', cert), session('127.0.0.3', cert)
        clients.extend((first, second))
        deadline = time.monotonic() + 60
        workers = set()
        while time.monotonic() < deadline:
            if any(process.poll() is not None for process in processes):
                raise RuntimeError('A test server exited; inspect its local log.')
            try:
                response = first.get(base + '/__proxy_probe', timeout=2)
                if response.status_code == 200:
                    workers.add(response.json()['worker'])
                    if len(workers) == 2:
                        break
            except requests.RequestException:
                pass
            time.sleep(.5)
        assert len(workers) == 2, 'Both real backend processes must receive HTTPS traffic.'
        results['workers_seen'] = len(workers)
        spoof = {'X-Forwarded-For': '198.51.100.77', 'X-Forwarded-Proto': 'http',
                 'Forwarded': 'for=198.51.100.88;proto=http'}
        observed = first.get(base + '/__proxy_probe', headers=spoof, timeout=10).json()
        assert observed['client'] == '127.0.0.2' and observed['scheme'] == 'https', observed
        observed2 = second.get(base + '/__proxy_probe', timeout=10).json()
        assert observed2['client'] == '127.0.0.3'
        direct = first.get('http://127.0.0.1:18081/__proxy_probe',
                           headers={'X-Forwarded-For': '198.51.100.77', 'X-Forwarded-Proto': 'https'}, timeout=10).json()
        assert direct['client'] == '127.0.0.2' and direct['scheme'] == 'http'
        results['checks'].append('TLS verified; two source addresses preserved; spoofed forwarding headers replaced; direct untrusted forwarding ignored')

        from passlib.context import CryptContext
        password = secrets.token_urlsafe(24)
        username = 'proxy-' + run_id + '@example.invalid'
        db.users.insert_one({'username': username, 'email': username, 'role': 'patient',
                             'hashed_password': CryptContext(schemes=['bcrypt']).hash(password)})
        login = first.post(base + '/auth/session', data={'username': username, 'password': password},
                           headers={'Origin': base}, timeout=15)
        assert login.status_code == 200
        cookie = login.headers['Set-Cookie'].lower()
        assert 'secure' in cookie and 'httponly' in cookie and 'samesite=strict' in cookie
        for _ in range(4):
            assert first.get(base + '/auth/me', timeout=10).status_code == 200
        for headers in ({}, {'Origin': 'https://untrusted.invalid'}):
            assert first.post(base + '/auth/logout', headers=headers, timeout=10).status_code == 403
        assert first.post(base + '/auth/logout', headers={'Origin': base}, timeout=10).status_code == 200
        assert first.get(base + '/auth/me', timeout=10).status_code == 401
        results['checks'].append('Secure HttpOnly Strict cookies usable across workers; CSRF rejects missing/untrusted origins; logout revokes session')

        # Avoid crossing the limiter's fixed minute boundary during the small burst.
        if time.time() % 60 > 20:
            time.sleep(61 - time.time() % 60)
        counter_window = int(time.time()) // 60
        first.cookies.clear()
        for i in range(20):
            response = first.post(base + '/voice-search', headers={'X-Forwarded-For': f'198.51.100.{i}'}, timeout=15)
            assert response.status_code == 422, response.status_code  # Missing file; no Whisper computation.
        assert first.post(base + '/voice-search', headers=spoof, timeout=15).status_code == 429
        assert second.post(base + '/voice-search', timeout=15).status_code == 422
        assert int(time.time()) // 60 == counter_window, 'Burst crossed minute boundary; rerun to avoid ambiguous counts.'
        assert db.request_limits.count_documents({}) > 0
        results['checks'].append('Real MongoDB quotas shared across two workers; spoofing cannot reset quota; independent client retains quota')

        # Isolated test data only: start a separate case for the aggregate IP cap.
        db.request_limits.delete_many({})
        tokens = []
        now = datetime.now(timezone.utc)
        for i in range(4):
            account = f'quota-{i}-{run_id}@example.invalid'
            token = secrets.token_urlsafe(32)
            tokens.append(token)
            db.users.insert_one({'username': account, 'email': account, 'role': 'patient'})
            db.browser_sessions.insert_one({'username': account,
                'digest': hashlib.sha256(token.encode()).hexdigest(),
                'expires_at': now + timedelta(minutes=30),
                'absolute_expires_at': now + timedelta(hours=1)})
        if time.time() % 60 > 20:
            time.sleep(61 - time.time() % 60)
        counter_window = int(time.time()) // 60
        for i in range(60):
            headers = {'Cookie': 'mmss_session=' + tokens[i % 3],
                       'X-Forwarded-For': f'198.51.100.{i}'}
            assert first.post(base + '/voice-search', headers=headers, timeout=15).status_code == 422
        fresh_account = {'Cookie': 'mmss_session=' + tokens[3]}
        assert first.post(base + '/voice-search', headers=fresh_account, timeout=15).status_code == 429
        assert second.post(base + '/voice-search', headers=fresh_account, timeout=15).status_code == 422
        assert int(time.time()) // 60 == counter_window, 'Aggregate burst crossed minute boundary; rerun.'
        results['checks'].append('60/minute heavy IP ceiling aggregates three signed-in accounts across workers; a fourth cannot reset it; second source remains independent')
        results['passed'] = True
    except Exception as error:
        results['error_type'] = type(error).__name__
        results['error'] = str(error) if isinstance(error, (AssertionError, RuntimeError)) else 'See local server logs; no request credentials recorded.'
        raise
    finally:
        for client in clients:
            client.close()
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
        for handle in handles:
            handle.close()
        if mongo is not None:
            try:
                if owns_database and database_name == 'mmss_proxy_probe_' + run_id:
                    results.update(remove_test_database(mongo, database_name))
            except Exception as error:
                results['disposable_database_removed'] = False
                results['cleanup_error_type'] = type(error).__name__
                results['passed'] = False
            finally:
                mongo.close()
        if private_key is not None and private_key.exists():
            private_key.unlink()
        results['temporary_private_key_removed'] = private_key is None or not private_key.exists()
        results['servers_stopped'] = all(p.poll() is not None for p in processes)
        (directory / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
        print(json.dumps(results, indent=2))
        print('Results:', directory / 'results.json')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--caddy', type=Path, default=ROOT / 'artifacts/proxy-test/bin/caddy.exe')
    outcome = run(parser.parse_args().caddy.resolve())
    raise SystemExit(0 if outcome['passed'] else 1)
