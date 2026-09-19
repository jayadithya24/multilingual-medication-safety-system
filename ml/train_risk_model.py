import os
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder


# ---------------------------------------------------------
# 1. Load datasets
# ---------------------------------------------------------

patients = pd.read_csv("datasets/synthetic_patients.csv")
interactions = pd.read_csv("datasets/synthetic_patient_interactions.csv")


# ---------------------------------------------------------
# 2. Join patient information with interaction records
# ---------------------------------------------------------

patient_features = [
    "patient_id",
    "age",
    "gender",
    "conditions",
    "kidney_function",
    "liver_function",
    "bmi_category",
    "n_drugs",
]

data = interactions.merge(
    patients[patient_features],
    on="patient_id",
    how="inner",
)


# ---------------------------------------------------------
# 3. Select features and target
# ---------------------------------------------------------

features = [
    "age",
    "gender",
    "conditions",
    "kidney_function",
    "liver_function",
    "bmi_category",
    "n_drugs",
    "drug_1",
    "drug_2",
]

target = "severity"

X = data[features]
y = data[target]


# ---------------------------------------------------------
# 4. Define feature types
# ---------------------------------------------------------

numeric_features = [
    "age",
    "n_drugs",
]

categorical_features = [
    "gender",
    "conditions",
    "kidney_function",
    "liver_function",
    "bmi_category",
    "drug_1",
    "drug_2",
]


# ---------------------------------------------------------
# 5. Encode categorical features
# ---------------------------------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features,
        ),
    ],
    remainder="passthrough",
)


# ---------------------------------------------------------
# 6. Train/test split
# ---------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


# ---------------------------------------------------------
# 7. Transform the data
# ---------------------------------------------------------

X_train_encoded = preprocessor.fit_transform(X_train)
X_test_encoded = preprocessor.transform(X_test)


# ---------------------------------------------------------
# 8. Train Random Forest
# ---------------------------------------------------------

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1,
)

model.fit(X_train_encoded, y_train)


# ---------------------------------------------------------
# 9. Evaluate
# ---------------------------------------------------------

predictions = model.predict(X_test_encoded)

print("\n==============================")
print("ML RISK MODEL RESULTS")
print("==============================")

print(f"\nTraining rows: {len(X_train)}")
print(f"Testing rows:  {len(X_test)}")

print(f"\nAccuracy: {accuracy_score(y_test, predictions):.4f}")

print("\nClassification Report:")
print(classification_report(y_test, predictions))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))


# ---------------------------------------------------------
# 10. Save model + preprocessor
# ---------------------------------------------------------

os.makedirs("ml/models", exist_ok=True)

joblib.dump(
    model,
    "ml/models/risk_model.joblib",
)

joblib.dump(
    preprocessor,
    "ml/models/risk_preprocessor.joblib",
)

print("\nModel saved:")
print("ml/models/risk_model.joblib")
print("ml/models/risk_preprocessor.joblib")