"""Validate and export a reproducible synthetic patient-severity training bundle.

Run from any directory: python datasets/prepare_ml_data.py
Source CSVs are never modified. No clinical validity is inferred from passing checks.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
RANK = {"None": 0, "Mild": 1, "Moderate": 2, "Severe": 3}
CONDITIONS = {"Diabetes": "type_2_diabetes", "Type 2 Diabetes": "type_2_diabetes",
              "Hypertension": "hypertension", "Arthritis": "arthritis"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_csv(path):
    # 'None' is a real synthetic label, not a missing value.
    frame = pd.read_csv(path, keep_default_na=False)
    require(not frame.empty, f"Empty dataset: {path.name}")
    require(not frame.astype(str).apply(lambda col: col.str.strip().eq("")).any().any(),
            f"Blank cells in {path.name}")
    return frame


def split_patients(labels, seed=42):
    """Stratify existing classes without inventing or oversampling labels."""
    assignments = {}
    for _, group in labels.groupby("target_severity", sort=True):
        ids = sorted(group.patient_id, key=lambda value: hashlib.sha256(f"{seed}:{value}".encode()).hexdigest())
        require(len(ids) >= 10, "Each observed class needs at least 10 patients for this split")
        train_end, val_end = int(len(ids) * .8), int(len(ids) * .9)
        for split, subset in (("train", ids[:train_end]), ("validation", ids[train_end:val_end]), ("test", ids[val_end:])):
            assignments.update(dict.fromkeys(subset, split))
    return assignments


def prepare(source=ROOT, output=None, seed=42):
    source = Path(source).resolve()
    output = Path(output or source / "ml_ready").resolve()
    require(output != source, "Output must be separate from source datasets")
    inputs = {}
    def load(name):
        path = source / name
        inputs[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        return read_csv(path)

    masters = {lang: load(f"{name}_master_dataset.csv") for lang, name in
               (("en", "english"), ("kn", "kannada"), ("tulu", "tulu"))}
    canonical = masters["kn"][["drug_id", "drug_name"]].copy()
    require(canonical.drug_id.is_unique and canonical.drug_name.is_unique, "Duplicate master IDs/names")
    ids = set(canonical.drug_id)
    english = masters["en"]
    disease_map = english.set_index("drug_name").disease.map(CONDITIONS)
    require(disease_map.notna().all(), "Unmapped English disease label")
    canonical["disease_id"] = canonical.drug_name.map(disease_map)
    disease_by_id = canonical.set_index("drug_id").disease_id
    localized = []
    for lang, master in masters.items():
        require(master.drug_name.is_unique and set(master.drug_name) == set(canonical.drug_name), f"Medicine coverage differs: {lang}")
        aligned = canonical.merge(master, on="drug_name", suffixes=("", "_source"), validate="one_to_one")
        if "drug_id_source" in aligned:
            require(aligned.drug_id.eq(aligned.drug_id_source).all(), f"Drug IDs differ: {lang}")
            aligned = aligned.drop(columns="drug_id_source")
        # A translated category must correspond to exactly one canonical category.
        require(aligned.groupby("disease").disease_id.nunique().max() == 1 and
                aligned.groupby("disease_id").disease.nunique().max() == 1,
                f"Disease category assignments differ: {lang}")
        aligned["language"] = lang
        localized.append(aligned)

    patients = load("synthetic_patients.csv")
    drugs = load("synthetic_patient_drugs.csv")
    interactions = load("synthetic_patient_interactions.csv")
    rules = load("drug_interactions.csv")
    require(patients.patient_id.is_unique, "Duplicate patient IDs")
    require(patients.patient_share_id.is_unique, "Duplicate patient share IDs")
    require(not drugs.duplicated(["patient_id", "drug_id"]).any(), "Duplicate prescriptions")
    require(set(drugs.drug_id) <= ids, "Prescription references unknown drug")
    require(set(drugs.patient_id) == set(patients.patient_id), "Prescription/patient coverage mismatch")
    require(set(interactions.patient_id) <= set(patients.patient_id), "Orphan interaction")
    require(set(interactions.drug_1) | set(interactions.drug_2) <= ids, "Unknown interaction drug")
    for frame in (drugs, interactions):
        shares = frame.patient_id.map(patients.set_index("patient_id").patient_share_id)
        require(shares.eq(frame.patient_share_id).all(), "Patient share ID mismatch")
    require(set(patients.highest_severity) <= set(RANK), "Unknown patient severity")
    require(set(interactions.severity) <= set(RANK) - {"None"}, "Unexpected interaction severity")
    drugs["disease_id"] = drugs.condition_treated.map(CONDITIONS)
    require(drugs.disease_id.notna().all() and drugs.disease_id.eq(drugs.drug_id.map(disease_by_id)).all(), "Prescription disease mismatch")
    require(drugs.is_active.astype(str).str.lower().eq("true").all(), "Inactive prescriptions require explicit label policy")
    patient_conditions = patients.conditions.map(lambda value: value.split("|"))
    require(all(set(values) <= set(CONDITIONS) for values in patient_conditions), "Unknown patient condition")
    require(patient_conditions.map(len).eq(patients.n_conditions).all(), "Incorrect patient condition count")
    condition_sets = dict(zip(patients.patient_id, patient_conditions.map(lambda values: {CONDITIONS[v] for v in values})))
    require(all(row.disease_id in condition_sets[row.patient_id] for row in drugs.itertuples()), "Prescription condition absent from patient")

    # Mirror the existing generator's max-severity conflict policy, documenting
    # every conflict. This is an audit convention, not clinical adjudication.
    pair_rules, conflicts = {}, []
    for row in rules.itertuples():
        if row.drug1_id not in ids or row.drug2_id not in ids:
            continue
        require(row.severity in RANK, "Unknown rule severity")
        pair = tuple(sorted((row.drug1_id, row.drug2_id)))
        require(pair[0] != pair[1], "Self-interaction rule")
        old = pair_rules.get(pair)
        if old and old != row.severity:
            conflicts.append({"drug_ids": pair, "ratings": [old, row.severity]})
        pair_rules[pair] = max((old or "None", row.severity), key=RANK.get)
    require(pair_rules, "No usable interaction rules")
    actual = {}
    for row in interactions.itertuples():
        key = (row.patient_id, *sorted((row.drug_1, row.drug_2)))
        require(key not in actual, "Duplicate patient interaction pair")
        actual[key] = row.severity
    expected, highest = {}, {}
    grouped = drugs.groupby("patient_id").drug_id.agg(list)
    for patient, medicines in grouped.items():
        worst = "None"
        for pair in itertools.combinations(sorted(medicines), 2):
            severity = pair_rules.get(pair, "None")
            if severity != "None":
                expected[(patient, *pair)] = severity
            worst = max((worst, severity), key=RANK.get)
        highest[patient] = worst
    require(expected == actual, "Saved interactions disagree with prescriptions/source rules; regenerate or review sources")
    require(patients.patient_id.map(highest).eq(patients.highest_severity).all(), "Patient target severity mismatch")
    require(patients.patient_id.map(grouped.map(len)).eq(patients.n_drugs).all(), "Patient drug counts disagree")

    features = patients[["patient_id", "age", "gender", "kidney_function", "liver_function", "bmi_category"]].copy()
    for disease in sorted(set(CONDITIONS.values())):
        features[f"condition__{disease}"] = patients.patient_id.map(lambda pid: int(disease in condition_sets[pid]))
    presence = pd.crosstab(drugs.patient_id, drugs.drug_id).reindex(columns=sorted(ids), fill_value=0)
    presence.columns = [f"drug__{name}" for name in presence.columns]
    features = features.merge(presence, left_on="patient_id", right_index=True, validate="one_to_one")
    labels = patients[["patient_id", "highest_severity"]].rename(columns={"highest_severity": "target_severity"})
    splits = split_patients(labels, seed)
    features["split"] = features.patient_id.map(splits)
    table = features.merge(labels, on="patient_id", validate="one_to_one")
    feature_names = [c for c in features if c not in {"patient_id", "split"}]
    split_report = {}
    for split in ("train", "validation", "test"):
        subset = table[table.split.eq(split)]
        split_report[split] = {"patients": len(subset), "labels": subset.target_severity.value_counts().to_dict()}
    train_counts = table[table.split.eq("train")].target_severity.value_counts()
    weights = {label: float(train_counts.sum() / (len(train_counts) * count)) for label, count in train_counts.items()}
    report = {
        "task": "synthetic_patient_worst_recorded_interaction_severity",
        "seed": seed, "source_sha256": inputs, "splits": split_report,
        "features": feature_names, "target": "target_severity", "train_class_weights": weights,
        "absent_target_classes": sorted(set(RANK) - set(labels.target_severity)),
        "source_rule_conflicts": conflicts, "drug_count": len(ids),
        "patient_count": len(patients), "prescription_count": len(drugs),
        "interaction_count": len(interactions),
        "limitations": [
            "Synthetic rule-derived labels, not measured clinical outcomes.",
            "None means no recorded interaction in the supplied rules, not proven safety.",
            "Same medicine combinations may occur in different patient splits; this does not test unseen-pair generalization.",
            "Do not train on IDs, split, interaction severity, highest_severity, or master warning/interaction text.",
            "Class weights computed on training only; absent classes cannot be learned.",
            "Conflicting source ratings use the original generator's maximum-severity policy and need domain review.",
        ],
    }
    # Write only after all input validations succeed.
    output.mkdir(parents=True, exist_ok=True)
    canonical.to_csv(output / "drug_catalog.csv", index=False)
    pd.concat(localized, ignore_index=True).to_csv(output / "master_localized.csv", index=False)
    table[["patient_id", "split"]].to_csv(output / "patient_splits.csv", index=False)
    for split in split_report:
        table[table.split.eq(split)].drop(columns="split").to_csv(output / f"{split}.csv", index=False)
    for name, frame in (("patient_drugs", drugs), ("patient_interactions", interactions)):
        frame = frame.drop(columns=[c for c in ("patient_share_id", "disclaimer") if c in frame])
        frame["split"] = frame.patient_id.map(splits)
        frame.to_csv(output / f"{name}.csv", index=False)
    report["output_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.glob("*.csv"))}
    (output / "manifest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("patient_count", "prescription_count", "interaction_count", "splits", "absent_target_classes", "source_rule_conflicts")}, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    prepare(args.source, args.output, args.seed)
