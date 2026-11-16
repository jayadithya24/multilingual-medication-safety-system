import importlib
from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


def test_unknown_medicine_is_rejected_and_prediction_explains_its_scope():
    # Exercise the API contract without deserializing/versioning the production model.
    encoder = ColumnTransformer([("categorical", OneHotEncoder(handle_unknown="ignore"), ["drug_1", "drug_2"])], remainder="drop")
    encoder.fit(pd.DataFrame({"drug_1": ["a", "b"], "drug_2": ["b", "a"]}))

    class Model:
        classes_ = np.array(["Mild", "Moderate", "Severe"])

        def predict(self, _):
            return np.array(["Severe"])

        def predict_proba(self, _):
            return np.array([[.1, .2, .7]])

    import sys
    names = ("backend.app.services.risk_prediction_service", "backend.app.routes.risk_prediction")
    previous = {name: sys.modules.pop(name, None) for name in names}
    try:
        with patch("joblib.load", side_effect=[Model(), encoder]):
            importlib.import_module(names[0])
            route = importlib.import_module(names[1])
        app = FastAPI()
        app.include_router(route.router)
        client = TestClient(app)
        payload = dict(age=68, gender="Male", conditions="Diabetes", kidney_function="Normal",
                       liver_function="Normal", bmi_category="Normal", n_drugs=2, drug_1=" A ", drug_2="b")
        response = client.post("/ml/risk-predict", json=payload)
        assert response.status_code == 200
        assert response.json()["personalized_risk_validated"] is False
        assert response.json()["clinical_validation"] is False
        assert "not a probability of clinical harm" in response.json()["interpretation"]
        assert client.post("/ml/risk-predict", json={**payload, "drug_2": "new-drug"}).status_code == 422
        assert client.post("/ml/risk-predict", json={**payload, "drug_2": "a"}).status_code == 422
        with patch.object(route, "predict_risk", side_effect=ValueError("internal model detail")):
            failed = client.post("/ml/risk-predict", json=payload)
        assert failed.status_code == 500
        assert "internal model detail" not in failed.text
    finally:
        for name in names:
            sys.modules.pop(name, None)
            if previous[name] is not None:
                sys.modules[name] = previous[name]
