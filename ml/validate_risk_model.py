from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = PROJECT_ROOT / "datasets"
MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "risk_model.joblib"
PREPROCESSOR_PATH = PROJECT_ROOT / "ml" / "models" / "risk_preprocessor.joblib"

RANDOM_STATE = 42
TEST_SIZE = 0.20

PATIENT_FEATURES = [
    "patient_id",
    "age",
    "gender",
    "conditions",
    "kidney_function",
    "liver_function",
    "bmi_category",
    "n_drugs",
]

FEATURE_GROUPS = {
    "drug_pair_only": ["drug_1", "drug_2"],
    "patient_features_only": [
        "age",
        "gender",
        "conditions",
        "kidney_function",
        "liver_function",
        "bmi_category",
        "n_drugs",
    ],
    "full_feature_model": [
        "age",
        "gender",
        "conditions",
        "kidney_function",
        "liver_function",
        "bmi_category",
        "n_drugs",
        "drug_1",
        "drug_2",
    ],
}


def load_training_frame() -> pd.DataFrame:
    patients = pd.read_csv(DATASETS_DIR / "synthetic_patients.csv")
    interactions = pd.read_csv(DATASETS_DIR / "synthetic_patient_interactions.csv")

    return interactions.merge(
        patients[PATIENT_FEATURES],
        on="patient_id",
        how="inner",
    )


def build_preprocessor(features: list[str]) -> ColumnTransformer:
    categorical_features = [
        feature
        for feature in features
        if feature
        in {
            "gender",
            "conditions",
            "kidney_function",
            "liver_function",
            "bmi_category",
            "drug_1",
            "drug_2",
        }
    ]

    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
        ],
        remainder="passthrough",
    )


def build_model() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_STATE,
        class_weight="balanced",
        n_jobs=-1,
    )


def evaluate_feature_group(data: pd.DataFrame, name: str, features: list[str]) -> dict:
    x = data[features]
    y = data["severity"]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    preprocessor = build_preprocessor(features)
    model = build_model()

    x_train_encoded = preprocessor.fit_transform(x_train)
    x_test_encoded = preprocessor.transform(x_test)
    model.fit(x_train_encoded, y_train)

    predictions = model.predict(x_test_encoded)
    labels = sorted(y.unique())

    return {
        "name": name,
        "features": features,
        "training_rows": len(x_train),
        "testing_rows": len(x_test),
        "accuracy": accuracy_score(y_test, predictions),
        "precision_weighted": precision_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        ),
        "recall_weighted": recall_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        ),
        "f1_weighted": f1_score(
            y_test,
            predictions,
            average="weighted",
            zero_division=0,
        ),
        "labels": labels,
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=labels),
    }


def run_cross_validation(data: pd.DataFrame, features: list[str]) -> dict:
    x = data[features]
    y = data["severity"]

    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(features)),
            ("model", build_model()),
        ]
    )

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    scores = cross_validate(
        pipeline,
        x,
        y,
        cv=cv,
        scoring={
            "accuracy": "accuracy",
            "precision_weighted": "precision_weighted",
            "recall_weighted": "recall_weighted",
            "f1_weighted": "f1_weighted",
        },
        n_jobs=-1,
    )

    return {
        metric.replace("test_", ""): (
            scores[metric].mean(),
            scores[metric].std(),
        )
        for metric in scores
        if metric.startswith("test_")
    }


def analyze_drug_pair_severity(data: pd.DataFrame) -> dict:
    pair_counts = (
        data.groupby(["drug_1", "drug_2", "severity"]).size().reset_index(name="rows")
    )
    severity_per_pair = data.groupby(["drug_1", "drug_2"])["severity"].nunique()
    repeated_pairs = data.groupby(["drug_1", "drug_2"]).size().sort_values(ascending=False)

    canonical_data = data.copy()
    canonical_data["canonical_pair"] = canonical_data.apply(
        lambda row: " + ".join(sorted([row["drug_1"], row["drug_2"]])),
        axis=1,
    )
    severity_per_canonical_pair = canonical_data.groupby("canonical_pair")[
        "severity"
    ].nunique()

    return {
        "directed_pair_count": len(severity_per_pair),
        "directed_pairs_with_one_severity": int((severity_per_pair == 1).sum()),
        "directed_pairs_with_multiple_severities": int((severity_per_pair > 1).sum()),
        "canonical_pair_count": len(severity_per_canonical_pair),
        "canonical_pairs_with_one_severity": int(
            (severity_per_canonical_pair == 1).sum()
        ),
        "canonical_pairs_with_multiple_severities": int(
            (severity_per_canonical_pair > 1).sum()
        ),
        "most_repeated_pairs": repeated_pairs.head(10),
        "pair_severity_rows": pair_counts.sort_values("rows", ascending=False).head(10),
    }


