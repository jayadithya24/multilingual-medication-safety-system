from datetime import datetime, timezone
from backend.app.services.regimen_review import build_review


def test_regimen_coverage_and_day_counts_do_not_imply_all_doses_taken():
    now = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
    schedule = {'schedule_id': 'S1', 'medicine_name': 'Metformin', 'status': 'active',
                'created_at': datetime(2026, 10, 18, tzinfo=timezone.utc), 'scheduled_times': ['09:00', '12:00']}
    unknown = {**schedule, 'schedule_id': 'S2', 'medicine_name': 'Unknown brand'}
    history = [{'schedule_id': 'S1', 'status': 'TAKEN', 'taken_at': now},
               {'schedule_id': 'S1', 'status': 'TAKEN', 'taken_at': now}]
    result = build_review([schedule, unknown], history, now)
    assert result['coverage']['covered_medicines'] == 1 and result['coverage']['total_medicines'] == 2
    row = result['adherence']['rows'][0]
    assert row['scheduled_days'] == 3 and row['days_with_confirmation'] == 1 and row['unconfirmed_days'] == 2
    assert row['recorded_events'] == 2  # Duplicate clicks do not create extra confirmed days.
    assert 'not individual doses' in result['adherence']['interpretation']


def test_removed_and_unknown_schedules_are_not_extrapolated():
    now = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
    base = {'schedule_id': 'S1', 'medicine_name': 'Aspirin', 'status': 'inactive',
            'created_at': datetime(2026, 10, 18, tzinfo=timezone.utc), 'scheduled_times': ['09:00'],
            'deleted_at': datetime(2026, 10, 19, tzinfo=timezone.utc)}
    unknown = {'schedule_id': 'S2', 'medicine_name': 'Ibuprofen', 'status': 'active'}
    result = build_review([base, unknown], [], now)
    assert len(result['medications']) == 1
    assert result['adherence']['rows'][0]['scheduled_days'] == 1
    assert result['adherence']['rows'][1]['scheduled_days'] is None


def test_regimen_retains_sources_and_source_scale():
    rows = [{'status': 'active', 'medicine_name': name} for name in ('Methotrexate', 'Ibuprofen')]
    result = build_review(rows, [])
    assert result['interactions']
    pair = result['interactions'][0]
    assert pair['evidence_sources'] and pair['severity_basis']
    assert pair['severity_clinically_validated'] is False
