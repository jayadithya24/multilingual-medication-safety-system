from neo4j.load_data import Neo4jLoader


def test_resolve_drug_id_falls_back_to_drug_name_slug():
    row = {"drug_name": "Metformin HCl"}

    assert Neo4jLoader.resolve_drug_id(row) == "metformin-hcl"


def test_resolve_drug_id_keeps_existing_drug_id():
    row = {"drug_id": "metformin", "drug_name": "Metformin"}

    assert Neo4jLoader.resolve_drug_id(row) == "metformin"
