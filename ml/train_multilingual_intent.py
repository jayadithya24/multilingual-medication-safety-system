from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "datasets" / "ml_ready"
MODEL_DIR = PROJECT_ROOT / "ml" / "models"
MODEL_PATH = MODEL_DIR / "multilingual_intent_model.joblib"

TRAIN_PATH = DATA_DIR / "multilingual_train.csv"
VALIDATION_PATH = DATA_DIR / "multilingual_validation.csv"
TEST_PATH = DATA_DIR / "multilingual_test.csv"

REQUIRED_COLUMNS = {"language", "query", "medicine", "intent"}
LANGUAGES = ("en", "kn", "tulu")


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    dataset = pd.read_csv(path)
    missing_columns = REQUIRED_COLUMNS.difference(dataset.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{path.name} is missing required columns: {missing}")

    return dataset


def build_model() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(2, 5),
                    lowercase=True,
                    min_df=1,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def print_language_accuracies(
    test_df: pd.DataFrame, predictions: pd.Series | list[str]
) -> None:
    print("\nTest accuracy by language:")
    for language in LANGUAGES:
        language_mask = test_df["language"] == language
        if not language_mask.any():
            print(f"  {language}: no examples")
            continue

        language_accuracy = accuracy_score(
            test_df.loc[language_mask, "intent"],
            [prediction for prediction, keep in zip(predictions, language_mask) if keep],
        )
        language_count = int(language_mask.sum())
        print(f"  {language}: {language_accuracy:.4f} ({language_count} examples)")


def main() -> None:
    train_df = load_dataset(TRAIN_PATH)
    validation_df = load_dataset(VALIDATION_PATH)
    test_df = load_dataset(TEST_PATH)

    print("Dataset sizes:")
    print(f"  train: {len(train_df)}")
    print(f"  validation: {len(validation_df)}")
    print(f"  test: {len(test_df)}")

    model = build_model()
    model.fit(train_df["query"], train_df["intent"])

    validation_predictions = model.predict(validation_df["query"])
    validation_accuracy = accuracy_score(
        validation_df["intent"], validation_predictions
    )
    print(f"\nValidation accuracy: {validation_accuracy:.4f}")

    test_predictions = model.predict(test_df["query"])
    test_accuracy = accuracy_score(test_df["intent"], test_predictions)
    print(f"Overall test accuracy: {test_accuracy:.4f}")

    print("\nClassification report:")
    print(classification_report(test_df["intent"], test_predictions, digits=4))

    print_language_accuracies(test_df, test_predictions)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nSaved model to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
