"""Download official DDInter exports for noncommercial academic experiments."""
from pathlib import Path
import hashlib
import json
import requests

ROOT = Path(__file__).resolve().parents[1]

def main():
    target = ROOT / 'datasets/external/ddinter'
    target.mkdir(parents=True, exist_ok=True)
    records = []
    for code in 'ABDHLPRV':
        name = f'ddinter_downloads_code_{code}.csv'
        url = 'https://ddinter.scbdd.com/static/media/download/' + name
        path = target / name
        if not path.exists():
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            if 'Drug' not in response.text[:500]:
                raise ValueError('Unexpected download format')
            path.write_bytes(response.content)
        records.append({'file': name, 'url': url, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        print(name, path.stat().st_size, flush=True)
    (target / 'provenance.json').write_text(json.dumps({
        'source': 'DDInter', 'download_page': 'https://ddinter.scbdd.com/download/',
        'terms': 'https://ddinter.scbdd.com/terms/', 'license': 'CC BY-NC-SA 4.0',
        'citation': 'https://doi.org/10.1093/nar/gkab880', 'files': records
    }, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
