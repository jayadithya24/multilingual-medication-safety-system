"""Regression checks for reproducible English scope expansion."""
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_english", ROOT / "datasets/build_dataset.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def test_builder_reproduces_master_and_compatibility_copies(tmp_path):
    output = tmp_path / "english.csv"
    builder.main(dst=output)
    expected = (ROOT / "datasets/english_master_dataset.csv").read_bytes()
    assert output.read_bytes() == expected
    builder.main(dst=output)
    assert output.read_bytes() == expected
    for path in ("english_master_dataset.csv", "backend/app/datasets/english_master_dataset.csv"):
        assert (ROOT / path).read_bytes() == expected


def test_invalid_records_do_not_overwrite_output(tmp_path):
    source, target = tmp_path / "source.json", tmp_path / "out.csv"
    rows = json.loads((ROOT / "datasets/english_master_records.json").read_text(encoding="utf-8"))
    source.write_text(json.dumps(rows + [rows[0]]), encoding="utf-8")
    target.write_text("keep me", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate medicine"):
        builder.main(source, target)
    assert target.read_text() == "keep me"


def test_derived_tables_cover_expanded_scope():
    master = pd.read_csv(ROOT / "datasets/english_master_dataset.csv")
    diseases = pd.read_csv(ROOT / "datasets/drug_disease.csv")
    effects = pd.read_csv(ROOT / "datasets/drug_sideeffects.csv")
    assert len(master) == 100 and master.disease.nunique() == 10
    assert set(diseases.drug_name) == set(master.drug_name)
    assert set(effects.drug_id) == set(diseases.drug_id)
    interactions = pd.read_csv(ROOT / "datasets/drug_interactions.csv")
    assert interactions.drug2_in_scope.eq("yes").equals(interactions.drug2_id.isin(diseases.drug_id))


def test_new_named_interactions_are_ungraded_and_comparisons_are_excluded():
    from backend.app.services.interaction_service import get_interaction
    result = get_interaction("Ciprofloxacin", "Tizanidine")
    assert result["review_required"]
    assert result["source_severities"] == ["Unknown"]
    assert "must not be combined" in result["description"].lower() or "dangerously" in result["description"].lower()
    assert get_interaction("Pantoprazole", "Omeprazole") is None


def test_new_medicines_are_available_through_english_api():
    from backend.app.services.medicine_service import search_medicine, list_medicine_names
    assert len(list_medicine_names("en")) == 100
    assert search_medicine("Ringer's Lactate")["drug_name"] == "Ringer's Lactate"


def test_graph_uses_one_consistent_id_per_medicine():
    from neo4j.load_data import Neo4jLoader
    graph = Neo4jLoader.prepare_graph()
    medicines = [node for node in graph["nodes"] if node["type"] == "drug"]
    assert len(medicines) == 100
    ringer = next(node for node in medicines if node["name"] == "Ringer's Lactate")
    assert ringer["node_id"] == "ringer-s-lactate"
    assert Neo4jLoader.resolve_drug_id({"drug_name": "Ringer's Lactate"}) == "ringer-s-lactate"
    assert any(edge["source"] == ringer["node_id"] and edge["relationship"] == "TREATS" for edge in graph["edges"])
