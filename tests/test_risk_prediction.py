from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.app.routes.risk_prediction import router
from backend.app.services.risk_prediction_service import predict_risk


VALID_PAYLOAD = {
    "age": 62,
    "gender": "Female",
    "conditions": "Hypertension|Arthritis",
    "kidney_function": "Mild Impairment",
    "liver_function": "Normal",
    "bmi_category": "Normal",
    "n_drugs": 3,
    "drug_1": "ibuprofen",
    "drug_2": "methotrexate",
}


def _assert_valid_prediction(result):
    assert result["risk_level"] in {"Mild", "Moderate", "Severe"}
    assert 0 <= result["confidence"] <= 1
    assert set(result["probabilities"]) == {"Mild", "Moderate", "Severe"}

    probability_sum = sum(result["probabilities"].values())
    assert probability_sum == pytest.approx(1.0, abs=0.001)

    for probability in result["probabilities"].values():
        assert 0 <= probability <= 1

    highest_probability_class = max(
        result["probabilities"],
        key=result["probabilities"].get,
    )
    assert result["risk_level"] == highest_probability_class


def test_predict_risk_output_structure_and_probabilities():
    result = predict_risk(**VALID_PAYLOAD)
    _assert_valid_prediction(result)


def test_risk_prediction_api_response():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.post("/ml/risk-predict", json=VALID_PAYLOAD)

    assert response.status_code == 200
    _assert_valid_prediction(response.json())


def test_risk_prediction_api_rejects_invalid_numeric_values():
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.post(
        "/ml/risk-predict",
        json={
            **VALID_PAYLOAD,
            "age": -1,
            "n_drugs": 0,
        },
    )

    assert response.status_code == 422
