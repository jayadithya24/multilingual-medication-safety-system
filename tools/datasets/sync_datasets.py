"""Validate maintained CSVs and refresh app copies/derived data; never rewrite masters."""
from pathlib import Path
import hashlib
import argparse
import json
import re
import shutil
import subprocess
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'datasets'
LANGUAGES = ('english', 'kannada', 'tulu')
REQUIRED = ('drug_id', 'drug_name', 'generic_name', 'disease', 'drug_class', 'active_ingredient',
            'description', 'side_effects', 'contraindications', 'warnings', 'major_interactions', 'source')

def validate(directory=DATA, allow_incomplete=False):
    frames = {}
    for language in LANGUAGES:
        path = directory / f'{language}_master_dataset.csv'
        data = pd.read_csv(path, keep_default_na=False)
        if set(data.columns) != set(REQUIRED):
            raise ValueError(f'{language}: expected 12 CSV columns; check delimiter and headers')
        if len(data) != 100 or data.disease.nunique() != 10:
            raise ValueError(f'{language}: expected 100 medicines and 10 disease categories')
        for field in ('drug_id', 'drug_name'):
            if not data[field].is_unique:
                raise ValueError(f'{language}: duplicate {field}')
        for field in set(REQUIRED) - {'drug_class'}:
            if data[field].str.strip().eq('').any():
                raise ValueError(f'{language}: missing required {field}')
        if not allow_incomplete and data.drug_class.str.strip().eq('').any():
            missing = data.loc[data.drug_class.str.strip().eq(''), 'drug_id'].tolist()
            raise ValueError(f'{language}: missing required drug_class for {len(missing)} medicines: {missing}. '
                             'Obtain reviewed content; --allow-incomplete is an explicit demo-only exception.')
        ids = data.drug_name.map(lambda name: re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-'))
        if not ids.eq(data.drug_id).all():
            raise ValueError(f'{language}: IDs do not match canonical medicine names')
        frames[language] = data
    en = frames['english'].set_index('drug_id')
    for language, data in frames.items():
        if set(data.drug_id) != set(en.index):
            raise ValueError(f'{language}: medicine coverage differs')
        aligned = data.set_index('drug_id').join(en[['drug_name', 'disease']], rsuffix='_english')
        if not aligned.drug_name.eq(aligned.drug_name_english).all():
            raise ValueError(f'{language}: medicine names differ')
        if aligned.groupby('disease').disease_english.nunique().max() != 1 or aligned.groupby('disease_english').disease.nunique().max() != 1:
            raise ValueError(f'{language}: disease categories do not align')
    return frames

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-incomplete', action='store_true', help='Explicit demo-only exception for missing drug classes; does not fill or validate medical content')
    args = parser.parse_args()
    frames = validate(allow_incomplete=args.allow_incomplete)
    original = {name: hashlib.sha256((DATA / f'{name}_master_dataset.csv').read_bytes()).hexdigest() for name in LANGUAGES}
    subprocess.run([sys.executable, str(Path(__file__).with_name('split_master_dataset.py'))], check=True)
    for name in ('english_master_dataset.csv', 'drug_disease.csv', 'drug_sideeffects.csv', 'drug_interactions.csv'):
        for folder in (ROOT, ROOT / 'backend/app/datasets'):
            destination = folder / name
            if destination.exists():
                shutil.copyfile(DATA / name, destination)
    subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_ml_data.py'))], check=True)
    assert all(hashlib.sha256((DATA / f'{name}_master_dataset.csv').read_bytes()).hexdigest() == digest for name, digest in original.items())
    print(json.dumps({'master_files_unchanged': True, 'incomplete_content_allowed': args.allow_incomplete,
        'missing_drug_classes': {name: int(data.drug_class.str.strip().eq('').sum()) for name, data in frames.items()},
        'scopes': {name: {'medicines': len(data), 'diseases': data.disease.nunique()} for name, data in frames.items()}}))

if __name__ == '__main__':
    main()
