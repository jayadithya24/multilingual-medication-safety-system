"""Real HTTP + browser acceptance check with disposable MongoDB accounts.

Run manually with both servers running; not part of pytest/mongomock tests.
Seeds only a temporary admin (there is no public admin registration), then uses
real registration, password login and UI consent/report actions. No API stubs.
Deletes only this run's uniquely identified test records in finally.
"""
import json
import secrets
import sys
import time
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.database import db, USE_MONGOMOCK
from backend.app.auth import get_password_hash


def main(record=False):
    assert not USE_MONGOMOCK, 'This acceptance test requires real MongoDB.'
    suffix = secrets.token_hex(8)
    patient = f'acceptance-patient-{suffix}@example.invalid'
    doctor = f'acceptance-doctor-{suffix}@example.invalid'
    admin = f'acceptance-admin-{suffix}@example.invalid'
    password = secrets.token_urlsafe(24)
    base = 'http://127.0.0.1:8000'
    ui = 'http://localhost:5173'
    results = {'database': 'real configured MongoDB', 'api_stubs': False,
               'time_utc': datetime.now(timezone.utc).isoformat(), 'checks': [], 'passed': False}
    patient_id = None
    video_dir = ROOT / 'artifacts' / 'demo-video'
    video_dir.mkdir(parents=True, exist_ok=True)
    timeline = []
    started = time.monotonic()

    def show(role):
        if record:
            timeline.append({'seconds': round(time.monotonic() - started, 3), 'role': role})

    def call(method, path, status=200, **kwargs):
        request_headers = {"Origin": "http://localhost:5173", **kwargs.pop("headers", {})}
        response = requests.request(method, base + path, timeout=30, headers=request_headers, **kwargs)
        assert response.status_code == status, f'{method} {path}: {response.status_code}'
        return response.json()

    def api_login(username):
        response = requests.post(base + '/auth/session', data={'username': username, 'password': password},
                                 headers={'Origin': 'http://localhost:5173'}, timeout=30)
        assert response.status_code == 200
        return {'Cookie': 'mmss_session=' + response.cookies['mmss_session']}

    def login(page, role, email):
        page.goto(ui + {'patient': '/public', 'doctor': '/research', 'admin': '/admin'}[role])
        if role == 'patient':
            page.get_by_role('button', name='Login', exact=True).click()
        page.get_by_label({'patient': 'Email or username', 'doctor': 'Doctor email or username', 'admin': 'Admin email or username'}[role], exact=True).fill(email)
        page.get_by_label('Password', exact=True).fill(password)
        if role == 'patient':
            page.get_by_label('Password', exact=True).press('Enter')
        else:
            page.get_by_role('button', name='Login', exact=True).click()
        page.wait_for_url('**/' + {'patient': 'patient-profile', 'doctor': 'doctor-dashboard', 'admin': 'admin-dashboard'}[role], timeout=20000)

    try:
        call('GET', '/health')
        db.users.insert_one({'username': admin, 'email': admin, 'full_name': 'Acceptance admin',
            'role': 'admin', 'hashed_password': get_password_hash(password)})
        call('POST', '/auth/register-session', json={'name': 'Acceptance patient', 'email': patient,
            'password': password, 'confirm_password': password})
        headers = api_login(patient)
        patient_id = call('GET', '/patient/profile', headers=headers)['profile']['patient_id']
        call('PUT', '/patient/profile', headers=headers, json={'full_name': 'Acceptance patient', 'age': 40,
            'gender': 'Other', 'medical_condition': 'Essential Hypertension (High BP)'})
        schedule = call('POST', '/patient-schedule', headers=headers, json={'medicine_name': 'Metformin',
            'dosage': 'Acceptance test only', 'frequency': 'Daily', 'scheduled_times': ['09:00'], 'reminder_enabled': False})['schedule']
        call('POST', f'/patient-schedule/{schedule["schedule_id"]}/taken', headers=headers)
        for medicine in ('Methotrexate', 'Ibuprofen', 'Unlisted test medicine'):
            call('POST', '/patient-schedule', headers=headers, json={'medicine_name': medicine,
                'dosage': 'Acceptance test only', 'frequency': 'Daily', 'scheduled_times': ['09:00'], 'reminder_enabled': False})
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='msedge', headless=True, slow_mo=180 if record else 0)
            video_options = {'record_video_dir': str(video_dir / 'raw'), 'record_video_size': {'width': 1280, 'height': 720}} if record else {}
            contexts = [browser.new_context(viewport={'width': 1280, 'height': 720}, **video_options) for _ in range(3)]
            patient_page, doctor_page, admin_page = [context.new_page() for context in contexts]
            started = time.monotonic()
            errors = []
            for page in (patient_page, doctor_page, admin_page):
                page.on('pageerror', lambda error: errors.append(str(error)))
            show('doctor')
            doctor_page.goto(ui + '/research')
            doctor_page.get_by_role('button', name='Request Doctor Account', exact=True).click()
            for label, value in [('Name', 'Acceptance doctor'), ('Email', doctor), ('Medical Registration No.', 'TEST-' + suffix),
                ('Specialization', 'General Medicine'), ('Password', password), ('Confirm Password', password)]:
                doctor_page.get_by_label(label, exact=True).fill(value)
            with doctor_page.expect_response(lambda r: '/auth/doctor-request' in r.url) as submitted:
                doctor_page.get_by_role('button', name='Submit Request', exact=True).click()
            assert submitted.value.status == 200
            call('POST', '/auth/session', status=401, data={'username': doctor, 'password': password})
            show('admin')
            login(admin_page, 'admin', admin)
            row = admin_page.locator('tr').filter(has_text=doctor)
            with admin_page.expect_response(lambda r: '/approve' in r.url) as approved:
                row.get_by_role('button', name='Approve', exact=True).click()
            assert approved.value.status == 200
            show('doctor')
            login(doctor_page, 'doctor', doctor)
            show('patient')
            login(patient_page, 'patient', patient)
            results['checks'].append('Doctor registration, admin approval, and real password login for all three roles')
            show('doctor')
            doctor_page.goto(ui + '/doctor-patients')
            expect(doctor_page.get_by_text('No patients have active approved access.', exact=True)).to_be_visible()
            show('patient')
            patient_page.get_by_role('link', name='My Medicines', exact=True).click()
            expect(patient_page.get_by_role('button', name='Create sharing code')).to_be_visible()

            def share():
                show('patient')
                with patient_page.expect_response(lambda r: '/patient/share-code' in r.url) as code_response:
                    patient_page.get_by_role('button', name='Create sharing code').click()
                code = code_response.value.json()['share_code']
                show('doctor')
                doctor_page.get_by_label('Patient sharing code').fill(code)
                with doctor_page.expect_response(lambda r: '/doctor/access-request' in r.url) as response:
                    doctor_page.get_by_role('button', name='Request patient access', exact=True).click()
                assert response.value.status == 200
                rid = response.value.json()['request']['requestId']
                show('patient')
                patient_page.get_by_role('button', name='Refresh access and log').click()
                expect(patient_page.get_by_role('button', name='Reject', exact=True)).to_be_visible()
                return rid

            rid = share()
            with patient_page.expect_response(lambda r: '/reject' in r.url) as rejected:
                patient_page.get_by_role('button', name='Reject', exact=True).click()
            assert rejected.value.status == 200
            rid = share()
            with patient_page.expect_response(lambda r: '/accept' in r.url) as granted:
                patient_page.get_by_role('button', name='Grant access for 7 days').click()
            assert granted.value.status == 200
            show('doctor')
            doctor_page.get_by_role('button', name='Refresh patients').click()
            expect(doctor_page.get_by_text('Acceptance patient', exact=True)).to_be_visible()
            doctor_page.get_by_role('button', name='View Patient History & Drugs').click()
            expect(doctor_page.get_by_text('Metformin', exact=True).first).to_be_visible()
            expect(doctor_page.get_by_role('heading', name='Full regimen review')).to_be_visible()
            expect(doctor_page.get_by_text('3 of 4 medicines covered', exact=True)).to_be_visible()
            expect(doctor_page.locator('.regimen-interaction a').first).to_be_visible()
            expect(doctor_page.get_by_text('Not checked:', exact=False)).to_contain_text('unlisted test medicine')
            expect(doctor_page.get_by_role('heading', name='Last 28 days: taken records and unconfirmed days')).to_be_visible()
            doctor_page.get_by_role('region', name='Regimen review').screenshot(path=str(ROOT / 'artifacts' / 'regimen-review.png'))
            for page in (patient_page, doctor_page, admin_page):
                assert page.evaluate("localStorage.getItem('mmss_token')") is None
                assert 'mmss_session=' not in page.evaluate('document.cookie')
            results['checks'].append('HttpOnly browser sessions; full regimen coverage and day-level history visible')
            results['checks'].append('Private directory, single-use share code, patient rejection and approval in UI')
            doctor_page.goto(ui + '/reports')
            doctor_page.get_by_label('Report patient', exact=True).select_option(patient)
            doctor_page.get_by_role('button', name='Generate report', exact=True).click()
            expect(doctor_page.locator('.prescription-report')).to_contain_text('Patient consent granted:')
            expect(doctor_page.locator('.prescription-report')).to_contain_text('Metformin')
            with doctor_page.expect_download() as downloaded:
                doctor_page.get_by_role('button', name='Download report (HTML)', exact=True).click()
            assert downloaded.value.suggested_filename.endswith('.html')
            results['checks'].append('Doctor report from real saved schedule/history, consent timestamp, HTML download')
            show('patient')
            patient_page.get_by_role('button', name='Revoke access', exact=True).click()
            expect(patient_page.get_by_role('button', name='Revoke access', exact=True)).to_have_count(0)
            doctor_headers = api_login(doctor)
            for route in (f'/doctor/patients/{patient_id}/medications', f'/doctor/patients/{patient}/drugs', f'/doctor/patients/{patient}/report', f'/doctor/patients/{patient_id}/regimen'):
                call('GET', route, status=403, headers=doctor_headers)
            assert call('GET', '/doctor/patients', headers=doctor_headers)['patients'] == []
            log = call('GET', '/patient/access-log', headers=headers)['events']
            assert {'REJECTED', 'ACCEPTED', 'REVOKED', 'GENERATE_REPORT'} <= {e['action'] for e in log}
            results['checks'].append('Revocation denies all record routes; patient access log records actions')
            show('doctor')
            doctor_page.goto(ui + '/drug-interaction')
            expect(doctor_page.get_by_text('Predict with DDInter model', exact=True)).to_have_count(0)
            expect(doctor_page.get_by_text('Experimental ML comparison', exact=True)).to_have_count(0)
            doctor_page.get_by_label('Medicine 1', exact=True).select_option('Aspirin')
            doctor_page.get_by_label('Medicine 2', exact=True).select_option('Ibuprofen')
            doctor_page.locator('.interaction-button').click()
            expect(doctor_page.locator('.interaction-method[role="status"]')).to_contain_text('2 of 2 medicines')
            unsupported = call('POST', '/interaction/multi', json={'drugs': ['Aspirin', 'Ibuprofen', 'Unlisted medicine']})
            assert unsupported['coverage']['covered_medicines'] == 2
            assert unsupported['coverage']['total_medicines'] == 3
            results['checks'].append('Coverage displayed; research ML panels absent')
            assert not errors, errors
            results['browser_js_errors'] = errors
            if record:
                timeline.append({'seconds': round(time.monotonic() - started, 3), 'role': 'end'})
                for role, context, page in zip(('patient', 'doctor', 'admin'), contexts, (patient_page, doctor_page, admin_page)):
                    context.close()
                    page.video.save_as(str(video_dir / f'{role}.webm'))
                (video_dir / 'timeline.json').write_text(json.dumps(timeline, indent=2))
                results['recorded_video_directory'] = str(video_dir)
            browser.close()
        results['passed'] = True
    finally:
        if patient_id:
            for name in ('access_requests', 'share_codes', 'access_log'):
                db[name].delete_many({'patientId': patient_id})
        for name in ('patient_schedules', 'medication_history', 'fcm_tokens', 'reminder_deliveries'):
            db[name].delete_many({'patient_username': patient})
        db.doctor_requests.delete_many({'email': doctor})
        db.browser_sessions.delete_many({'username': {'$in': [patient, doctor, admin]}})
        db.consent_attempts.delete_many({'doctorId': doctor})
        db.users.delete_many({'username': {'$in': [patient, doctor, admin]}})
        results['disposable_records_removed'] = True
        destination = ROOT / 'artifacts' / 'three-role-live-results.json'
        destination.write_text(json.dumps(results, indent=2), encoding='utf-8')
        print(json.dumps(results, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true', help='Record the disposable-account rehearsal locally.')
    main(record=parser.parse_args().record)
