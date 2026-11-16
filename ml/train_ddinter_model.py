"""Train symmetric drug-identity baselines on real DDInter labels, with pair-disjoint evaluation.

No patient data, interaction text, existing project severity, or test labels are features.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
LABELS = ['Minor', 'Moderate', 'Major']

def normalize(value):
    return re.sub(r'\s+', ' ', str(value).strip().casefold())

def pair_features(a, b):
    # The same two active drug indicators in either input order.
    return {f'drug:{a}': 1.0, f'drug:{b}': 1.0}

def prepare_pairs(frames):
    data = pd.concat(frames, ignore_index=True)
    source_rows = len(data)
    data = data.dropna(subset=['DDInterID_A', 'DDInterID_B', 'Level']).copy()
    data['pair'] = [tuple(sorted((a, b))) for a, b in zip(data.DDInterID_A, data.DDInterID_B)]
    conflicts = set(data.groupby('pair').Level.nunique().loc[lambda x: x > 1].index)
    data = data[~data.pair.isin(conflicts) & data.Level.isin(LABELS)]
    data = data[data.DDInterID_A != data.DDInterID_B].drop_duplicates('pair').sort_values('pair').reset_index(drop=True)
    return data, {'raw_rows': source_rows, 'conflicting_pairs_excluded': len(conflicts), 'unique_graded_pairs': len(data)}

def metrics(y, probabilities, classes):
    pred = classes[np.argmax(probabilities, axis=1)]
    mask = probabilities.max(axis=1) >= .7
    return {'accuracy': float(accuracy_score(y, pred)), 'macro_f1': float(f1_score(y, pred, average='macro')),
            'classification_report': classification_report(y, pred, labels=LABELS, output_dict=True, zero_division=0),
            'confusion_matrix_labels': LABELS, 'confusion_matrix': confusion_matrix(y, pred, labels=LABELS).tolist(),
            'score_threshold': .7, 'selective_coverage': float(mask.mean()),
            'selective_accuracy': float(accuracy_score(np.asarray(y)[mask], pred[mask])) if mask.any() else None}

def main():
    source = ROOT / 'datasets/external/ddinter'
    provenance = json.loads((source / 'provenance.json').read_text())
    for record in provenance['files']:
        assert hashlib.sha256((source / record['file']).read_bytes()).hexdigest() == record['sha256'], 'Source checksum changed'
    frames = [pd.read_csv(source / f['file']) for f in provenance['files']]
    data, audit = prepare_pairs(frames)
    train, rest = train_test_split(data, test_size=.3, stratify=data.Level, random_state=42)
    validation, test = train_test_split(rest, test_size=.5, stratify=rest.Level, random_state=43)
    assert not (set(train.pair) & set(test.pair) or set(train.pair) & set(validation.pair) or set(test.pair) & set(validation.pair))
    vectorizer = DictVectorizer()
    def features(frame):
        return [pair_features(a, b) for a, b in frame.pair]
    xtrain = vectorizer.fit_transform(features(train))
    xval, xtest = vectorizer.transform(features(validation)), vectorizer.transform(features(test))
    candidates = {
        'Logistic regression': LogisticRegression(max_iter=1500, class_weight='balanced', random_state=42),
        'Multinomial naive Bayes': MultinomialNB(alpha=1.0),
        'Majority baseline': DummyClassifier(strategy='most_frequent'),
    }
    results = {}
    for name, model in candidates.items():
        print('Training', name, flush=True)
        model.fit(xtrain, train.Level)
        results[name] = {'validation': metrics(validation.Level, model.predict_proba(xval), model.classes_)}
    selected = max((n for n in candidates if n != 'Majority baseline'), key=lambda n: results[n]['validation']['macro_f1'])
    for name, model in candidates.items():
        results[name]['test'] = metrics(test.Level, model.predict_proba(xtest), model.classes_)
    # No refit on validation or test: shipped artifact retains the measured training split.
    model = candidates[selected]
    support = Counter(drug for pair in train.pair for drug in pair)
    allrows = pd.concat(frames, ignore_index=True)
    names = {}
    for side in ('A', 'B'):
        for identifier, name in zip(allrows[f'DDInterID_{side}'], allrows[f'Drug_{side}']):
            names.setdefault(normalize(name), set()).add(identifier)
    names = {name: next(iter(ids)) for name, ids in names.items() if len(ids) == 1}
    catalog = pd.read_csv(ROOT / 'datasets/english_master_dataset.csv')
    mapping = {name: names.get(normalize(name)) for name in catalog.drug_name}
    eligible = {name: identifier for name, identifier in mapping.items() if identifier and support[identifier] >= 5}
    catalog_mask = test.pair.map(lambda pair: all(drug in set(eligible.values()) for drug in pair)).to_numpy()
    catalog_test = metrics(test.Level[catalog_mask], model.predict_proba(xtest[catalog_mask]), model.classes_) if catalog_mask.any() else None
    partitions = {pair: split for split, frame in [('train', train), ('validation', validation), ('test', test)] for pair in frame.pair}
    records = {row.pair: {'label': row.Level, 'partition': partitions[row.pair]} for row in data.itertuples()}
    report = {'source': provenance, 'audit': audit, 'algorithm': selected, 'models': results,
              'split': {name: {'pairs': len(frame), 'labels': frame.Level.value_counts().to_dict()} for name, frame in [('train', train), ('validation', validation), ('test', test)]},
              'features': 'Unordered binary drug identity indicators; no interaction text or severity input',
              'coverage': {'catalog_size': len(catalog), 'exact_name_matches': sum(v is not None for v in mapping.values()),
                           'supported_medicines': sorted(eligible), 'unsupported_medicines': sorted(set(mapping) - set(eligible))},
              'catalog_heldout_pairs': int(catalog_mask.sum()), 'catalog_heldout_metrics': catalog_test,
              'clinical_validation': False, 'limitations': [
                  'Predicts severity conditional on a documented interaction; cannot determine whether an interaction exists.',
                  'Pair-disjoint evaluation allows the same drugs in multiple splits; it is not unseen-drug or prospective clinical validation.',
                  'Identity features learn drug-associated severity patterns, not biological mechanisms or patient-specific risk.',
                  'Model scores are not calibrated probabilities of harm. Scores below 0.70 abstain.',
                  'Only exact unambiguous catalog names with at least five training pairs are supported; no guessed aliases.',
                  'Minor/Moderate/Major are source labels, not silently equated with the older project rating scale.',
                  'Eight published therapeutic-area downloads are overlapping and do not guarantee full DDInter coverage.']}
    output = ROOT / 'ml/models'
    output.mkdir(exist_ok=True)
    joblib.dump({'model': model, 'vectorizer': vectorizer, 'mapping': mapping, 'support': dict(support), 'records': records, 'report': report}, output / 'ddinter_severity.joblib')
    (output / 'ddinter_evaluation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    data.assign(pair=data.pair.map(lambda p: '|'.join(p)), split=data.pair.map(partitions)).to_csv(source / 'deduplicated_pairs.csv', index=False)
    print(json.dumps({'selected': selected, 'test': results[selected]['test'], 'coverage': report['coverage']}, indent=2), flush=True)

if __name__ == '__main__':
    main()
