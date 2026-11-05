"""Reference-pair review and explicitly day-level patient-reported history."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import os
from backend.app.services.interaction_service import interaction_coverage, get_multi_drug_interactions, _catalog_names


def timestamp(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    return value.replace(tzinfo=timezone.utc) if isinstance(value, datetime) and value.tzinfo is None else value


def build_review(schedules, history, now=None):
    now = now or datetime.now(timezone.utc)
    zone = ZoneInfo(os.getenv('REMINDER_TIMEZONE', 'Asia/Kolkata'))
    start_day = now.astimezone(zone).date() - timedelta(days=27)
    window_start = datetime.combine(start_day, datetime.min.time(), zone)
    active = [row for row in schedules if row.get('status') == 'active']
    names = list(dict.fromkeys(str(row.get('medicine_name', '')).strip().lower() for row in active if row.get('medicine_name')))
    coverage = interaction_coverage(names)
    supported = [name for name in names if name in _catalog_names()]
    interactions = get_multi_drug_interactions(supported)['interactions'] if len(supported) > 1 else []
    priority = {'Review required': 0, 'Severe': 1, 'Major': 1, 'Moderate': 2, 'Mild': 3}
    interactions.sort(key=lambda row: priority.get(row['severity'], 4))
    rows = []
    for schedule in schedules:
        created = timestamp(schedule.get('created_at'))
        removed = timestamp(schedule.get('deleted_at'))
        times = []
        for value in schedule.get('scheduled_times', []):
            try:
                times.append(datetime.strptime(value, '%H:%M').time())
            except (ValueError, TypeError):
                pass
        known = bool(created and times and (schedule.get('status') == 'active' or removed))
        due_days = set()
        if known:
            for offset in range(28):
                day = start_day + timedelta(days=offset)
                if any(created <= datetime.combine(day, time, zone) <= now and
                       (removed is None or datetime.combine(day, time, zone) < removed) for time in times):
                    due_days.add(day)
        logs = [row for row in history if schedule.get('schedule_id') and row.get('schedule_id') == schedule['schedule_id']
                and row.get('status') == 'TAKEN' and timestamp(row.get('taken_at'))
                and window_start <= timestamp(row['taken_at']) <= now]
        recorded_days = {timestamp(row['taken_at']).astimezone(zone).date() for row in logs}
        if due_days or logs or schedule in active:
            rows.append({'schedule_id': schedule.get('schedule_id'), 'medicine_name': schedule.get('medicine_name'),
                         'recorded_events': len(logs), 'scheduled_days': len(due_days) if known else None,
                         'days_with_confirmation': len(due_days & recorded_days) if known else None,
                         'unconfirmed_days': len(due_days - recorded_days) if known else None})
    return {'generated_at': now.isoformat(), 'medications': active, 'coverage': coverage, 'interactions': interactions,
            'adherence': {'days': 28, 'timezone': str(zone), 'from_date': start_day.isoformat(), 'rows': rows,
                'interpretation': 'Patient-reported records, not verified ingestion. Counts are scheduled days with at least one taken record, not individual doses. A day with a record does not confirm every dose. Unconfirmed does not mean missed. Unknown schedule dates or times are not estimated.'}}
