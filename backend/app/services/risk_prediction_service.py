from pathlib import Path
import joblib
import pandas as pd


# Project root:
# multilingual-medication-safety-system/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "risk_model.joblib"
PREPROCESSOR_PATH = PROJECT_ROOT / "ml" / "models" / "risk_preprocessor.joblib"


# Load model and preprocessor once when the service starts
model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)


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
    }
