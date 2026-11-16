import pandas as pd

from ml.audit_risk_evaluation import canonical_pairs, evaluation_splits


def test_grouped_splits_keep_reverse_pairs_and_patients_together():
    records = []
    for patient in range(20):
        for pair in range(5):
            drugs = (f"drug-{pair}", f"partner-{pair}")
            for first, second in (drugs, drugs[::-1]):
                records.append({"patient_id": f"P{patient}", "drug_1": first,
                                "drug_2": second, "severity": "Mild" if pair < 2 else "Severe"})
    data = pd.DataFrame(records)
    for name, train, test in evaluation_splits(data):
        assert set(train).isdisjoint(test)
        assert len(train) + len(test) == len(data)
        if name == "unseen_pairs":
            assert set(canonical_pairs(data.iloc[train])).isdisjoint(canonical_pairs(data.iloc[test]))
        if name == "unseen_patients":
            assert set(data.iloc[train].patient_id).isdisjoint(data.iloc[test].patient_id)
