"""Regression checks for reproducible English scope expansion."""
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sync_datasets", ROOT / "tools/datasets/sync_datasets.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_builder_reproduces_master_and_compatibility_copies(tmp_path):
    builder.validate(allow_incomplete=True)
    expected = (ROOT / "datasets/english_master_dataset.csv").read_bytes()
    for path in ("english_master_dataset.csv", "backend/app/datasets/english_master_dataset.csv"):
        assert (ROOT / path).read_bytes() == expected


def test_invalid_records_do_not_overwrite_output(tmp_path):
    import shutil
    for language in builder.LANGUAGES:
        name = f'{language}_master_dataset.csv'
        shutil.copyfile(ROOT / 'datasets' / name, tmp_path / name)
    path = tmp_path / 'english_master_dataset.csv'
    rows = pd.read_csv(path)
    rows.loc[1, 'drug_id'] = rows.loc[0, 'drug_id']
    rows.to_csv(path, index=False)
    before = path.read_bytes()
    with pytest.raises(ValueError, match="duplicate"):
        builder.validate(tmp_path)
    assert path.read_bytes() == before


def test_default_validation_blocks_unreviewed_missing_classes():
    with pytest.raises(ValueError, match="missing required drug_class for 11 medicines"):
        builder.validate()


def test_derived_tables_cover_expanded_scope():
    master = pd.read_csv(ROOT / "datasets/english_master_dataset.csv")
    diseases = pd.read_csv(ROOT / "datasets/drug_disease.csv")
    effects = pd.read_csv(ROOT / "datasets/drug_sideeffects.csv")
    assert len(master) == 100 and master.disease.nunique() == 10
    assert set(diseases.drug_name) == set(master.drug_name)
    assert set(effects.drug_id) == set(diseases.drug_id)
    interactions = pd.read_csv(ROOT / "datasets/drug_interactions.csv")
    assert interactions.drug2_in_scope.eq("yes").equals(interactions.drug2_id.isin(diseases.drug_id))


def test_generic_replacement_text_does_not_invent_named_interactions():
    from backend.app.services.interaction_service import get_interaction
    result = get_interaction("Ciprofloxacin", "Tizanidine")
    assert result is None
    assert get_interaction("Pantoprazole", "Omeprazole") is None


def test_new_medicines_are_available_through_english_api():
    from backend.app.services.medicine_service import search_medicine, list_medicine_names
    assert len(list_medicine_names("en")) == 100
    assert search_medicine("Ringer's Lactate")["drug_name"] == "Ringer's Lactate"


def test_every_english_disease_and_medicine_is_available_in_protocols():
    from backend.app.routes.neo4j import disease_list, disease_drugs
    from backend.app.services.medicine_service import search_medicine
    master = pd.read_csv(ROOT / "datasets/english_master_dataset.csv")
    assert set(disease_list("en")["diseases"]) == set(master.disease)
    for disease, rows in master.groupby("disease"):
        actual = disease_drugs(disease)["drugs"]
        assert {row["drug_name"] for row in actual} == set(rows.drug_name)
        for name in rows.drug_name:
            assert search_medicine(name, "en")["disease"] == disease


def test_graph_uses_one_consistent_id_per_medicine():
    from neo4j.load_data import Neo4jLoader
    graph = Neo4jLoader.prepare_graph()
    medicines = [node for node in graph["nodes"] if node["type"] == "drug"]
    assert len(medicines) == 100
    ringer = next(node for node in medicines if node["name"] == "Ringer's Lactate")
    assert ringer["node_id"] == "ringer-s-lactate"
    assert Neo4jLoader.resolve_drug_id({"drug_name": "Ringer's Lactate"}) == "ringer-s-lactate"
    assert any(edge["source"] == ringer["node_id"] and edge["relationship"] == "TREATS" for edge in graph["edges"])
