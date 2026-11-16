"""Export a review queue without changing or filling any master CSV fields."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = ROOT / 'artifacts' / 'content-review'
    destination.mkdir(parents=True, exist_ok=True)
    tables = {}
    hashes = {}
    for language in ('english', 'kannada', 'tulu'):
        path = ROOT / 'datasets' / f'{language}_master_dataset.csv'
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(encoding='utf-8-sig', newline='') as stream:
            tables[language] = list(csv.DictReader(stream))
    english = {row['drug_id']: row for row in tables['english']}
    columns = ['drug_id', 'english_name', 'language', 'issue', 'proposed_correction',
               'source_url_or_reference', 'native_reviewer', 'pharmacist_reviewer', 'review_date', 'status']
    rows = []
    for language in ('kannada', 'tulu'):
        for row in tables[language]:
            issues = ['Review translation, medicine names, warnings and pronunciation']
            if not row['drug_class'].strip():
                issues.insert(0, 'Missing drug_class')
            rows.append(dict.fromkeys(columns, '') | {'drug_id': row['drug_id'],
                'english_name': english.get(row['drug_id'], {}).get('drug_name', ''),
                'language': language, 'issue': '; '.join(issues), 'status': 'Pending human review'})
    with (destination / 'language-review.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    missing = [row['drug_id'] for row in tables['tulu'] if not row['drug_class'].strip()]
    manifest = {'source_sha256': hashes, 'review_rows': len(rows), 'tulu_missing_class_ids': missing,
                'approved': False, 'master_files_modified': False}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'review_rows': len(rows), 'tulu_missing_classes': len(missing), 'output': str(destination)}))


if __name__ == '__main__':
    main()
