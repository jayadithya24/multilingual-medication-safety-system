from pathlib import Path
import joblib
import pandas as pd
from backend.app.services.risk_contract import UnsupportedModelInput


# Project root:
# multilingual-medication-safety-system/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "risk_model.joblib"
PREPROCESSOR_PATH = PROJECT_ROOT / "ml" / "models" / "risk_preprocessor.joblib"


# Load model and preprocessor once when the service starts
model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)


def get_model_info():
    encoder = preprocessor.named_transformers_["categorical"]
    columns = next(columns for name, _, columns in preprocessor.transformers_ if name == "categorical")
    return {
        "algorithm": "Random Forest classifier",
        "trees": int(model.n_estimators),
        "preprocessing": "One-hot encoding of categorical fields; numeric age and medicine count passed through.",
        "training_data": "Synthetic patient and drug-pair records",
        "target": "Recorded Mild / Moderate / Severe interaction label",
        "categorical_options": {column: [str(value) for value in values]
                                for column, values in zip(columns, encoder.categories_)},
        "clinical_validation": False,
        "interpretation": "Research demonstration only. Labels depend on drug pairs in synthetic data; patient-specific clinical risk has not been validated. Model probability is not the probability of harm.",
    }


def _validate_drug_names(drug_1, drug_2):
    """Do not let handle_unknown='ignore' silently encode an unknown drug."""
    names = [str(drug_1).strip().lower(), str(drug_2).strip().lower()]
    if names[0] == names[1]:
        raise UnsupportedModelInput("Select two different medicines.")
    encoder = preprocessor.named_transformers_["categorical"]
    columns = next(columns for name, _, columns in preprocessor.transformers_ if name == "categorical")
    for field, value in zip(("drug_1", "drug_2"), names):
        supported = set(encoder.categories_[list(columns).index(field)])
        if value not in supported:
            raise UnsupportedModelInput(f"{field} is outside this model's training vocabulary. Updated catalog entries require model retraining.")
    return names


def _validate_prediction_output(prediction, probabilities):
    probability_map = {
        str(class_name): round(float(probability), 4)
        for class_name, probability in zip(
            model.classes_,
            probabilities,
        )
    }

    if str(prediction) not in probability_map:
        raise ValueError("Model returned a class that is not present in probabilities.")

    probability_sum = sum(probability_map.values())
    if not 0.999 <= probability_sum <= 1.001:
        raise ValueError("Model returned probabilities that do not sum to 1.")

    for class_name, probability in probability_map.items():
        if not 0 <= probability <= 1:
            raise ValueError(f"Invalid probability for {class_name}.")

    confidence = max(probability_map.values())
    if not 0 <= confidence <= 1:
        raise ValueError("Model returned an invalid confidence.")

    highest_probability_class = max(probability_map, key=probability_map.get)
    if str(prediction) != highest_probability_class:
        raise ValueError("Predicted risk does not match the highest probability class.")

    return probability_map, confidence


def predict_risk(
    age,
    gender,
    conditions,
    kidney_function,
    liver_function,
    bmi_category,
    n_drugs,
    drug_1,
    drug_2,
):
    drug_1, drug_2 = _validate_drug_names(drug_1, drug_2)
    categorical = {"gender": gender, "conditions": conditions, "kidney_function": kidney_function,
                   "liver_function": liver_function, "bmi_category": bmi_category}
    encoder = preprocessor.named_transformers_["categorical"]
    columns = next(columns for name, _, columns in preprocessor.transformers_ if name == "categorical")
    for column, values in zip(columns, encoder.categories_):
        if column in categorical and categorical[column] not in set(values):
            raise UnsupportedModelInput(f"{column} is outside this model's training vocabulary.")
    data = pd.DataFrame(
        [
            {
                "age": age,
                "gender": gender,
                "conditions": conditions,
                "kidney_function": kidney_function,
                "liver_function": liver_function,
                "bmi_category": bmi_category,
                "n_drugs": n_drugs,
                "drug_1": drug_1,
                "drug_2": drug_2,
            }
        ]
    )

    encoded_data = preprocessor.transform(data)

    prediction = model.predict(encoded_data)[0]

    probabilities = model.predict_proba(encoded_data)[0]

    probability_map, confidence = _validate_prediction_output(
        prediction,
        probabilities,
    )

    return {
        "risk_level": str(prediction),
        "confidence": confidence,
        "probabilities": probability_map,
        "prediction_task": "synthetic_recorded_drug_pair_severity",
        "personalized_risk_validated": False,
        "clinical_validation": False,
        "interpretation": "Experimental classification of synthetic interaction labels. Patient-specific risk and unseen-pair generalization have not been established. Confidence is a model class probability, not a probability of clinical harm.",
    }
