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

TRAIN_PATH = DATA_DIR / "multilingual_natural_train.csv"
VALIDATION_PATH = DATA_DIR / "multilingual_natural_validation.csv"
TEST_PATH = DATA_DIR / "multilingual_natural_test.csv"

MODEL_PATH = MODEL_DIR / "multilingual_intent_model_v2.joblib"


def load_dataset(path):
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    return pd.read_csv(path)


def build_model():
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


def main():

    train_df = load_dataset(TRAIN_PATH)
    validation_df = load_dataset(VALIDATION_PATH)
    test_df = load_dataset(TEST_PATH)

    print("Dataset sizes:")
    print(f"  train: {len(train_df)}")
    print(f"  validation: {len(validation_df)}")
    print(f"  test: {len(test_df)}")

    model = build_model()

    model.fit(
        train_df["query"],
        train_df["intent"]
    )

    validation_predictions = model.predict(
        validation_df["query"]
    )

    validation_accuracy = accuracy_score(
        validation_df["intent"],
        validation_predictions
    )

    print(
        f"\nValidation accuracy: "
        f"{validation_accuracy:.4f}"
    )

    test_predictions = model.predict(
        test_df["query"]
    )

    test_accuracy = accuracy_score(
        test_df["intent"],
        test_predictions
    )

    print(
        f"Test accuracy: "
        f"{test_accuracy:.4f}"
    )

    print("\nClassification report:")
    print(
        classification_report(
            test_df["intent"],
            test_predictions,
            digits=4
        )
    )

    print("\nTest accuracy by language:")

    for language in ["en", "kn", "tulu"]:

        mask = test_df["language"] == language

        if mask.sum() == 0:
            continue

        language_accuracy = accuracy_score(
            test_df.loc[mask, "intent"],
            test_predictions[mask]
        )

        print(
            f"  {language}: "
            f"{language_accuracy:.4f} "
            f"({mask.sum()} examples)"
        )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_PATH
    )

    print(
        f"\nSaved V2 model to: "
        f"{MODEL_PATH}"
    )


if __name__ == "__main__":
    main()