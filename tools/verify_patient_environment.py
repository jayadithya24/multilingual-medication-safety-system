"""Read-only service/dataset audit. Never prints secrets or patient records.

Run from the repository root: python tools/verify_patient_environment.py
FCM uses dry_run=True: no device is notified. No datasets are imported or deleted.
"""
import json
import os
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.env_loader import load_project_env
load_project_env()


def main():
    report = {}
    from backend.app.database import db
    db.command('ping')
    report['mongodb_connected'] = True
    report['collections'] = {name: db[name].count_documents({}) for name in (
        'users', 'fcm_tokens', 'patient_schedules', 'medication_history', 'reminder_deliveries')}
    from backend.app.services.fcm_service import _firebase
    try:
        app = _firebase()
        report['firebase_admin_initialized'] = True
        public_path = ROOT / 'frontend/public/firebase-public-config.js'
        if public_path.exists():
            public = json.loads(public_path.read_text().split('=', 1)[1].strip().rstrip(';'))
            report['firebase_public_config_generated'] = True
            report['firebase_project_matches'] = public.get('projectId') == app.project_id
        tokens = list(db.fcm_tokens.find({}, {'token': 1}))
        if tokens:
            from firebase_admin import messaging
            report['fcm_dry_run'] = {'accepted': 0, 'errors': {}}
            for token in tokens:
                try:
                    messaging.send(messaging.Message(token=token['token'], data={'type': 'configuration_validation'}), dry_run=True, app=app)
                    report['fcm_dry_run']['accepted'] += 1
                except Exception as error:
                    errors = report['fcm_dry_run']['errors']
                    errors[type(error).__name__] = errors.get(type(error).__name__, 0) + 1
        else:
            report['fcm_dry_run'] = 'No registered browser token'
    except Exception as error:
        report['firebase_admin_error'] = type(error).__name__
    from backend.app.services.neo4j_service import _get_driver
    try:
        with _get_driver() as driver:
            driver.verify_connectivity()
            with driver.session() as session:
                report['neo4j_counts'] = {
                    'Drugs': session.run('MATCH (n:Drug) RETURN count(n) AS total').single()['total'],
                    'Diseases': session.run('MATCH (n:Disease) RETURN count(n) AS total').single()['total'],
                    'relationships': session.run('MATCH ()-[r]->() RETURN count(r) AS total').single()['total'],
                }
    except Exception as error:
        report['neo4j_error'] = type(error).__name__
    import pandas as pd
    names = {}
    report['datasets'] = {}
    for lang, filename in [('en', 'english'), ('kn', 'kannada'), ('tulu', 'tulu')]:
        frame = pd.read_csv(ROOT / 'datasets' / f'{filename}_master_dataset.csv').fillna('')
        names[lang] = set(frame['drug_name'].str.strip().str.lower())
        report['datasets'][lang] = {
            'rows': len(frame), 'duplicate_drug_names': int(frame['drug_name'].duplicated().sum()),
            'empty_drug_names': int((frame['drug_name'].str.strip() == '').sum()),
        }
    report['datasets_same_drug_names'] = names['en'] == names['kn'] == names['tulu']
    from backend.app.services.neo4j_service import search_drug_by_text
    report['search_all_records'] = {}
    for lang, drug_names in names.items():
        durations, missing = [], 0
        for name in sorted(drug_names):
            start = perf_counter()
            results = search_drug_by_text(name, lang=lang)
            durations.append((perf_counter() - start) * 1000)
            missing += not bool(results)
        report['search_all_records'][lang] = {'missing': missing, 'max_ms': round(max(durations), 2)}
    report['reminder_timezone'] = os.getenv('REMINDER_TIMEZONE', 'Asia/Kolkata')
    report['reminder_poll_seconds'] = int(os.getenv('REMINDER_POLL_SECONDS', '2'))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
