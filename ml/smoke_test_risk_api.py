from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.routes.risk_prediction import router


PROFILES = [
    {
        "age": 62,
        "gender": "Female",
        "conditions": "Hypertension",
        "kidney_function": "Mild Impairment",
        "liver_function": "Normal",
        "bmi_category": "Normal",
        "n_drugs": 3,
        "drug_1": "ibuprofen",
        "drug_2": "methotrexate",
    },
    {
        "age": 75,
        "gender": "Male",
        "conditions": "Diabetes",
        "kidney_function": "Moderate Impairment",
        "liver_function": "Normal",
        "bmi_category": "Overweight",
        "n_drugs": 2,
        "drug_1": "atenolol",
        "drug_2": "clonidine",
    },
    {
        "age": 83,
        "gender": "Female",
        "conditions": "Diabetes",
        "kidney_function": "Mild Impairment",
        "liver_function": "Impaired",
        "bmi_category": "Normal",
        "n_drugs": 2,
        "drug_1": "naproxen",
        "drug_2": "methotrexate",
    },
    {
        "age": 58,
        "gender": "Male",
        "conditions": "Hypertension",
        "kidney_function": "Normal",
        "liver_function": "Normal",
        "bmi_category": "Obese",
        "n_drugs": 4,
        "drug_1": "diclofenac",
        "drug_2": "methotrexate",
    },
    {
        "age": 49,
        "gender": "Female",
        "conditions": "Arthritis",
        "kidney_function": "Normal",
        "liver_function": "Impaired",
        "bmi_category": "Underweight",
        "n_drugs": 5,
        "drug_1": "telmisartan",
        "drug_2": "ramipril",
    },
]


def assert_valid_response(body: dict) -> None:
    probabilities = body["probabilities"]
    probability_sum = sum(probabilities.values())
    highest_probability_class = max(probabilities, key=probabilities.get)

    assert body["risk_level"] in {"Mild", "Moderate", "Severe"}
    assert 0 <= body["confidence"] <= 1
    assert set(probabilities) == {"Mild", "Moderate", "Severe"}
    assert abs(probability_sum - 1.0) <= 0.001
    assert all(0 <= probability <= 1 for probability in probabilities.values())
    assert body["risk_level"] == highest_probability_class


def main() -> None:
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    for index, profile in enumerate(PROFILES, start=1):
        response = client.post("/ml/risk-predict", json=profile)
        assert response.status_code == 200, response.text

        body = response.json()
        assert_valid_response(body)

        probability_sum = sum(body["probabilities"].values())
        print(
            "case {index}: status={status} risk={risk} "
            "confidence={confidence} probability_sum={probability_sum:.6f}".format(
                index=index,
                status=response.status_code,
                risk=body["risk_level"],
                confidence=body["confidence"],
                probability_sum=probability_sum,
            )
        )

    print("All risk API smoke profiles passed.")

    invalid_cases = [
        ("missing age", {key: value for key, value in PROFILES[0].items() if key != "age"}),
        ("invalid age", {**PROFILES[0], "age": -1}),
        ("invalid n_drugs", {**PROFILES[0], "n_drugs": 0}),
        ("missing drug_1", {key: value for key, value in PROFILES[0].items() if key != "drug_1"}),
        ("missing drug_2", {key: value for key, value in PROFILES[0].items() if key != "drug_2"}),
    ]

    for label, payload in invalid_cases:
        response = client.post("/ml/risk-predict", json=payload)
        assert response.status_code == 422, (label, response.status_code, response.text)
        print(f"invalid case passed: {label} -> {response.status_code}")

    print("Risk API invalid-input checks passed.")


if __name__ == "__main__":
    main()
