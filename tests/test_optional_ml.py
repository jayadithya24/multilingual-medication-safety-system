from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app


def test_unavailable_ml_does_not_disable_health_or_login_configuration():
    with patch.dict('sys.modules', {'backend.app.services.risk_prediction_service': None}):
        client = TestClient(app)
        assert client.get('/health').status_code == 200
        assert client.get('/auth/providers').status_code == 200
        assert client.get('/ml/model-info').status_code == 503
        response = client.post('/ml/risk-predict', json=dict(age=60, gender='Male', conditions='Hypertension',
            kidney_function='Normal', liver_function='Normal', bmi_category='Normal', n_drugs=2,
            drug_1='Ibuprofen', drug_2='Methotrexate'))
        assert response.status_code == 503
        assert 'reference-based interaction checker remains available' in response.json()['detail']
