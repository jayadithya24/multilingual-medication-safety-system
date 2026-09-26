import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_ml_data", ROOT / "datasets/prepare_ml_data.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_split_is_reproducible_and_patient_disjoint():
    labels = pd.DataFrame({"patient_id": [f"P{i}" for i in range(100)],
                           "target_severity": ["None"] * 80 + ["Severe"] * 20})
    first = module.split_patients(labels)
    assert first == module.split_patients(labels.sample(frac=1, random_state=2))
    assert set(first) == set(labels.patient_id)
    assert set(first.values()) == {"train", "validation", "test"}
    assert first != module.split_patients(labels, seed=43)


def test_unknown_or_rare_class_is_not_silently_dropped():
    labels = pd.DataFrame({"patient_id": ["P1"], "target_severity": ["Moderate"]})
    with pytest.raises(ValueError, match="at least 10"):
        module.split_patients(labels)


def test_full_export_integrity(tmp_path):
    report = module.prepare(ROOT / "datasets", tmp_path)
    groups = {name: pd.read_csv(tmp_path / f"{name}.csv", keep_default_na=False)
              for name in ("train", "validation", "test")}
    seen = set()
    for data in groups.values():
        ids = set(data.patient_id)
        assert not ids & seen
        seen |= ids
        assert "None" in set(data.target_severity)
        assert set(data.columns) == set(report["features"]) | {"patient_id", "target_severity"}
    assert len(seen) == report["patient_count"]
    assert not {"highest_severity", "severity", "patient_id", "target_severity", "major_interactions"} & set(report["features"])
    localized = pd.read_csv(tmp_path / "master_localized.csv", keep_default_na=False)
    assert not localized.duplicated(["drug_id", "language"]).any()
    assert len(localized) == report["drug_count"] * 3
    assert json.loads((tmp_path / "manifest.json").read_text())["source_sha256"] == report["source_sha256"]
    repeated = module.prepare(ROOT / "datasets", tmp_path / "repeat")
    assert repeated["output_sha256"] == report["output_sha256"]


def test_invalid_prescription_is_rejected(tmp_path):
    # Reuse source files by links/copies, then alter one input in the isolated copy.
    import shutil
    for name in ("english_master_dataset.csv", "kannada_master_dataset.csv", "tulu_master_dataset.csv",
                 "synthetic_patients.csv", "synthetic_patient_drugs.csv",
                 "synthetic_patient_interactions.csv", "drug_interactions.csv"):
        shutil.copyfile(ROOT / "datasets" / name, tmp_path / name)
    path = tmp_path / "synthetic_patient_drugs.csv"
    data = pd.read_csv(path, keep_default_na=False)
    data.loc[0, "drug_id"] = "not-a-real-drug"
    data.to_csv(path, index=False)
    with pytest.raises(ValueError, match="unknown drug"):
        module.prepare(tmp_path, tmp_path / "out")
    assert not (tmp_path / "out").exists()