def validate_saved_artifacts(sample: pd.DataFrame) -> dict:
    model = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)

    encoded_sample = preprocessor.transform(sample)
    prediction = model.predict(encoded_sample)[0]
    probabilities = model.predict_proba(encoded_sample)[0]

    probability_map = {
        class_name: float(probability)
        for class_name, probability in zip(model.classes_, probabilities)
    }

    return {
        "prediction": prediction,
        "probabilities": probability_map,
        "probability_sum": float(probabilities.sum()),
        "highest_probability_class": max(probability_map, key=probability_map.get),
    }


def print_feature_result(result: dict) -> None:
    print(f"\n{result['name']}")
    print("-" * len(result["name"]))
    print(f"Features: {', '.join(result['features'])}")
    print(f"Training rows: {result['training_rows']}")
    print(f"Testing rows:  {result['testing_rows']}")
    print(f"Accuracy:  {result['accuracy']:.4f}")
    print(f"Precision: {result['precision_weighted']:.4f} (weighted)")
    print(f"Recall:    {result['recall_weighted']:.4f} (weighted)")
    print(f"F1-score:  {result['f1_weighted']:.4f} (weighted)")
    print("Labels:", ", ".join(result["labels"]))
    print("Confusion matrix:")
    print(result["confusion_matrix"])


def main() -> None:
    data = load_training_frame()
    print("Patient-risk ML validation")
    print("==========================")
    print(f"Rows: {len(data)}")
    print("Target distribution:")
    print(data["severity"].value_counts().to_string())

    results = [
        evaluate_feature_group(data, name, features)
        for name, features in FEATURE_GROUPS.items()
    ]

    for result in results:
        print_feature_result(result)

    print("\nStratified 5-fold cross-validation: full feature model")
    print("------------------------------------------------------")
    cv_results = run_cross_validation(data, FEATURE_GROUPS["full_feature_model"])
    for metric, (mean, std) in cv_results.items():
        print(f"{metric}: mean={mean:.4f}, std={std:.4f}")

    print("\nDrug-pair severity pattern check")
    print("--------------------------------")
    pair_analysis = analyze_drug_pair_severity(data)
    print(
        "Directed pairs with one severity: "
        f"{pair_analysis['directed_pairs_with_one_severity']} / "
        f"{pair_analysis['directed_pair_count']}"
    )
    print(
        "Canonical pairs with one severity: "
        f"{pair_analysis['canonical_pairs_with_one_severity']} / "
        f"{pair_analysis['canonical_pair_count']}"
    )
    print("Most repeated directed pairs:")
    print(pair_analysis["most_repeated_pairs"].to_string())
    print("Most repeated directed pair/severity rows:")
    print(pair_analysis["pair_severity_rows"].to_string(index=False))

    print("\nSaved artifact smoke test")
    print("-------------------------")
    sample = data[FEATURE_GROUPS["full_feature_model"]].head(1)
    artifact_result = validate_saved_artifacts(sample)
    print(f"Prediction: {artifact_result['prediction']}")
    print(f"Probabilities: {artifact_result['probabilities']}")
    print(f"Probability sum: {artifact_result['probability_sum']:.6f}")
    print(
        "Highest probability class: "
        f"{artifact_result['highest_probability_class']}"
    )

    drug_pair_accuracy = next(
        result["accuracy"] for result in results if result["name"] == "drug_pair_only"
    )
    full_accuracy = next(
        result["accuracy"] for result in results if result["name"] == "full_feature_model"
    )

    print("\nInterpretation")
    print("--------------")
    print(
        "Drug pairs are a dominant signal when the drug-pair-only model is close "
        "to the full model and repeated pairs carry a single severity."
    )
    print(f"Drug-pair-only accuracy: {drug_pair_accuracy:.4f}")
    print(f"Full-model accuracy:     {full_accuracy:.4f}")
    print(
        "Do not present this as clinical validation. The data is synthetic and "
        "the same drug pairs repeatedly map to the same severity, so the high "
        "score should be reported only as internal synthetic-dataset performance "
        "with leakage/simplification limitations."
    )


if __name__ == "__main__":
    main()
