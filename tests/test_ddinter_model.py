import pandas as pd
from backend.app.services import ddinter_prediction_service as service
from ml.train_ddinter_model import pair_features, prepare_pairs


def test_reversed_duplicates_and_conflicting_labels_are_not_training_examples():
    data = pd.DataFrame([
        ['A', 'B', 'Major'], ['B', 'A', 'Major'],
        ['C', 'D', 'Minor'], ['D', 'C', 'Major'], ['A', 'E', 'Unknown'],
    ], columns=['DDInterID_A', 'DDInterID_B', 'Level'])
    pairs, audit = prepare_pairs([data])
    assert len(pairs) == 1
    assert audit['conflicting_pairs_excluded'] == 1
    assert pair_features('A', 'B') == pair_features('B', 'A')


def test_real_model_is_symmetric_and_separates_source_from_prediction():
    result = service.predict('Metformin', 'Glipizide')
    assert result == service.predict('Glipizide', 'Metformin')
    assert not result['clinical_validation']
    assert result['algorithm'] == 'Logistic regression'
    if 'model_scores' in result:
        assert abs(sum(result['model_scores'].values()) - 1) < 1e-8
        assert 'documented_severity' in result
        assert 'seen_during_training' in result


def test_unsupported_and_identical_drugs_abstain():
    for a, b in [('not-a-drug', 'Metformin'), ('Metformin', 'Metformin'), ('Paracetamol', 'Metformin')]:
        result = service.predict(a, b)
        assert result['status'] == 'insufficient_evidence'
        assert result['predicted_severity'] is None


def test_no_record_does_not_predict_safety():
    bundle = service.load_bundle()
    names = bundle['report']['coverage']['supported_medicines']
    for a in names:
        for b in names:
            pair = tuple(sorted((bundle['mapping'][a], bundle['mapping'][b])))
            if a != b and pair not in bundle['records']:
                result = service.predict(a, b)
                assert result['status'] == 'insufficient_evidence'
                assert 'absence does not mean safe' in result['reason']
                return
    raise AssertionError('Expected a pair without evidence')


def test_low_scores_abstain_even_when_recorded_label_exists(monkeypatch):
    import numpy as np
    bundle = dict(service.load_bundle())
    class Model:
        classes_ = np.array(['Major', 'Minor', 'Moderate'])
        def predict_proba(self, matrix):
            return np.array([[.34, .33, .33]])
    bundle['model'] = Model()
    pair = tuple(sorted((bundle['mapping']['Metformin'], bundle['mapping']['Glipizide'])))
    bundle['records'] = {pair: {'label': 'Major', 'partition': 'test'}}
    monkeypatch.setattr(service, 'load_bundle', lambda: bundle)
    result = service.predict('Metformin', 'Glipizide')
    assert result['status'] == 'insufficient_evidence'
    assert result['documented_severity'] == 'Major'
    assert result['predicted_severity'] is None


def test_saved_splits_have_no_pair_overlap():
    from pathlib import Path
    data = pd.read_csv(Path(__file__).resolve().parents[1] / 'datasets/external/ddinter/deduplicated_pairs.csv')
    assert data.pair.is_unique
    assert set(data.split) == {'train', 'validation', 'test'}


def test_tulu_requested_word_correction():
    from pathlib import Path
    text = (Path(__file__).resolve().parents[1] / 'datasets/tulu_master_dataset.csv').read_text(encoding='utf-8')
    assert '\u0ca8\u0ccb\u0cb5\u0cc1' not in text
    assert '\u0cac\u0cc7\u0ca8\u0cc6' in text
