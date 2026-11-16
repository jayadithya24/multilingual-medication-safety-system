"""Optional real-label research model; never overrides documented evidence."""
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).resolve().parents[3] / 'ml/models/ddinter_severity.joblib'

@lru_cache(maxsize=1)
def load_bundle():
    import joblib
    return joblib.load(PATH)

def model_info():
    report = load_bundle()['report']
    return {key: report[key] for key in ('algorithm', 'features', 'coverage', 'clinical_validation', 'limitations', 'models', 'split', 'catalog_heldout_pairs', 'catalog_heldout_metrics')}

def predict(drug1, drug2):
    bundle = load_bundle()
    mapping = {name.casefold(): identifier for name, identifier in bundle['mapping'].items()}
    names = [str(drug).strip().casefold() for drug in (drug1, drug2)]
    ids = [mapping.get(name) for name in names]
    base = {'source': 'DDInter', 'source_url': 'https://ddinter.scbdd.com/',
            'algorithm': bundle['report']['algorithm'], 'clinical_validation': False,
            'interpretation': 'Research classification of documented interaction severity, not a probability of harm or a patient-specific assessment.'}
    def abstain(reason):
        return {**base, 'status': 'insufficient_evidence', 'reason': reason, 'predicted_severity': None}
    if names[0] == names[1]:
        return abstain('Select two different medicines.')
    if any(not identifier or bundle['support'].get(identifier, 0) < 5 for identifier in ids):
        return abstain('A medicine is outside the exact-name training coverage. No alias or combination-product mapping was guessed.')
    pair = tuple(sorted(ids))
    record = bundle['records'].get(pair)
    if not record:
        return abstain('This pair has no graded record in the downloaded DDInter subset. A severity-only model cannot establish whether it interacts; absence does not mean safe.')
    base.update({'documented_severity': record['label'], 'evaluation_partition': record['partition'],
                 'seen_during_training': record['partition'] == 'train',
                 'source_drug_ids': list(pair)})
    features = {f'drug:{identifier}': 1.0 for identifier in pair}
    matrix = bundle['vectorizer'].transform([features])
    model = bundle['model']
    scores = model.predict_proba(matrix)[0]
    base['model_scores'] = {str(label): float(score) for label, score in zip(model.classes_, scores)}
    if float(max(scores)) < .7:
        return abstain('Model score is below the 0.70 display threshold. Consult the documented evidence.')
    return {**base, 'status': 'predicted', 'predicted_severity': str(model.classes_[scores.argmax()])}
