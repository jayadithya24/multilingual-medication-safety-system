import pytest
from backend.app.services.medicine_service import _load_dataset, list_medicine_names, search_medicine
from backend.app.services.neo4j_service import search_drug_by_text
from backend.app.routes.neo4j import disease_list, disease_drugs


def test_disease_names_with_slashes_work_over_http():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from urllib.parse import quote
    from backend.app.routes.neo4j import router
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        for language in ('en', 'kn', 'tulu'):
            for disease in disease_list(language)['diseases']:
                response = client.get('/neo4j/diseases/' + quote(disease, safe='') + '/drugs', params={'lang': language})
                assert response.status_code == 200
                assert response.json()['drugs']


@pytest.mark.parametrize('language,drugs,diseases', [('en', 100, 10), ('kn', 100, 10), ('tulu', 100, 10)])
def test_published_language_scope(language, drugs, diseases):
    assert len(list_medicine_names(language)) == drugs
    assert _load_dataset(language).disease.nunique() == diseases
    assert len(disease_list(language)['diseases']) == diseases
    assert disease_list(language)['disease_count'] == diseases
    assert disease_list(language)['medicine_count'] == drugs
    for disease, rows in _load_dataset(language).groupby('disease'):
        result = disease_drugs(disease, language)
        assert {row['drug_name'] for row in result['drugs']} == set(rows.drug_name)


@pytest.mark.parametrize('language', ['kn', 'tulu'])
def test_every_localized_medicine_uses_its_supplied_translation(language):
    data = _load_dataset(language)
    assert set(data.drug_name) == set(_load_dataset('en').drug_name)
    for row in data.to_dict('records'):
        medicine = search_medicine(row['drug_name'], language)
        assert medicine['lang'] == language
        assert medicine['description'] == row['description']
        assert medicine['disease'] == row['disease']
        assert search_drug_by_text(row['drug_name'], lang=language)
