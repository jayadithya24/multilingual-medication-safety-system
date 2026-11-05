"""Create isolated demo identities; credentials stay in ignored local artifacts.

The doctor remains pending so the live walkthrough includes admin approval.
Never resets existing accounts. Cleanup is restricted to this manifest's run.
"""
import argparse
import json
import secrets
import sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.database import db
from backend.app.auth import get_password_hash

MANIFEST = ROOT / 'artifacts' / 'demo-accounts.json'
BASE = 'http://127.0.0.1:8000'


def cleanup():
    if not MANIFEST.exists():
        print('No demo manifest; nothing removed.')
        return
    data = json.loads(MANIFEST.read_text())
    run = data['run_id']
    accounts = [item['username'] for item in data['accounts'].values()]
    owned = list(db.users.find({'username': {'$in': accounts}, 'demo_run': run}))
    # An approved doctor inherits no marker from the normal approval flow.
    doctor = data['accounts']['doctor']['username']
    request = db.doctor_requests.find_one({'email': doctor, 'demo_run': run})
    if request:
        user = db.users.find_one({'username': doctor, 'license_number': 'DEMO-' + run})
        if user:
            owned.append(user)
    for user in owned:
        username = user['username']
        for name in ('browser_sessions',):
            db[name].delete_many({'username': username})
        for name in ('patient_schedules', 'medication_history', 'fcm_tokens', 'reminder_deliveries'):
            db[name].delete_many({'patient_username': username})
        if user.get('patient_id'):
            for name in ('access_requests', 'share_codes', 'access_log'):
                db[name].delete_many({'patientId': user['patient_id']})
        db.consent_attempts.delete_many({'doctorId': username})
        db.users.delete_one({'_id': user['_id']})
    db.doctor_requests.delete_many({'email': doctor, 'demo_run': run})
    MANIFEST.unlink()
    print('Removed only the manifest-owned demo records and local credentials.')


def create():
    if MANIFEST.exists():
        raise SystemExit('Demo manifest already exists. Reuse it or run --cleanup first; no account was reset.')
    run = secrets.token_hex(8)
    accounts = {role: {'username': f'demo-{role}-{run}@example.invalid', 'password': secrets.token_urlsafe(24)}
                for role in ('patient', 'doctor', 'admin')}
    MANIFEST.parent.mkdir(exist_ok=True)
    # Exclusive create prevents accidental replacement and supports cleanup after partial failure.
    with MANIFEST.open('x', encoding='utf-8') as stream:
        json.dump({'run_id': run, 'accounts': accounts, 'doctor_status': 'pending'}, stream, indent=2)

    client = requests.Session()
    client.headers.update({"Origin": "http://localhost:5173"})

    def post(path, **kwargs):
        response = client.post(BASE + path, timeout=30, **kwargs)
        if response.status_code != 200:
            raise RuntimeError(f'Demo setup failed at {path} (HTTP {response.status_code}); no credentials printed.')
        return response.json()

    admin = accounts['admin']
    db.users.insert_one({'username': admin['username'], 'email': admin['username'], 'role': 'admin',
        'full_name': 'Demo Administrator', 'hashed_password': get_password_hash(admin['password']), 'demo_run': run})
    patient = accounts['patient']
    post('/auth/register-session', json={'name': 'Demo Patient — fictional', 'email': patient['username'],
        'password': patient['password'], 'confirm_password': patient['password']})
    db.users.update_one({'username': patient['username']}, {'$set': {'demo_run': run}})
    doctor = accounts['doctor']
    post('/auth/doctor-request', json={'name': 'Demo Doctor — fictional', 'email': doctor['username'],
        'doctor_id': 'DEMO-' + run, 'specialization': 'Demonstration only',
        'password': doctor['password'], 'confirm_password': doctor['password']})
    db.doctor_requests.update_one({'email': doctor['username']}, {'$set': {'demo_run': run}})
    post('/auth/session', data=patient)
    headers = {}
    for medicine in ('Metformin', 'Ibuprofen', 'Methotrexate', 'Unlisted demo medicine'):
        post('/patient-schedule', headers=headers, json={'medicine_name': medicine,
             'dosage': 'DEMO ONLY — not a prescription', 'frequency': 'Daily',
             'scheduled_times': ['09:00'], 'reminder_enabled': False})
    print('Created fictional patient, pending doctor and administrator. Reminders are disabled.')
    print('Private credentials: artifacts/demo-accounts.json (ignored by Git; do not share or screen-project).')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cleanup', action='store_true')
    args = parser.parse_args()
    cleanup() if args.cleanup else create()
