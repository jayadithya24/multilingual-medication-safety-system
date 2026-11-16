from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import threading
import mongomock
import pytest
from backend.app.services import fcm_service as service

send_via_firebase = service._send


@pytest.fixture
def setup(monkeypatch):
    db = mongomock.MongoClient().test
    for name in ('fcm_tokens', 'patient_schedules', 'reminder_deliveries'):
        monkeypatch.setattr(service, name + '_collection', db[name])
    db.reminder_deliveries.create_index([('schedule_id', 1), ('due_at', 1)], unique=True)
    monkeypatch.setenv('REMINDER_TIMEZONE', 'Asia/Kolkata')
    monkeypatch.setenv('REMINDER_CATCHUP_MINUTES', '5')
    now = datetime(2026, 9, 20, 4, 30, 2, tzinfo=timezone.utc)  # 10:00:02 IST
    db.patient_schedules.insert_one({
        'schedule_id': 'TEST', 'patient_username': 'test', 'medicine_name': 'Test',
        'dosage': 'test only', 'status': 'active', 'scheduled_times': ['10:00'],
        'created_at': now - timedelta(days=1),
    })
    db.fcm_tokens.insert_one({'patient_username': 'test', 'token': 'device-a'})
    calls = []
    def send(tokens, *args):
        calls.append(list(tokens))
        return tokens, []
    monkeypatch.setattr(service, '_send', send)
    return db, now, calls


def test_timezone_and_once_per_occurrence(setup):
    db, now, calls = setup
    assert service.process_due_reminders(now) == 1
    assert service.process_due_reminders(now + timedelta(seconds=2)) == 0
    assert calls == [['device-a']]
    assert db.reminder_deliveries.find_one()['status'] == 'sent'
    assert service.process_due_reminders(now + timedelta(days=1)) == 1


def test_catches_missed_minute_but_not_stale_doses(setup):
    _, now, calls = setup
    assert service.process_due_reminders(now + timedelta(minutes=6)) == 0
    assert service.process_due_reminders(now + timedelta(minutes=2)) == 1
    assert len(calls) == 1


@pytest.mark.parametrize('change', [
    {'reminder_enabled': False}, {'is_active': False}, {'status': 'inactive'},
    {'created_at': datetime(2026, 9, 20, 4, 30, 1, tzinfo=timezone.utc)},
    {'last_taken_at': datetime(2026, 9, 20, 4, 30, 1, tzinfo=timezone.utc)},
])
def test_skips_disabled_removed_new_and_taken_doses(setup, change):
    db, now, calls = setup
    db.patient_schedules.update_one({}, {'$set': change})
    assert service.process_due_reminders(now) == 0
    assert not calls


def test_partial_failure_retries_only_failed_device(setup, monkeypatch):
    db, now, calls = setup
    db.fcm_tokens.insert_one({'patient_username': 'test', 'token': 'device-b'})
    def send(tokens, *args):
        calls.append(tokens)
        return (['device-a'] if len(calls) == 1 else tokens), []
    monkeypatch.setattr(service, '_send', send)
    assert service.process_due_reminders(now) == 0
    assert service.process_due_reminders(now + timedelta(seconds=2)) == 0
    assert service.process_due_reminders(now + timedelta(seconds=16)) == 1
    assert calls == [['device-a', 'device-b'], ['device-b']]
    assert db.reminder_deliveries.find_one()['accepted_count'] == 2


def test_concurrent_workers_claim_once(setup, monkeypatch):
    _, now, calls = setup
    entered, release = threading.Event(), threading.Event()
    def send(tokens, *args):
        calls.append(tokens)
        entered.set()
        assert release.wait(3)
        return tokens, []
    monkeypatch.setattr(service, '_send', send)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(service.process_due_reminders, now)
        assert entered.wait(3)
        try:
            assert service.process_due_reminders(now) == 0
        finally:
            release.set()
        assert first.result() == 1
    assert len(calls) == 1


def test_failure_is_visible_and_retried(setup, monkeypatch):
    db, now, _ = setup
    def fail(*args):
        raise RuntimeError('provider unavailable')
    monkeypatch.setattr(service, '_send', fail)
    assert service.process_due_reminders(now) == 0
    attempt = db.reminder_deliveries.find_one()
    assert attempt['status'] == 'retry'
    assert attempt['last_error'] == 'RuntimeError'
    assert 'lease_until' not in attempt


def test_midnight_catchup(setup):
    db, _, calls = setup
    db.patient_schedules.update_one({}, {'$set': {'scheduled_times': ['23:59']}})
    assert service.process_due_reminders(datetime(2026, 9, 20, 18, 31, tzinfo=timezone.utc)) == 1
    assert len(calls) == 1


def test_expired_claim_can_recover_after_worker_stops(setup):
    db, now, calls = setup
    db.reminder_deliveries.insert_one({
        'schedule_id': 'TEST', 'due_at': now.replace(second=0), 'status': 'pending',
        'owner': 'stopped-worker', 'lease_until': now + timedelta(seconds=30),
    })
    assert service.process_due_reminders(now) == 0
    assert service.process_due_reminders(now + timedelta(seconds=31)) == 1
    assert len(calls) == 1


def test_future_dose_is_not_sent_early(setup):
    db, now, calls = setup
    db.patient_schedules.update_one({}, {'$set': {'scheduled_times': ['10:01']}})
    assert service.process_due_reminders(now) == 0
    assert not calls


def test_fcm_webpush_options_and_stale_token_cleanup(setup, monkeypatch):
    from types import SimpleNamespace
    from firebase_admin import messaging
    db, _, _ = setup
    monkeypatch.setattr(service, '_firebase', lambda: object())
    captured = []
    def send(message, app):
        captured.append(message)
        return SimpleNamespace(responses=[
            SimpleNamespace(success=False, exception=messaging.UnregisteredError('expired')),
            SimpleNamespace(success=True, exception=None),
        ])
    monkeypatch.setattr(messaging, 'send_each_for_multicast', send)
    accepted, invalid = send_via_firebase(['device-a', 'device-b'], 'Test', 'Test', {'event_id': 'same-event'})
    assert accepted == ['device-b'] and invalid == ['device-a']
    assert db.fcm_tokens.count_documents({}) == 0
    assert captured[0].webpush.headers == {'Urgency': 'high', 'TTL': '300'}
    assert captured[0].webpush.notification.tag == 'same-event'
