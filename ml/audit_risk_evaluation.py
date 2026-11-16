"""Read-only evaluation: never replaces the deployed model or datasets."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import make_pipeline

from ml.validate_risk_model import (
    FEATURE_GROUPS, build_model, build_preprocessor, load_training_frame,
    analyze_drug_pair_severity, DATASETS_DIR,
)


def canonical_pairs(data):
    return data.apply(lambda row: " + ".join(sorted((row.drug_1, row.drug_2))), axis=1)


def evaluation_splits(data):
    indices = np.arange(len(data))
    train, test = train_test_split(indices, test_size=.2, random_state=42, stratify=data.severity)
    yield "random_rows", train, test
    for name, groups in (("unseen_patients", data.patient_id), ("unseen_pairs", canonical_pairs(data))):
        train, test = next(GroupShuffleSplit(n_splits=1, test_size=.2, random_state=42).split(data, groups=groups))
        yield name, train, test


def metrics(y, predictions, labels):
    return {
        "accuracy": float(accuracy_score(y, predictions)),
        "macro_f1": float(f1_score(y, predictions, labels=labels, average="macro", zero_division=0)),
        "per_class": classification_report(y, predictions, labels=labels, output_dict=True, zero_division=0),
    }


def run_audit():
    data = load_training_frame()
    labels = sorted(data.severity.unique().tolist())
    pair_analysis = analyze_drug_pair_severity(data)
    result = {
        "task": "synthetic_recorded_drug_pair_severity",
        "rows": len(data), "class_counts": data.severity.value_counts().to_dict(),
        "sources_sha256": {name: hashlib.sha256((DATASETS_DIR / name).read_bytes()).hexdigest()
                           for name in ("synthetic_patients.csv", "synthetic_patient_interactions.csv")},
        "pair_patterns": {key: value for key, value in pair_analysis.items() if isinstance(value, int)},
        "evaluations": {},
        "limitations": [
            "Synthetic rule-derived labels are not clinical outcomes.",
            "Grouped splits cannot establish personalization when labels depend only on drug identity.",
            "A single fixed-seed grouped holdout is exploratory, especially with few unique pairs.",
            "Absent training classes cannot be learned; absent test classes cannot be evaluated.",
            "These results apply only to the hashed source files, not automatically to an expanded catalog.",
        ],
    }
    for name, train_index, test_index in evaluation_splits(data):
        train, test = data.iloc[train_index], data.iloc[test_index]
        baseline = DummyClassifier(strategy="most_frequent").fit(train[["age"]], train.severity)
        predictions = baseline.predict(test[["age"]])
        summary = {
            "train_rows": len(train), "test_rows": len(test),
            "train_class_counts": train.severity.value_counts().to_dict(),
            "test_class_counts": test.severity.value_counts().to_dict(),
            "missing_train_classes": sorted(set(labels) - set(train.severity)),
            "missing_test_classes": sorted(set(labels) - set(test.severity)),
            "patient_overlap": len(set(train.patient_id) & set(test.patient_id)),
            "canonical_pair_overlap": len(set(canonical_pairs(train)) & set(canonical_pairs(test))),
            "majority_baseline": metrics(test.severity, predictions, labels),
            "models": {},
        }
        # An exact lookup abstains on pairs absent from training instead of inventing safety.
        lookup = train.assign(pair=canonical_pairs(train)).groupby("pair").severity.agg(lambda values: values.mode().iloc[0])
        mapped = canonical_pairs(test).map(lookup)
        covered = mapped.notna()
        summary["pair_lookup"] = {"coverage": float(covered.mean()), "covered_rows": int(covered.sum()),
            "covered_metrics": metrics(test.severity[covered], mapped[covered], labels) if covered.any() else None}
        for group, features in FEATURE_GROUPS.items():
            pipeline = make_pipeline(build_preprocessor(features), build_model())
            pipeline.fit(train[features], train.severity)
            summary["models"][group] = metrics(test.severity, pipeline.predict(test[features]), labels)
        result["evaluations"][name] = summary
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for name, summary in report["evaluations"].items():
        print(name, "baseline", round(summary["majority_baseline"]["accuracy"], 4),
              "model accuracy", {group: round(values["accuracy"], 4) for group, values in summary["models"].items()})


if __name__ == "__main__":
    main()
